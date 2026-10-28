"""
corpus_quality_filter.py — Sprint Tumbuh 50%→75%

Pre-add filter untuk corpus auto-grow pipeline (learn/run + process_queue).
Tanpa filter, corpus bisa kemasukan junk (404 pages, spam, halu LLM output).
Filter ini gate quality SEBELUM corpus expand → LoRA training data clean.

Filter rules:
1. Min length (avoid stub content)
2. Max length (avoid full HTML page dump)
3. No spam patterns (excessive caps, repeated chars, base64 blobs)
4. No 404/error page indicators
5. Language consistency check (ID + EN allowed, others flagged)
6. No PII leak (email, phone, credit card patterns)

Returns: QualityScore (accept/reject + reason).

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class QualityScore:
    accept: bool
    score: float  # 0.0 - 1.0
    reason: str
    flags: list[str]


# Spam / junk patterns
_HTML_404_RE = re.compile(
    r"\b(404|not found|page not found|halaman tidak ditemukan|error|access denied|forbidden)\b",
    re.IGNORECASE,
)
_EXCESSIVE_CAPS_RE = re.compile(r"[A-Z]{20,}")
_REPEATED_CHAR_RE = re.compile(r"(.)\1{15,}")
_BASE64_BLOB_RE = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")

# PII patterns (basic, conservative)
_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
_PHONE_ID_RE = re.compile(r"\b(\+?62|0)[-\s]?(8[1-9])[-\s]?\d{3,4}[-\s]?\d{3,4}\b")
_CC_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

# Indonesian + English language markers
_ID_MARKERS = ("yang", "dan", "untuk", "dari", "dengan", "adalah", "ini", "itu", "saya", "kita")
_EN_MARKERS = ("the", "and", "for", "from", "with", "is", "are", "this", "that")


def assess_corpus_quality(
    text: str,
    min_chars: int = 80,
    max_chars: int = 8000,
) -> QualityScore:
    """Assess kualitas text sebelum di-add ke corpus."""
    flags: list[str] = []
    score = 1.0

    if not text or not text.strip():
        return QualityScore(accept=False, score=0.0, reason="empty", flags=["empty"])

    text = text.strip()
    n = len(text)

    # Length check
    if n < min_chars:
        return QualityScore(accept=False, score=0.0, reason=f"too_short_{n}c", flags=["too_short"])
    if n > max_chars:
        return QualityScore(accept=False, score=0.2, reason=f"too_long_{n}c", flags=["too_long"])

    # 404 / error page check
    if _HTML_404_RE.search(text[:500]):
        # In header → likely error page
        return QualityScore(accept=False, score=0.1, reason="404_or_error_page", flags=["error_page"])

    # Spam patterns
    if _EXCESSIVE_CAPS_RE.search(text):
        flags.append("excessive_caps")
        score -= 0.3
    if _REPEATED_CHAR_RE.search(text):
        flags.append("repeated_char_spam")
        score -= 0.4
    if _BASE64_BLOB_RE.search(text):
        flags.append("base64_blob")
        score -= 0.5

    # PII check (reject if found, privacy-first)
    if _EMAIL_RE.search(text):
        flags.append("pii_email")
        score -= 0.6
    if _PHONE_ID_RE.search(text):
        flags.append("pii_phone")
        score -= 0.6
    if _CC_RE.search(text):
        return QualityScore(accept=False, score=0.0, reason="pii_credit_card", flags=["pii_cc"])

    # Language consistency (basic)
    lower = text.lower()
    id_hits = sum(1 for w in _ID_MARKERS if f" {w} " in lower)
    en_hits = sum(1 for w in _EN_MARKERS if f" {w} " in lower)
    if id_hits == 0 and en_hits == 0 and n > 200:
        flags.append("no_id_or_en_markers")
        score -= 0.3

    # Final accept threshold
    if score < 0.4:
        return QualityScore(accept=False, score=score, reason="low_quality", flags=flags)

    return QualityScore(accept=True, score=score, reason="ok", flags=flags)


def filter_corpus_batch(items: list[dict], text_key: str = "text") -> tuple[list[dict], dict]:
    """Filter batch dari list of dicts. Return (accepted, stats).

    items: [{text: str, ...other_fields}, ...]
    text_key: kunci yang punya text content
    """
    accepted = []
    rejected_count = 0
    flag_counter: dict[str, int] = {}

    for item in items:
        text = str(item.get(text_key, ""))
        score = assess_corpus_quality(text)
        if score.accept:
            item["_quality_score"] = score.score
            item["_quality_flags"] = score.flags
            accepted.append(item)
        else:
            rejected_count += 1
            for flag in score.flags:
                flag_counter[flag] = flag_counter.get(flag, 0) + 1

    return accepted, {
        "total": len(items),
        "accepted": len(accepted),
        "rejected": rejected_count,
        "accept_rate": len(accepted) / len(items) if items else 0.0,
        "flag_distribution": flag_counter,
    }


__all__ = [
    "QualityScore",
    "assess_corpus_quality",
    "filter_corpus_batch",
]
