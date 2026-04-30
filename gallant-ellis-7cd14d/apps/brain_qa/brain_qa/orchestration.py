"""
orchestration.py — Metode orkestrasi kognitif multi-aspek untuk SIDIX.

Menjembatani:
- **Archetype** internal (invent, deduce, connect, synthesize, orient) — metafora desain
  (iterasi/verifikasi/antarmuka/integrasi/ringkas), bukan klaim biografi.
- **Satelit fiksi** (edison, pythagoras, shaka, lilith, atlas, york) — label inspiratif
  untuk *role fan-out* dan bobot; bukan konten bajakan One Piece.
- **Persona SIDIX** yang sudah ada (TOARD/FACH/MIGHAN/HAYFAR/INAN) lewat `persona.route_persona`.

Modul ini murni deterministik (regex + skor), aman diimpor dari tool, API, atau planner LLM nanti.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# Sinkron dengan agent_react (intent implement / app / game).
_AGENT_BUILD_INTENT_RE = re.compile(
    r"\b(buat(?:kan)?|implement|implementasi|scaffold|generate|kode\s+baru|source\s+code|"
    r"python\s+script|tulis\s+file|write\s+file|aplikasi|app\b|game\b|projek|project)\b",
    re.IGNORECASE,
)

_INVENT_RE = re.compile(
    r"\b(prototype|mvp|poc|deploy|docker|kubernetes|k8s|ci\s*/\s*cd|build|compile|"
    r"hardware|firmware|iot|embedded|experiment|ekperimen)\b",
    re.IGNORECASE,
)
_DEDUCE_RE = re.compile(
    r"\b(bukti|proof|verify|verifikasi|logika|konsisten|formal|audit|teorema|"
    r"epistem|maqashid|statistik|signifikan|p-value|hipotesis|null)\b",
    re.IGNORECASE,
)
_CONNECT_RE = re.compile(
    r"\b(api|endpoint|grpc|rest|graphql|http|https|websocket|protocol|socket|"
    r"webhook|oauth|jwt|antarmuka|interface|integrasi|middleware)\b",
    re.IGNORECASE,
)
_SYNTHESIZE_RE = re.compile(
    r"\b(orchestr|orkestra|multi[\s-]?agen|multi[\s-]?agent|pipeline|dag|etl|"
    r"workflow|langkah\s+bertahap|koordinasi)\b",
    re.IGNORECASE,
)

ARCHETYPE_ORDER = ("deduce", "connect", "invent", "synthesize", "orient")

# Bobot satelit (fiksi) <- kombinasi archetype — untuk telemetry / UI / RAG feeding.
_SAT_KEYS = ("edison", "pythagoras", "shaka", "lilith", "atlas", "york")


def agent_build_intent(question: str) -> bool:
    """True jika pertanyaan mengarah implementasi perangkat lunak / app / game."""
    return bool(_AGENT_BUILD_INTENT_RE.search(question or ""))


def score_archetypes(question: str) -> dict[str, float]:
    """Skor archetype [0,inf) — angka mentah sebelum normalisasi tampilan."""
    q = question or ""
    s = {k: 0.0 for k in ARCHETYPE_ORDER}
    s["orient"] = 0.35  # baseline: selalu sedikit orientasi ringkas
    if agent_build_intent(q):
        s["invent"] += 1.4
    if _INVENT_RE.search(q):
        s["invent"] += 0.9
    if _DEDUCE_RE.search(q):
        s["deduce"] += 1.1
    if _CONNECT_RE.search(q):
        s["connect"] += 1.0
    if _SYNTHESIZE_RE.search(q):
        s["synthesize"] += 1.2
    if re.search(r"\b(ringkas|singkat|tl;dr|tldr|cepat)\b", q, re.I):
        s["orient"] += 0.8
    return s


def satellite_weights(archetype_scores: dict[str, float]) -> dict[str, float]:
    """
    Proyeksi skor archetype ke bobot 'satelit' inspiratif (enam nama internal).
    """
    inv = archetype_scores.get("invent", 0.0)
    ded = archetype_scores.get("deduce", 0.0)
    con = archetype_scores.get("connect", 0.0)
    syn = archetype_scores.get("synthesize", 0.0)
    ori = archetype_scores.get("orient", 0.0)

    raw = {
        "edison": inv * 1.15 + syn * 0.35,
        "pythagoras": ded * 1.05 + con * 0.75,
        "shaka": ded * 0.85,
        "lilith": inv * 0.25,
        "atlas": inv * 0.45 + syn * 0.2,
        "york": syn * 0.5 + ori * 0.3,
    }
    t = sum(raw.values()) or 1.0
    return {k: round(v / t, 4) for k, v in raw.items()}


def _archetype_to_persona_hint(arch: str) -> str:
    return {
        "invent": "HAYFAR",
        "deduce": "FACH",
        "connect": "HAYFAR",
        "synthesize": "TOARD",
        "orient": "INAN",
    }.get(arch, "INAN")


def _phase_hint(arch: str) -> str:
    return {
        "deduce": "Korpus + epistemologi; bedakan fakta vs hipotesis.",
        "connect": "Tebalkan batas API/protokol; minimalkan permukaan serangan.",
        "invent": "Iterasi di sandbox agent_workspace; workspace_write butuh allow_restricted.",
        "synthesize": "Pecah tugas besar; urutkan dependensi; delegasi persona.",
        "orient": "Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit.",
    }.get(arch, "Lanjutkan dengan persona default.")


@dataclass
class OrchestrationPlan:
    """Rencana orkestrasi deterministik untuk satu pertanyaan."""

    request_persona: str
    router_persona: str
    router_reason: str
    archetype_scores: dict[str, float]
    satellite_weights: dict[str, float]
    phases: list[tuple[str, str, str]] = field(default_factory=list)
    """(archetype_id, persona_hint, action_hint) — urutan eksekusi disarankan."""

    def to_json_dict(self) -> dict:
        return {
            "request_persona": self.request_persona,
            "router_persona": self.router_persona,
            "router_reason": self.router_reason,
            "archetype_scores": self.archetype_scores,
            "satellite_weights": self.satellite_weights,
            "phases": [{"archetype": a, "persona": p, "hint": h} for a, p, h in self.phases],
        }


def build_orchestration_plan(question: str, request_persona: str = "INAN") -> OrchestrationPlan:
    from .persona import route_persona

    decision = route_persona(question)
    scores = score_archetypes(question)
    sats = satellite_weights(scores)

    # Urut fase: archetype tertinggi dulu (deduce biasanya di depan untuk jaga sanad).
    ranked = sorted(ARCHETYPE_ORDER, key=lambda k: scores.get(k, 0.0), reverse=True)
    phases: list[tuple[str, str, str]] = []
    for arch in ranked:
        if scores.get(arch, 0.0) <= 0.05 and arch != "orient":
            continue
        phases.append((arch, _archetype_to_persona_hint(arch), _phase_hint(arch)))

    if not phases:
        phases.append(("orient", "INAN", _phase_hint("orient")))

    return OrchestrationPlan(
        request_persona=request_persona.strip().upper() or "INAN",
        router_persona=decision.persona,
        router_reason=decision.reason,
        archetype_scores=scores,
        satellite_weights=sats,
        phases=phases,
    )


def format_plan_text(plan: OrchestrationPlan, *, max_lines: int = 40) -> str:
    """Teks ringkas untuk disematkan di sesi agen atau tool output."""
    lines = [
        "SIDIX OrchestrationPlan (deterministik)",
        f"request_persona={plan.request_persona} router={plan.router_persona}",
        f"router_reason: {plan.router_reason[:220]}",
        "",
        "Archetype scores:",
    ]
    for k in ARCHETYPE_ORDER:
        lines.append(f"  - {k}: {plan.archetype_scores.get(k, 0.0):.3f}")
    lines.append("")
    lines.append("Satellite weights (inspirasi fiksi / dev labels):")
    for k in _SAT_KEYS:
        lines.append(f"  - {k}: {plan.satellite_weights.get(k, 0.0):.4f}")
    lines.append("")
    lines.append("Suggested phase order:")
    for i, (a, p, h) in enumerate(plan.phases[:max_lines], 1):
        lines.append(f"  {i}. [{a}] persona~{p} -> {h}")
    lines.append("")
    lines.append("JSON:")
    lines.append(json.dumps(plan.to_json_dict(), ensure_ascii=False)[:3500])
    return "\n".join(lines)


def format_plan_json(plan: OrchestrationPlan) -> str:
    return json.dumps(plan.to_json_dict(), ensure_ascii=False, indent=2)
