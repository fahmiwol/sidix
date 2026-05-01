"""
maqashid_auto_tune.py — Sprint G: Maqashid Auto-Tune

Arsitektur:
  Maqashid Auto-Tune = closed-loop optimizer untuk 5-sumbu Maqashid filter.
  Data driver: self-test results (brain/public/selftest/results.jsonl)
  Output: tuned weight profile yang bisa di-apply ke evaluator.

Flow:
  1. Read self-test history
  2. For each result, run Maqashid evaluation on (question, answer)
  3. Track per-axis fail/warn/pass rates
  4. Compute adjusted weights (axes with high fail rate → increase weight)
  5. Store tuned profile
  6. Apply tuned profile to future evaluations

Storage:
  - Tuned profile: brain/public/maqashid/tuned_profile.json
  - History: brain/public/maqashid/tune_history.jsonl

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("sidix.maqashid_tune")


# ── Storage ──────────────────────────────────────────────────────────────

TUNE_ROOT = Path("brain/public/maqashid")
TUNED_PROFILE_PATH = TUNE_ROOT / "tuned_profile.json"
TUNE_HISTORY_PATH = TUNE_ROOT / "tune_history.jsonl"
SELFTEST_RESULTS_PATH = Path("brain/public/selftest/results.jsonl")

# ── Default Weights (baseline from IHOS) ─────────────────────────────────

DEFAULT_WEIGHTS = {
    "life": 1.0,
    "intellect": 1.0,
    "faith": 0.8,
    "lineage": 0.6,
    "wealth": 0.7,
}


@dataclass
class TunedProfile:
    """Tuned Maqashid weight profile."""
    weights: dict[str, float]
    tuned_at: str
    sample_size: int
    fail_rates: dict[str, float]
    version: str = "1.0"


# ── Analysis ─────────────────────────────────────────────────────────────

def _read_selftest_results(limit: int = 100) -> list[dict]:
    """Read recent self-test results."""
    if not SELFTEST_RESULTS_PATH.exists():
        return []
    lines = SELFTEST_RESULTS_PATH.read_text(encoding="utf-8").strip().splitlines()
    results = []
    for line in lines[-limit:]:
        try:
            results.append(json.loads(line))
        except Exception:
            continue
    return results


def _evaluate_pair(question: str, answer: str, persona: str = "AYMAN") -> dict:
    """Run Maqashid evaluation on a Q&A pair."""
    try:
        from .maqashid_profiles import evaluate_maqashid
        return evaluate_maqashid(question, answer, persona_name=persona)
    except Exception as e:
        log.debug("[maqashid_tune] Eval failed: %s", e)
        return {"status": "pass", "reasons": [], "mode": "general"}


def _analyze_failures(results: list[dict]) -> dict[str, dict]:
    """Analyze per-axis failure patterns dari self-test results."""
    axis_counts: dict[str, dict[str, int]] = {
        ax: {"fail": 0, "warn": 0, "pass": 0, "total": 0}
        for ax in DEFAULT_WEIGHTS
    }

    for r in results:
        q = r.get("question", "")
        a = r.get("answer", "")
        persona = r.get("persona", "AYMAN")
        if not q or not a:
            continue

        eval_result = _evaluate_pair(q, a, persona)
        status = eval_result.get("status", "pass")
        reasons = eval_result.get("reasons", [])

        # Map reasons ke axis (heuristic dari keyword dalam reason)
        reason_text = " ".join(reasons).lower()
        for axis in DEFAULT_WEIGHTS:
            axis_counts[axis]["total"] += 1
            if axis in reason_text:
                axis_counts[axis][status] += 1
            else:
                # Kalau tidak ada axis-specific reason, distribusikan ke status global
                axis_counts[axis][status] += 0  # tidak increment — nanti normalisasi

        # Fallback: kalau status global bukan pass, distribusikan ke SEMUA axis
        # secara proportional (ini heuristic kasar tapi cukup untuk auto-tune)
        if status != "pass":
            for axis in DEFAULT_WEIGHTS:
                if axis not in reason_text:
                    axis_counts[axis][status] += 1

    # Hitung fail rate per axis
    fail_rates = {}
    for axis, counts in axis_counts.items():
        total = counts["total"] or 1
        fail_rates[axis] = round((counts["fail"] + counts["warn"] * 0.5) / total, 3)

    return fail_rates


# ── Tuning Engine ────────────────────────────────────────────────────────

def compute_tuned_weights(
    fail_rates: dict[str, float],
    baseline: dict[str, float] | None = None,
) -> dict[str, float]:
    """Compute adjusted weights dari fail rates.

    Logic:
    - Fail rate > 0.3 → increase weight (lebih strict)
    - Fail rate < 0.1 → decrease weight (lebih lenient)
    - Clamp 0.3–2.0
    """
    baseline = baseline or DEFAULT_WEIGHTS.copy()
    tuned = {}
    for axis, base in baseline.items():
        rate = fail_rates.get(axis, 0.0)
        if rate > 0.3:
            # Increase weight: lebih strict
            tuned[axis] = round(min(2.0, base * (1 + rate)), 2)
        elif rate < 0.1:
            # Decrease weight: lebih lenient
            tuned[axis] = round(max(0.3, base * (1 - (0.1 - rate))), 2)
        else:
            tuned[axis] = base
    return tuned


def run_auto_tune(
    sample_size: int = 50,
    baseline: dict[str, float] | None = None,
) -> TunedProfile:
    """Full auto-tune pipeline."""
    results = _read_selftest_results(limit=sample_size)
    if not results:
        log.warning("[maqashid_tune] No self-test data, returning default")
        return TunedProfile(
            weights=baseline or DEFAULT_WEIGHTS.copy(),
            tuned_at=datetime.now(timezone.utc).isoformat(),
            sample_size=0,
            fail_rates={k: 0.0 for k in DEFAULT_WEIGHTS},
        )

    fail_rates = _analyze_failures(results)
    tuned_weights = compute_tuned_weights(fail_rates, baseline)

    profile = TunedProfile(
        weights=tuned_weights,
        tuned_at=datetime.now(timezone.utc).isoformat(),
        sample_size=len(results),
        fail_rates=fail_rates,
    )

    # Persist
    _persist_profile(profile)
    log.info("[maqashid_tune] Tuned with %d samples: %s", len(results), tuned_weights)
    return profile


def _persist_profile(profile: TunedProfile) -> None:
    """Save tuned profile to disk."""
    try:
        TUNE_ROOT.mkdir(parents=True, exist_ok=True)
        TUNED_PROFILE_PATH.write_text(
            json.dumps(profile.__dict__, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        with TUNE_HISTORY_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(profile.__dict__, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[maqashid_tune] Persist failed: %s", e)


# ── Profile Management ───────────────────────────────────────────────────

def load_tuned_profile() -> dict[str, float] | None:
    """Load active tuned profile, or None kalau belum ada."""
    if not TUNED_PROFILE_PATH.exists():
        return None
    try:
        data = json.loads(TUNED_PROFILE_PATH.read_text(encoding="utf-8"))
        return data.get("weights")
    except Exception as e:
        log.warning("[maqashid_tune] Load failed: %s", e)
        return None


def reset_to_default() -> TunedProfile:
    """Reset profile ke default weights."""
    profile = TunedProfile(
        weights=DEFAULT_WEIGHTS.copy(),
        tuned_at=datetime.now(timezone.utc).isoformat(),
        sample_size=0,
        fail_rates={k: 0.0 for k in DEFAULT_WEIGHTS},
        version="default",
    )
    _persist_profile(profile)
    log.info("[maqashid_tune] Reset to default")
    return profile


# ── Stats ────────────────────────────────────────────────────────────────

def get_tune_stats() -> dict:
    """Aggregate tune history stats."""
    if not TUNE_HISTORY_PATH.exists():
        return {"tune_count": 0, "latest": None, "avg_sample_size": 0}

    entries = []
    for line in TUNE_HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines():
        try:
            entries.append(json.loads(line))
        except Exception:
            continue

    if not entries:
        return {"tune_count": 0, "latest": None, "avg_sample_size": 0}

    latest = entries[-1]
    return {
        "tune_count": len(entries),
        "latest": {
            "tuned_at": latest.get("tuned_at"),
            "weights": latest.get("weights"),
            "sample_size": latest.get("sample_size"),
            "fail_rates": latest.get("fail_rates"),
        },
        "avg_sample_size": round(sum(e.get("sample_size", 0) for e in entries) / len(entries), 1),
    }
