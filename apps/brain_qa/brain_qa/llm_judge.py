"""
llm_judge.py — SIDIX LLM-as-Judge Evaluator (Sprint 5)

Tujuan: evaluasi output creative agents secara eksplisit, dapat-diaudit,
        lebih kaya konteks daripada CQF heuristic saja.

Pipeline:
  content + brief + domain + criteria
    → build evaluation prompt
    → LLM call (local_llm → multi_llm_router → heuristic fallback)
    → parse scores per criterion
    → return {ok, scores, total, tier, rationale, recommendation, elapsed_s}

Default criteria per domain:
  content  — hook_strength, message_clarity, cta_effectiveness,
             engagement_potential, authenticity
  brand    — voice_consistency, archetype_alignment, differentiation,
             memorability, trustworthiness
  campaign — strategic_clarity, funnel_alignment, budget_efficiency,
             conversion_focus, measurability
  design   — visual_hierarchy, brand_consistency, audience_appeal,
             cta_prominence, originality

Score format: 0.0–10.0 per criterion, average = total.
  total ≥ 8.5 → tier "premium"
  total ≥ 7.0 → tier "delivery"
  total < 7.0 → tier "needs_work"
"""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

logger = logging.getLogger("sidix.llm_judge")

# ── Default criteria per domain ───────────────────────────────────────────────
DOMAIN_CRITERIA: dict[str, list[str]] = {
    "content": [
        "hook_strength",
        "message_clarity",
        "cta_effectiveness",
        "engagement_potential",
        "authenticity",
    ],
    "brand": [
        "voice_consistency",
        "archetype_alignment",
        "differentiation",
        "memorability",
        "trustworthiness",
    ],
    "campaign": [
        "strategic_clarity",
        "funnel_alignment",
        "budget_efficiency",
        "conversion_focus",
        "measurability",
    ],
    "design": [
        "visual_hierarchy",
        "brand_consistency",
        "audience_appeal",
        "cta_prominence",
        "originality",
    ],
}

# Tier thresholds
PREMIUM_THRESHOLD = 8.5
DELIVERY_THRESHOLD = 7.0


# ── LLM helper — graceful fallback (pola sama dengan debate_ring.py) ──────────
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

    # 3. Fallback — return sentinel untuk heuristic scoring
    logger.warning("llm_judge: semua LLM unavailable, pakai heuristic fallback")
    return "__HEURISTIC_FALLBACK__"


# ── Prompt builder ─────────────────────────────────────────────────────────────
def _build_judge_prompt(
    content: str,
    brief: str,
    domain: str,
    criteria: list[str],
) -> str:
    """Build prompt untuk LLM-as-Judge evaluation."""
    criteria_str = "\n".join(f"- {c}: skor 0.0–10.0" for c in criteria)
    brief_str = f"BRIEF / KONTEKS:\n{brief[:400]}\n\n" if brief else ""

    return (
        f"Kamu adalah evaluator konten profesional (LLM-as-Judge). "
        f"Nilai output berikut secara objektif dan eksplisit.\n\n"
        f"{brief_str}"
        f"DOMAIN: {domain}\n\n"
        f"KONTEN YANG DIEVALUASI:\n{content[:800]}\n\n"
        f"Berikan skor untuk setiap kriteria berikut:\n{criteria_str}\n\n"
        f"Format jawaban WAJIB:\n"
        f"SKOR:\n"
        + "\n".join(f"{c}: [0.0-10.0]" for c in criteria)
        + "\n\nRATIONALE: [penjelasan singkat evaluasi]\n"
        f"REKOMENDASI: [saran perbaikan konkret atau 'sudah baik']"
    )


def _build_compare_prompt(
    variants: list[str],
    brief: str,
    domain: str,
    criteria: list[str],
) -> str:
    """Build prompt untuk perbandingan beberapa variant."""
    criteria_str = ", ".join(criteria)
    brief_str = f"BRIEF:\n{brief[:300]}\n\n" if brief else ""
    variants_str = "\n\n".join(
        f"VARIANT {i+1}:\n{v[:400]}" for i, v in enumerate(variants)
    )

    return (
        f"Kamu adalah evaluator konten (LLM-as-Judge). "
        f"Bandingkan {len(variants)} variant konten berikut.\n\n"
        f"{brief_str}"
        f"DOMAIN: {domain} | Kriteria: {criteria_str}\n\n"
        f"{variants_str}\n\n"
        f"Jawab format:\n"
        f"WINNER: [nomor variant terbaik, misal: 2]\n"
        f"REASONING: [kenapa variant itu terbaik]\n"
        f"SCORES_V1: [skor rata-rata 0.0-10.0 untuk variant 1]\n"
        + "\n".join(f"SCORES_V{i+1}: [skor 0.0-10.0]" for i in range(1, len(variants)))
    )


# ── Response parsers ─────────────────────────────────────────────────────────
def _parse_judge_response(
    response: str,
    criteria: list[str],
) -> tuple[dict[str, float], str, str]:
    """
    Parse LLM judge response.
    Returns: (scores_dict, rationale, recommendation)
    """
    scores: dict[str, float] = {}
    rationale = ""
    recommendation = ""

    # Extract scores per criterion
    for criterion in criteria:
        # Match: "criterion_name: 8.5" atau "criterion_name : 8"
        pattern = rf"{re.escape(criterion)}\s*[:=]\s*(\d+(?:\.\d+)?)"
        m = re.search(pattern, response, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            scores[criterion] = max(0.0, min(10.0, val))
        else:
            scores[criterion] = 6.5  # default netral jika tidak ditemukan

    # Extract rationale
    m_rat = re.search(r"RATIONALE\s*:\s*(.+?)(?=REKOMENDASI|$)", response, re.IGNORECASE | re.DOTALL)
    if m_rat:
        rationale = m_rat.group(1).strip()[:500]

    # Extract recommendation
    m_rec = re.search(r"REKOMENDASI\s*:\s*(.+?)$", response, re.IGNORECASE | re.DOTALL)
    if m_rec:
        recommendation = m_rec.group(1).strip()[:300]

    return scores, rationale, recommendation


def _parse_compare_response(
    response: str,
    n_variants: int,
) -> tuple[int, str, list[float]]:
    """
    Parse comparison response.
    Returns: (winner_idx_0based, reasoning, scores_per_variant)
    """
    winner_idx = 0  # default variant 1
    reasoning = ""
    scores: list[float] = [6.5] * n_variants

    # Winner
    m_win = re.search(r"WINNER\s*:\s*(\d+)", response, re.IGNORECASE)
    if m_win:
        idx = int(m_win.group(1)) - 1  # convert to 0-based
        winner_idx = max(0, min(idx, n_variants - 1))

    # Reasoning
    m_reas = re.search(r"REASONING\s*:\s*(.+?)(?=SCORES_|$)", response, re.IGNORECASE | re.DOTALL)
    if m_reas:
        reasoning = m_reas.group(1).strip()[:400]

    # Scores per variant
    for i in range(n_variants):
        m_s = re.search(rf"SCORES_V{i+1}\s*:\s*(\d+(?:\.\d+)?)", response, re.IGNORECASE)
        if m_s:
            scores[i] = max(0.0, min(10.0, float(m_s.group(1))))

    return winner_idx, reasoning, scores


# ── Heuristic fallback scorer ─────────────────────────────────────────────────
def _heuristic_score(
    content: str,
    brief: str,
    criteria: list[str],
) -> tuple[dict[str, float], str, str]:
    """
    Fallback saat LLM unavailable. Gunakan quality_gate dari creative_quality
    sebagai proxy, map ke format judge output.
    """
    try:
        from .creative_quality import quality_gate
        gate = quality_gate(content, brief=brief, domain="content", use_llm=False)
        base_score = gate.get("total", 6.5)
        cqf_detail = gate.get("score", {})
    except Exception:
        base_score = 6.5
        cqf_detail = {}

    # Map CQF dimensions ke criteria
    cqf_map = {
        "hook_strength": cqf_detail.get("relevance", base_score),
        "message_clarity": cqf_detail.get("quality", base_score),
        "cta_effectiveness": cqf_detail.get("actionability", base_score),
        "engagement_potential": cqf_detail.get("creativity", base_score),
        "authenticity": cqf_detail.get("brand_alignment", base_score),
        # brand criteria
        "voice_consistency": cqf_detail.get("brand_alignment", base_score),
        "archetype_alignment": cqf_detail.get("brand_alignment", base_score),
        "differentiation": cqf_detail.get("creativity", base_score),
        "memorability": cqf_detail.get("creativity", base_score),
        "trustworthiness": cqf_detail.get("quality", base_score),
        # campaign criteria
        "strategic_clarity": cqf_detail.get("quality", base_score),
        "funnel_alignment": cqf_detail.get("relevance", base_score),
        "budget_efficiency": cqf_detail.get("actionability", base_score),
        "conversion_focus": cqf_detail.get("actionability", base_score),
        "measurability": cqf_detail.get("quality", base_score),
        # design criteria
        "visual_hierarchy": cqf_detail.get("quality", base_score),
        "brand_consistency": cqf_detail.get("brand_alignment", base_score),
        "audience_appeal": cqf_detail.get("relevance", base_score),
        "cta_prominence": cqf_detail.get("actionability", base_score),
        "originality": cqf_detail.get("creativity", base_score),
    }

    scores = {c: round(cqf_map.get(c, base_score), 2) for c in criteria}
    rationale = (
        f"[Heuristic fallback via CQF] Base score: {base_score:.1f}. "
        f"LLM tidak tersedia saat evaluasi."
    )
    hints = gate.get("refinement_hints", []) if "gate" in dir() else []
    recommendation = "; ".join(hints[:3]) if hints else "Tidak ada rekomendasi spesifik (heuristic mode)."

    return scores, rationale, recommendation


# ── Core judge function ───────────────────────────────────────────────────────
def judge_content(
    content: str,
    brief: str = "",
    domain: str = "content",
    criteria: Optional[list[str]] = None,
    model_override: Optional[str] = None,
) -> dict:
    """
    Minta LLM untuk menilai content secara eksplisit.

    Args:
        content: konten yang akan dievaluasi
        brief: konteks / brief (opsional tapi sangat membantu)
        domain: "content" | "brand" | "campaign" | "design"
        criteria: custom criteria; jika None → pakai default per domain
        model_override: (future use) override model tertentu

    Returns:
        {
            ok: bool,
            scores: {criterion: score},
            total: float,
            tier: "premium" | "delivery" | "needs_work",
            rationale: str,
            recommendation: str,
            elapsed_s: float,
            mode: "llm" | "heuristic",
        }
    """
    start = time.time()

    if not content or not content.strip():
        return {"ok": False, "error": "content wajib diisi", "elapsed_s": 0.0}

    # Tentukan criteria
    effective_domain = domain if domain in DOMAIN_CRITERIA else "content"
    effective_criteria = criteria if criteria else DOMAIN_CRITERIA[effective_domain]

    # Build prompt dan call LLM
    prompt = _build_judge_prompt(content, brief, effective_domain, effective_criteria)
    response = _llm_call(prompt, max_tokens=512)

    # Tentukan mode dan parse
    mode = "llm"
    if response == "__HEURISTIC_FALLBACK__":
        mode = "heuristic"
        scores, rationale, recommendation = _heuristic_score(content, brief, effective_criteria)
    else:
        scores, rationale, recommendation = _parse_judge_response(response, effective_criteria)

    # Hitung total
    total = round(sum(scores.values()) / max(1, len(scores)), 2) if scores else 0.0

    # Tentukan tier
    if total >= PREMIUM_THRESHOLD:
        tier = "premium"
    elif total >= DELIVERY_THRESHOLD:
        tier = "delivery"
    else:
        tier = "needs_work"

    elapsed = round(time.time() - start, 3)

    logger.info(
        "judge_content: domain=%s total=%.2f tier=%s mode=%s elapsed=%.2fs",
        effective_domain, total, tier, mode, elapsed,
    )

    return {
        "ok": True,
        "scores": scores,
        "total": total,
        "tier": tier,
        "rationale": rationale,
        "recommendation": recommendation,
        "elapsed_s": elapsed,
        "mode": mode,
        "domain": effective_domain,
        "criteria": effective_criteria,
    }


def judge_batch(
    items: list[dict],
    concurrency: int = 3,
) -> list[dict]:
    """
    Jalankan judge_content untuk banyak item secara paralel.

    Args:
        items: list of dicts, tiap item = {content, brief?, domain?}
        concurrency: max parallel workers (default 3)

    Returns:
        list[dict] — hasil judge per item, urutan sama dengan input
    """
    if not items:
        return []

    concurrency = max(1, min(concurrency, 10))
    results: list[dict] = [{}] * len(items)

    def _judge_one(idx: int, item: dict) -> tuple[int, dict]:
        r = judge_content(
            content=item.get("content", ""),
            brief=item.get("brief", ""),
            domain=item.get("domain", "content"),
            criteria=item.get("criteria"),
        )
        return idx, r

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_judge_one, i, item): i
            for i, item in enumerate(items)
        }
        for future in as_completed(futures):
            try:
                idx, result = future.result()
                results[idx] = result
            except Exception as exc:
                orig_idx = futures[future]
                results[orig_idx] = {
                    "ok": False,
                    "error": f"judge_batch item {orig_idx}: {exc}",
                }

    return results


def compare_variants(
    variants: list[str],
    brief: str,
    domain: str = "content",
) -> dict:
    """
    Bandingkan beberapa variant konten, pilih yang terbaik.

    Args:
        variants: list string konten yang akan dibandingkan (min 2)
        brief: konteks / brief
        domain: "content" | "brand" | "campaign" | "design"

    Returns:
        {
            ok: bool,
            winner_idx: int,  # 0-based index
            winner: str,      # konten pemenang
            scores: list[float],  # skor rata-rata per variant
            all_scores: list[dict],  # detail skor tiap variant
            rationale: str,
            elapsed_s: float,
        }
    """
    start = time.time()

    if not variants or len(variants) < 2:
        return {"ok": False, "error": "Minimal 2 variant diperlukan untuk perbandingan"}

    effective_domain = domain if domain in DOMAIN_CRITERIA else "content"
    effective_criteria = DOMAIN_CRITERIA[effective_domain]

    # Build compare prompt
    prompt = _build_compare_prompt(variants, brief, effective_domain, effective_criteria)
    response = _llm_call(prompt, max_tokens=400)

    winner_idx = 0
    reasoning = ""
    avg_scores: list[float] = []

    if response == "__HEURISTIC_FALLBACK__":
        # Score tiap variant secara heuristik
        all_results = judge_batch(
            [{"content": v, "brief": brief, "domain": domain} for v in variants],
            concurrency=min(len(variants), 4),
        )
        avg_scores = [r.get("total", 0.0) for r in all_results]
        winner_idx = avg_scores.index(max(avg_scores)) if avg_scores else 0
        reasoning = f"[Heuristic] Variant {winner_idx + 1} memiliki skor tertinggi ({avg_scores[winner_idx]:.2f})"
        all_detail_scores = [r.get("scores", {}) for r in all_results]
    else:
        winner_idx, reasoning, avg_scores = _parse_compare_response(response, len(variants))
        # Get detail scores per variant via individual judges
        all_results = judge_batch(
            [{"content": v, "brief": brief, "domain": domain} for v in variants],
            concurrency=min(len(variants), 4),
        )
        # Prefer LLM compare scores if parsed successfully
        for i, s in enumerate(avg_scores):
            if s == 6.5 and all_results[i].get("total"):
                avg_scores[i] = all_results[i]["total"]
        all_detail_scores = [r.get("scores", {}) for r in all_results]

    elapsed = round(time.time() - start, 3)

    return {
        "ok": True,
        "winner_idx": winner_idx,
        "winner": variants[winner_idx] if winner_idx < len(variants) else "",
        "scores": avg_scores,
        "all_scores": all_detail_scores,
        "rationale": reasoning,
        "elapsed_s": elapsed,
        "domain": effective_domain,
    }
