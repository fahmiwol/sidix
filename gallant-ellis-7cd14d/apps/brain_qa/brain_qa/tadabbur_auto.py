"""
tadabbur_auto.py — Auto-Trigger Tadabbur Mode untuk Deep Questions
======================================================================

Per DIRECTION_LOCK Q3 P1 + Vol 19 user priority "benerin jawaban relevan".

Tadabbur Mode (vol 10) = 3-persona iterate konvergensi → answer deeper.
Cost: 7 LLM call (mahal). Tidak boleh trigger semua chat (bankrupt + slow).

Solusi: **Selective expert routing** (Sebastian Raschka 2024 pattern).
Cheap classifier (regex + length + keyword) → decide pakai Tadabbur atau
default ReAct.

Trigger criteria (any-of):
1. Question length > 120 char (sign complex)
2. Multiple question marks (compound question)
3. Strategic/philosophical keyword detected
4. User explicit minta "deep dive" / "tadabbur" / "rinciin"
5. Complexity score > 0.7 (combine factors)

Anti-trigger (block tadabbur):
- Casual chat (halo, apa kabar, makasih)
- Single fact lookup (siapa X, kapan Y)
- Short question < 30 char
- Code/technical specific (lebih cocok ABOO direct)

Fallback: kalau Tadabbur fail/timeout, return ReAct standard.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


# ── Trigger keywords ───────────────────────────────────────────────────────────

# Strategic/philosophical (favor Tadabbur)
_DEEP_KEYWORDS = [
    # Strategic
    r"\bstrategi\b", r"\broadmap\b", r"\bvision\b", r"\bvisi\b",
    r"\bjangka panjang\b", r"\b5\s*tahun\b", r"\bmasa depan\b",
    # Philosophical
    r"\bfilosofi\b", r"\bmakna\b", r"\bessens\b", r"\bhakikat\b",
    r"\bwhy\b.*\bworld\b", r"\bkenapa\b.*\bharus\b",
    # Complex tradeoff
    r"\bdilema\b", r"\btradeoff\b", r"\bbalance\b", r"\bvs\b",
    r"\bdibanding\b", r"\bversus\b",
    # Multi-perspective
    r"\bdari\s+(?:berbagai|banyak|sudut)\b",
    r"\bperspektif\s+(?:lain|berbeda|dari)\b",
    r"\b(?:pro|kontra|positif|negatif)\b.*\b(?:dari|untuk)\b",
    # Decision-heavy
    r"\bharus(?:nya|ku)?\b.*\b(?:pilih|ambil|putuskan)\b",
    r"\bkalau\s+saya\b.*\b(?:bagaimana|gimana|harus)\b",
    r"\bbagaimana\s+(?:cara|kalau|jika)\b",
    # Explicit tadabbur request
    r"\bdeep\s*dive\b", r"\btadabbur\b", r"\brinciin\b",
    r"\bmendalam\b", r"\bbedah\s+(?:secara|dengan)?\s*(?:detail|mendalam)\b",
]

_COMPILED_DEEP = re.compile("|".join(_DEEP_KEYWORDS), re.IGNORECASE)


# Casual/short → block tadabbur
_CASUAL_KEYWORDS = [
    r"\b(?:halo|hi|hai|hello|hey)\b",
    r"\b(?:apa\s*kabar|makasih|thanks?|terima\s*kasih)\b",
    r"^(?:ya|iya|ok|oke|sip|gass?|ga|tidak|no)$",
]

_COMPILED_CASUAL = re.compile("|".join(_CASUAL_KEYWORDS), re.IGNORECASE)


# Code/technical → ABOO direct, bukan multi-persona
# Note: hindari kata yang ambigu ("go", "java" sebagai language vs general)
_CODE_KEYWORDS = [
    r"\b(?:debug|error|exception|stacktrace|traceback)\b",
    r"\b(?:python|javascript|typescript|rust|kotlin|swift)\b",
    r"\b(?:fastapi|django|flask|express|nextjs|react|vue)\b",
    r"\b(?:bug|fix)\s+(?:di|in|the)\b",  # "bug di X", "fix di Y"
    r"\b(?:endpoint|database|sql|docker|kubernetes)\b",
    r"\bdeploy(?:ment)?\b.*\b(?:server|production|staging)\b",
    r"```",  # contains code block
]

_COMPILED_CODE = re.compile("|".join(_CODE_KEYWORDS), re.IGNORECASE)


# ── Decision dataclass ────────────────────────────────────────────────────────

@dataclass
class TadabburDecision:
    """Hasil keputusan auto-trigger."""
    should_trigger: bool
    score: float                       # 0.0 - 1.0 complexity
    reasons: list[str]
    blocked_by: str = ""               # alasan kalau block (casual/code/short)
    estimated_cost_llm_calls: int = 0  # 7 kalau trigger, 0 kalau skip


# ── Decision logic ────────────────────────────────────────────────────────────

def should_trigger_tadabbur(
    question: str,
    *,
    user_explicit_request: bool = False,
    min_length: int = 30,
    deep_threshold: float = 0.6,
) -> TadabburDecision:
    """
    Selective expert routing — decide Tadabbur (deep, 7 LLM call) atau
    ReAct standard (cheap).

    Args:
        question: user message
        user_explicit_request: kalau user explicit minta deep mode
        min_length: minimum question length untuk consider
        deep_threshold: complexity score minimum untuk trigger

    Returns TadabburDecision lengkap.
    """
    text = (question or "").strip()

    # Hard block: explicit casual or too short
    if not text:
        return TadabburDecision(
            should_trigger=False, score=0.0, reasons=[],
            blocked_by="empty question",
        )

    if len(text) < min_length and not user_explicit_request:
        return TadabburDecision(
            should_trigger=False, score=0.0, reasons=[],
            blocked_by=f"too short (<{min_length} char)",
        )

    # Casual block (kecuali user explicit)
    if not user_explicit_request and _COMPILED_CASUAL.search(text):
        return TadabburDecision(
            should_trigger=False, score=0.1, reasons=[],
            blocked_by="casual chat detected",
        )

    # Code block (ABOO direct, no multi-persona)
    if _COMPILED_CODE.search(text):
        return TadabburDecision(
            should_trigger=False, score=0.3,
            reasons=["code/technical → ABOO direct"],
            blocked_by="code-specific question",
        )

    # User explicit override = always trigger (kalau panjang minimum)
    if user_explicit_request:
        return TadabburDecision(
            should_trigger=True,
            score=1.0,
            reasons=["user explicit request"],
            estimated_cost_llm_calls=7,
        )

    # Score factors
    reasons = []
    score = 0.0

    # Factor 1: length signal
    if len(text) > 200:
        score += 0.3
        reasons.append(f"long question ({len(text)} char)")
    elif len(text) > 120:
        score += 0.2
        reasons.append(f"medium-long ({len(text)} char)")

    # Factor 2: multiple question marks (compound)
    qmark_count = text.count("?")
    if qmark_count >= 2:
        score += 0.25
        reasons.append(f"compound question ({qmark_count} '?')")

    # Factor 3: deep keywords (high-signal weight, multi-keyword bonus)
    deep_matches = _COMPILED_DEEP.findall(text)
    if deep_matches:
        # Flatten tuples kalau ada
        flat = []
        for m in deep_matches:
            if isinstance(m, tuple):
                flat.extend([x for x in m if x])
            elif m:
                flat.append(m)
        unique_count = len(set(flat))
        # Multi-keyword cluster bonus (≥3 unique = high signal)
        kw_score = unique_count * 0.18
        if unique_count >= 3:
            kw_score += 0.15  # bonus
        score += min(0.65, kw_score)
        reasons.append(f"deep keywords: {flat[:3]} (unique={unique_count})")

    # Factor 4: comma count (sign complexity)
    comma_count = text.count(",")
    if comma_count >= 4:
        score += 0.1
        reasons.append(f"complex structure ({comma_count} commas)")

    # Factor 5: dan/atau frequency (multi-clause)
    multi_clause = len(re.findall(r"\b(?:dan|atau|tapi|namun|walaupun|meskipun)\b", text, re.IGNORECASE))
    if multi_clause >= 2:
        score += 0.15
        reasons.append(f"multi-clause ({multi_clause} connectors)")

    score = min(1.0, score)

    return TadabburDecision(
        should_trigger=score >= deep_threshold,
        score=round(score, 2),
        reasons=reasons,
        estimated_cost_llm_calls=7 if score >= deep_threshold else 0,
    )


# ── Adaptive trigger (with cost guard) ────────────────────────────────────────

def adaptive_trigger(
    question: str,
    *,
    user_explicit_request: bool = False,
    daily_tadabbur_used: int = 0,
    daily_tadabbur_limit: int = 50,
) -> TadabburDecision:
    """
    Trigger dengan daily budget guard. Kalau quota Tadabbur hari ini
    sudah habis, force ReAct standard (cost protection).
    """
    decision = should_trigger_tadabbur(question, user_explicit_request=user_explicit_request)

    if decision.should_trigger and daily_tadabbur_used >= daily_tadabbur_limit:
        return TadabburDecision(
            should_trigger=False,
            score=decision.score,
            reasons=decision.reasons + [f"daily Tadabbur quota habis ({daily_tadabbur_used}/{daily_tadabbur_limit})"],
            blocked_by="daily_quota_exceeded",
        )

    return decision


__all__ = [
    "TadabburDecision",
    "should_trigger_tadabbur",
    "adaptive_trigger",
]
