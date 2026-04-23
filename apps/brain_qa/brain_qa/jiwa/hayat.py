"""
Hayat — Self-Iteration System (Pilar 5)

Generate → Evaluate (CQF) → Refine → Repeat (max 3x, target CQF ≥ 8.0).

Wrapper tipis di atas muhasabah_loop.py yang sudah ada, dengan:
- Gate: hanya aktif untuk jawaban substantif (> 80 karakter)
- Skip: casual chat, salam, pertanyaan sangat pendek
- Timeout-safe: non-blocking, fallback ke jawaban asli jika refine gagal
"""

from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger("sidix.jiwa.hayat")

_MIN_ANSWER_LEN = 80   # minimal panjang jawaban agar iterasi dijalankan
_CQF_TARGET = 8.0
_MAX_ROUNDS = 2        # hemat inference — 2 round cukup untuk improvement awal


def hayat_refine(
    *,
    question: str,
    initial_answer: str,
    generate_fn: Callable[[str], str],
    domain: str = "generic",
    max_rounds: int = _MAX_ROUNDS,
    min_score: float = _CQF_TARGET,
) -> dict:
    """
    Jalankan self-iteration pada `initial_answer`.

    Args:
        question: pertanyaan original (jadi 'brief' untuk CQF)
        initial_answer: jawaban pertama dari Ollama/model
        generate_fn: callable(prompt) → str, dipakai untuk refinement
        domain: domain CQF (generic / copywriting / education / etc)
        max_rounds: maksimum iterasi
        min_score: target CQF score

    Returns:
        dict dengan key:
            "final": str — jawaban terbaik
            "score": float — CQF score final
            "rounds": int — berapa round dijalankan
            "improved": bool — apakah jawaban membaik
    """
    # Gate: skip kalau jawaban terlalu pendek
    if len((initial_answer or "").strip()) < _MIN_ANSWER_LEN:
        return {
            "final": initial_answer,
            "score": 0.0,
            "rounds": 0,
            "improved": False,
            "skipped": "too_short",
        }

    try:
        from ..muhasabah_loop import run_muhasabah_loop

        def _gen_fn(brief: str) -> str:
            return initial_answer  # start dari jawaban yang sudah ada

        def _refine_fn(current: str, hints: list[str]) -> str:
            hint_text = "; ".join(hints) if hints else "tingkatkan kualitas dan kedalaman jawaban"
            refine_prompt = (
                f"Pertanyaan: {question}\n\n"
                f"Jawaban sebelumnya:\n{current}\n\n"
                f"Feedback untuk perbaikan: {hint_text}\n\n"
                "Tulis ulang jawaban yang lebih baik, lebih lengkap, dan lebih berkarakter:"
            )
            result = generate_fn(refine_prompt)
            return result if result and len(result) > 50 else current

        result = run_muhasabah_loop(
            brief=question,
            domain=domain,
            generate_fn=_gen_fn,
            refine_fn=_refine_fn,
            max_rounds=max_rounds,
            min_score=min_score,
        )

        final = result.get("final", initial_answer) or initial_answer
        score = result.get("score_final", 0.0)
        rounds = len(result.get("history", []))
        improved = final != initial_answer and len(final) >= len(initial_answer) * 0.8

        if improved:
            log.info(f"Hayat improved answer — rounds={rounds} score={score:.1f}")

        return {
            "final": final,
            "score": score,
            "rounds": rounds,
            "improved": improved,
        }

    except Exception as exc:
        log.warning(f"Hayat iteration failed (non-blocking): {exc}")
        return {
            "final": initial_answer,
            "score": 0.0,
            "rounds": 0,
            "improved": False,
            "error": str(exc),
        }
