"""
complexity_router.py — Complexity-Tier Routing (Vol 20-fu2 #7)
==========================================================================

Route question ke tier reasoning yang sesuai untuk hemat compute + UX
visible. Per NeuralRouting research (note 235): Llama 70B within 3%
GPT-4o di ROUGE, routing 79-93% cost reduction di production.

3 tier:
- `simple` → corpus-only direct path, <100ms (greeting, short Q,
   ack/yes/no, exact corpus match potensial)
- `standard` → single-pass ReAct (current default), 5-30s
- `deep` → Tadabbur 3-persona iteration eligible, 30-120s

Detection priority (target <5ms, no model):
1. Regex keyword + length heuristik (paling cepat)
2. Persona override (UTZ creative bias standard, ALEY akademik bias deep)
3. Adapter ke `tadabbur_auto.adaptive_trigger` (existing logic)

Anti-pattern dihindari:
- ❌ ML classifier (overkill, embed bottleneck)
- ❌ LLM-as-classifier (cost + latency)
- ✅ Regex + persona heuristik

Reference:
- Note 235 NeuralRouting decision matrix
- Note 234 persona-aware spec routing (Q3 plan)
- Note 237 Vol 20-closure: tadabbur observability ready

Output:
- ComplexityDecision dataclass: tier + rationale + estimated_latency_class
- detect_tier(question, persona) → ComplexityDecision
- explain_tier() debug helper
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Literal

log = logging.getLogger(__name__)


Tier = Literal["simple", "standard", "deep"]


# ── Patterns ─────────────────────────────────────────────────────────────────

# Simple tier: greeting, ack, very short, factual lookup
_SIMPLE_GREETING_RE = re.compile(
    r"^(halo|hai|hi|hello|assalamu.?alaikum|salam|pagi|siang|sore|malam|"
    r"selamat\s+(pagi|siang|sore|malam)|"
    r"thanks|thank|terima\s*kasih|makasih|"
    r"ok|oke|sip|mantap|baik|"
    r"bye|sampai\s*jumpa|dadah)\b",
    re.I,
)

_SIMPLE_ACK_RE = re.compile(
    r"^(ya|iya|ok|oke|tidak|nggak|gak|setuju|tidak\s+setuju|benar|salah|"
    r"yes|no|sure|nope|maybe)\s*[!?.]*\s*$",
    re.I,
)

# Deep tier: multi-clause, deep keywords, long, compound
_DEEP_KEYWORDS_RE = re.compile(
    r"\b("
    r"strategi|strategy|roadmap|"
    r"trade.?off|tradeoff|"
    r"perbandingan\s+(antara|dengan)|"
    r"analisis|analysis|"
    r"evaluasi|evaluate|"
    r"sintesis|synthesis|"
    r"impact|dampak|implikasi|"
    r"pro.?(s|kontra)|pros?\s*(and|dan)\s*cons?|"
    r"why\s+(should|would|could)|kenapa\s+(harus|sebaiknya|akan)|"
    r"how\s+to\s+(decide|choose|approach)|cara\s+(memilih|menentukan|mendekati)|"
    r"filosofi|philosophy|"
    r"holistic|menyeluruh|"
    r"long.?term|jangka\s+panjang|"
    r"architectural|arsitektur"
    r")\b",
    re.I,
)

# Code question - bias standard (single-pass ReAct enough untuk most)
_CODE_RE = re.compile(
    r"\b("
    r"python|javascript|typescript|java|golang|rust|"
    r"react|vue|angular|svelte|"
    r"docker|kubernetes|nginx|postgres|mysql|"
    r"function|class|method|loop|"
    r"error|exception|stack\s+trace|debug|"
    r"\.py\b|\.js\b|\.ts\b|\.go\b|\.rs\b"
    r")\b",
    re.I,
)


# ── Persona priors ────────────────────────────────────────────────────────────

# Default tier bias per persona kalau ambigu
PERSONA_TIER_BIAS: dict[str, Tier] = {
    "UTZ":   "standard",   # creative — single-pass cukup, no over-think
    "ABOO":  "standard",   # engineer — code questions ReAct cukup
    "OOMAR": "standard",   # strategist — bisa deep kalau keyword match
    "ALEY":  "standard",   # akademik — bisa deep kalau keyword match
    "AYMAN": "standard",   # general — default standard
}


# ── Decision data ─────────────────────────────────────────────────────────────

@dataclass
class ComplexityDecision:
    """Decision tier + rationale untuk routing."""
    tier: Tier
    matched_rules: list[str] = field(default_factory=list)
    score: float = 0.0  # 0=simple, 0.5=standard, 1.0=deep
    estimated_latency_class: str = "5-30s"  # for telemetry
    persona_bias_applied: bool = False

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "matched_rules": self.matched_rules,
            "score": round(self.score, 2),
            "estimated_latency_class": self.estimated_latency_class,
            "persona_bias_applied": self.persona_bias_applied,
        }


# ── Main classifier ───────────────────────────────────────────────────────────

def detect_tier(
    question: str,
    persona: str = "AYMAN",
    *,
    user_explicit_deep: bool = False,
) -> ComplexityDecision:
    """
    Classify question complexity → tier untuk routing.

    Priority:
    1. user_explicit_deep → "deep"
    2. SIMPLE: greeting/ack/very short → "simple"
    3. DEEP: multi-clause + deep keywords + length → "deep"
    4. Code question → "standard" (ReAct cukup)
    5. Fallback persona bias → "standard"

    Returns ComplexityDecision dengan tier + rationale.
    Target latency: <5ms.
    """
    q = (question or "").strip()
    rules: list[str] = []
    score = 0.5  # default standard

    # User explicit override
    if user_explicit_deep:
        return ComplexityDecision(
            tier="deep",
            matched_rules=["user_explicit_deep"],
            score=1.0,
            estimated_latency_class="30-120s",
        )

    # Empty
    if not q:
        return ComplexityDecision(
            tier="simple",
            matched_rules=["empty_question"],
            score=0.0,
            estimated_latency_class="<100ms",
        )

    # ── SIMPLE tier ──────────────────────────────────────────────────────────
    # Very short (< 8 char)
    if len(q) < 8:
        return ComplexityDecision(
            tier="simple",
            matched_rules=[f"too_short ({len(q)} char)"],
            score=0.05,
            estimated_latency_class="<100ms",
        )

    # Greeting/salutation
    if _SIMPLE_GREETING_RE.match(q):
        return ComplexityDecision(
            tier="simple",
            matched_rules=["greeting"],
            score=0.1,
            estimated_latency_class="<100ms",
        )

    # Ack/yes-no
    if _SIMPLE_ACK_RE.match(q):
        return ComplexityDecision(
            tier="simple",
            matched_rules=["ack_yes_no"],
            score=0.1,
            estimated_latency_class="<100ms",
        )

    # Short factual (< 25 char, no deep keyword)
    if len(q) < 25 and not _DEEP_KEYWORDS_RE.search(q):
        return ComplexityDecision(
            tier="simple",
            matched_rules=[f"short_factual ({len(q)} char)"],
            score=0.2,
            estimated_latency_class="<100ms",
        )

    # ── DEEP tier ────────────────────────────────────────────────────────────
    # Code question — ReAct cukup, jangan eskalasi ke deep
    code_match = _CODE_RE.search(q)
    if code_match:
        rules.append(f"code_keyword:{code_match.group()[:20]}")

    # Deep keywords (re.findall returns tuples kalau pattern punya groups)
    deep_matches = _DEEP_KEYWORDS_RE.findall(q)
    if deep_matches:
        flat: list[str] = []
        for m in deep_matches:
            if isinstance(m, tuple):
                flat.extend([x for x in m if x])
            elif m:
                flat.append(m)
        unique = len({s.lower() for s in flat})
        kw_score = min(0.5, unique * 0.18)
        score += kw_score
        rules.append(f"deep_keywords ({unique} unique)")

    # Length signals
    if len(q) > 200:
        score += 0.2
        rules.append(f"long_question ({len(q)} char)")
    elif len(q) > 120:
        score += 0.1
        rules.append(f"medium_long ({len(q)} char)")

    # Multi-clause
    multi_clause = len(re.findall(
        r"\b(?:dan|atau|tapi|namun|walaupun|meskipun|serta|kemudian)\b",
        q, re.IGNORECASE,
    ))
    if multi_clause >= 2:
        score += 0.15
        rules.append(f"multi_clause ({multi_clause})")

    # Multiple question marks
    if q.count("?") >= 2:
        score += 0.15
        rules.append(f"compound_question ({q.count('?')} ?)")

    # Code question caps at standard (no deep escalation)
    if code_match:
        tier_final: Tier = "standard"
        score = min(score, 0.6)
        return ComplexityDecision(
            tier=tier_final,
            matched_rules=rules + ["capped_at_standard:code"],
            score=score,
            estimated_latency_class="5-30s",
        )

    # Decision threshold
    if score >= 0.7:
        return ComplexityDecision(
            tier="deep",
            matched_rules=rules,
            score=score,
            estimated_latency_class="30-120s",
        )

    # Fallback to persona bias
    persona_bias = PERSONA_TIER_BIAS.get(persona.upper(), "standard")
    return ComplexityDecision(
        tier=persona_bias,
        matched_rules=rules + [f"persona_bias:{persona.upper()}"],
        score=score,
        estimated_latency_class="5-30s" if persona_bias == "standard" else "30-120s",
        persona_bias_applied=True,
    )


def explain_tier(question: str, persona: str = "AYMAN") -> dict:
    """Debug helper — full decision breakdown."""
    decision = detect_tier(question, persona)
    return {
        "question": question[:80],
        "persona": persona,
        **decision.to_dict(),
    }


__all__ = [
    "Tier",
    "ComplexityDecision",
    "detect_tier",
    "explain_tier",
    "PERSONA_TIER_BIAS",
]
