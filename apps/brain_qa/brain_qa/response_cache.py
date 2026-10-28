"""
response_cache.py — In-Memory LRU Cache untuk SIDIX (Best Practice)
========================================================================

Per Vol 19 priority: improve speed untuk common queries.

Phase A (this — vol 19): exact-match LRU dengan TTL.
- Hash (question + persona + mode) → cache_key
- TTL default 1 jam
- Max 500 entries (memory cap)
- Cache hit return <50ms (vs LLM 5-30s)

Phase B (Q3 2026): semantic cache via embedding similarity.
- Hash question → embedding (BGE-M3)
- Cosine similarity > 0.92 = cache hit
- Pakai Qdrant (vol 16 planned)

Reference best practice:
- Redis Search Semantic Cache (2024): https://redis.io/docs/latest/develop/ai/search-and-query/vectors/semantic-caching/
- LangChain CacheBackedEmbeddings
- LiteLLM cache module

Anti-pattern dihindari:
- ❌ Cache personal/user-specific response (tergantung context_triple zaman/makan/haal)
- ❌ Cache stream output (token-by-token)
- ❌ Cache web_search result (current events change)

✅ Cache hanya: corpus-based factual Q (pertanyaan stabil, jawaban
  consistent kalau pakai same model+LoRA).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class CacheEntry:
    """1 cache entry."""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    hit_count: int = 0


# ── In-memory LRU dengan TTL ──────────────────────────────────────────────────

class ResponseLRUCache:
    """
    Thread-safe LRU cache dengan TTL.

    Defaults:
    - max_size: 500 entries
    - ttl_seconds: 3600 (1 jam)

    Bukan distributed cache — restart sidix-brain = cache cleared.
    Untuk distributed (multi-instance) Q4 2026: Redis backend.
    """

    def __init__(self, max_size: int = 500, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        # Stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def _make_key(self, *parts) -> str:
        """Hash composite key dari parts."""
        canonical = "|".join(str(p) for p in parts if p is not None)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]

    def get(self, *key_parts) -> Optional[Any]:
        """Get value, return None kalau miss atau expired."""
        key = self._make_key(*key_parts)
        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                self._misses += 1
                return None

            # Check TTL
            now = time.time()
            if now - entry.created_at > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None

            # Hit — move to end (LRU)
            entry.last_accessed = now
            entry.hit_count += 1
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, value: Any, *key_parts) -> str:
        """Set value, return cache key. Evict oldest kalau full."""
        key = self._make_key(*key_parts)
        with self._lock:
            now = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                hit_count=0,
            )
            # Remove kalau exists (refresh)
            if key in self._cache:
                del self._cache[key]
            self._cache[key] = entry
            self._cache.move_to_end(key)

            # Evict oldest kalau over limit
            while len(self._cache) > self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self._evictions += 1

            return key

    def invalidate(self, *key_parts) -> bool:
        """Manual invalidate. Useful saat user request 'jangan cached'."""
        key = self._make_key(*key_parts)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False

    def clear(self) -> int:
        """Clear all entries. Return count cleared."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def stats(self) -> dict:
        """Cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": round(hit_rate, 3),
                "ttl_seconds": self.ttl_seconds,
            }


# ── Global singleton ──────────────────────────────────────────────────────────

# Single instance untuk seluruh app (in-memory, per-process)
_cache_instance: Optional[ResponseLRUCache] = None
_init_lock = Lock()


def get_cache() -> ResponseLRUCache:
    """Lazy init global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        with _init_lock:
            if _cache_instance is None:
                _cache_instance = ResponseLRUCache(max_size=500, ttl_seconds=3600)
    return _cache_instance


# ── Cacheable decision (which queries cache) ─────────────────────────────────

def is_cacheable(
    question: str,
    *,
    persona: str = "",
    mode: str = "",
    has_user_context: bool = False,
    is_current_events: bool = False,
) -> tuple[bool, str]:
    """
    Decide apakah query ini cocok di-cache.

    Anti-cache (return False):
    - User-specific context (zaman/makan/haal personalized)
    - Current events (web_search heavy)
    - Streaming response (token-by-token, tidak makes sense)
    - Mode = strict (academic, jawaban harus fresh)

    Cacheable (return True):
    - Stable factual Q (corpus-based)
    - Common how-to question
    - Tutorial-style query
    """
    if has_user_context:
        return False, "user-specific context (personalized)"

    if is_current_events:
        return False, "current events (need fresh data)"

    if mode == "strict":
        return False, "strict mode (always fresh)"

    # Detect current event keywords (simple)
    current_keywords = [
        "hari ini", "kemarin", "minggu lalu", "bulan ini",
        "harga sekarang", "tanggal", "jam berapa", "now", "today",
        "berita", "trending", "live", "terkini",
    ]
    text_lower = (question or "").lower()
    if any(kw in text_lower for kw in current_keywords):
        return False, "current events keyword detected"

    # Question yang terlalu pendek (mungkin casual, jangan cache)
    if len(text_lower.strip()) < 15:
        return False, "too short (likely casual)"

    return True, ""


# ── Convenience helpers untuk /ask flow ───────────────────────────────────────

def get_ask_cache(question: str, persona: str = "AYMAN", mode: str = "agent") -> Optional[dict]:
    """Helper untuk /ask endpoint cache lookup."""
    cache = get_cache()
    return cache.get("ask", question, persona, mode)


def set_ask_cache(
    response: dict,
    question: str,
    persona: str = "AYMAN",
    mode: str = "agent",
) -> str:
    """Helper untuk /ask endpoint cache store."""
    cache = get_cache()
    return cache.set(response, "ask", question, persona, mode)


__all__ = [
    "CacheEntry",
    "ResponseLRUCache",
    "get_cache",
    "is_cacheable",
    "get_ask_cache",
    "set_ask_cache",
]
