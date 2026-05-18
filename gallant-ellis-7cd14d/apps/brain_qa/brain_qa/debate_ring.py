"""
debate_ring.py — SIDIX Multi-Agent Debate (Sprint 5)

Protokol: Creator ↔ Critic berdebat output kreatif, konsensus via CQF ≥ threshold.

3 pair wajib Sprint 5:
  1. copywriter   ↔ campaign_strategist  (copy vs strategi)
  2. brand_builder ↔ design_critic       (identitas vs estetika)
  3. script_hook   ↔ audience_lens       (hook vs relevansi audiens)

Flow per round:
  Critic → evaluasi prototype → approve (CQF ≥ threshold) atau critique
  Creator → terima critique → revisi
  Max 3 round. Jika tidak konsensus → return last + warning.

LLM call: pakai local_llm.generate_sidix() kalau tersedia, fallback ke
          multi_llm_router jika tidak, fallback heuristik jika semua mati.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Callable

from .creative_quality import quality_gate, CQF_WEIGHTS, DELIVERY_THRESHOLD

logger = logging.getLogger("sidix.debate_ring")

# ── LLM helper — graceful fallback ───────────────────────────────────────────
def _llm_call(prompt: str, max_tokens: int = 512) -> str:
    """Try local_llm → multi_llm_router → heuristic fallback."""
    # 1. Coba local_llm (Qwen + LoRA)
    try:
        from .local_llm import generate_sidix
        return generate_sidix(prompt, max_new_tokens=max_tokens)
    except Exception:
        pass

    # 2. Coba multi_llm_router
    try:
        from .multi_llm_router import route_generate
        result = route_generate(prompt, max_tokens=max_tokens)
        # route_generate returns LLMResult object, extract text
        return result.text if hasattr(result, "text") else str(result)
    except Exception:
        pass

    # 3. Fallback heuristik: return prompt digest sebagai placeholder
    logger.warning("debate_ring: semua LLM unavailable, pakai heuristic fallback")
    words = prompt.split()[:30]
    return f"[Heuristic revision]: {' '.join(words)}... — diperbaiki berdasarkan kritik."


# ── Critic prompt builder ─────────────────────────────────────────────────────
_CRITIC_PROMPTS = {
    "campaign_strategist": (
        "Kamu adalah Campaign Strategist SIDIX. Evaluasi copy berikut dari perspektif strategi:\n"
        "1. Apakah pesan selaras dengan AARRR funnel?\n"
        "2. Apakah ada CTA yang jelas?\n"
        "3. Apakah tone sesuai target audiens?\n"
        "Beri skor 1-10. Jika skor < 7, berikan 2-3 poin perbaikan konkret.\n\n"
        "COPY:\n{prototype}\n\nKONTEKS:\n{context}\n\n"
        "Jawab format: SKOR:[1-10] | APPROVE:[ya/tidak] | KRITIK:[poin perbaikan atau 'approved']"
    ),
    "design_critic": (
        "Kamu adalah Design Critic SIDIX. Evaluasi brand kit ini dari perspektif desain:\n"
        "1. Apakah voice tone konsisten?\n"
        "2. Apakah archetype selaras dengan target pasar?\n"
        "3. Apakah ada inkonsistensi identitas?\n"
        "Beri skor 1-10. Jika skor < 7, berikan 2-3 poin perbaikan.\n\n"
        "BRAND KIT:\n{prototype}\n\nKONTEKS:\n{context}\n\n"
        "Jawab format: SKOR:[1-10] | APPROVE:[ya/tidak] | KRITIK:[poin perbaikan atau 'approved']"
    ),
    "audience_lens": (
        "Kamu adalah Audience Analyst SIDIX. Evaluasi script/hook ini dari perspektif audiens:\n"
        "1. Apakah hook relevan untuk audiens Indonesia?\n"
        "2. Apakah bahasa natural (bukan terjemahan)?\n"
        "3. Apakah opening 3 detik menarik perhatian?\n"
        "Beri skor 1-10. Jika skor < 7, berikan 2-3 poin perbaikan.\n\n"
        "SCRIPT:\n{prototype}\n\nKONTEKS:\n{context}\n\n"
        "Jawab format: SKOR:[1-10] | APPROVE:[ya/tidak] | KRITIK:[poin perbaikan atau 'approved']"
    ),
}

_CREATOR_PROMPTS = {
    "copywriter": (
        "Kamu adalah Copywriter SIDIX. Revisi copy ini berdasarkan kritik:\n\n"
        "COPY SEBELUMNYA:\n{prototype}\n\n"
        "KRITIK DITERIMA:\n{critique}\n\n"
        "Tulis ulang copy yang lebih kuat. Pertahankan formula asli, perbaiki kelemahan."
    ),
    "brand_builder": (
        "Kamu adalah Brand Builder SIDIX. Revisi brand kit ini berdasarkan kritik:\n\n"
        "BRAND KIT SEBELUMNYA:\n{prototype}\n\n"
        "KRITIK DITERIMA:\n{critique}\n\n"
        "Perkuat konsistensi identitas brand. Selaraskan voice, archetype, dan tone."
    ),
    "script_hook": (
        "Kamu adalah Script Writer SIDIX. Revisi hook ini berdasarkan kritik:\n\n"
        "HOOK SEBELUMNYA:\n{prototype}\n\n"
        "KRITIK DITERIMA:\n{critique}\n\n"
        "Tulis ulang hook yang lebih kuat untuk audiens Indonesia. Natural, tidak robotic."
    ),
}


# ── Data models ────────────────────────────────────────────────────────────────
@dataclass
class DebateRound:
    round_num: int
    critic_agent: str
    creator_agent: str
    critique: str
    revised_prototype: str
    cqf_score: float
    approved: bool


@dataclass
class DebateResult:
    pair_id: str
    final_prototype: str
    consensus: bool
    rounds_taken: int
    final_cqf: float
    transcript: list[dict] = field(default_factory=list)
    elapsed_s: float = 0.0


# ── Core debate logic ──────────────────────────────────────────────────────────
def _parse_critic_response(response: str) -> tuple[float, bool, str]:
    """Parse 'SKOR:X | APPROVE:ya/tidak | KRITIK:...' → (score, approved, critique)."""
    import re
    score = 5.0
    approved = False
    critique = response

    m_score = re.search(r"SKOR:\s*(\d+(?:\.\d+)?)", response, re.IGNORECASE)
    if m_score:
        score = min(10.0, float(m_score.group(1)))

    m_approve = re.search(r"APPROVE:\s*(ya|tidak|yes|no)", response, re.IGNORECASE)
    if m_approve:
        approved = m_approve.group(1).lower() in ("ya", "yes")

    m_critique = re.search(r"KRITIK:\s*(.+)", response, re.IGNORECASE | re.DOTALL)
    if m_critique:
        critique = m_critique.group(1).strip()

    # fallback: jika score ≥ 7 → auto approve
    if score >= 7.0:
        approved = True

    return score, approved, critique


def run_debate(
    *,
    pair_id: str,
    creator_agent: str,
    critic_agent: str,
    prototype: str,
    context: str = "",
    domain: str = "content",
    max_rounds: int = 3,
    threshold: float = DELIVERY_THRESHOLD,
) -> DebateResult:
    """
    Jalankan debate antara creator ↔ critic.

    pair_id contoh: 'copywriter_vs_strategist'
    """
    start = time.time()
    transcript: list[dict] = []
    current = prototype
    consensus = False
    rounds_taken = 0

    # Ambil prompt templates
    critic_tmpl = _CRITIC_PROMPTS.get(
        critic_agent,
        "Evaluasi output berikut:\n{prototype}\nKONTEKS:{context}\n"
        "SKOR:[1-10] | APPROVE:[ya/tidak] | KRITIK:[catatan]"
    )
    creator_tmpl = _CREATOR_PROMPTS.get(
        creator_agent,
        "Revisi output berikut berdasarkan kritik:\n{prototype}\nKRITIK:{critique}\n"
        "Tulis ulang yang lebih baik."
    )

    for round_num in range(1, max_rounds + 1):
        rounds_taken = round_num
        logger.info("[DebateRing] Round %d — %s critiques %s", round_num, critic_agent, creator_agent)

        # ── Critic evaluates ──────────────────────────────────────────────────
        critic_prompt = critic_tmpl.format(prototype=current[:600], context=context[:200])
        critic_response = _llm_call(critic_prompt, max_tokens=256)
        score, approved, critique = _parse_critic_response(critic_response)

        # Also run CQF heuristic untuk double-check
        gate = quality_gate(current, brief=context or pair_id, domain=domain, use_llm=False)
        cqf_score = gate["total"]
        if cqf_score >= threshold:
            approved = True

        transcript.append({
            "round": round_num,
            "speaker": critic_agent,
            "action": "critique",
            "llm_score": round(score, 2),
            "cqf_score": round(cqf_score, 2),
            "approved": approved,
            "critique_preview": critique[:200],
        })

        if approved:
            logger.info("[DebateRing] Konsensus tercapai round %d, cqf=%.2f", round_num, cqf_score)
            consensus = True
            break

        if round_num == max_rounds:
            logger.warning("[DebateRing] Max round tercapai tanpa konsensus, cqf=%.2f", cqf_score)
            break

        # ── Creator revises ───────────────────────────────────────────────────
        creator_prompt = creator_tmpl.format(prototype=current[:600], critique=critique[:300])
        revised = _llm_call(creator_prompt, max_tokens=512)

        # pastikan hasil revisi tidak kosong
        if len(revised.strip()) > 20:
            current = revised

        transcript.append({
            "round": round_num,
            "speaker": creator_agent,
            "action": "revision",
            "revised_preview": current[:200],
        })

    final_gate = quality_gate(current, brief=context or pair_id, domain=domain, use_llm=False)

    return DebateResult(
        pair_id=pair_id,
        final_prototype=current,
        consensus=consensus,
        rounds_taken=rounds_taken,
        final_cqf=final_gate["total"],
        transcript=transcript,
        elapsed_s=round(time.time() - start, 2),
    )


# ── 3 Standard Debate Pairs ───────────────────────────────────────────────────
def debate_copy_vs_strategy(copy_text: str, context: str = "") -> DebateResult:
    """Pair 1: Copywriter ↔ Campaign Strategist."""
    return run_debate(
        pair_id="copywriter_vs_strategist",
        creator_agent="copywriter",
        critic_agent="campaign_strategist",
        prototype=copy_text,
        context=context,
        domain="content",
    )


def debate_brand_vs_design(brand_text: str, context: str = "") -> DebateResult:
    """Pair 2: Brand Builder ↔ Design Critic."""
    return run_debate(
        pair_id="brand_vs_design",
        creator_agent="brand_builder",
        critic_agent="design_critic",
        prototype=brand_text,
        context=context,
        domain="design",
    )


def debate_hook_vs_audience(hook_text: str, context: str = "") -> DebateResult:
    """Pair 3: Script Hook ↔ Audience Lens."""
    return run_debate(
        pair_id="hook_vs_audience",
        creator_agent="script_hook",
        critic_agent="audience_lens",
        prototype=hook_text,
        context=context,
        domain="content",
    )


def run_debate_as_dict(result: DebateResult) -> dict:
    """Serialize DebateResult ke dict untuk API response."""
    return {
        "pair_id": result.pair_id,
        "consensus": result.consensus,
        "rounds_taken": result.rounds_taken,
        "final_cqf": result.final_cqf,
        "final_prototype": result.final_prototype,
        "elapsed_s": result.elapsed_s,
        "transcript": result.transcript,
    }
