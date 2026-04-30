"""
agent_odoa.py — Sprint 23: ODOA Daily Compound Improvement Tracker

Per note 248 line 109 EKSPLISIT (Wahdah/Kitabah/ODOA self-learning protocol):
  "ODOA → incremental innovation (One Day One Achievement)"

Closes self-learning trilogy:
  - WAHDAH: deep focus iteration (defer — needs LoRA training trigger)
  - KITABAH: generation-test validation (Sprint 22+22b shipped)
  - ODOA: incremental innovation tracking (THIS Sprint 23)

Pre-Execution Alignment Check (per CLAUDE.md 6.4):
- Note 248 line 109 explicit ODOA mandate ✓
- Compound Sprint 15 (visioner) + 21 (RASA) + 22 (KITABAH)
- Pivot 2026-04-25: aggregator endpoint, no persona prompt change ✓
- 10 hard rules: own data, no vendor, MIT, self-hosted ✓
- Anti-halusinasi: aggregate metrics dari files existing (mtime + content)
- Budget: 1 LLM call narrative synthesis only

Aggregate metrics dari .data/ subdirectories untuk date target:
- creative_briefs/<slug>/metadata.json (mtime today)
- rasa_reports/<slug>/structured.json (overall_score)
- wisdom_reports/<slug>/structured.json (verdict)
- integrated_reports/<slug>/bundle.json
- kitabah_loops/<slug>/history.json (iterations)
- visioner_reports/YYYY-WNN.md (this week)
- research_queue.jsonl (today entries)

Output:
- prose markdown narrative (AYMAN persona warm summary)
- structured JSON metrics
- persist .data/odoa_reports/<date>.md

Public API:
  odoa_daily(date_str=None) -> dict   # default today UTC
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, date as date_type
from pathlib import Path
from typing import Any, Optional

try:
    from .ollama_llm import ollama_generate
except Exception:  # pragma: no cover
    def ollama_generate(*_a, **_k):  # type: ignore
        return ("(LLM unavailable)", {})


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
CREATIVE_BRIEFS_DIR = DATA_DIR / "creative_briefs"
RASA_REPORTS_DIR = DATA_DIR / "rasa_reports"
WISDOM_REPORTS_DIR = DATA_DIR / "wisdom_reports"
INTEGRATED_DIR = DATA_DIR / "integrated_reports"
KITABAH_LOOPS_DIR = DATA_DIR / "kitabah_loops"
VISIONER_REPORTS_DIR = DATA_DIR / "visioner_reports"
RESEARCH_QUEUE = DATA_DIR / "research_queue.jsonl"
ODOA_REPORTS_DIR = DATA_DIR / "odoa_reports"


# ── Date helpers ────────────────────────────────────────────────────────────

def _parse_date(date_str: Optional[str]) -> date_type:
    """Parse YYYY-MM-DD atau default today UTC."""
    if not date_str:
        return datetime.now(timezone.utc).date()
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return datetime.now(timezone.utc).date()


def _is_same_date(file_path: Path, target: date_type) -> bool:
    """File modified pada target date (UTC)?"""
    try:
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).date()
        return mtime == target
    except Exception:
        return False


def _iso_year_week(d: date_type) -> str:
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


# ── Aggregators ─────────────────────────────────────────────────────────────

def _aggregate_creative_briefs(target: date_type) -> dict[str, Any]:
    """Count + slugs creative briefs created on target date."""
    out = {"count": 0, "slugs": []}
    if not CREATIVE_BRIEFS_DIR.exists():
        return out
    for slug_dir in CREATIVE_BRIEFS_DIR.iterdir():
        if not slug_dir.is_dir():
            continue
        meta = slug_dir / "metadata.json"
        if meta.exists() and _is_same_date(meta, target):
            out["count"] += 1
            out["slugs"].append(slug_dir.name)
    return out


def _aggregate_rasa_reports(target: date_type) -> dict[str, Any]:
    """RASA scores aggregated. Avg + verdict distribution + slugs."""
    out: dict[str, Any] = {"count": 0, "avg_score": None, "verdicts": {}, "slugs": []}
    if not RASA_REPORTS_DIR.exists():
        return out
    scores: list[float] = []
    for slug_dir in RASA_REPORTS_DIR.iterdir():
        if not slug_dir.is_dir():
            continue
        structured = slug_dir / "structured.json"
        if structured.exists() and _is_same_date(structured, target):
            try:
                data = json.loads(structured.read_text(encoding="utf-8"))
                overall = data.get("overall_score")
                verdict = data.get("verdict") or "unknown"
                if isinstance(overall, (int, float)):
                    scores.append(float(overall))
                out["verdicts"][verdict] = out["verdicts"].get(verdict, 0) + 1
                out["count"] += 1
                out["slugs"].append(slug_dir.name)
            except Exception:
                continue
    if scores:
        out["avg_score"] = round(sum(scores) / len(scores), 2)
    return out


def _aggregate_wisdom_reports(target: date_type) -> dict[str, Any]:
    out: dict[str, Any] = {"count": 0, "slugs": [], "topics": []}
    if not WISDOM_REPORTS_DIR.exists():
        return out
    for slug_dir in WISDOM_REPORTS_DIR.iterdir():
        if not slug_dir.is_dir():
            continue
        meta = slug_dir / "metadata.json"
        if meta.exists() and _is_same_date(meta, target):
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
                topic = data.get("topic", slug_dir.name)
                out["count"] += 1
                out["slugs"].append(slug_dir.name)
                out["topics"].append(topic[:80])
            except Exception:
                continue
    return out


def _aggregate_integrated(target: date_type) -> dict[str, Any]:
    out: dict[str, Any] = {"count": 0, "slugs": []}
    if not INTEGRATED_DIR.exists():
        return out
    for slug_dir in INTEGRATED_DIR.iterdir():
        if not slug_dir.is_dir():
            continue
        bundle = slug_dir / "bundle.json"
        if bundle.exists() and _is_same_date(bundle, target):
            out["count"] += 1
            out["slugs"].append(slug_dir.name)
    return out


def _aggregate_kitabah(target: date_type) -> dict[str, Any]:
    out: dict[str, Any] = {"count": 0, "iterations_total": 0, "slugs": []}
    if not KITABAH_LOOPS_DIR.exists():
        return out
    for slug_dir in KITABAH_LOOPS_DIR.iterdir():
        if not slug_dir.is_dir():
            continue
        history_file = slug_dir / "history.json"
        if history_file.exists() and _is_same_date(history_file, target):
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                iters = data.get("iterations_run", 0)
                out["iterations_total"] += iters
                out["count"] += 1
                out["slugs"].append(slug_dir.name)
            except Exception:
                continue
    return out


def _aggregate_visioner_thisweek(target: date_type) -> dict[str, Any]:
    """Visioner reports untuk week yang sama dengan target."""
    out: dict[str, Any] = {"week": _iso_year_week(target), "report_exists": False, "report_path": None}
    if not VISIONER_REPORTS_DIR.exists():
        return out
    target_week = _iso_year_week(target)
    expected = VISIONER_REPORTS_DIR / f"{target_week}.md"
    if expected.exists():
        out["report_exists"] = True
        out["report_path"] = str(expected)
    return out


def _aggregate_wahdah_corpus_signal() -> dict[str, Any]:
    """Sprint 24: WAHDAH corpus growth signal monitor (note 248 line 109).

    MVP: count research_notes/, AKU inventory, training pairs (kalau ada).
    Threshold detection: signal 'ready_for_lora_retrain' kalau growth indicators
    exceed N. BUKAN actual LoRA trigger — itu defer pending Sprint 13 DoRA infra.

    Self-learning trilogy completion (note 248 line 109-114):
      - WAHDAH (this signal MVP): deep focus iteration trigger
      - KITABAH (Sprint 22+22b): generation-test validation loop
      - ODOA (Sprint 23): incremental innovation tracking
    """
    notes_dir = SIDIX_PATH / "brain" / "public" / "research_notes"
    aku_inventory = DATA_DIR / "aku_inventory.jsonl"
    training_pairs = DATA_DIR / "training" / "lora_pairs.jsonl"

    notes_count = 0
    if notes_dir.exists():
        try:
            notes_count = len([f for f in notes_dir.iterdir()
                              if f.is_file() and f.suffix == ".md"])
        except Exception:
            pass

    aku_entries = 0
    if aku_inventory.exists():
        try:
            with open(aku_inventory, encoding="utf-8") as f:
                aku_entries = sum(1 for _ in f)
        except Exception:
            pass

    training_pairs_count = 0
    if training_pairs.exists():
        try:
            with open(training_pairs, encoding="utf-8") as f:
                training_pairs_count = sum(1 for _ in f)
        except Exception:
            pass

    # Threshold heuristic (per note 248 spirit — corpus 6-12 bulan ahead):
    # - 250+ notes = substantial corpus
    # - 100+ AKU entries = memory mature
    # - 1000+ training pairs = enough untuk LoRA retrain (per HF guidelines)
    NOTES_THRESHOLD = 250
    AKU_THRESHOLD = 100
    PAIRS_THRESHOLD = 1000

    signals = {
        "corpus_notes_ready": notes_count >= NOTES_THRESHOLD,
        "aku_memory_ready": aku_entries >= AKU_THRESHOLD,
        "training_pairs_ready": training_pairs_count >= PAIRS_THRESHOLD,
    }
    ready_count = sum(signals.values())

    # Composite signal: 2 dari 3 = "approaching", 3 dari 3 = "ready_for_lora_retrain"
    if ready_count >= 3:
        composite = "ready_for_lora_retrain"
    elif ready_count == 2:
        composite = "approaching_threshold"
    else:
        composite = "growing"

    return {
        "notes_count": notes_count,
        "aku_entries": aku_entries,
        "training_pairs_count": training_pairs_count,
        "thresholds": {
            "notes": NOTES_THRESHOLD,
            "aku": AKU_THRESHOLD,
            "pairs": PAIRS_THRESHOLD,
        },
        "signals": signals,
        "composite_signal": composite,
        "ready_count": f"{ready_count}/3",
    }


def _aggregate_research_queue(target: date_type) -> dict[str, Any]:
    """Count research queue entries dari target date."""
    out: dict[str, Any] = {"count": 0, "topics": []}
    if not RESEARCH_QUEUE.exists():
        return out
    try:
        target_iso = target.isoformat()
        with open(RESEARCH_QUEUE, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    ts = d.get("ts", "")
                    if ts.startswith(target_iso):
                        out["count"] += 1
                        if d.get("topic"):
                            out["topics"].append(d["topic"])
                except Exception:
                    continue
    except Exception:
        pass
    return out


# ── Narrative synthesis (AYMAN warm voice) ─────────────────────────────────

_AYMAN_ODOA_SYSTEM = (
    "Kamu AYMAN — pendengar hangat SIDIX. Voice: 'aku' atau 'kita', empati, "
    "analogi sehari-hari. Bahasa Indonesia.\n\n"
    "TUGAS — ODOA narrative (One Day One Achievement):\n"
    "Diberikan metrics aktivitas SIDIX hari ini dari berbagai sub-system "
    "(creative pipeline, RASA scoring, wisdom analysis, KITABAH loop, "
    "visioner foresight, research queue), tulis 5-7 kalimat narrative hangat:\n"
    "1. Highlight 1-2 achievement paling impactful hari ini\n"
    "2. Sebut metric konkret (jumlah artifact, score average, dll)\n"
    "3. Reflect 1 pattern atau insight dari hari ini\n"
    "4. Closing: 1 kalimat optimistic untuk besok\n\n"
    "Format: prose mengalir, BUKAN bullet list. Tone hangat tapi grounded di "
    "data konkret. Domain ini = self-reflection narrative, BUKAN sensitive "
    "(fiqh/medis/data sensitif) — natural language hedging, BUKAN bracket "
    "[SPEKULASI] tag per claim."
)


# ── Main pipeline ───────────────────────────────────────────────────────────

def odoa_daily(
    date_str: Optional[str] = None,
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Sprint 23 ODOA daily aggregation + narrative.

    Args:
      date_str: 'YYYY-MM-DD' atau None untuk today UTC
      persist: write report ke .data/odoa_reports/
    """
    target = _parse_date(date_str)

    metrics = {
        "creative_briefs": _aggregate_creative_briefs(target),
        "rasa_reports": _aggregate_rasa_reports(target),
        "wisdom_reports": _aggregate_wisdom_reports(target),
        "integrated_reports": _aggregate_integrated(target),
        "kitabah_loops": _aggregate_kitabah(target),
        "visioner_thisweek": _aggregate_visioner_thisweek(target),
        "research_queue_today": _aggregate_research_queue(target),
        "wahdah_corpus_signal": _aggregate_wahdah_corpus_signal(),  # Sprint 24
    }

    # Compute headline summary
    total_artifacts = (
        metrics["creative_briefs"]["count"] +
        metrics["rasa_reports"]["count"] +
        metrics["wisdom_reports"]["count"] +
        metrics["integrated_reports"]["count"] +
        metrics["kitabah_loops"]["count"]
    )

    # Generate narrative via AYMAN
    import time as _t
    t0 = _t.time()
    summary_prompt = (
        f"DATE: {target.isoformat()}\n\n"
        f"METRICS HARI INI:\n"
        f"- Creative briefs: {metrics['creative_briefs']['count']} artifact\n"
        f"- RASA scoring: {metrics['rasa_reports']['count']} runs, avg score {metrics['rasa_reports']['avg_score']}\n"
        f"  Verdicts: {metrics['rasa_reports']['verdicts']}\n"
        f"- Wisdom analysis: {metrics['wisdom_reports']['count']} topics\n"
        f"  Topics sample: {metrics['wisdom_reports']['topics'][:3]}\n"
        f"- Integrated bundles: {metrics['integrated_reports']['count']}\n"
        f"- KITABAH loops: {metrics['kitabah_loops']['count']} runs, {metrics['kitabah_loops']['iterations_total']} iterations total\n"
        f"- Visioner this week ({metrics['visioner_thisweek']['week']}): {'available' if metrics['visioner_thisweek']['report_exists'] else 'not yet'}\n"
        f"- Research queue today: {metrics['research_queue_today']['count']} new tasks\n"
        f"- WAHDAH corpus signal: {metrics['wahdah_corpus_signal']['composite_signal']} "
        f"({metrics['wahdah_corpus_signal']['ready_count']} indicators) — "
        f"{metrics['wahdah_corpus_signal']['notes_count']} notes, "
        f"{metrics['wahdah_corpus_signal']['aku_entries']} AKU, "
        f"{metrics['wahdah_corpus_signal']['training_pairs_count']} training pairs\n\n"
        f"TOTAL artifacts created: {total_artifacts}\n\n"
        f"Tulis ODOA narrative hangat 5-7 kalimat."
    )
    narrative, _ = ollama_generate(
        summary_prompt, system=_AYMAN_ODOA_SYSTEM,
        max_tokens=400, temperature=0.6,
    )
    elapsed_ms = int((_t.time() - t0) * 1000)

    result = {
        "date": target.isoformat(),
        "ts_generated": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "total_artifacts": total_artifacts,
        "narrative": (narrative or "").strip(),
        "elapsed_ms": elapsed_ms,
        "paths": {},
    }

    if persist:
        ODOA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_md = _render_report_md(result)
        report_path = ODOA_REPORTS_DIR / f"{target.isoformat()}.md"
        report_path.write_text(report_md, encoding="utf-8")
        json_path = ODOA_REPORTS_DIR / f"{target.isoformat()}.json"
        json_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
        result["paths"] = {
            "report": str(report_path),
            "json": str(json_path),
        }

    return result


def _render_report_md(r: dict[str, Any]) -> str:
    m = r["metrics"]
    lines = [
        f"# ODOA Daily — {r['date']}",
        "",
        f"_Generated_: {r['ts_generated']}",
        f"_Pipeline_: SIDIX Sprint 23 / ODOA (One Day One Achievement)",
        f"_Total artifacts_: {r['total_artifacts']}",
        "",
        "---",
        "",
        "## 🌅 Today's Narrative (AYMAN)",
        "",
        r["narrative"] or "(narrative unavailable)",
        "",
        "---",
        "",
        "## 📊 Metrics",
        "",
        "### Creative Output",
        f"- **Creative briefs**: {m['creative_briefs']['count']} artifact",
        f"- **Slugs**: {', '.join(m['creative_briefs']['slugs'][:5])}{'...' if len(m['creative_briefs']['slugs']) > 5 else ''}",
        "",
        "### Quality (RASA)",
        f"- **Runs**: {m['rasa_reports']['count']}",
        f"- **Avg score**: {m['rasa_reports']['avg_score']}/5" if m['rasa_reports']['avg_score'] else "- **Avg score**: —",
        f"- **Verdicts**: {m['rasa_reports']['verdicts']}",
        "",
        "### Wisdom Analysis",
        f"- **Topics**: {m['wisdom_reports']['count']}",
        f"- **Sample**: {m['wisdom_reports']['topics'][:3]}" if m['wisdom_reports']['topics'] else "- (no topics today)",
        "",
        "### Integrated + KITABAH",
        f"- **Integrated bundles**: {m['integrated_reports']['count']}",
        f"- **KITABAH loops**: {m['kitabah_loops']['count']} ({m['kitabah_loops']['iterations_total']} iterations total)",
        "",
        "### Visioner + Research",
        f"- **Visioner week** {m['visioner_thisweek']['week']}: {'✅ available' if m['visioner_thisweek']['report_exists'] else '⏸ not yet'}",
        f"- **Research queue today**: {m['research_queue_today']['count']} new tasks",
        f"  - Topics: {', '.join(m['research_queue_today']['topics'][:5])}{'...' if len(m['research_queue_today']['topics']) > 5 else ''}" if m['research_queue_today']['topics'] else "  - (none today)",
        "",
        "### 🧬 WAHDAH Corpus Signal (Sprint 24 — note 248 line 109)",
        f"- **Composite signal**: `{m['wahdah_corpus_signal']['composite_signal']}` ({m['wahdah_corpus_signal']['ready_count']} indicators)",
        f"- **Research notes**: {m['wahdah_corpus_signal']['notes_count']} (threshold {m['wahdah_corpus_signal']['thresholds']['notes']}) {'✅' if m['wahdah_corpus_signal']['signals']['corpus_notes_ready'] else '⏸'}",
        f"- **AKU memory entries**: {m['wahdah_corpus_signal']['aku_entries']} (threshold {m['wahdah_corpus_signal']['thresholds']['aku']}) {'✅' if m['wahdah_corpus_signal']['signals']['aku_memory_ready'] else '⏸'}",
        f"- **Training pairs**: {m['wahdah_corpus_signal']['training_pairs_count']} (threshold {m['wahdah_corpus_signal']['thresholds']['pairs']}) {'✅' if m['wahdah_corpus_signal']['signals']['training_pairs_ready'] else '⏸'}",
        "",
        "_WAHDAH protocol_: signal MVP saja (Sprint 24). Actual LoRA retrain trigger _defer_ pending Sprint 13 DoRA infrastructure._",
        "",
        "---",
        "",
        f"_LLM elapsed_: {r['elapsed_ms']}ms",
        "",
        "## ODOA Protocol Reference",
        "",
        "Per note 248 line 109 — ODOA = One Day One Achievement = incremental innovation tracking.",
        "Compound dengan WAHDAH (deep focus iteration, pending) + KITABAH (gen-test loop, Sprint 22+22b).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = odoa_daily(date_arg)
    print(json.dumps({
        "date": result["date"],
        "total_artifacts": result["total_artifacts"],
        "metrics_summary": {k: v.get("count", v) if isinstance(v, dict) else v
                            for k, v in result["metrics"].items()},
        "narrative_len": len(result["narrative"]),
        "paths": result["paths"],
    }, indent=2, ensure_ascii=False, default=str))
