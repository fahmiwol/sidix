"""
maqashid_profiles.py — Maqashid Filter v2 (Mode-Based, IHOS-Aligned)

SIDIX v0.6 — menggantikan pendekatan keyword-blacklist dengan mode kontekstual.
Dirancang agar TIDAK memblokir creative output (copywriting, branding, marketing, ads).

Terinspirasi dari analisis arsitektur IHOS (Islamic Holistic Ontological System):
  Maqashid al-Syariah = objective function, BUKAN content police.

Mode yang tersedia:
  CREATIVE  — Branding, ads, design, marketing, copywriting
  ACADEMIC  — Research, fiqh, ilmu eksakta (label sanad wajib)
  IJTIHAD   — Eksplorasi, hipotesis, brainstorming (tag [EXPLORATORY])
  GENERAL   — Chat biasa, daily tasks

Keputusan (2026-04-23):
  - Maqashid jadi SCORE MULTIPLIER di Creative mode, bukan pemblokir
  - Hard-block hanya untuk dangerous_intents (harm nyata, bukan content type)
  - Backward compatible: caller lama yang tidak pass mode → fallback ke GENERAL

Refs:
  - docs/CREATIVE_AGENT_TAXONOMY.md
  - brain/public/research_notes/183_maqashid_profiles_mode_based.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ── Mode Enum ──────────────────────────────────────────────────────────────────

class MaqashidMode(Enum):
    CREATIVE  = "creative"   # branding, ads, design, marketing
    ACADEMIC  = "academic"   # research, fiqh, ilmu eksakta
    IJTIHAD   = "ijtihad"    # eksplorasi, hipotesis, brainstorming
    GENERAL   = "general"    # chat biasa


class MaqashidAction(Enum):
    BLOCK   = "block"    # hard stop, jelaskan kenapa
    WARN    = "warn"     # output jalan + disclaimer
    BOOST   = "boost"    # highlight / encourage
    NEUTRAL = "neutral"  # tidak ada intervensi


# ── Rule per Mode ──────────────────────────────────────────────────────────────

@dataclass
class MaqashidRule:
    """5-sumbu Maqashid al-Syariah → action per mode."""
    life:     MaqashidAction = MaqashidAction.NEUTRAL
    intellect: MaqashidAction = MaqashidAction.NEUTRAL
    faith:    MaqashidAction = MaqashidAction.NEUTRAL
    lineage:  MaqashidAction = MaqashidAction.NEUTRAL
    wealth:   MaqashidAction = MaqashidAction.NEUTRAL


PROFILES: dict[MaqashidMode, MaqashidRule] = {
    MaqashidMode.CREATIVE: MaqashidRule(
        life=MaqashidAction.WARN,       # boleh dark humor/satire, jangan promosi self-harm
        intellect=MaqashidAction.BOOST, # kreativitas = intellect maksimal
        faith=MaqashidAction.NEUTRAL,   # iklan sneaker tidak perlu sebut Islam
        lineage=MaqashidAction.WARN,    # satire sosial boleh, jangan hina keluarga spesifik
        wealth=MaqashidAction.BOOST,    # marketing = optimize value creation
    ),
    MaqashidMode.ACADEMIC: MaqashidRule(
        life=MaqashidAction.BLOCK,
        intellect=MaqashidAction.BLOCK,
        faith=MaqashidAction.BLOCK,
        lineage=MaqashidAction.BLOCK,
        wealth=MaqashidAction.BLOCK,
    ),
    MaqashidMode.IJTIHAD: MaqashidRule(
        life=MaqashidAction.WARN,
        intellect=MaqashidAction.BOOST,
        faith=MaqashidAction.WARN,
        lineage=MaqashidAction.NEUTRAL,
        wealth=MaqashidAction.NEUTRAL,
    ),
    MaqashidMode.GENERAL: MaqashidRule(
        life=MaqashidAction.WARN,
        intellect=MaqashidAction.NEUTRAL,
        faith=MaqashidAction.NEUTRAL,
        lineage=MaqashidAction.NEUTRAL,
        wealth=MaqashidAction.NEUTRAL,
    ),
}


# ── Dangerous Intents (hard-block di SEMUA mode) ───────────────────────────────

_DANGEROUS_INTENTS: dict[str, list[str]] = {
    "life": [
        "cara bunuh diri", "cara melukai diri", "racun untuk manusia",
        "cara membuat bom untuk bunuh", "self-harm guide",
    ],
    "faith": [
        "cara menghina nabi", "cara merusak mushaf",
        "taktik penistaan agama",
    ],
}


# ── Persona → Mode Mapping ─────────────────────────────────────────────────────

_PERSONA_MODE_MAP: dict[str, MaqashidMode] = {
    # Nama persona baru (2026-04-23)
    "AYMAN":  MaqashidMode.IJTIHAD,   # Strategic Sage — deep thinking, visioner
    "ABOO":   MaqashidMode.ACADEMIC,  # The Analyst — strict, logis, sanad
    "OOMAR":  MaqashidMode.IJTIHAD,   # The Craftsman — technical exploration
    "ALEY":   MaqashidMode.GENERAL,   # The Learner — general, beginner-friendly
    "UTZ":    MaqashidMode.CREATIVE,  # The Generalist — creative default
    # Alias nama lama (backward compat — deprecated, pakai nama baru)
    "MIGHAN": MaqashidMode.IJTIHAD,
    "TOARD":  MaqashidMode.ACADEMIC,
    "FACH":   MaqashidMode.IJTIHAD,
    "HAYFAR": MaqashidMode.GENERAL,
    "INAN":   MaqashidMode.CREATIVE,
    # fallback
    "DEFAULT": MaqashidMode.GENERAL,
}


def get_mode_by_persona(persona_name: str) -> MaqashidMode:
    """Map nama persona ke mode Maqashid yang sesuai."""
    return _PERSONA_MODE_MAP.get(
        (persona_name or "").upper(),
        MaqashidMode.GENERAL,
    )


# ── Main Evaluator ────────────────────────────────────────────────────────────

def evaluate_maqashid(
    user_query: str,
    generated_output: str,
    mode: Optional[MaqashidMode] = None,
    persona_name: str = "UTZ",
) -> dict:
    """
    Evaluasi output berdasarkan mode persona.

    Args:
        user_query:       teks query asli dari user
        generated_output: output yang sudah di-generate SIDIX
        mode:             override mode; kalau None → resolve dari persona_name
        persona_name:     dipakai kalau mode tidak di-pass

    Returns dict:
        {
          "status":        "pass" | "warn" | "block",
          "mode":          str,
          "reasons":       list[str],
          "tagged_output": str,        # output (mungkin dengan disclaimer/tag ditambah)
        }
    """
    if mode is None:
        mode = get_mode_by_persona(persona_name)

    query_lower = (user_query or "").lower()
    output_lower = (generated_output or "").lower()

    # ── 1. Dangerous intent check (hard-block, semua mode) ────────────────────
    for category, phrases in _DANGEROUS_INTENTS.items():
        for phrase in phrases:
            if phrase in query_lower:
                return {
                    "status": "block",
                    "mode": mode.value,
                    "reasons": [f"Kandungan berbahaya [{category}]: '{phrase}'"],
                    "tagged_output": (
                        "[BLOCKED] Maaf, SIDIX tidak bisa membantu permintaan ini karena "
                        "berpotensi membahayakan keselamatan jiwa atau kehormatan agama."
                    ),
                }

    # ── 2. Mode-specific handling ─────────────────────────────────────────────
    if mode == MaqashidMode.CREATIVE:
        # Di mode Creative: block hanya kalau output benar-benar mengandung
        # self-harm eksplisit TANPA konteks bantuan
        if "bunuh diri" in output_lower or "self harm" in output_lower:
            if "berhenti" not in output_lower and "bantuan" not in output_lower:
                return {
                    "status": "warn",
                    "mode": mode.value,
                    "reasons": ["Output creative mengandung tema self-harm tanpa konteks bantuan"],
                    "tagged_output": (
                        generated_output
                        + "\n\n[CATATAN SIDIX: Jika kamu atau orang di sekitarmu butuh bantuan, "
                        "hubungi 119 ext 8.]\n"
                    ),
                }

        # Tambah boost tag kalau relevan
        tags: list[str] = []
        profile = PROFILES[MaqashidMode.CREATIVE]
        if profile.intellect == MaqashidAction.BOOST:
            tags.append("Intellect-Optimized")
        if profile.wealth == MaqashidAction.BOOST:
            tags.append("Value-Creation Mode")

        tagged = generated_output
        if tags:
            tagged += f"\n\n[{' | '.join(tags)}]"

        return {
            "status": "pass",
            "mode": mode.value,
            "reasons": [],
            "tagged_output": tagged,
        }

    elif mode == MaqashidMode.ACADEMIC:
        # Academic: sanad label wajib
        has_label = any(
            label in generated_output
            for label in ["[FACT]", "[FAKTA]", "[OPINION]", "[OPINI]",
                          "[SPECULATION]", "[SPEKULASI]", "[UNKNOWN]"]
        )
        if not has_label:
            return {
                "status": "warn",
                "mode": mode.value,
                "reasons": ["Output akademik wajib punya label epistemik [FAKTA]/[OPINI]"],
                "tagged_output": "[⚠️ SANAD MISSING]\n" + generated_output,
            }
        return {
            "status": "pass",
            "mode": mode.value,
            "reasons": [],
            "tagged_output": generated_output,
        }

    elif mode == MaqashidMode.IJTIHAD:
        # Ijtihad: tag [EXPLORATORY], bukan [FATWA]
        tagged = generated_output
        if "[EXPLORATORY]" not in generated_output and "[FATWA]" not in generated_output:
            tagged += "\n\n[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]"
        return {
            "status": "pass",
            "mode": mode.value,
            "reasons": [],
            "tagged_output": tagged,
        }

    # GENERAL + fallback
    return {
        "status": "pass",
        "mode": mode.value,
        "reasons": [],
        "tagged_output": generated_output,
    }


def maqashid_score_from_content(text: str) -> float:
    """
    Hitung skor Maqashid 0.0-1.0 dari konten teks.
    Dipakai oleh curator_agent + muhasabah_loop.

    5 sumbu × 0.20 maks = 1.0
    """
    lower = text.lower()
    _AXIS_KEYWORDS: dict[str, list[str]] = {
        "life":     ["kesehatan", "keselamatan", "jiwa", "kehidupan", "selamat", "hidup"],
        "intellect":["ilmu", "belajar", "riset", "analisis", "pengetahuan", "logika"],
        "faith":    ["iman", "ibadah", "quran", "sunnah", "tauhid", "ikhlas"],
        "lineage":  ["keluarga", "anak", "generasi", "masyarakat", "sosial", "pendidikan"],
        "wealth":   ["ekonomi", "bisnis", "kerja", "produktivitas", "halal", "usaha"],
    }
    score = 0.0
    for keywords in _AXIS_KEYWORDS.values():
        if any(k in lower for k in keywords):
            score += 0.20
    return round(score, 4)
