"""
code_diff_planner.py — Sprint 40 Phase 1 (Autonomous Developer LLM-based diff planner)

Take a DevTask + repo context → produce structured code change proposal
(file additions, modifications, deletions) yang bisa di-apply ke worktree.

Pattern: LLM brain (Qwen+LoRA SIDIX) read scaffold + production criteria
       → propose diff → validated structurally → returned for application.

Scope MVP Phase 1: function signatures + dataclass. LLM call wired to
existing local_llm.generate_sidix() di Phase 2.

Multi-persona fan-out (per project_sidix_multi_agent_pattern.md): if
DevTask.persona_fanout = True, planner invokes 5 persona researchers
(UTZ/ABOO/OOMAR/ALEY/AYMAN) for cross-perspective context, then synthesize
unified diff. Default = single ABOO (engineer) for simple tasks.

Reference:
- docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md
- project_sidix_multi_agent_pattern.md
- research note 281 (sintesis multi-dimensi)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class FileChange:
    """One file change proposal: create / modify / delete."""
    path: str                        # repo-relative path
    action: str                      # "create" | "modify" | "delete"
    content: str = ""                # full new content (create) or new text (modify)
    diff: str = ""                   # unified diff representation (modify)
    rationale: str = ""              # WHY this change


@dataclass
class DiffPlan:
    """Structured plan output by planner."""
    task_id: str = ""
    files: list[FileChange] = field(default_factory=list)
    summary: str = ""                # 1-line human summary
    rationale: str = ""              # multi-line WHY explanation
    risks: list[str] = field(default_factory=list)
    test_additions: list[str] = field(default_factory=list)
    persona_contributions: dict = field(default_factory=dict)  # if fanout
    confidence: float = 0.5
    iteration: int = 1


# ── Public API ───────────────────────────────────────────────────────────────

def plan_changes(
    task_id: str,
    target_path: str,
    goal: str,
    repo_root: Path,
    iteration: int = 1,
    previous_error: str = "",
    persona_fanout: bool = False,
) -> DiffPlan:
    """Plan code changes for an autonomous dev task.

    Args:
        task_id: dev task identifier
        target_path: repo-relative path of scaffold to bring to production
        goal: human description of production-ready criteria
        repo_root: project root for context reading
        iteration: 1-indexed iteration number (for retry context)
        previous_error: error context from prior failed iteration
        persona_fanout: spawn 5-persona researcher fan-out (for complex)

    Returns:
        DiffPlan dengan file changes + rationale + risks.

    Phase 1 scope: scaffold returns empty DiffPlan dengan stub.
    Phase 2 wires LLM call.
    """
    log.info("[code_diff_planner] task=%s iter=%d fanout=%s",
             task_id, iteration, persona_fanout)

    # Phase 1 scaffold — return empty plan with stub fields
    plan = DiffPlan(
        task_id=task_id,
        summary=f"[STUB] Plan for {target_path} iter {iteration}",
        rationale=f"Goal: {goal}\nPhase 1 scaffold — LLM wiring pending Phase 2.",
        confidence=0.0,
        iteration=iteration,
    )

    if persona_fanout:
        # Phase 2 will invoke persona_research_fanout.gather()
        plan.persona_contributions = {
            "UTZ": "[pending fanout] creative direction",
            "ABOO": "[pending fanout] engineering best practices",
            "OOMAR": "[pending fanout] strategy/market context",
            "ALEY": "[pending fanout] academic precedent",
            "AYMAN": "[pending fanout] community/UX feedback",
        }

    return plan


def validate_plan(plan: DiffPlan, repo_root: Path) -> tuple[bool, list[str]]:
    """Sanity-check a DiffPlan before applying.

    Returns (ok, list_of_issues).
    """
    issues: list[str] = []
    if not plan.files and plan.confidence > 0.0:
        issues.append("no file changes despite confidence > 0")

    for fc in plan.files:
        if fc.action not in ("create", "modify", "delete"):
            issues.append(f"invalid action {fc.action!r} for {fc.path}")
        # security: prevent escaping repo root
        try:
            full = (repo_root / fc.path).resolve()
            if not str(full).startswith(str(repo_root.resolve())):
                issues.append(f"path escape: {fc.path}")
        except Exception as e:
            issues.append(f"path resolve error {fc.path}: {e}")

        # Hard-blocked sensitive files
        blocked = (".env", ".gitignore", "CLAUDE.md", "MEMORY.md")
        if any(fc.path.endswith(b) for b in blocked):
            issues.append(f"blocked path: {fc.path}")

    return (len(issues) == 0, issues)


def apply_plan(plan: DiffPlan, repo_root: Path, dry_run: bool = False) -> list[str]:
    """Apply DiffPlan to filesystem. Returns list of touched paths.

    Phase 1: dry_run only (logs intended changes).
    Phase 2: actual file writes with git stage.
    """
    touched: list[str] = []
    for fc in plan.files:
        if dry_run:
            log.info("[code_diff_planner] DRY %s %s", fc.action, fc.path)
        else:
            log.warning("[code_diff_planner] apply NOT YET IMPLEMENTED Phase 2")
        touched.append(fc.path)
    return touched


__all__ = ["FileChange", "DiffPlan", "plan_changes", "validate_plan", "apply_plan"]
