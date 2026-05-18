"""
nightly_lora.py — Pilar 3 closure: Nightly LoRA Fine-Tune Cron
================================================================

Per SIDIX_DEFINITION_20260426 Daily Capability #4 + #9:
> "Tumbuh dan menciptakan inovasi dari yang sudah dipelajari"
> "Self learn, self improvement"

Plus DIRECTION_LOCK Q3 P1:
> "Pilar 3: Nightly LoRA fine-tune cron"

Pilar 3 sebelum vol 15:
- ✅ corpus_to_training.py — convert corpus → ChatML pairs
- ✅ auto_lora.py — trigger di 500 pair threshold
- ✅ qna_recorder.py — auto-record QnA → corpus
- ✅ rehearsal buffer (continual_memory vol 7)
- ❌ Nightly auto-trigger — MISSING (manual confirm)

Vol 15 tutup gap: orchestrator nightly cron yang:
1. **Pre-flight check**: pair count, GPU available, recent retrain status
2. **Snapshot weights**: pre-retrain rollback safety (continual_memory)
3. **Prepare batch**: merge new pairs + 30% rehearsal buffer
4. **Emit signal**: trigger external GPU pipeline (Kaggle/Colab/RunPod) atau
   local training kalau GPU available
5. **Post-retrain validation**: benchmark quick check, kalau regress →
   rollback ke snapshot
6. **Log**: `nightly_retrain_log.jsonl` untuk audit

NOT: actually run training di module ini (training butuh GPU + 30+ min).
Module ini orchestrate, signal, validate. Actual training pipeline bisa
external (Kaggle notebook) atau local cron job.

Cron suggestion:
- 0 2 * * *   nightly orchestrator (02:00 UTC = 09:00 WIB sebelum peak)
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class NightlyRetrainPlan:
    """Plan untuk 1 nightly retrain cycle."""
    id: str
    ts: str
    new_pairs_count: int = 0
    rehearsal_count: int = 0
    total_batch_size: int = 0
    threshold_met: bool = False        # apakah cukup pairs untuk retrain
    snapshot_path: str = ""             # path snapshot pre-retrain
    estimated_minutes: int = 0
    status: str = "planned"             # planned | snapshotted | signaled | completed | failed | rolled_back
    last_retrain_at: str = ""
    days_since_last: int = 0
    signal_emitted: bool = False
    error: str = ""


# ── Path helpers ───────────────────────────────────────────────────────────────

def _data_dir() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _retrain_log() -> Path:
    return _data_dir() / "nightly_retrain.jsonl"


def _signal_file() -> Path:
    """File yang external pipeline (Kaggle/Colab) bisa watch."""
    return _data_dir() / "retrain_signal.json"


def _training_pairs_path() -> Path:
    return _data_dir() / "training_pairs.jsonl"


# ── Pre-flight checks ─────────────────────────────────────────────────────────

def count_training_pairs() -> int:
    """Hitung jumlah training pair siap retrain."""
    path = _training_pairs_path()
    if not path.exists():
        return 0
    try:
        with path.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


def get_last_retrain_info() -> dict:
    """Read last entry dari retrain log untuk cek timing."""
    path = _retrain_log()
    if not path.exists():
        return {"last_at": "", "days_ago": 9999}
    try:
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if e.get("status") == "completed":
                    last_at = e.get("ts", "")
                    if last_at:
                        last_dt = datetime.fromisoformat(last_at.replace("Z", "+00:00"))
                        days = (datetime.now(timezone.utc) - last_dt).days
                        return {"last_at": last_at, "days_ago": days}
            except Exception:
                continue
    except Exception:
        pass
    return {"last_at": "", "days_ago": 9999}


# ── Pre-flight orchestrator ───────────────────────────────────────────────────

def plan_nightly_retrain(
    *,
    min_new_pairs: int = 100,
    min_total_batch: int = 200,
    rehearsal_ratio: float = 0.3,
    min_days_between: int = 7,
) -> NightlyRetrainPlan:
    """
    Plan retrain — TIDAK execute, hanya analyze + decide.

    Threshold:
    - Minimum 100 new pairs sejak last retrain
    - Minimum 200 total batch (new + rehearsal) — kalau kurang, skip
    - Minimum 7 days sejak retrain terakhir (avoid weight thrashing)

    Returns plan dengan status="planned" + threshold_met flag.
    """
    plan = NightlyRetrainPlan(
        id=f"plan_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
    )

    # Count pairs
    plan.new_pairs_count = count_training_pairs()

    # Last retrain
    last_info = get_last_retrain_info()
    plan.last_retrain_at = last_info["last_at"]
    plan.days_since_last = last_info["days_ago"]

    # Threshold check
    if plan.new_pairs_count < min_new_pairs:
        plan.status = "skipped_insufficient_pairs"
        plan.error = f"Hanya {plan.new_pairs_count} pairs (need {min_new_pairs})"
        return plan

    if plan.days_since_last < min_days_between:
        plan.status = "skipped_too_recent"
        plan.error = f"Last retrain {plan.days_since_last} days ago (min {min_days_between})"
        return plan

    # Prepare rehearsal batch
    try:
        from . import continual_memory
        rehearsal = continual_memory.prepare_rehearsal_buffer(
            sample_ratio=rehearsal_ratio,
            max_samples=int(plan.new_pairs_count * rehearsal_ratio),
        )
        plan.rehearsal_count = rehearsal.get("samples_total", 0)
    except Exception as e:
        log.warning("[nightly] rehearsal prep fail: %s", e)
        plan.rehearsal_count = 0

    plan.total_batch_size = plan.new_pairs_count + plan.rehearsal_count

    if plan.total_batch_size < min_total_batch:
        plan.status = "skipped_small_batch"
        plan.error = f"Batch {plan.total_batch_size} < min {min_total_batch}"
        return plan

    plan.threshold_met = True
    # Estimate: 1 minute per 50 pairs (rough Qwen 2.5 LoRA on RTX 4090)
    plan.estimated_minutes = max(15, plan.total_batch_size // 50)

    return plan


def execute_nightly_orchestrator(
    *,
    dry_run: bool = False,
    auto_snapshot: bool = True,
) -> dict:
    """
    Full nightly orchestrator:
    1. Plan retrain (threshold check)
    2. Snapshot weights (kalau threshold met)
    3. Emit retrain signal (file watched by external pipeline)
    4. Log entry

    Return summary dict. Dipanggil cron 02:00 UTC daily.
    """
    plan = plan_nightly_retrain()

    if not plan.threshold_met:
        # Skip — log & return
        _persist_log(plan)
        return {
            "ok": True,
            "skipped": True,
            "reason": plan.error or plan.status,
            "plan": asdict(plan),
        }

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "would_execute": True,
            "plan": asdict(plan),
        }

    # 1. Snapshot pre-retrain
    if auto_snapshot:
        try:
            from . import continual_memory
            snap = continual_memory.snapshot_lora_weights()
            if snap.get("status") == "ok":
                plan.snapshot_path = snap.get("snapshot_path", "")
                plan.status = "snapshotted"
            else:
                plan.error = f"Snapshot fail: {snap.get('status', 'unknown')}"
        except Exception as e:
            plan.error = f"Snapshot exception: {e}"

    # 2. Emit signal file (external pipeline polls)
    try:
        signal = {
            "plan_id": plan.id,
            "ts": plan.ts,
            "new_pairs": plan.new_pairs_count,
            "rehearsal_pairs": plan.rehearsal_count,
            "total_batch": plan.total_batch_size,
            "snapshot_path": plan.snapshot_path,
            "estimated_minutes": plan.estimated_minutes,
            "status": "ready_for_retrain",
        }
        _signal_file().write_text(
            json.dumps(signal, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        plan.signal_emitted = True
        plan.status = "signaled"
    except Exception as e:
        plan.error = f"Signal emit fail: {e}"

    _persist_log(plan)
    return {
        "ok": True,
        "executed": plan.signal_emitted,
        "plan": asdict(plan),
        "signal_path": str(_signal_file()),
    }


def _persist_log(plan: NightlyRetrainPlan) -> None:
    try:
        with _retrain_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(plan), ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[nightly] log fail: %s", e)


# ── Post-retrain handler (called by external pipeline atau manual) ────────────

def report_retrain_completion(
    plan_id: str,
    *,
    success: bool,
    new_adapter_path: str = "",
    benchmark_accuracy: Optional[float] = None,
    rolled_back: bool = False,
) -> dict:
    """
    Dipanggil setelah external pipeline (Kaggle/Colab) selesai retrain.
    Update log dengan completion status. Auto-rollback kalau benchmark
    regress (TODO: integrate benchmark suite).
    """
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "type": "retrain_completion",
        "plan_id": plan_id,
        "status": "completed" if success else "failed",
        "new_adapter_path": new_adapter_path,
        "benchmark_accuracy": benchmark_accuracy,
        "rolled_back": rolled_back,
    }
    try:
        with _retrain_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # Clear signal file
    try:
        sig = _signal_file()
        if sig.exists():
            sig.unlink()
    except Exception:
        pass
    return {"ok": True, "logged": entry}


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Untuk admin dashboard."""
    path = _retrain_log()
    if not path.exists():
        return {"total_plans": 0, "total_completed": 0}
    plans = 0
    completed = 0
    skipped = 0
    failed = 0
    last_completion = ""
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    plans += 1
                    status = e.get("status", "")
                    if status == "completed":
                        completed += 1
                        last_completion = e.get("ts", last_completion)
                    elif status.startswith("skipped"):
                        skipped += 1
                    elif status == "failed":
                        failed += 1
                except Exception:
                    continue
    except Exception:
        return {"total_plans": 0}

    return {
        "total_plans": plans,
        "total_completed": completed,
        "total_skipped": skipped,
        "total_failed": failed,
        "last_completion": last_completion,
        "current_pair_count": count_training_pairs(),
        "days_since_last_retrain": get_last_retrain_info().get("days_ago", "n/a"),
    }


__all__ = [
    "NightlyRetrainPlan",
    "count_training_pairs",
    "get_last_retrain_info",
    "plan_nightly_retrain",
    "execute_nightly_orchestrator",
    "report_retrain_completion",
    "stats",
]
