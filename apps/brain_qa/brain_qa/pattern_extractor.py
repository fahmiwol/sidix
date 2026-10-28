"""
pattern_extractor.py — Induktif Generalization Engine
=======================================================

User insight 2026-04-26:
> "Misalnya 'oh kalo batok kelapa dibakar, bisa jadi arang. artinya kayu juga
> kalo dibakar jadi arang' — bagaimana sidix bisa ditahap itu?"

Ini adalah **induktif generalization** — dari satu contoh konkret, ekstrak
prinsip umum yang applicable ke kasus lain. Pattern human cognition yang
LLM biasa GAGAL — mereka memorize fakta, tidak generalize prinsip.

SIDIX approach:
  1. Saat conversation muncul observation faktual ("batok kelapa dibakar →
     arang"), trigger LLM untuk ekstrak general principle.
  2. Simpan principle ke `brain/patterns/induction.jsonl` dengan metadata:
     - source_example
     - extracted_principle
     - applicable_domain (organic/physics/social/etc.)
     - confidence
  3. Saat query baru match domain, retrieve top-K patterns sebagai context
     ke ReAct loop.
  4. Pattern bisa di-corroborate (multiple example same principle → confidence
     naik) atau di-falsify (counter-example → flag review).

Output bukan rule rigid — pattern adalah **soft prior** yang diinjeksi ke
prompt LLM, biarkan LLM final-judge applicability.

Filosofi: bukan "AI tahu semua", tapi "AI mengabstraksi struktur dari
pengalaman". Ini fondasi reasoning > retrieval.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class Pattern:
    """1 pattern induktif yang diekstrak dari observation."""
    id: str
    ts: str
    source_example: str               # observation asli
    extracted_principle: str          # general rule
    applicable_domain: list[str]      # ["organic", "biomass", "thermal"]
    keywords: list[str]               # untuk retrieval (BM25-like)
    confidence: float = 0.5            # awal medium, naik kalau corroborated
    corroborations: int = 0            # berapa kali confirmed by similar cases
    falsifications: int = 0            # berapa kali kontradiksi
    counter_examples: list[str] = field(default_factory=list)
    derived_from: str = ""             # session_id atau user_id asal


# ── Path helpers ───────────────────────────────────────────────────────────────

def _patterns_dir() -> Path:
    here = Path(__file__).resolve().parent
    # Save di brain/patterns/ supaya jadi bagian growth corpus, bukan .data internal
    root = here.parent.parent.parent  # apps/brain_qa/brain_qa → apps/brain_qa → apps → root
    d = root / "brain" / "patterns"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _patterns_file() -> Path:
    return _patterns_dir() / "induction.jsonl"


# ── LLM-based extraction ───────────────────────────────────────────────────────

_TRIGGER_PHRASES = [
    # Indonesia
    r"\bartinya\b", r"\bberarti\b", r"\bmaka\b", r"\bmaksudnya\b",
    r"jadi (kalau|kalo)", r"prinsipnya", r"polanya", r"hukum(nya)?",
    # English
    r"\bmeans\b", r"\btherefore\b", r"\bthus\b", r"in general",
    r"the principle", r"the pattern",
]

_COMPILED_TRIGGERS = re.compile("|".join(_TRIGGER_PHRASES), re.IGNORECASE)


# ── LLM helper (unified — handle ollama_llm + local_llm signature differences) ─

def _call_llm(prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str:
    """
    Unified LLM call yang handle 2 backend (ollama production / local_llm fallback).
    Return string response atau "" kalau gagal.
    """
    # Try ollama (production) dulu — signature: ollama_generate(prompt, system, ...)
    try:
        from .ollama_llm import ollama_generate
        text, mode = ollama_generate(
            prompt,
            system="",
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if text and not mode.startswith("mock_error"):
            return text
    except Exception as e:
        log.debug("[pattern_extractor] ollama_generate fail: %s", e)

    # Fallback ke local_llm (kalau ada adapter LoRA)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(
            prompt,
            system="",
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if text:
            return text
    except Exception as e:
        log.debug("[pattern_extractor] generate_sidix fail: %s", e)

    return ""


def looks_like_inductive_claim(text: str) -> bool:
    """
    Cepat detect apakah text mengandung klaim induktif (ada generalization).
    Bukan ML, hanya regex untuk pre-filter sebelum LLM call (efficiency).
    """
    if not text or len(text) < 20:
        return False
    return bool(_COMPILED_TRIGGERS.search(text))


def extract_pattern_from_text(
    text: str,
    *,
    source_example: str = "",
    derived_from: str = "",
) -> Optional[Pattern]:
    """
    Pakai LLM untuk ekstrak prinsip umum dari observation faktual.

    Args:
        text: full passage berisi observation
        source_example: konkret kasus (default = text)
        derived_from: session_id atau user_id

    Returns Pattern atau None kalau gagal extract.
    """
    if not text or len(text) < 20:
        return None

    prompt = f"""Berikut adalah pengamatan / klaim:

"{text}"

Tugas: ekstrak prinsip umum (induktif generalization) dari pengamatan ini.
Output JSON pendek (maks 6 baris) dengan key:
- principle: kalimat 1-2 baris yang menggeneralisasi pola
- domain: 2-4 keyword domain (contoh: "organic", "thermal", "social")
- keywords: 3-6 keyword untuk indexing (lowercase)
- confidence: 0.0-1.0 (seberapa yakin prinsip ini berlaku umum)

Jangan generic. Yang spesifik tapi applicable. Output ONLY JSON:"""

    response = _call_llm(prompt, max_tokens=200, temperature=0.4)
    if not response:
        return None

    try:
        from .llm_json_robust import robust_json_parse
        data = robust_json_parse(response)
        if not data:
            raise ValueError("robust_json_parse returned None")
        principle = (data.get("principle") or "").strip()
        if not principle or len(principle) < 10:
            return None

        return Pattern(
            id=f"pat_{uuid.uuid4().hex[:10]}",
            ts=datetime.now(timezone.utc).isoformat(),
            source_example=(source_example or text)[:400],
            extracted_principle=principle[:500],
            applicable_domain=[d.lower().strip() for d in (data.get("domain") or [])][:5],
            keywords=[k.lower().strip() for k in (data.get("keywords") or [])][:8],
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
            derived_from=derived_from,
        )
    except json.JSONDecodeError:
        log.debug("[pattern_extractor] JSON parse fail, response: %s", response[:200])
        return None
    except Exception as e:
        log.warning("[pattern_extractor] extract fail: %s", e)
        return None


# ── Storage ────────────────────────────────────────────────────────────────────

def save_pattern(p: Pattern) -> None:
    """Append pattern ke induction.jsonl."""
    try:
        with _patterns_file().open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[pattern_extractor] save fail: %s", e)


def list_patterns(limit: int = 200) -> list[dict]:
    """Read all patterns (atau tail-N)."""
    path = _patterns_file()
    if not path.exists():
        return []
    out = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out[-limit:] if len(out) > limit else out
    except Exception:
        return []


def search_patterns(
    query: str,
    *,
    domain_hint: str = "",
    top_k: int = 5,
    min_confidence: float = 0.3,
) -> list[dict]:
    """
    Sederhana keyword overlap retrieval. BM25-lite, bukan vector.
    Untuk MVP cukup. Upgrade ke embedding kalau >1000 patterns.
    """
    q_lower = (query or "").lower()
    q_tokens = set(re.findall(r"\w+", q_lower))
    if not q_tokens:
        return []

    domain_lower = (domain_hint or "").lower()
    candidates = list_patterns(limit=2000)
    scored = []

    for p in candidates:
        if p.get("confidence", 0) < min_confidence:
            continue
        # Score: keyword overlap + domain bonus + confidence multiplier
        kw_set = set(p.get("keywords", []))
        overlap = len(q_tokens & kw_set)
        # Also check principle text overlap
        principle_tokens = set(re.findall(r"\w+", p.get("extracted_principle", "").lower()))
        principle_overlap = len(q_tokens & principle_tokens)

        domain_bonus = 0.0
        if domain_lower and any(domain_lower in d for d in p.get("applicable_domain", [])):
            domain_bonus = 1.0

        score = overlap * 1.5 + principle_overlap * 0.5 + domain_bonus
        score *= p.get("confidence", 0.5)

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:top_k]]


def corroborate_pattern(pattern_id: str) -> bool:
    """
    Saat pattern berhasil applied + verified, increment corroborations +
    naikkan confidence. Reload + rewrite (tidak optimal untuk scale, tapi
    OK untuk <10k patterns).
    """
    path = _patterns_file()
    if not path.exists():
        return False
    try:
        all_patterns = []
        found = False
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    p = json.loads(line)
                    if p.get("id") == pattern_id:
                        p["corroborations"] = p.get("corroborations", 0) + 1
                        # Confidence rising with diminishing returns
                        new_conf = min(0.95, p.get("confidence", 0.5) + 0.05)
                        p["confidence"] = new_conf
                        found = True
                    all_patterns.append(p)
                except Exception:
                    continue
        if found:
            with path.open("w", encoding="utf-8") as f:
                for p in all_patterns:
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
        return found
    except Exception as e:
        log.warning("[pattern_extractor] corroborate fail: %s", e)
        return False


def falsify_pattern(pattern_id: str, counter_example: str) -> bool:
    """
    Saat pattern menemui counter-example, increment falsifications +
    turunkan confidence. Kalau confidence < 0.2, pattern auto-archive.
    """
    path = _patterns_file()
    if not path.exists():
        return False
    try:
        all_patterns = []
        found = False
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    p = json.loads(line)
                    if p.get("id") == pattern_id:
                        p["falsifications"] = p.get("falsifications", 0) + 1
                        p.setdefault("counter_examples", []).append(counter_example[:200])
                        new_conf = max(0.05, p.get("confidence", 0.5) - 0.15)
                        p["confidence"] = new_conf
                        found = True
                    all_patterns.append(p)
                except Exception:
                    continue
        if found:
            with path.open("w", encoding="utf-8") as f:
                for p in all_patterns:
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
        return found
    except Exception as e:
        log.warning("[pattern_extractor] falsify fail: %s", e)
        return False


def stats() -> dict:
    """Summary stats untuk admin dashboard."""
    patterns = list_patterns(limit=5000)
    if not patterns:
        return {"total": 0, "avg_confidence": 0.0, "by_domain": {},
                "high_conf": 0, "low_conf": 0}

    by_domain: dict[str, int] = {}
    confs: list[float] = []
    for p in patterns:
        for d in p.get("applicable_domain", []):
            by_domain[d] = by_domain.get(d, 0) + 1
        confs.append(p.get("confidence", 0.5))

    return {
        "total": len(patterns),
        "avg_confidence": round(sum(confs) / len(confs), 3),
        "by_domain": dict(sorted(by_domain.items(), key=lambda x: -x[1])[:15]),
        "high_conf": sum(1 for c in confs if c >= 0.75),
        "low_conf": sum(1 for c in confs if c < 0.4),
    }


# ── Hook untuk auto-extract dari conversation ──────────────────────────────────

def maybe_extract_from_conversation(
    user_message: str,
    assistant_response: str,
    *,
    session_id: str = "",
) -> Optional[Pattern]:
    """
    Hook yang dipanggil di end of /ask: kalau user/assistant bicara klaim
    induktif, ekstrak + simpan pattern. Best-effort, non-blocking.

    Disebut di:
      - /ask endpoint (after generate, before return)
      - daily_growth REMEMBER phase (batch dari approved notes)
    """
    # Check user message dulu (lebih sering source insight)
    for src_text, src_type in [(user_message, "user"), (assistant_response, "assistant")]:
        if not looks_like_inductive_claim(src_text):
            continue
        pattern = extract_pattern_from_text(
            src_text,
            source_example=src_text[:400],
            derived_from=f"{src_type}:{session_id}",
        )
        if pattern:
            save_pattern(pattern)
            log.info("[pattern_extractor] saved pattern %s from %s",
                     pattern.id, src_type)
            return pattern
    return None


__all__ = [
    "Pattern", "looks_like_inductive_claim", "extract_pattern_from_text",
    "save_pattern", "list_patterns", "search_patterns",
    "corroborate_pattern", "falsify_pattern", "stats",
    "maybe_extract_from_conversation",
]
