"""
cloud_run_iterator.py — Sprint 14a candidate, lahir dari note 288 cognitive synthesis.

Abstract retry-with-fix loop untuk cloud compute task. Operational pattern yang
disintesis dari real Sprint 13 debugging journey (14 iterasi: 7 Kaggle abandoned
+ 4 RunPod + 3 marker).

Goal: SIDIX punya **structured prior** untuk iterate cloud platform issues
secara autonomous, bukan trial-and-error random.

Filosofi (note 288):
- iteration_cost ∝ opacity(platform) × depth(assumption_stack)
- Setiap layer abstraction punya invariant assumption yang TIDAK explicit
- Kalau invariant clash dengan environment actual → fail di runtime
- Pattern matching root cause → save iteration cost compound

Phase status: SCAFFOLD (Sprint 14a candidate, not yet wired ke production).
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Optional

log = logging.getLogger(__name__)


# ── Error category enum (dari real Sprint 13 patterns) ───────────────────────

class ErrorCategory(Enum):
    """Common error categories observable di cloud compute tasks."""
    TIMING_RACE = "timing_race"              # resource not ready (Sprint 13 v1)
    NAMING_SLUG = "naming_slug"               # id mismatch dgn platform-derived (v2)
    PATH_RESOLUTION = "path_resolution"       # mount path differs (v3)
    LIBRARY_VERSION = "library_version"       # version pin incompat (v4-v5)
    HARDWARE_COMPAT = "hardware_compat"       # GPU CC mismatch (v6-v7)
    DEPENDENCY_CHAIN = "dependency_chain"     # transitive dep missing (v8a)
    DEVICE_PLACEMENT = "device_placement"     # meta tensor / device_map (v8c)
    OUT_OF_MEMORY = "out_of_memory"           # OOM at forward/grad (v8c → v8d)
    NETWORK_FAIL = "network_fail"             # API timeout / dropped
    QUOTA_EXCEEDED = "quota_exceeded"         # rate limit / billing
    UNKNOWN = "unknown"                       # fallback


# ── Pattern signatures (regex/heuristic per kategori) ─────────────────────────

_PATTERN_SIGNATURES: list[tuple[ErrorCategory, list[str]]] = [
    (ErrorCategory.PATH_RESOLUTION, [
        r"FileNotFoundError.*Unable to find",
        r"No such file or directory",
        r"could not find.*file",
    ]),
    (ErrorCategory.HARDWARE_COMPAT, [
        r"cudaErrorNoKernelImageForDevice",
        r"no kernel image is available for execution on the device",
        r"named symbol not found",
    ]),
    (ErrorCategory.OUT_OF_MEMORY, [
        r"CUDA out of memory",
        r"OutOfMemoryError",
        r"failed to allocate.*memory",
    ]),
    (ErrorCategory.LIBRARY_VERSION, [
        r"ImportError.*incompatible version",
        r"requires.*version.*but found",
        r"AttributeError.*module.*has no attribute",
    ]),
    (ErrorCategory.DEVICE_PLACEMENT, [
        r"Cannot copy out of meta tensor",
        r"meta tensor.*no data",
    ]),
    (ErrorCategory.DEPENDENCY_CHAIN, [
        r"No module named",
        r"ImportError.*cannot import name",
    ]),
    (ErrorCategory.NAMING_SLUG, [
        r"409 Client Error.*Conflict",
        r"slug.*does not match",
        r"id.*mismatch",
    ]),
    (ErrorCategory.QUOTA_EXCEEDED, [
        r"429.*Too Many Requests",
        r"quota exceeded",
        r"rate limit",
    ]),
    (ErrorCategory.NETWORK_FAIL, [
        r"ConnectionError",
        r"TimeoutError",
        r"Connection refused",
    ]),
    (ErrorCategory.TIMING_RACE, [
        r"resource not ready",
        r"not yet available",
        r"still provisioning",
    ]),
]


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class IterationResult:
    """Hasil 1 iterasi push-run-classify cycle."""
    iter_num: int
    pushed_at: str
    final_status: str  # "COMPLETE" | "ERROR" | "TIMEOUT"
    error_category: Optional[ErrorCategory] = None
    error_excerpt: str = ""
    patch_applied: str = ""
    duration_seconds: float = 0.0


@dataclass
class IterationLog:
    """Append-only history untuk Hafidz Ledger integration (Sprint 14a)."""
    task_id: str
    platform: str  # "kaggle" | "runpod" | "colab" | etc
    iterations: list[IterationResult] = field(default_factory=list)
    started_at: str = ""
    final_status: str = "in_progress"  # "in_progress" | "succeeded" | "failed_max_iter"


# ── Core API ──────────────────────────────────────────────────────────────────

def classify_error(log_text: str) -> tuple[ErrorCategory, str]:
    """Match log_text against pattern signatures → category + excerpt.

    Returns first matching category (priority by _PATTERN_SIGNATURES order).
    Returns (UNKNOWN, "") kalau tidak match.
    """
    text = log_text.lower()
    for category, patterns in _PATTERN_SIGNATURES:
        for pattern in patterns:
            match = re.search(pattern.lower(), text)
            if match:
                # Extract surrounding context (max 200 chars)
                start = max(0, match.start() - 50)
                end = min(len(log_text), match.end() + 100)
                excerpt = log_text[start:end].strip()
                return (category, excerpt[:300])
    return (ErrorCategory.UNKNOWN, log_text[-300:] if log_text else "")


@dataclass
class CloudRunIterator:
    """Generic iterate-fix-retry loop untuk cloud compute task.

    Caller provides 4 callables:
    - push_fn(task_config) → task_id_or_handle
    - status_fn(handle) → str (one of "RUNNING", "COMPLETE", "ERROR", "TIMEOUT")
    - log_fn(handle) → str (full stderr/stdout log on terminal state)
    - patch_fn(task_config, error_category, error_excerpt) → patched_task_config

    Returns IterationLog dengan full history.

    Example:
    ```python
    iterator = CloudRunIterator(
        push_fn=kaggle_push, status_fn=kaggle_status,
        log_fn=kaggle_logs, patch_fn=my_kaggle_patch_fn,
        platform="kaggle", task_id="dora-train-v1",
    )
    result = iterator.run(initial_task, max_iter=8, poll_interval=15)
    ```
    """
    push_fn: Callable
    status_fn: Callable
    log_fn: Callable
    patch_fn: Callable
    platform: str = "unknown"
    task_id: str = ""

    def run(
        self,
        task_config: dict,
        max_iter: int = 10,
        poll_interval: int = 15,
        terminal_states: tuple = ("COMPLETE", "ERROR", "TIMEOUT"),
    ) -> IterationLog:
        """Run iterate-fix loop. Stops when COMPLETE atau max_iter exhausted."""
        log_record = IterationLog(
            task_id=self.task_id,
            platform=self.platform,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        current_task = dict(task_config)
        for iter_num in range(1, max_iter + 1):
            t0 = time.time()
            push_ts = datetime.now(timezone.utc).isoformat()

            log.info("[cloud_iter] %s iter=%d push", self.platform, iter_num)
            handle = self.push_fn(current_task)

            # Poll status
            final_status = "TIMEOUT"
            while time.time() - t0 < 3600:  # 1 hour max
                status = self.status_fn(handle)
                if status in terminal_states:
                    final_status = status
                    break
                time.sleep(poll_interval)

            duration = time.time() - t0
            iter_result = IterationResult(
                iter_num=iter_num,
                pushed_at=push_ts,
                final_status=final_status,
                duration_seconds=round(duration, 2),
            )

            if final_status == "COMPLETE":
                log_record.iterations.append(iter_result)
                log_record.final_status = "succeeded"
                log.info("[cloud_iter] iter=%d COMPLETE (%.1fs)", iter_num, duration)
                return log_record

            # Failed → classify + patch
            log_text = self.log_fn(handle)
            category, excerpt = classify_error(log_text)
            iter_result.error_category = category
            iter_result.error_excerpt = excerpt

            log.warning("[cloud_iter] iter=%d %s: %s",
                        iter_num, final_status, category.value)
            log.debug("[cloud_iter] excerpt: %s", excerpt[:200])

            # Apply patch via caller-provided fn
            try:
                patched = self.patch_fn(current_task, category, excerpt)
                iter_result.patch_applied = f"category={category.value}"
                current_task = patched
            except Exception as e:
                log.error("[cloud_iter] patch_fn raised: %s", e)
                iter_result.patch_applied = f"PATCH_FAILED: {e}"
                log_record.iterations.append(iter_result)
                log_record.final_status = "failed_patch_error"
                return log_record

            log_record.iterations.append(iter_result)

        # Max iter exhausted
        log_record.final_status = "failed_max_iter"
        log.warning("[cloud_iter] max_iter=%d exhausted, final=%s",
                    max_iter, log_record.iterations[-1].error_category if log_record.iterations else "none")
        return log_record


# ── Convenience helpers ───────────────────────────────────────────────────────

def hafidz_log_iteration(log_record: IterationLog) -> None:
    """Sprint 14a wire-pattern: append iteration history ke Hafidz Ledger
    untuk audit trail / sanad-as-governance."""
    try:
        from .hafidz_ledger import write_entry
        from dataclasses import asdict
        write_entry(
            content=str([asdict(it) for it in log_record.iterations]),
            content_id=f"cloud-iter-{log_record.platform}-{log_record.task_id}",
            content_type="cloud_iteration_log",
            isnad_chain=[],
            metadata={
                "platform": log_record.platform,
                "task_id": log_record.task_id,
                "final_status": log_record.final_status,
                "iter_count": len(log_record.iterations),
            },
            cycle_id=f"cloud-iter-{int(time.time())}",
        )
        log.info("[cloud_iter] hafidz entry written")
    except Exception as e:
        log.debug("[cloud_iter] hafidz hook skip: %s", e)


__all__ = [
    "ErrorCategory",
    "IterationResult",
    "IterationLog",
    "CloudRunIterator",
    "classify_error",
    "hafidz_log_iteration",
]
