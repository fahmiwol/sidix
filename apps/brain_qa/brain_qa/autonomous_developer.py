"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

autonomous_developer.py — Sprint 40 (SIDIX Autonomous Scaffold-to-Production Builder)

Main orchestrator. Pick top-priority task from dev_task_queue → optional
persona fan-out → plan diff → apply → test → submit PR → notify owner.

Founder mandate (LOCK 2026-04-29): SIDIX kerjain scaffold yang ada jadi
product ready di background, owner-approval gated. NO auto-merge ke main.

Pipeline (one tick):

    pick_next() → DevTask
       │
       ├─ persona_fanout? → persona_research_fanout.gather()
       │                  → synthesize → context
       │
       ├─ code_diff_planner.plan_changes(context)
       │     ↓
       ├─ code_diff_planner.validate_plan()
       │     ↓
       ├─ create branch + apply diff
       │     ↓
       ├─ dev_sandbox.full_check()
       │     ↓ if fail and iter < max_iter:
       │       └─ cloud_run_iterator.classify_error()
       │       └─ retry with previous_error context
       │     ↓ if pass:
       ├─ dev_pr_submitter.submit() → branch+commit+push
       │     ↓
       ├─ hafidz_ledger.write_entry() — audit trail
       │     ↓
       └─ notify_owner() → Telegram + dashboard
            ↓
       update_state(task, "review")

Phase 1 scope: orchestrator skeleton with stub calls. Phase 2 wires actual
LLM diff generation + git operations + Telegram bot.

Reference:
- docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md
- project_sidix_autonomous_dev_mandate.md
- project_sidix_multi_agent_pattern.md
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from . import (dev_task_queue, code_diff_planner, dev_sandbox,
               dev_pr_submitter, persona_research_fanout)
from .cloud_run_iterator import classify_error, ErrorCategory

log = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # SIDIX-AI/<worktree>


@dataclass
class TickResult:
    """Outcome of one tick(): pick + work one task."""
    picked: bool = False
    task_id: str = ""
    state_after: str = ""
    iter_used: int = 0
    test_ok: bool = False
    submitted: bool = False
    pr_url: str = ""
    error: str = ""


def tick(
    repo_root: Optional[Path] = None,
    dry_run: Optional[bool] = None,
) -> TickResult:
    """One cron iteration: pick top pending task + work it.

    Args:
        repo_root: project root for context + file writes (default: repo root)
        dry_run: if True, apply_plan logs but does NOT write files.
                 Default: read AUTODEV_DRY_RUN env var (0=real, 1=dry).
                 Production VPS: set AUTODEV_DRY_RUN=0 to enable real writes.
                 Tests: pass dry_run=True to isolate from filesystem.

    Returns TickResult dengan summary. Cron caller logs ke
    /var/log/sidix_autodev.log.
    """
    repo_root = repo_root or _REPO_ROOT

    # Env var override: AUTODEV_DRY_RUN=1 = safe mode (no actual writes)
    if dry_run is None:
        dry_run = os.getenv("AUTODEV_DRY_RUN", "0") == "1"

    log.info("[autodev] tick start repo_root=%s dry_run=%s", repo_root, dry_run)

    task = dev_task_queue.pick_next()
    if task is None:
        log.info("[autodev] no pending task — idle")
        return TickResult(picked=False)

    log.info("[autodev] picked task=%s target=%s iter=%d/%d fanout=%s",
             task.task_id, task.target_path,
             task.iter_count + 1, task.max_iter, task.persona_fanout)

    dev_task_queue.update_state(task.task_id, "in_progress",
                                iter_count=task.iter_count + 1)

    result = TickResult(picked=True, task_id=task.task_id,
                        iter_used=task.iter_count + 1)

    try:
        # 1. Optional persona fan-out
        fanout_bundle = None
        if task.persona_fanout:
            fanout_bundle = persona_research_fanout.gather(
                task.task_id, task.target_path, task.goal,
            )
            log.info("[autodev] fanout %d personas", len(fanout_bundle.contributions))

        # 2. Plan diff
        plan = code_diff_planner.plan_changes(
            task_id=task.task_id,
            target_path=task.target_path,
            goal=task.goal,
            repo_root=repo_root,
            iteration=task.iter_count + 1,
            previous_error=task.error_log,
            persona_fanout=task.persona_fanout,
        )

        # 3. Validate
        ok, issues = code_diff_planner.validate_plan(plan, repo_root)
        if not ok:
            result.error = f"plan validation failed: {issues}"
            _maybe_escalate(task, result.error)
            result.state_after = dev_task_queue.get_task(task.task_id).state
            return result

        # 4. Apply (Sprint 59: real writes when dry_run=False)
        touched = code_diff_planner.apply_plan(plan, repo_root, dry_run=dry_run)
        log.info("[autodev] applied %d files (dry_run=%s)", len(touched), dry_run)

        # Guard: if plan had file changes but none were written (e.g. size-safety
        # guard blocked ALL modifications), treat as a failed iteration so the
        # LLM gets another chance with the previous error as context.
        if plan.files and not touched and not dry_run:
            err_msg = (
                f"iter {task.iter_count+1}: apply_plan wrote 0/{len(plan.files)} files "
                f"— likely partial-snippet blocked by size-safety guard. "
                f"LLM must output FULL file content for MODIFY operations."
            )
            log.warning("[autodev] %s", err_msg)
            dev_task_queue.update_state(task.task_id, "pending", error_log=err_msg)
            result.error = err_msg
            result.state_after = "pending"
            return result

        # 5. Test (Phase 1 = stub run)
        test_result = dev_sandbox.full_check(repo_root)
        result.test_ok = test_result.ok

        if not test_result.ok and task.iter_count < task.max_iter - 1:
            # Classify error + queue retry
            category, excerpt = classify_error(test_result.log_excerpt)
            err_log = f"iter {task.iter_count+1}: {category.value}: {excerpt[:300]}"
            dev_task_queue.update_state(
                task.task_id, "pending",  # retry on next tick
                error_log=err_log,
            )
            result.error = err_log
            result.state_after = "pending"
            return result

        if not test_result.ok:
            # Max iter exhausted
            _maybe_escalate(task, "max iter exhausted")
            result.state_after = "escalated"
            return result

        # 6. Submit PR
        # Phase 1 stub — Phase 2 actual git ops
        diff_summary = plan.summary
        test_summary = (
            f"Tests: {test_result.pytest_passed} pass / "
            f"{test_result.pytest_failed} fail"
        )
        submit_result = dev_pr_submitter.submit(
            task_id=task.task_id,
            branch_name=task.branch_name,
            diff_summary=diff_summary,
            test_summary=test_summary,
            touched_paths=touched,
            repo_root=repo_root,
        )

        if submit_result.ok:
            dev_task_queue.update_state(
                task.task_id, "review",
                pr_url=submit_result.pr_url,
            )
            dev_pr_submitter.notify_owner(
                task.task_id, diff_summary, submit_result.pr_url,
            )
            result.submitted = True
            result.pr_url = submit_result.pr_url
            result.state_after = "review"

            # Hafidz Ledger entry (Phase 2 wires properly)
            _write_audit_trail(task, plan, test_result, submit_result)
        else:
            result.error = f"submit failed: {submit_result.error}"
            _maybe_escalate(task, result.error)
            result.state_after = "escalated"

    except Exception as e:
        log.exception("[autodev] tick exception")
        result.error = f"unhandled exception: {e}"
        _maybe_escalate(task, result.error)
        result.state_after = "escalated"

    return result


def owner_approve(task_id: str) -> bool:
    """Owner approves a task in review. Marks for merge."""
    task = dev_task_queue.get_task(task_id)
    if not task:
        return False
    if task.state != "review":
        log.warning("[autodev] approve task=%s not in review (state=%s)",
                    task_id, task.state)
        return False
    return dev_task_queue.update_state(task_id, "approved",
                                       owner_verdict="approved")


def owner_reject(task_id: str, reason: str = "") -> bool:
    """Owner rejects a task in review."""
    return dev_task_queue.update_state(task_id, "rejected",
                                       owner_verdict="rejected",
                                       owner_feedback=reason)


def owner_request_changes(task_id: str, feedback: str) -> bool:
    """Owner requests iteration with feedback."""
    task = dev_task_queue.get_task(task_id)
    if not task:
        return False
    if task.iter_count >= task.max_iter:
        return False
    return dev_task_queue.update_state(
        task_id, "pending",
        owner_feedback=feedback,
        error_log=f"owner_feedback: {feedback}",
    )


# ── Internal helpers ─────────────────────────────────────────────────────────

def _maybe_escalate(task, reason: str) -> None:
    """If iter exhausted or critical failure → escalate to owner."""
    next_iter = task.iter_count + 1
    if next_iter >= task.max_iter:
        dev_task_queue.update_state(
            task.task_id, "escalated",
            error_log=f"escalated: {reason}",
        )
        log.warning("[autodev] task=%s ESCALATED: %s", task.task_id, reason)
    else:
        dev_task_queue.update_state(
            task.task_id, "pending",
            error_log=f"retry pending: {reason}",
        )


def _write_audit_trail(task, plan, test_result, submit_result) -> None:
    """Write Hafidz Ledger entry (Phase 2 wires properly)."""
    try:
        from .hafidz_ledger import write_entry
        write_entry(
            content=f"autodev iter={task.iter_count}: {plan.summary}",
            content_id=f"autodev-{task.task_id}-iter-{task.iter_count}",
            content_type="autonomous_dev_iteration",
            isnad_chain=[
                {"role": "agent", "name": "sidix_autonomous_developer"},
                {"role": "tools", "names": ["code_diff_planner", "dev_sandbox", "dev_pr_submitter"]},
            ],
            metadata={
                "task_id": task.task_id,
                "target_path": task.target_path,
                "goal": task.goal,
                "iter": task.iter_count,
                "test_passed": test_result.pytest_passed,
                "test_failed": test_result.pytest_failed,
                "branch": submit_result.branch,
                "pr_url": submit_result.pr_url,
            },
            cycle_id=task.cycle_id,
        )
    except Exception as e:
        log.debug("[autodev] hafidz write skipped: %s", e)


__all__ = ["TickResult", "tick", "owner_approve", "owner_reject",
           "owner_request_changes"]
