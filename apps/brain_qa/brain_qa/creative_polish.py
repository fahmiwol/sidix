"""
creative_polish.py — Sprint H: Creative Output Polish

Arsitektur:
  Creative Polish = iteration loop yang memperbaiki kualitas output Pencipta
  sebelum di-ship ke user atau di-store ke corpus.

Flow:
  1. evaluate_quality(output) → 4-dimension score (originality, clarity, usefulness, maqashid)
  2. generate_feedback(scores) → structured improvement suggestions
  3. polish_output(output, feedback) → LLM rewrite dengan guidance
  4. iterate_polish(output, max_iter=3) → loop sampai convergen

Integration:
  - Dipanggil oleh run_pencipta() sebelum save_output()
  - Bisa dipanggil manual via endpoint /agent/pencipta/polish

Storage:
  - Polish history: brain/public/pencipta/polish_history.jsonl

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("sidix.creative_polish")


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class QualityScore:
    """4-dimension quality score untuk creative output."""
    originality: float   # 0-1, seberapa unik vs existing corpus
    clarity: float       # 0-1, seberapa jelas struktur & bahasa
    usefulness: float    # 0-1, seberapa actionable / applicable
    maqashid: float      # 0-1, alignment dengan 5 sumbu Maqashid
    composite: float     # weighted average
    feedback: str        # structured improvement suggestions


@dataclass
class PolishResult:
    """Result dari satu iteration polish."""
    iteration: int
    input_content: str
    output_content: str
    scores_before: QualityScore
    scores_after: QualityScore
    improvement: float   # delta composite
    converged: bool      # True kalau improvement < threshold


# ── Storage ──────────────────────────────────────────────────────────────

POLISH_DIR = Path("brain/public/pencipta")
POLISH_HISTORY_PATH = POLISH_DIR / "polish_history.jsonl"


# ── Quality Evaluation ───────────────────────────────────────────────────

_EVAL_PROMPT_TEMPLATE = """Kamu adalah kurator kualitas kreatif. Evaluasi output berikut di 4 dimensi:

Output:
---
{content}
---

Beri skor 0.0–1.0 dan 1 kalimat feedback per dimensi:
1. Originality — seberapa unik dan novel?
2. Clarity — seberapa jelas struktur dan bahasa?
3. Usefulness — seberapa actionable dan applicable?
4. Maqashid — seberapa selaras dengan nilai kehidupan, ilmu, iman, keturunan, kekayaan?

Format HARUS:
Originality: <score> | <feedback>
Clarity: <score> | <feedback>
Usefulness: <score> | <feedback>
Maqashid: <score> | <feedback>
Composite: <score>"""


def _call_llm(prompt: str, max_tokens: int = 600, temperature: float = 0.4) -> str:
    """Lightweight LLM call via Ollama."""
    try:
        from .ollama_llm import ollama_generate
        response, _mode = ollama_generate(
            prompt,
            system="",
            model="qwen2.5:1.5b",
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response or ""
    except Exception as e:
        log.warning("[creative_polish] LLM call failed: %s", e)
        return ""


def _parse_eval_response(text: str) -> QualityScore:
    """Parse evaluation response ke QualityScore."""
    scores = {"originality": 0.5, "clarity": 0.5, "usefulness": 0.5, "maqashid": 0.5}
    feedback_parts = []

    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'(Originality|Clarity|Usefulness|Maqashid):\s*([0-9.]+)\s*\|\s*(.+)', line, re.I)
        if m:
            dim = m.group(1).lower()
            score = float(m.group(2))
            fb = m.group(3).strip()
            scores[dim] = min(1.0, max(0.0, score))
            feedback_parts.append(f"{dim}: {fb}")

    # Composite = weighted average
    composite = (
        scores["originality"] * 0.25 +
        scores["clarity"] * 0.25 +
        scores["usefulness"] * 0.30 +
        scores["maqashid"] * 0.20
    )

    return QualityScore(
        originality=scores["originality"],
        clarity=scores["clarity"],
        usefulness=scores["usefulness"],
        maqashid=scores["maqashid"],
        composite=round(composite, 3),
        feedback="; ".join(feedback_parts) or "No feedback parsed",
    )


def evaluate_quality(content: str) -> QualityScore:
    """Evaluate creative content quality via LLM."""
    prompt = _EVAL_PROMPT_TEMPLATE.format(content=content[:2000])
    response = _call_llm(prompt, max_tokens=400, temperature=0.3)
    return _parse_eval_response(response)


# ── Polish / Rewrite ─────────────────────────────────────────────────────

_POLISH_PROMPT_TEMPLATE = """Kamu adalah editor kreatif senior. Perbaiki output berikut berdasarkan feedback:

Output Asli:
---
{content}
---

Feedback:
{feedback}

Instruksi:
- Pertahankan ide inti dan struktur
- Perbaiki kelemahan yang disebutkan feedback
- Tambah detail konkret di bagian yang vague
- Pastikan bahasa Indonesia natural dan fasih
- Output HANYA versi perbaikan, tanpa penjelasan

Versi Perbaikan:"""


def polish_output(content: str, feedback: str) -> str:
    """Rewrite content dengan improvement guidance."""
    prompt = _POLISH_PROMPT_TEMPLATE.format(
        content=content[:2000],
        feedback=feedback[:800],
    )
    return _call_llm(prompt, max_tokens=900, temperature=0.5)


# ── Iteration Loop ───────────────────────────────────────────────────────

def iterate_polish(
    content: str,
    max_iterations: int = 3,
    convergence_threshold: float = 0.03,
) -> list[PolishResult]:
    """Iterate evaluate → polish sampai convergen atau max iter.

    Returns list of PolishResult per iteration.
    """
    results = []
    current = content
    prev_score = None

    for i in range(1, max_iterations + 1):
        log.info("[creative_polish] Iteration %d starting...", i)

        # Evaluate current
        scores_before = evaluate_quality(current)
        if prev_score is None:
            prev_score = scores_before

        # Polish
        improved = polish_output(current, scores_before.feedback)
        if not improved or improved.strip() == current.strip():
            log.info("[creative_polish] No change at iteration %d", i)
            break

        # Evaluate improved
        scores_after = evaluate_quality(improved)
        improvement = scores_after.composite - scores_before.composite
        converged = improvement < convergence_threshold

        result = PolishResult(
            iteration=i,
            input_content=current[:500],
            output_content=improved[:500],
            scores_before=scores_before,
            scores_after=scores_after,
            improvement=round(improvement, 3),
            converged=converged,
        )
        results.append(result)
        _persist_polish(result)

        log.info(
            "[creative_polish] Iteration %d: composite %.2f → %.2f (Δ %.3f) %s",
            i, scores_before.composite, scores_after.composite,
            improvement, "CONVERGED" if converged else "CONTINUE",
        )

        current = improved
        prev_score = scores_after

        if converged:
            break

    return results


def _persist_polish(result: PolishResult) -> None:
    """Append polish result to history."""
    try:
        POLISH_DIR.mkdir(parents=True, exist_ok=True)
        with POLISH_HISTORY_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
    except Exception as e:
        log.debug("[creative_polish] Persist failed: %s", e)


# ── Stats ────────────────────────────────────────────────────────────────

def get_polish_stats() -> dict:
    """Aggregate polish history stats."""
    if not POLISH_HISTORY_PATH.exists():
        return {"total_polishes": 0, "avg_improvement": 0.0, "convergence_rate": 0.0}

    entries = []
    for line in POLISH_HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines():
        try:
            entries.append(json.loads(line))
        except Exception:
            continue

    if not entries:
        return {"total_polishes": 0, "avg_improvement": 0.0, "convergence_rate": 0.0}

    improvements = [e.get("improvement", 0) for e in entries]
    converged = sum(1 for e in entries if e.get("converged"))
    return {
        "total_polishes": len(entries),
        "avg_improvement": round(sum(improvements) / len(improvements), 3),
        "convergence_rate": round(converged / len(entries), 2),
    }
