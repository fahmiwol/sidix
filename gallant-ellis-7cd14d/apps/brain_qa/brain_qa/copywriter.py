"""
copywriter.py — Sprint 4 P0 creative copy generator.

Tujuan:
- Generate copy/caption yang siap pakai (bukan directory/search output).
- Integrasi CQF + iterasi ringan (3 varian → pilih top).
- Default own-stack: template heuristik dulu, LLM opsional bila tersedia.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .creative_quality import rank_variants, quality_gate

Formula = Literal["AIDA", "PAS", "FAB"]


@dataclass(frozen=True)
class CopyVariant:
    text: str
    formula: Formula
    angle: str


def _compose_aida(topic: str, audience: str, cta: str, tone: str, angle: str) -> str:
    return (
        f"{'🔥' if tone == 'bold' else '✨'} {topic} untuk {audience}.\n"
        f"Attention: {angle} yang sering diabaikan orang.\n"
        f"Interest: bayangkan hasil nyata dalam 7 hari dengan langkah sederhana.\n"
        f"Desire: lebih hemat waktu, lebih konsisten, dan hasil lebih terukur.\n"
        f"Action: {cta}"
    )


def _compose_pas(topic: str, audience: str, cta: str, tone: str, angle: str) -> str:
    return (
        f"{'⚠️' if tone == 'bold' else '🧩'} {audience} sering mentok di {topic}.\n"
        f"Problem: strategi terasa ramai tapi tidak bergerak.\n"
        f"Agitate: tiap hari posting, tapi tetap sepi dan capek sendiri.\n"
        f"Solution: fokus ke {angle} + eksekusi 1 jam/hari, hasil lebih konsisten.\n"
        f"{cta}"
    )


def _compose_fab(topic: str, audience: str, cta: str, tone: str, angle: str) -> str:
    return (
        f"{'✅' if tone != 'playful' else '🎯'} Solusi {topic} untuk {audience}.\n"
        f"Feature: framework {angle} + checklist eksekusi.\n"
        f"Advantage: proses jelas, cepat dipraktikkan, mudah diulang.\n"
        f"Benefit: produktivitas naik tanpa menambah beban kerja berlebihan.\n"
        f"{cta}"
    )


def _build_variant(formula: Formula, topic: str, audience: str, cta: str, tone: str, angle: str) -> CopyVariant:
    if formula == "PAS":
        text = _compose_pas(topic, audience, cta, tone, angle)
    elif formula == "FAB":
        text = _compose_fab(topic, audience, cta, tone, angle)
    else:
        text = _compose_aida(topic, audience, cta, tone, angle)
    return CopyVariant(text=text.strip(), formula=formula, angle=angle)


def generate_copy(
    *,
    topic: str,
    channel: str = "instagram",
    formula: Formula = "AIDA",
    audience: str = "audiens Indonesia",
    cta: str = "Komentar 'MAU' kalau ingin templatenya.",
    tone: str = "friendly",
    variant_count: int = 3,
    min_score: float = 7.0,
) -> dict:
    """
    Generate 3 varian copy + quality gate.

    Return:
    {
      ok, channel, formula, best_text, variants, cqf, needs_refinement
    }
    """
    clean_topic = (topic or "").strip()
    if not clean_topic:
        return {"ok": False, "error": "topic wajib diisi"}

    vc = max(1, min(int(variant_count), 5))
    angles = [
        "problem-solution praktis",
        "hasil cepat yang realistis",
        "langkah sederhana tapi konsisten",
        "framework ringkas anti-ribet",
        "before-after terukur",
    ]

    variants: list[CopyVariant] = []
    for index in range(vc):
        local_formula: Formula = formula
        if formula == "AIDA" and index == 1:
            local_formula = "PAS"
        elif formula == "AIDA" and index >= 2:
            local_formula = "FAB"
        variants.append(
            _build_variant(
                local_formula,
                clean_topic,
                audience.strip() or "audiens Indonesia",
                cta.strip() or "Yuk mulai dari langkah kecil hari ini.",
                tone.strip().lower() or "friendly",
                angles[index % len(angles)],
            )
        )

    variant_texts = [v.text for v in variants]
    ranked = rank_variants(
        variant_texts,
        brief=f"{clean_topic} untuk {channel} formula {formula}",
        domain="content",
        top_k=1,
    )
    best_idx, best_score = ranked[0]
    best_text = variants[best_idx].text
    gate = quality_gate(
        best_text,
        brief=f"{clean_topic} | {channel} | {audience} | {formula}",
        domain="content",
        use_llm=False,
    )

    return {
        "ok": True,
        "channel": channel,
        "formula": formula,
        "best_text": best_text,
        "best_formula": variants[best_idx].formula,
        "variants": [
            {"formula": v.formula, "angle": v.angle, "text": v.text}
            for v in variants
        ],
        "cqf": gate,
        "score_total": gate["total"],
        "needs_refinement": bool(gate["needs_refinement"]) or gate["total"] < float(min_score),
        "next_action": "refine_copy" if gate["total"] < float(min_score) else "ready_to_publish",
        "ranking_preview": {
            "selected_variant_index": best_idx,
            "selected_variant_score": round(best_score.total, 2),
        },
    }

