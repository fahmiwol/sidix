"""
Intent classifier ringan (few-shot pola teks) untuk orchestration & routing.

Bukan model neural: deterministik, cepat, mudah diaudit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class QueryIntent(Enum):
    FACTUAL = "factual"
    CREATIVE = "creative"
    CODE = "code"
    RESEARCH = "research"
    SOCIAL = "social"
    META = "meta"
    SAFETY_PROBE = "safety_probe"


@dataclass
class IntentResult:
    intent: QueryIntent
    confidence: float
    matched_rule: str


_RULES: list[tuple[str, QueryIntent, float]] = [
    (r"\b(cara bunuh|bom rakitan|racun manusia|self[- ]harm)\b", QueryIntent.SAFETY_PROBE, 0.95),
    (r"\b(python|javascript|typescript|rust|golang|sql|dockerfile|implementasi fungsi|debug error)\b", QueryIntent.CODE, 0.88),
    (r"\b(jurnal|hipotesis|metodologi|p-value|literatur|paper|arxiv)\b", QueryIntent.RESEARCH, 0.82),
    (r"\b(iklan|copywriting|slogan|brand persona|narasi kreatif)\b", QueryIntent.CREATIVE, 0.8),
    (r"\b(instagram|twitter|tiktok|linkedin|kampanye|viral|komentar netizen)\b", QueryIntent.SOCIAL, 0.78),
    (r"\b(siapa kamu|help|bantuan|perintah apa|/agent)\b", QueryIntent.META, 0.75),
]


def classify_intent(text: str) -> IntentResult:
    """Klasifikasi intent utama dari satu query user."""
    t = (text or "").strip()
    lower = t.lower()
    if not lower:
        return IntentResult(QueryIntent.FACTUAL, 0.3, "empty")

    for pattern, intent, conf in _RULES:
        if re.search(pattern, lower, re.I):
            return IntentResult(intent, conf, pattern)

    wc = len(t.split())
    if wc <= 3 and "?" in t:
        return IntentResult(QueryIntent.FACTUAL, 0.55, "short_question")

    return IntentResult(QueryIntent.FACTUAL, 0.5, "default")
