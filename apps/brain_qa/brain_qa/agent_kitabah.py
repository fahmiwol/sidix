"""
agent_kitabah.py — Sprint 22: KITABAH Auto-iterate (Generation-Test Validation Loop)

Per note 248 line 109-114 EKSPLISIT (Wahdah/Kitabah/ODOA self-learning protocol):
  "WAHDAH    → deep focus iteration (training berulang sampai jadi 'refleks')
   KITABAH   → generation-test validation (produce → validate own output)
   ODOA      → incremental innovation (One Day One Achievement)"

Sprint 22 implements **KITABAH** pattern: automated creative refinement loop.

Pre-Execution Alignment Check (per CLAUDE.md 6.4):
- Note 248 line 109-114 EXPLICIT KITABAH mandate ✓
- Compound Sprint 14 (creative) + Sprint 21 (RASA) — orchestrator only ✓
- Pivot 2026-04-25: workflow orchestration, no persona prompt change ✓
- 10 hard rules: own LLM, 5 persona, MIT, self-hosted ✓
- Anti-halusinasi: RASA validation grounded di artifact existing ✓
- Budget: max 3 iterations cap = controlled burn ✓

Loop algorithm:
  1. iter=0: run creative_brief_pipeline(brief, with prior improvement context if any)
  2. Run rasa_score(slug)
  3. Track (iter, overall_score, top_priority_improvement) ke history
  4. If overall_score >= threshold OR iter >= max_iter → STOP, return best
  5. Else: extract top_priority_improvement → augment context → iter++ → goto 1

Output: best iteration (highest overall_score) + full history.

Public API:
  kitabah_iterate(brief, max_iter=3, score_threshold=4.0, persist=True) -> dict
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
KITABAH_LOOPS_DIR = DATA_DIR / "kitabah_loops"


def _slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "topic"


# ── Iteration core ──────────────────────────────────────────────────────────

@dataclass
class IterationStep:
    iteration: int
    creative_slug: str
    rasa_overall_score: Optional[float]
    rasa_verdict: Optional[str]
    top_priority_improvement: Optional[str]
    creative_paths: dict[str, str] = field(default_factory=dict)
    rasa_paths: dict[str, str] = field(default_factory=dict)
    elapsed_ms: int = 0


def kitabah_iterate(
    brief: str,
    *,
    max_iter: int = 3,
    score_threshold: float = 4.0,
    persist: bool = True,
) -> dict[str, Any]:
    """KITABAH self-iteration loop: creative produce → RASA validate → iterate.

    Args:
      brief: input brief teks
      max_iter: cap iterations (default 3, budget control)
      score_threshold: stop kalau overall_score >= threshold (default 4.0)
      persist: save loop history
    """
    if not (brief or "").strip():
        raise ValueError("brief kosong")

    # Lazy import inside function so test can mock
    from .creative_pipeline import creative_brief_pipeline
    from .agent_rasa import rasa_score

    base_slug = _slugify(brief)
    ts = datetime.now(timezone.utc).isoformat()

    history: list[IterationStep] = []
    current_brief = brief
    accumulated_improvements: list[str] = []
    best_iter: Optional[IterationStep] = None

    for iteration in range(max_iter):
        import time as _t
        t0 = _t.time()

        # Build brief untuk this iteration
        if accumulated_improvements:
            improvement_context = "\n".join(
                f"- Iter {i+1}: {imp}"
                for i, imp in enumerate(accumulated_improvements)
            )
            iter_brief = (
                f"{brief}\n\n"
                f"REFINEMENT FROM PRIOR ITERATIONS (apply these improvements):\n"
                f"{improvement_context}"
            )
        else:
            iter_brief = brief

        # Step 1: Run creative
        try:
            creative_result = creative_brief_pipeline(
                iter_brief,
                # Slug akan beda tiap iter karena brief beda (kecuali iter 0)
                persist=True,
            )
            creative_slug = creative_result.get("slug")
            creative_paths = creative_result.get("paths", {})
        except Exception as e:
            history.append(IterationStep(
                iteration=iteration + 1,
                creative_slug="",
                rasa_overall_score=None,
                rasa_verdict=None,
                top_priority_improvement=None,
                elapsed_ms=int((_t.time() - t0) * 1000),
                creative_paths={},
                rasa_paths={},
            ))
            break

        # Step 2: Run RASA
        try:
            rasa_result = rasa_score(creative_slug, persist=True)
            if rasa_result.get("success"):
                structured = rasa_result.get("structured", {})
                overall = structured.get("overall_score")
                verdict = structured.get("verdict")
                improvement = structured.get("top_priority_improvement")
                rasa_paths = rasa_result.get("paths", {})
            else:
                overall = None
                verdict = None
                improvement = None
                rasa_paths = {}
        except Exception:
            overall = None
            verdict = None
            improvement = None
            rasa_paths = {}

        elapsed_ms = int((_t.time() - t0) * 1000)
        step = IterationStep(
            iteration=iteration + 1,
            creative_slug=creative_slug,
            rasa_overall_score=overall,
            rasa_verdict=verdict,
            top_priority_improvement=improvement,
            creative_paths=creative_paths,
            rasa_paths=rasa_paths,
            elapsed_ms=elapsed_ms,
        )
        history.append(step)

        # Track best (highest score)
        if overall is not None:
            if best_iter is None or (best_iter.rasa_overall_score or 0) < overall:
                best_iter = step

        # Stop conditions
        if overall is not None and overall >= score_threshold:
            break  # Achieved target quality

        if improvement:
            accumulated_improvements.append(improvement)
        else:
            break  # No improvement direction = can't iterate productively

    result = {
        "brief": brief,
        "base_slug": base_slug,
        "ts": ts,
        "max_iter": max_iter,
        "score_threshold": score_threshold,
        "iterations_run": len(history),
        "history": [asdict(s) for s in history],
        "best_iteration": asdict(best_iter) if best_iter else None,
        "stopped_reason": _stop_reason(history, max_iter, score_threshold),
        "paths": {},
    }

    if persist:
        target = KITABAH_LOOPS_DIR / base_slug
        target.mkdir(parents=True, exist_ok=True)
        history_path = target / "history.json"
        history_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
        summary_md = _render_summary_md(result)
        summary_path = target / "summary.md"
        summary_path.write_text(summary_md, encoding="utf-8")
        result["paths"] = {
            "history": str(history_path),
            "summary": str(summary_path),
        }

    return result


def _stop_reason(
    history: list[IterationStep],
    max_iter: int,
    threshold: float,
) -> str:
    if not history:
        return "no iterations completed"
    last = history[-1]
    if last.rasa_overall_score is not None and last.rasa_overall_score >= threshold:
        return f"achieved threshold ({last.rasa_overall_score} >= {threshold})"
    if len(history) >= max_iter:
        return f"max iterations reached ({max_iter})"
    if last.top_priority_improvement is None:
        return "no improvement direction available"
    return "loop terminated"


def _render_summary_md(result: dict[str, Any]) -> str:
    lines = [
        f"# KITABAH Iteration Summary — {result['base_slug']}",
        "",
        f"_Generated_: {result['ts']}",
        f"_Brief_: {result['brief']}",
        f"_Pipeline_: SIDIX Sprint 22 / KITABAH (generation-test validation loop)",
        f"_Max iterations_: {result['max_iter']} · _Score threshold_: {result['score_threshold']}",
        f"_Iterations run_: {result['iterations_run']} · _Stopped_: {result['stopped_reason']}",
        "",
        "---",
        "",
        "## Iteration History",
        "",
        "| Iter | Slug | Overall Score | Verdict | Improvement |",
        "|---|---|---|---|---|",
    ]
    for step in result.get("history", []):
        score = step.get("rasa_overall_score") or "—"
        verdict = step.get("rasa_verdict") or "—"
        imp = (step.get("top_priority_improvement") or "—")[:80]
        slug_short = (step.get("creative_slug") or "")[:40]
        lines.append(
            f"| {step.get('iteration','?')} | {slug_short} | {score}/5 | {verdict} | {imp} |"
        )
    lines.append("")
    best = result.get("best_iteration")
    if best:
        lines.append("## Best Iteration")
        lines.append("")
        lines.append(f"- **Iter #{best.get('iteration','?')}** dengan score **{best.get('rasa_overall_score','?')}/5**")
        lines.append(f"- Verdict: `{best.get('rasa_verdict','?')}`")
        lines.append(f"- Slug: `{best.get('creative_slug','?')}`")
        creative_paths = best.get("creative_paths", {})
        if creative_paths.get("report"):
            lines.append(f"- Creative report: [`{creative_paths['report']}`]({creative_paths['report']})")
        rasa_paths = best.get("rasa_paths", {})
        if rasa_paths.get("report"):
            lines.append(f"- RASA report: [`{rasa_paths['report']}`]({rasa_paths['report']})")
    lines.append("")
    lines.append("## Workflow notes (KITABAH self-learning protocol)")
    lines.append("")
    lines.append("- KITABAH = produce → validate → iterate with own output as feedback")
    lines.append("- Per note 248 line 109-114 (Wahdah/Kitabah/ODOA self-learning protocol)")
    lines.append("- Customer benefit: AI self-critique without human creative director")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    brief = " ".join(sys.argv[1:]) or "Maskot brand makanan ringan kawaii ulat kuning untuk anak Indonesia"
    result = kitabah_iterate(brief, max_iter=2, score_threshold=4.5)
    print(json.dumps({
        "iterations_run": result["iterations_run"],
        "stopped_reason": result["stopped_reason"],
        "best_iteration": result.get("best_iteration"),
        "paths": result.get("paths"),
    }, indent=2, ensure_ascii=False, default=str))
