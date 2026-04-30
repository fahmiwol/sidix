"""
semantic_cache.py — Phase B Semantic Cache Layer (Vol 20b)
==========================================================================

Pasangan dari `response_cache.py` (Phase A exact LRU+TTL).

Arsitektur 2-tier dari riset 2025-2026 (note 233):
  L1 exact (existing response_cache.py)
    └─ MISS → L2 semantic (this module)
        └─ MISS → run_react()

Berdasarkan synthesis 18 paper/blog 2025-2026 (Spheron, Preto.ai, n1n.ai,
Bifrost, Provara, TokenMix, Brightlume, Azure, Maxim, dll). Ringkas:

- **Embedding-agnostic**: inject `embed_fn` saat deploy. Default = None →
  semua lookup return None (graceful disable, safe untuk environment yang
  belum punya embedding model loaded).
- **Per-domain threshold**: fiqh/medis 0.96, factual 0.92, casual 0.88.
  Default KONSERVATIF (mulai 0.95) — better skip than wrong-answer.
- **Per-domain TTL**: factual 72h, current_events 24h (atau skip),
  fiqh 7 hari (immutable knowledge), casual 12h.
- **Per-bucket storage**: key = `persona:lora_version:system_prompt_hash`.
  Mencegah cross-persona contamination + auto-invalidate kalau LoRA
  retrain (growth loop).
- **Eligibility skip**: temperature>0.1, multi-turn>3, current events
  keyword, personal regex (email/phone/saya punya), <8 char, output
  yang [SPEKULASI]/[TIDAK TAHU].
- **Metrics**: hits/misses/scores histogram (Prometheus-ready).

Anti-pattern yang dihindari (per failure mode catalog):
- ❌ Cross-persona contamination → per-persona bucket wajib
- ❌ Cache stampede → not yet, defer ke Phase C kalau >100 RPS
- ❌ PII leak → personal regex skip + per-persona scoping
- ❌ Cache "saya tidak tahu" answers → caller harus filter sebelum store
- ❌ Threshold tuning blind → similarity score histogram metric

Reference riset:
- Spheron 2026 GPTCache + Redis Vector + Prompt Cache Setup (per-domain threshold)
- Preto.ai Architecture & Real-World Hit Rates (BGE-M3 @ 512 MRL recommendation)
- n1n.ai Production Guide (numpy + DB mirror pattern, MiniLM fallback)
- Provara Issue #120 (konservatif 0.97, brute-force ≤10K)
- TokenMix L1+L2 architecture (exact-first cost saving)
- Bifrost Multi-Tenant (per-tenant scoping, conversation_history_threshold)
- Redis DEV semantic-cache-eligibility (skip rules taxonomy)

Vol 20b ship: module + wiring stub + test. Deploy step (BGE-M3 / MiniLM
loader) di Vol 20c saat user pilih embedding model.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


# ── Per-domain config (best practice 2025-2026) ───────────────────────────────

# Threshold cosine similarity per domain.
# Konservatif default — start tinggi, tune turun setelah false-positive
# rate diukur (target <1%).
THRESHOLDS_PER_DOMAIN: dict[str, float] = {
    "fiqh":           0.96,  # klaim hukum/spiritual, skip-rather-than-mismatch
    "medis":          0.96,
    "data":           0.95,  # statistik/angka
    "coding":         0.92,
    "factual":        0.92,
    "casual":         0.88,  # chat AYMAN/UTZ vibe, drift OK
    "current_events": 0.99,  # effectively skip (also TTL=0)
    "default":        0.95,
}

# TTL per domain (detik). 0 = SKIP cache entirely.
TTL_PER_DOMAIN: dict[str, int] = {
    "fiqh":           7 * 86400,    # immutable knowledge, 7 hari
    "medis":          7 * 86400,
    "data":           24 * 3600,    # 1 hari
    "coding":         24 * 3600,
    "factual":        72 * 3600,    # 3 hari
    "casual":         12 * 3600,    # 12 jam
    "current_events": 0,            # SKIP
    "default":        24 * 3600,
}

# Per-bucket cap. 5 persona × 10K = 50K total max.
MAX_ENTRIES_PER_BUCKET: int = 10_000

# Eligibility regex.
_PERSONAL_RE = re.compile(
    r"\b(saya punya|aku punya|email saya|nomor saya|nomor hp saya|"
    r"my email|my phone|my address|@[\w.-]+\.\w+|"
    r"\+?\d{10,15})\b",
    re.I,
)
_CURRENT_EVENTS_RE = re.compile(
    r"\b(hari ini|kemarin|sekarang|today|yesterday|now|"
    r"berita|trending|live|terkini|harga.*sekarang|"
    r"jam berapa|tanggal berapa)\b",
    re.I,
)
_LOW_CONFIDENCE_LABELS = ("[SPEKULASI]", "[TIDAK TAHU]", "[UNKNOWN]")


# ── Data ──────────────────────────────────────────────────────────────────────

@dataclass
class SemanticCacheEntry:
    """1 cache entry. embedding L2-normalized float32."""
    embedding: Any  # np.ndarray (D,) float32 normalized
    response: dict
    domain: str
    created_at: float
    last_hit_at: float
    hit_count: int = 0
    query_preview: str = ""  # first 64 char untuk debug


@dataclass
class SemanticCacheMetrics:
    """In-memory metrics (Prometheus-shape ready)."""
    hits: int = 0
    misses: int = 0
    skipped_ineligible: int = 0
    score_buckets: dict[str, int] = field(
        default_factory=lambda: {
            "0.80-0.85": 0, "0.85-0.88": 0, "0.88-0.90": 0,
            "0.90-0.92": 0, "0.92-0.94": 0, "0.94-0.96": 0,
            "0.96-0.98": 0, "0.98-1.00": 0,
        }
    )
    last_hit_score: float = 0.0
    total_lookup_ms: float = 0.0
    lookup_count: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total else 0.0

    @property
    def avg_lookup_ms(self) -> float:
        return (self.total_lookup_ms / self.lookup_count) if self.lookup_count else 0.0

    def record_score(self, score: float) -> None:
        for bucket, lo_hi in (
            ("0.80-0.85", (0.80, 0.85)),
            ("0.85-0.88", (0.85, 0.88)),
            ("0.88-0.90", (0.88, 0.90)),
            ("0.90-0.92", (0.90, 0.92)),
            ("0.92-0.94", (0.92, 0.94)),
            ("0.94-0.96", (0.94, 0.96)),
            ("0.96-0.98", (0.96, 0.98)),
            ("0.98-1.00", (0.98, 1.001)),
        ):
            if lo_hi[0] <= score < lo_hi[1]:
                self.score_buckets[bucket] += 1
                return

    def snapshot(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "skipped_ineligible": self.skipped_ineligible,
            "hit_rate": round(self.hit_rate, 3),
            "score_histogram": dict(self.score_buckets),
            "last_hit_score": round(self.last_hit_score, 3),
            "avg_lookup_ms": round(self.avg_lookup_ms, 2),
            "lookup_count": self.lookup_count,
        }


# ── Eligibility check ─────────────────────────────────────────────────────────

def is_eligible(
    query: str,
    *,
    domain: str = "default",
    msg_history_len: int = 0,
    temperature: float = 0.0,
    output: str = "",
) -> tuple[bool, str]:
    """
    Decide apakah query+domain cocok di-semantic-cache.

    Returns (eligible, reason). reason kosong kalau eligible.
    """
    if not query or len(query.strip()) < 8:
        return False, "too short (<8 char)"

    if temperature > 0.1:
        return False, "non-deterministic (temperature>0.1)"

    if msg_history_len > 3:
        return False, f"multi-turn ({msg_history_len} messages > 3)"

    if domain == "current_events":
        return False, "current_events domain (TTL=0)"

    if TTL_PER_DOMAIN.get(domain, 0) == 0:
        return False, f"domain '{domain}' TTL=0"

    if _CURRENT_EVENTS_RE.search(query):
        return False, "current events keyword detected"

    if _PERSONAL_RE.search(query):
        return False, "personal/PII content detected"

    # Output filter: jangan cache jawaban low-confidence
    if output:
        for label in _LOW_CONFIDENCE_LABELS:
            if label in output:
                return False, f"output contains {label}"

    return True, ""


# ── Main store ────────────────────────────────────────────────────────────────

class SemanticCache:
    """
    Embedding-agnostic semantic cache. Thread-safe. In-memory + LRU + TTL.

    Inject `embed_fn(text: str) -> np.ndarray` saat construct atau via
    `set_embed_fn()`. Kalau embed_fn=None, semua lookup/store return None
    (graceful disable, safe sebelum embedding model loaded).
    """

    def __init__(
        self,
        embed_fn: Optional[Callable[[str], Any]] = None,
        max_entries_per_bucket: int = MAX_ENTRIES_PER_BUCKET,
    ):
        self._embed_fn = embed_fn
        self._max_entries = max_entries_per_bucket
        # bucket_key → OrderedDict[entry_id → SemanticCacheEntry]
        self._store: dict[str, OrderedDict[str, SemanticCacheEntry]] = {}
        self._lock = Lock()
        self._metrics = SemanticCacheMetrics()

    def set_embed_fn(self, fn: Optional[Callable[[str], Any]]) -> None:
        """Set/replace embedding function. Set None → disable semantic layer."""
        with self._lock:
            self._embed_fn = fn
            log.info("[semantic_cache] embed_fn %s", "set" if fn else "cleared")

    @property
    def enabled(self) -> bool:
        return self._embed_fn is not None

    @staticmethod
    def make_bucket_key(persona: str, lora_version: str, system_prompt: str) -> str:
        """Bucket key encoding persona + LoRA version + system prompt hash.

        Auto-invalidate saat:
        - persona berbeda (cross-persona contamination)
        - LoRA SIDIX retrain (growth loop) → new lora_version → new bucket
        - System prompt berubah (vol 14 LIBERATION pivot, dll)
        """
        h = hashlib.sha256((system_prompt or "").encode("utf-8")).hexdigest()[:12]
        return f"{persona or 'default'}:{lora_version or 'v0'}:{h}"

    @staticmethod
    def _entry_id(query: str) -> str:
        return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

    def _evict_if_needed(self, bucket: OrderedDict, now: float, ttl: int) -> int:
        """TTL purge + LRU cap. Return jumlah evict."""
        evicted = 0
        # 1. TTL purge
        expired = [k for k, e in bucket.items() if (now - e.created_at) > ttl]
        for k in expired:
            del bucket[k]
            evicted += 1
        # 2. LRU cap (oldest by insertion / move_to_end touch)
        while len(bucket) > self._max_entries:
            bucket.popitem(last=False)
            evicted += 1
        return evicted

    def lookup(
        self,
        *,
        query: str,
        persona: str,
        lora_version: str,
        system_prompt: str,
        domain: str = "default",
        msg_history_len: int = 0,
        temperature: float = 0.0,
    ) -> Optional[tuple[dict, float]]:
        """
        Returns (cached_response_dict, similarity_score) atau None.

        Graceful: kalau embed_fn=None atau ineligible atau bucket kosong
        atau best score < threshold → return None. Caller fall through ke
        LLM call.
        """
        if not self.enabled:
            return None

        eligible, reason = is_eligible(
            query, domain=domain,
            msg_history_len=msg_history_len, temperature=temperature,
        )
        if not eligible:
            with self._lock:
                self._metrics.skipped_ineligible += 1
            log.debug("[semantic_cache] skip lookup: %s", reason)
            return None

        threshold = THRESHOLDS_PER_DOMAIN.get(domain, THRESHOLDS_PER_DOMAIN["default"])
        ttl = TTL_PER_DOMAIN.get(domain, TTL_PER_DOMAIN["default"])
        bucket_key = self.make_bucket_key(persona, lora_version, system_prompt)

        t_start = time.time()
        try:
            q_emb = self._embed_fn(query)  # heavy op outside lock kalau possible
        except Exception as e:
            log.warning("[semantic_cache] embed_fn failed: %s", e)
            return None

        # Lazy import numpy (only needed kalau embed_fn returns ndarray)
        try:
            import numpy as np
        except ImportError:
            log.warning("[semantic_cache] numpy not available")
            return None

        with self._lock:
            bucket = self._store.get(bucket_key)
            if not bucket:
                self._metrics.misses += 1
                self._metrics.lookup_count += 1
                self._metrics.total_lookup_ms += (time.time() - t_start) * 1000
                return None

            now = time.time()
            best_score = -1.0
            best_id: Optional[str] = None
            stale_keys = []
            for k, entry in bucket.items():
                if (now - entry.created_at) > ttl:
                    stale_keys.append(k)
                    continue
                # Cosine = dot product (assuming both L2-normalized)
                try:
                    score = float(np.dot(q_emb, entry.embedding))
                except Exception:
                    continue
                if score > best_score:
                    best_score = score
                    best_id = k
            for k in stale_keys:
                del bucket[k]

            self._metrics.lookup_count += 1
            self._metrics.total_lookup_ms += (time.time() - t_start) * 1000

            if best_id is not None and best_score >= threshold:
                entry = bucket[best_id]
                entry.hit_count += 1
                entry.last_hit_at = now
                bucket.move_to_end(best_id, last=True)  # LRU touch
                self._metrics.hits += 1
                self._metrics.last_hit_score = best_score
                self._metrics.record_score(best_score)
                log.info(
                    "[semantic_cache] HIT bucket=%s score=%.3f threshold=%.2f",
                    bucket_key, best_score, threshold,
                )
                return (entry.response, best_score)

            self._metrics.misses += 1
            if best_score >= 0:
                self._metrics.record_score(best_score)  # near-miss observability
            return None

    def store(
        self,
        *,
        query: str,
        response: dict,
        persona: str,
        lora_version: str,
        system_prompt: str,
        domain: str = "default",
        output: str = "",
    ) -> bool:
        """
        Store response. Returns True kalau ke-cache, False kalau di-skip.

        Skip kalau:
        - embed_fn=None
        - TTL_PER_DOMAIN[domain] = 0 (current_events)
        - is_eligible() return False (PII/short/etc)
        - embed_fn raises
        """
        if not self.enabled:
            return False

        eligible, reason = is_eligible(
            query, domain=domain, msg_history_len=0,  # store-time, history tidak relevan
            temperature=0.0, output=output,
        )
        if not eligible:
            log.debug("[semantic_cache] skip store: %s", reason)
            return False

        ttl = TTL_PER_DOMAIN.get(domain, TTL_PER_DOMAIN["default"])
        if ttl == 0:
            return False

        try:
            q_emb = self._embed_fn(query)
        except Exception as e:
            log.warning("[semantic_cache] embed_fn failed at store: %s", e)
            return False

        bucket_key = self.make_bucket_key(persona, lora_version, system_prompt)
        entry_id = self._entry_id(query)
        now = time.time()
        entry = SemanticCacheEntry(
            embedding=q_emb,
            response=response,
            domain=domain,
            created_at=now,
            last_hit_at=now,
            query_preview=query[:64],
        )
        with self._lock:
            bucket = self._store.setdefault(bucket_key, OrderedDict())
            bucket[entry_id] = entry
            bucket.move_to_end(entry_id, last=True)
            self._evict_if_needed(bucket, now, ttl)
        return True

    def clear(self, persona: Optional[str] = None) -> int:
        """Clear all atau persona-specific. Return count cleared."""
        with self._lock:
            if persona is None:
                count = sum(len(b) for b in self._store.values())
                self._store.clear()
                return count
            count = 0
            for k in list(self._store.keys()):
                if k.startswith(f"{persona}:"):
                    count += len(self._store[k])
                    del self._store[k]
            return count

    def stats(self) -> dict:
        with self._lock:
            return {
                **self._metrics.snapshot(),
                "enabled": self.enabled,
                "buckets": len(self._store),
                "total_entries": sum(len(b) for b in self._store.values()),
                "max_entries_per_bucket": self._max_entries,
            }


# ── Global singleton ──────────────────────────────────────────────────────────

_semantic_cache_instance: Optional[SemanticCache] = None
_init_lock = Lock()


def get_semantic_cache() -> SemanticCache:
    """Lazy init global singleton. embed_fn perlu di-set via set_embed_fn()."""
    global _semantic_cache_instance
    if _semantic_cache_instance is None:
        with _init_lock:
            if _semantic_cache_instance is None:
                _semantic_cache_instance = SemanticCache()
    return _semantic_cache_instance


__all__ = [
    "SemanticCache",
    "SemanticCacheEntry",
    "SemanticCacheMetrics",
    "get_semantic_cache",
    "is_eligible",
    "THRESHOLDS_PER_DOMAIN",
    "TTL_PER_DOMAIN",
    "MAX_ENTRIES_PER_BUCKET",
]
