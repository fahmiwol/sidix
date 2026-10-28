"""
persona_router.py — Auto-detect user style → match persona optimal
====================================================================

Per DIRECTION_LOCK_20260426 P1 Q3 2026:
> "Persona Auto-Routing: detect user style → match optimal persona"

Saat ini user harus manual pilih persona di UI. Pengguna casual chat
tidak peduli persona — mereka cuma mau jawaban yang cocok. Auto-routing
= UX yang natural, bukan beban kognitif.

5 persona SIDIX (LOCKED, per DIRECTION_LOCK section 5):

| Persona | Cocok untuk |
|---|---|
| **UTZ** | Creative/visual: brainstorm, naming, design, metafora, story |
| **ABOO** | Engineer/teknis: coding, debugging, system design, tradeoff |
| **OOMAR** | Strategist: bisnis, market, ROI, decision, go-to-market |
| **ALEY** | Akademik: riset, paper, evidence, theory, citation |
| **AYMAN** | General/hangat: casual chat, life advice, ringkas |

Mekanisme routing (3-tier, hierarchy of cost):

1. **TIER 1 — Keyword Heuristic** (free, <1ms):
   - "bikin gambar/design/visual" → UTZ
   - "code/python/debug/api" → ABOO
   - "bisnis/strategi/cost/market" → OOMAR
   - "paper/jurnal/penelitian" → ALEY
   - default → AYMAN

2. **TIER 2 — Embedding Similarity** (cheap, ~10ms):
   - Encode user message + persona-anchor sentences
   - Cosine similarity → top match
   - (Future P2 — butuh embedding model)

3. **TIER 3 — LLM Classification** (mahal, ~500ms):
   - Pakai LLM untuk classify dengan context
   - Hanya kalau Tier 1 ambiguous (≥3 persona match similar)
   - (Future P2)

Vol 11 implement Tier 1 only (keyword) + history-aware override
(kalau user pernah explicit pilih persona, prefer itu).

Output: persona_decision dengan confidence + reason. Caller decide
apakah override req.persona atau biarkan.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class PersonaDecision:
    """Hasil auto-routing decision."""
    persona: str
    confidence: float          # 0.0 - 1.0
    reason: str
    matched_keywords: list[str] = field(default_factory=list)
    tier_used: str = "tier1_keyword"
    fallback_used: bool = False


# ── Keyword maps (LOCKED 5 persona per DIRECTION_LOCK section 4) ──────────────

_PERSONA_KEYWORDS = {
    "UTZ": [
        # Indonesia — creative/visual
        r"\b(bikin|buat|gambar|gambarkan|design|desain|ilustrasi|foto|poster|logo)\b",
        r"\b(visual|warna|palet|estetika|seni|artwork|kreatif|imajinasi)\b",
        r"\b(metafora|cerita|story|narasi|brand|naming)\b",
        r"\b(video|animasi|render|3d|capcut|figma)\b",
        # English
        r"\b(create|generate|illustrate|design|visual|story|brand|logo)\b",
    ],
    "ABOO": [
        # Indonesia — engineer/teknis
        r"\b(code|coding|kode|program|debug|error|bug|fix)\b",
        r"\b(python|javascript|typescript|react|vue|fastapi|django)\b",
        r"\b(api|endpoint|server|database|sql|deployment|deploy)\b",
        r"\b(arsitektur|implementasi|tradeoff|edge case|optimasi)\b",
        r"\b(github|git|docker|kubernetes|aws|cloud)\b",
        # English
        r"\b(implement|debug|architecture|optimize|deploy|backend|frontend)\b",
    ],
    "OOMAR": [
        # Indonesia — strategist/bisnis
        r"\b(bisnis|business|strategi|strategy|market|pasar|kompetitor)\b",
        r"\b(cost|budget|harga|pricing|revenue|profit|roi|margin)\b",
        r"\b(go.?to.?market|gtm|launch|akuisisi|customer|user growth)\b",
        r"\b(decision|keputusan|risk|risiko|monetisasi|sponsor)\b",
        r"\b(startup|founder|investor|pitch|fundraise|valuation)\b",
        # English
        r"\b(strategy|business|monetize|competitor|launch|growth|funding)\b",
    ],
    "ALEY": [
        # Indonesia — akademik/riset
        r"\b(paper|jurnal|penelitian|riset|research|studi|literatur)\b",
        r"\b(teori|theory|empirical|evidence|hipotesis|hypothesis)\b",
        r"\b(citation|sitasi|sumber|referensi|bibliography)\b",
        r"\b(arxiv|hugging\s*face|nature|science|ieee)\b",
        r"\b(akademik|academic|scholar|peer.?review|metodologi)\b",
        # English
        r"\b(research|paper|study|theory|empirical|literature|citation)\b",
    ],
    "AYMAN": [
        # Default fallback — casual/general
        # No specific keywords — assigned kalau no other match
    ],
}

# Compile regex
_COMPILED = {
    persona: [re.compile(p, re.IGNORECASE) for p in patterns]
    for persona, patterns in _PERSONA_KEYWORDS.items() if patterns
}


# ── Path ───────────────────────────────────────────────────────────────────────

def _routing_log() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "persona_routing.jsonl"


# ── User history (override kalau explicit pernah pilih) ────────────────────────

def _user_persona_history(user_id: str = "", limit: int = 20) -> Optional[str]:
    """
    Cek activity log: kalau user 5+ chat terakhir pakai persona yang sama
    explicit, prefer itu (user preference signal).
    """
    if not user_id:
        return None
    try:
        from . import auth_google
        entries = auth_google.list_activity(limit=limit, user_id=user_id)
    except Exception:
        return None
    if not entries:
        return None
    from collections import Counter
    personas = [e.get("persona", "") for e in entries if e.get("persona")]
    if len(personas) < 5:
        return None
    top, count = Counter(personas).most_common(1)[0]
    if count / len(personas) >= 0.7 and top not in ("?", ""):
        return top
    return None


# ── Main routing function ──────────────────────────────────────────────────────

def route_persona(
    user_message: str,
    *,
    user_id: str = "",
    explicit_persona: str = "",
    log_decision: bool = True,
) -> PersonaDecision:
    """
    Auto-detect optimal persona dari user message.

    Args:
        user_message: pertanyaan/pesan user
        user_id: optional, untuk history-aware override
        explicit_persona: kalau user explicit set, langsung pakai (skip routing)
        log_decision: persist ke routing log (default True)

    Returns PersonaDecision lengkap.
    """
    # Priority 1: explicit user choice
    if explicit_persona and explicit_persona in _PERSONA_KEYWORDS:
        return PersonaDecision(
            persona=explicit_persona,
            confidence=1.0,
            reason="explicit user choice",
            tier_used="explicit",
        )

    # Priority 2: user history bias (kalau user keep pakai persona yang sama)
    history_persona = _user_persona_history(user_id)

    # Tier 1: Keyword scoring
    text = (user_message or "").strip()
    if not text:
        decision = PersonaDecision(
            persona=history_persona or "AYMAN",
            confidence=0.5,
            reason="empty message → fallback default",
            tier_used="fallback",
            fallback_used=True,
        )
        if log_decision:
            _persist(decision, user_message, user_id)
        return decision

    scores: dict[str, dict] = {}
    for persona, patterns in _COMPILED.items():
        matched = []
        for pat in patterns:
            for match in pat.findall(text):
                # findall might return tuple (regex with alternation)
                if isinstance(match, tuple):
                    m_str = next((m for m in match if m), "")
                else:
                    m_str = match
                if m_str:
                    matched.append(m_str.lower())
        if matched:
            # Score: jumlah unique keyword × log(total match count)
            unique = len(set(matched))
            total = len(matched)
            import math
            scores[persona] = {
                "unique": unique,
                "total": total,
                "matched": list(set(matched))[:8],
                "score": unique * (1 + math.log(1 + total)),
            }

    if not scores:
        # No keyword match → AYMAN default (atau history bias)
        decision = PersonaDecision(
            persona=history_persona or "AYMAN",
            confidence=0.6 if history_persona else 0.5,
            reason="no keyword match → " + (
                f"user history bias ({history_persona})" if history_persona
                else "AYMAN default (general/casual)"
            ),
            tier_used="tier1_keyword",
            fallback_used=True,
        )
        if log_decision:
            _persist(decision, user_message, user_id)
        return decision

    # Pick top scoring persona
    sorted_personas = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    top_persona, top_data = sorted_personas[0]

    # Confidence: ratio of top vs second
    if len(sorted_personas) > 1:
        second_score = sorted_personas[1][1]["score"]
        ratio = top_data["score"] / max(0.1, top_data["score"] + second_score)
        confidence = min(0.95, 0.5 + ratio * 0.5)
    else:
        confidence = min(0.9, 0.6 + top_data["unique"] * 0.05)

    # History bias: kalau user history dominan + top match marginal, pakai history
    if history_persona and history_persona != top_persona and confidence < 0.7:
        decision = PersonaDecision(
            persona=history_persona,
            confidence=0.65,
            reason=f"keyword suggest '{top_persona}' tapi user history dominan '{history_persona}' (low confidence override)",
            matched_keywords=top_data["matched"],
            tier_used="tier1_keyword + history_override",
        )
    else:
        decision = PersonaDecision(
            persona=top_persona,
            confidence=round(confidence, 2),
            reason=f"keyword match {top_data['unique']} unique × {top_data['total']} total → '{top_persona}'",
            matched_keywords=top_data["matched"],
            tier_used="tier1_keyword",
        )

    if log_decision:
        _persist(decision, user_message, user_id)
    return decision


# ── Persistence ────────────────────────────────────────────────────────────────

def _persist(decision: PersonaDecision, user_message: str, user_id: str) -> None:
    try:
        with _routing_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id[:32],
                "user_message_preview": (user_message or "")[:120],
                **asdict(decision),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Persona routing distribution untuk admin dashboard."""
    path = _routing_log()
    if not path.exists():
        return {"total": 0, "by_persona": {}, "avg_confidence": 0.0}

    by_persona: dict[str, int] = {}
    confidences: list[float] = []
    by_tier: dict[str, int] = {}
    fallback_count = 0

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    p = e.get("persona", "?")
                    by_persona[p] = by_persona.get(p, 0) + 1
                    if e.get("confidence"):
                        confidences.append(float(e["confidence"]))
                    t = e.get("tier_used", "?")
                    by_tier[t] = by_tier.get(t, 0) + 1
                    if e.get("fallback_used"):
                        fallback_count += 1
                except Exception:
                    continue
    except Exception:
        return {"total": 0, "by_persona": {}, "avg_confidence": 0.0}

    return {
        "total": sum(by_persona.values()),
        "by_persona": by_persona,
        "by_tier": by_tier,
        "fallback_count": fallback_count,
        "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
    }


__all__ = ["PersonaDecision", "route_persona", "stats"]
