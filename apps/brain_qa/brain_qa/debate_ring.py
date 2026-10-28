"""
debate_ring.py — SIDIX Debate Ring REAL
Multi-agent consensus via Qwen LLM (self-hosted only).

Flow (3 rounds):
  Round 1: Creator (Persona A) presents initial proposal
  Round 2: Critic (Persona B) critiques + suggests improvements
  Round 3: Creator revises based on critique + Critic final review
  Consensus: Neutral synthesizer merges best elements from both

All inference via generate_sidix() — NEVER external APIs.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel

try:
    from .local_llm import generate_sidix
except ImportError:  # pragma: no cover
    def generate_sidix(prompt: str, system: str, *, max_tokens: int = 256, temperature: float = 0.7) -> tuple[str, str]:
        return "[mock]", "mock"

try:
    from .creative_quality import heuristic_score
except ImportError:  # pragma: no cover
    heuristic_score = None

try:
    from .cot_system_prompts import PERSONA_DESCRIPTIONS
except ImportError:  # pragma: no cover
    PERSONA_DESCRIPTIONS = {}

log = logging.getLogger(__name__)

_ALLOWED_PERSONAS = {"AYMAN", "ABOO", "OOMAR", "ALEY", "UTZ"}

_DEFAULT_DEBATE_PAIRS: list[dict[str, str]] = [
    {"name": "Copywriter \u2194 Strategist", "persona_a": "UTZ", "persona_b": "OOMAR"},
    {"name": "Brand Builder \u2194 Designer", "persona_a": "UTZ", "persona_b": "ABOO"},
    {"name": "Script Writer \u2194 Hook Finder", "persona_a": "UTZ", "persona_b": "ALEY"},
    {"name": "General AYMAN \u2194 OOMAR", "persona_a": "AYMAN", "persona_b": "OOMAR"},
    {"name": "Technical ABOO \u2194 Research ALEY", "persona_a": "ABOO", "persona_b": "ALEY"},
]


# ── Models ────────────────────────────────────────────────────────────────────

class DebateRole(BaseModel):
    name: str
    persona: str
    system_prompt: str
    stance: str  # "creator" | "critic" | "synthesizer"


class DebateRound(BaseModel):
    round_number: int
    speaker: str
    text: str
    critique_score: float = 0.0


class DebateResult(BaseModel):
    topic: str
    rounds: list[DebateRound]
    consensus_text: str
    winner: str
    cqf_score: float
    duration_ms: int


# ── CQF Scoring (minimal heuristic fallback) ──────────────────────────────────

def _heuristic_cqf(text: str, brief: str = "") -> dict[str, Any]:
    """
    Minimal heuristic CQF scorer — fail-safe tanpa LLM.
    Relevance: keyword density
    Quality: length proxy + sentence count
    Creativity: vocabulary diversity
    Brand: default neutral
    Actionability: CTA presence
    """
    out = str(text or "").strip()
    br = str(brief or "").strip()
    out_len = len(out)

    # Relevance: shared word overlap
    br_words = set(w.lower() for w in br.split() if len(w) > 3)
    out_words = set(w.lower() for w in out.split() if len(w) > 3)
    overlap = len(br_words & out_words) / max(1, len(br_words))
    relevance = 5.0 + 4.0 * overlap

    # Quality: length proxy + sentence count
    sentences = [s for s in out.split(".") if s.strip()]
    quality = 6.0 + min(3.0, out_len / 200) + min(1.0, len(sentences) / 5)

    # Creativity: unique word ratio
    all_words = out.split()
    unique_ratio = len(set(all_words)) / max(1, len(all_words))
    creativity = 6.0 + (3.0 if unique_ratio > 0.6 else 1.5)

    # Brand alignment: neutral default
    brand = 7.0

    # Actionability: CTA markers
    cta_markers = ["coba", "mulai", "daftar", "hubungi", "klik", "download", "gunakan", "install", "bergabung"]
    has_cta = any(m in out.lower() for m in cta_markers)
    actionability = 8.0 if has_cta else 6.0

    def clamp(x: float) -> float:
        return max(1.0, min(10.0, x))

    relevance = clamp(relevance)
    quality = clamp(quality)
    creativity = clamp(creativity)
    brand = clamp(brand)
    actionability = clamp(actionability)

    total = (
        relevance * 0.25
        + quality * 0.25
        + creativity * 0.20
        + brand * 0.15
        + actionability * 0.15
    )

    return {
        "relevance": round(relevance, 1),
        "quality": round(quality, 1),
        "creativity": round(creativity, 1),
        "brand": round(brand, 1),
        "actionability": round(actionability, 1),
        "total": round(total, 2),
    }


def _score_cqf(text: str, brief: str = "") -> dict[str, Any]:
    """Route ke creative_quality heuristic kalau tersedia, else fallback."""
    if heuristic_score is not None:
        try:
            score = heuristic_score(text, brief, domain="generic")
            return {
                "relevance": round(score.relevance, 1),
                "quality": round(score.quality, 1),
                "creativity": round(score.creativity, 1),
                "brand": round(score.brand_alignment, 1),
                "actionability": round(score.actionability, 1),
                "total": round(score.total, 2),
            }
        except Exception as e:
            log.debug("[debate_ring] creative_quality heuristic failed: %s", e)
    return _heuristic_cqf(text, brief)


# ── Persona helpers ───────────────────────────────────────────────────────────

def _get_persona_system(persona: str) -> str:
    p = persona.strip().upper()
    if p not in _ALLOWED_PERSONAS:
        p = "UTZ"
    desc = PERSONA_DESCRIPTIONS.get(p, "")
    base = (
        "Kamu adalah SIDIX — Sistem Intelijen Digital Indonesia eXtended. "
        "Berpikir jujur, bersumber, dan verifikasi."
    )
    if desc:
        return f"{base}\n\n{desc}"
    return base


def _call_sidix(prompt: str, system: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """Wrapper generate_sidix dengan timeout guard via fail-open."""
    try:
        text, mode = generate_sidix(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if mode == "mock" and text.startswith("[SIDIX]"):
            # Adapter/model tidak tersedia — return placeholder agar tidak crash
            log.warning("[debate_ring] generate_sidix mock mode: %s", text[:80])
        return str(text or "").strip()
    except Exception as e:
        log.warning("[debate_ring] generate_sidix error: %s", e)
        return ""


# ── Core Debate Flow ──────────────────────────────────────────────────────────

def run_debate(
    topic: str,
    persona_a: str,
    persona_b: str,
    max_rounds: int = 3,
) -> DebateResult:
    """
    Run multi-agent debate consensus.

    Args:
        topic: Debate topic / brief
        persona_a: Creator persona (e.g. "UTZ")
        persona_b: Critic persona (e.g. "OOMAR")
        max_rounds: Cap rounds (default 3)

    Returns:
        DebateResult with consensus_text, rounds, and CQF score.
    """
    t0 = time.time()
    pa = persona_a.strip().upper()
    pb = persona_b.strip().upper()
    if pa not in _ALLOWED_PERSONAS:
        pa = "UTZ"
    if pb not in _ALLOWED_PERSONAS:
        pb = "OOMAR"

    sys_a = _get_persona_system(pa)
    sys_b = _get_persona_system(pb)
    sys_neutral = (
        "Kamu adalah SIDIX Synthesizer — netral, objektif, dan kritis. "
        "Tugasmu: gabungkan elemen terbaik dari dua perspektif menjadi satu output final "
        "yang koheren, actionable, dan berkualitas tinggi. "
        "Hindari repetisi, pilih inti terbaik dari masing-masing sisi, dan polish menjadi satu kesatuan."
    )

    rounds: list[DebateRound] = []
    best_text_so_far = ""

    # ── Round 1: Creator presents proposal ──────────────────────────────────
    prompt_r1 = (
        f"Topik/Brief: {topic}\n\n"
        f"Kamu adalah {pa} (Creator). Buatlah proposal awal yang kreatif, "
        f"konkret, dan actionable untuk topik di atas. "
        f"Langsung ke inti — jangan ulang brief secara mentah."
    )
    text_r1 = _call_sidix(prompt_r1, sys_a)
    best_text_so_far = text_r1 or best_text_so_far
    rounds.append(DebateRound(round_number=1, speaker=pa, text=text_r1, critique_score=0.0))

    # ── Round 2: Critic critiques ───────────────────────────────────────────
    prompt_r2 = (
        f"Topik/Brief: {topic}\n\n"
        f"Proposal dari {pa}:\n{text_r1}\n\n"
        f"Kamu adalah {pb} (Critic). Berikan kritik konstruktif yang spesifik: "
        f"1) Apa kelemahan proposal ini? 2) Apa yang bisa diperbaiki? 3) Apa alternatif/saran konkretmu? "
        f"Gunakan format: [KEKUATAN] / [KELEMAHAN] / [SARAN]."
    )
    text_r2 = _call_sidix(prompt_r2, sys_b)
    best_text_so_far = text_r2 or best_text_so_far
    rounds.append(DebateRound(round_number=2, speaker=pb, text=text_r2, critique_score=0.0))

    # ── Round 3: Creator revises ────────────────────────────────────────────
    prompt_r3 = (
        f"Topik/Brief: {topic}\n\n"
        f"Proposal awalmu:\n{text_r1}\n\n"
        f"Kritik dari {pb}:\n{text_r2}\n\n"
        f"Kamu adalah {pa} (Creator). Revisi proposal awalmu berdasarkan kritik di atas. "
        f"Gabungkan yang terbaik dari ide asli + saran kritik. Outputkan proposal revisi final."
    )
    text_r3 = _call_sidix(prompt_r3, sys_a)
    best_text_so_far = text_r3 or best_text_so_far
    rounds.append(DebateRound(round_number=3, speaker=pa, text=text_r3, critique_score=0.0))

    # ── Consensus: Neutral synthesizer ──────────────────────────────────────
    prompt_consensus = (
        f"Topik/Brief: {topic}\n\n"
        f"Proposal Revisi ({pa}):\n{text_r3}\n\n"
        f"Kritik & Saran ({pb}):\n{text_r2}\n\n"
        f"Gabungkan elemen terbaik dari kedua sisi menjadi satu output final yang: "
        f"koheren, tidak repetitif, actionable, dan siap digunakan. "
        f"Jangan sebutkan nama persona — output netral."
    )
    consensus = _call_sidix(prompt_consensus, sys_neutral)
    final_text = consensus or best_text_so_far

    # ── CQF Score ───────────────────────────────────────────────────────────
    cqf = _score_cqf(final_text, brief=topic)
    cqf_total = float(cqf.get("total", 7.0))

    # ── Winner heuristic ────────────────────────────────────────────────────
    score_a = _score_cqf(text_r3, brief=topic).get("total", 0.0)
    score_b = _score_cqf(text_r2, brief=topic).get("total", 0.0)
    winner = pa if score_a >= score_b else pb

    duration_ms = int((time.time() - t0) * 1000)

    return DebateResult(
        topic=topic,
        rounds=rounds,
        consensus_text=final_text,
        winner=winner,
        cqf_score=cqf_total,
        duration_ms=duration_ms,
    )


# ── Agency Kit Integration ────────────────────────────────────────────────────

def debate_layer_output(
    layer_name: str,
    output_text: str,
    persona_a: str,
    persona_b: str,
) -> str:
    """
    Run mini-debate on a layer output (Agency Kit pipeline).
    Returns improved text.

    Args:
        layer_name: Name of the Agency Kit layer (e.g. "concept", "copy", "design")
        output_text: Current layer output
        persona_a: Creator persona
        persona_b: Critic persona

    Returns:
        Improved text after debate consensus.
    """
    topic = f"Layer: {layer_name}\n\nOutput:\n{output_text}"
    result = run_debate(topic, persona_a, persona_b, max_rounds=3)
    return result.consensus_text or output_text


# ── Persona listing ───────────────────────────────────────────────────────────

def get_debate_personas() -> list[dict[str, str]]:
    """Return available debate pairs."""
    return list(_DEFAULT_DEBATE_PAIRS)
