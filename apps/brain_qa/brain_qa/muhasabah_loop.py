"""
muhasabah_loop.py — Niyah → Amal → Muhasabah iteration wrapper.

Sprint 4: wrapper ringan agar agent generatif bisa refine sampai CQF minimum.
"""

from __future__ import annotations

from typing import Callable

from .creative_quality import quality_gate


def run_muhasabah_loop(
    *,
    brief: str,
    domain: str,
    generate_fn: Callable[[str], str],
    refine_fn: Callable[[str, list[str]], str] | None = None,
    max_rounds: int = 3,
    min_score: float = 7.0,
) -> dict:
    """
    Execute iterative generation:
    1) Niyah: brief
    2) Amal: generate output
    3) Muhasabah: quality gate + refine bila perlu
    """
    if not brief.strip():
        return {"ok": False, "error": "brief wajib diisi"}

    rounds = max(1, min(int(max_rounds), 5))
    history: list[dict] = []
    current = generate_fn(brief)

    for round_index in range(1, rounds + 1):
        gate = quality_gate(current, brief=brief, domain=domain, use_llm=False)
        history.append(
            {
                "round": round_index,
                "text_preview": current[:220],
                "score_total": gate["total"],
                "tier": gate["tier"],
                "needs_refinement": gate["needs_refinement"],
                "hints": gate["refinement_hints"],
            }
        )
        if gate["total"] >= float(min_score):
            # Flywheel L1: catat accepted output agar prompt_optimizer bisa belajar
            try:
                from .prompt_optimizer import log_accepted_output
                log_accepted_output(
                    agent=domain,
                    prompt_params={"brief": brief},
                    output_text=current,
                    score=gate["total"],
                    domain=domain,
                )
            except Exception:
                pass  # non-blocking
            return {
                "ok": True,
                "passed": True,
                "final_text": current,
                "final_score": gate["total"],
                "history": history,
                "loop_state": "stabilized",
            }
        if round_index == rounds:
            break
        if refine_fn is not None:
            current = refine_fn(current, gate["refinement_hints"])
        else:
            hints = "; ".join(gate["refinement_hints"][:3]) or "improve clarity"
            current = f"{current}\n\nRefinement: {hints}."

    return {
        "ok": True,
        "passed": False,
        "final_text": current,
        "final_score": history[-1]["score_total"] if history else 0.0,
        "history": history,
        "loop_state": "needs_human_review",
    }

