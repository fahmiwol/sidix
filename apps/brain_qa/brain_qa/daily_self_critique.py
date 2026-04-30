"""
daily_self_critique.py — SIDIX Self-Critique & Growth Scaffold
===============================================================

Founder vision (2026-04-30 diagram v2):
    OUTPUT → OTAK+ (Self-critique) → INOVASI → ITERASI → PENCIPTA → HAFIDZ

This module implements the OTAK+ layer: evaluate yesterday's outputs,
detect weaknesses, propose innovations, and feed back into training corpus.

Phase 1: rule-based critique (fast, no LLM call)
Phase 2: LLM-based deep critique (after LoRA v2)
Phase 3: auto-generate improvement scripts (Self-Bootstrap)

Cron: run daily at 03:00 UTC (after learn_agent 04:00, before daily_growth)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
_CRITIQUE_DATA_DIR = Path(".data/critique")
_MIN_RELEVAN_FOR_PASS = 9.5
_MIN_SOURCES_FOR_PASS = 2
_MAX_HALU_SCORE = 0.3  # lower = better


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class CritiqueItem:
    """One output item being critiqued."""
    session_id: str
    question: str
    output: str
    persona: str = "AYMAN"
    relevan_score: float = 0.0
    source_count: int = 0
    agreement_pct: float = 0.0
    iteration_count: int = 1
    has_citation: bool = False
    timestamp: str = ""


@dataclass
class CritiqueReport:
    """Daily aggregated self-critique report."""
    date: str
    items_evaluated: int = 0
    items_passed: int = 0
    items_failed: int = 0
    avg_relevan: float = 0.0
    avg_source_count: float = 0.0
    halu_flags: list[dict] = field(default_factory=list)
    persona_drift_flags: list[dict] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    improvement_notes: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Rule-based critique engine (Phase 1) ─────────────────────────────────────

def _extract_critique_items(sessions_dir: Path) -> list[CritiqueItem]:
    """Read yesterday's session exports → CritiqueItem list."""
    items: list[CritiqueItem] = []
    if not sessions_dir.exists():
        return items
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    for f in sessions_dir.glob("session_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            ts = data.get("created_at", "")
            if yesterday not in ts and not _is_within_last_24h(ts):
                continue
            items.append(CritiqueItem(
                session_id=data.get("session_id", f.stem),
                question=data.get("question", ""),
                output=data.get("final_answer", ""),
                persona=data.get("persona", "AYMAN"),
                relevan_score=data.get("relevan_score", 0.0),
                source_count=len(data.get("citations", [])),
                agreement_pct=data.get("agreement_pct", 0.0),
                iteration_count=data.get("iteration_count", 1),
                has_citation=bool(data.get("citations")),
                timestamp=ts,
            ))
        except Exception as e:
            log.warning("[critique] skip malformed session %s: %s", f.name, e)
    return items


def _is_within_last_24h(timestamp_str: str) -> bool:
    """Check if timestamp is within last 24 hours."""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt) < timedelta(hours=24)
    except Exception:
        return False


def _detect_halu(item: CritiqueItem) -> Optional[str]:
    """Detect hallucination: high-confidence claim without citation."""
    if item.relevan_score < 7.0 and not item.has_citation:
        return f"[{item.session_id}] Low relevan ({item.relevan_score}) + no citation — possible halu"
    if item.agreement_pct < 0.3 and item.source_count == 0:
        return f"[{item.session_id}] Single source (agreement={item.agreement_pct:.2f}) — unverified claim"
    return None


def _detect_persona_drift(item: CritiqueItem) -> Optional[str]:
    """Detect persona inconsistency: output style doesn't match persona."""
    # Phase 1: simple keyword check
    persona_markers = {
        "UTZ": ["aku", "nih", "ajaian", "seru", "kreatif"],
        "ABOO": ["gue", "teknik", "engineering", "implementasi"],
        "OOMAR": ["saya", "strategi", "bisnis", "ROI", "market"],
        "ALEY": ["saya", "penelitian", "metodologi", "citation", "paper"],
        "AYMAN": ["halo", "senang", "bantu", "general"],
    }
    markers = persona_markers.get(item.persona, [])
    if not markers:
        return None
    output_lower = item.output.lower()
    hit_count = sum(1 for m in markers if m in output_lower)
    # UTZ should have at least 1 marker per 200 chars; others per 300 chars
    threshold = max(1, len(item.output) // (200 if item.persona == "UTZ" else 300))
    if hit_count < threshold and len(item.output) > 100:
        return f"[{item.persona}] Drift detected: only {hit_count}/{threshold} markers in {len(item.output)} chars"
    return None


def _detect_coverage_gap(item: CritiqueItem) -> Optional[str]:
    """Detect missing source types."""
    gaps = []
    if item.source_count < _MIN_SOURCES_FOR_PASS:
        gaps.append(f"only {item.source_count} sources (< {_MIN_SOURCES_FOR_PASS})")
    if item.iteration_count > 1:
        gaps.append(f"required {item.iteration_count} iterations — initial query weak")
    if gaps:
        return f"[{item.session_id}] Coverage gap: {', '.join(gaps)}"
    return None


def _generate_improvement_notes(report: CritiqueReport) -> list[str]:
    """Generate actionable improvement notes from critique."""
    notes = []
    if report.items_failed > 0:
        fail_rate = report.items_failed / max(1, report.items_evaluated)
        notes.append(f"Fail rate {fail_rate:.0%} — strengthen Sanad Orkestra threshold or expand corpus")
    if report.halu_flags:
        notes.append(f"{len(report.halu_flags)} halu flags — improve citation enforcement and web search depth")
    if report.persona_drift_flags:
        notes.append(f"{len(report.persona_drift_flags)} persona drift — retrain LoRA adapter or adjust prompt template")
    if report.coverage_gaps:
        notes.append(f"{len(report.coverage_gaps)} coverage gaps — add more diverse sources (dense index, tool registry)")
    if report.avg_relevan < 8.0:
        notes.append(f"Avg relevan {report.avg_relevan:.1f} — target 9.5++ needs better consensus algorithm")
    if not notes:
        notes.append("All metrics green — consider expanding to new domains or increasing question complexity")
    return notes


# ── Main entry point ─────────────────────────────────────────────────────────

def run_daily_critique(
    sessions_dir: Optional[Path] = None,
    out_dir: Optional[Path] = None,
) -> CritiqueReport:
    """Run self-critique on yesterday's outputs → generate improvement report.

    Returns CritiqueReport. Caller should append to LIVING_LOG and/or
    trigger corpus_to_training if improvements found.
    """
    t0 = time.time()
    sessions_dir = sessions_dir or Path(".data/sessions")
    out_dir = out_dir or _CRITIQUE_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    items = _extract_critique_items(sessions_dir)
    report = CritiqueReport(
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        items_evaluated=len(items),
    )

    relevan_sum = 0.0
    source_sum = 0
    for item in items:
        relevan_sum += item.relevan_score
        source_sum += item.source_count

        # Pass/fail
        passed = (
            item.relevan_score >= _MIN_RELEVAN_FOR_PASS
            and item.source_count >= _MIN_SOURCES_FOR_PASS
            and item.iteration_count == 1
        )
        if passed:
            report.items_passed += 1
        else:
            report.items_failed += 1

        # Halu detection
        halu = _detect_halu(item)
        if halu:
            report.halu_flags.append({"session_id": item.session_id, "reason": halu})

        # Persona drift
        drift = _detect_persona_drift(item)
        if drift:
            report.persona_drift_flags.append({"session_id": item.session_id, "reason": drift})

        # Coverage gap
        gap = _detect_coverage_gap(item)
        if gap:
            report.coverage_gaps.append(gap)

    if items:
        report.avg_relevan = round(relevan_sum / len(items), 2)
        report.avg_source_count = round(source_sum / len(items), 2)

    report.improvement_notes = _generate_improvement_notes(report)

    # Persist report
    report_file = out_dir / f"critique_{report.date}.json"
    report_file.write_text(
        json.dumps(report.__dict__, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    log.info(
        "[critique] evaluated=%d passed=%d failed=%d avg_relevan=%.2f halu=%d drift=%d duration=%dms",
        report.items_evaluated, report.items_passed, report.items_failed,
        report.avg_relevan, len(report.halu_flags), len(report.persona_drift_flags),
        int((time.time() - t0) * 1000),
    )
    return report


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    report = run_daily_critique()
    print(json.dumps(report.__dict__, indent=2, ensure_ascii=False, default=str))
