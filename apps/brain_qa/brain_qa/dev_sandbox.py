"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

dev_sandbox.py — Sprint 40 Phase 1 (Autonomous Developer test sandbox)

Run the project test suite against an applied DiffPlan untuk verify
production-ready criteria (tests pass, lint clean, type-check OK).

Pattern: invokes pytest + ruff + (optionally) mypy as subprocess in
a copy of the worktree branch. Returns structured TestResult per iter.

Phase 1 scope: function signatures + result dataclass + happy-path
pytest invocation. ruff/mypy wiring di Phase 2.

Reference: docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Outcome of running tests on applied diff."""
    ok: bool = False
    pytest_passed: int = 0
    pytest_failed: int = 0
    pytest_errors: int = 0
    ruff_issues: int = 0
    typecheck_issues: int = 0
    duration_seconds: float = 0.0
    log_excerpt: str = ""           # last ~2000 chars of output
    failure_classification: str = ""  # uses cloud_run_iterator.ErrorCategory


def run_pytest(repo_root: Path, paths: list[str] | None = None,
               timeout: int = 600) -> TestResult:
    """Run pytest. Returns TestResult.

    Phase 1: minimal subprocess invocation.
    """
    import time
    t0 = time.time()
    cmd = ["python", "-m", "pytest", "--tb=short", "-q"]
    if paths:
        cmd.extend(paths)

    log.info("[dev_sandbox] pytest cmd=%s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd, cwd=str(repo_root), capture_output=True, text=True,
            timeout=timeout,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        ok = proc.returncode == 0
        # Crude parsing — extract summary
        passed = failed = errors = 0
        for line in (proc.stdout or "").splitlines()[-20:]:
            if " passed" in line or " failed" in line or " error" in line:
                # e.g. "5 passed, 1 failed in 2.3s"
                tokens = line.replace(",", " ").split()
                for i, t in enumerate(tokens):
                    if t.isdigit():
                        n = int(t)
                        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
                        if "passed" in nxt:
                            passed = n
                        elif "failed" in nxt:
                            failed = n
                        elif "error" in nxt:
                            errors = n
        duration = time.time() - t0
        return TestResult(
            ok=ok, pytest_passed=passed, pytest_failed=failed,
            pytest_errors=errors, duration_seconds=round(duration, 2),
            log_excerpt=out[-2000:],
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            ok=False, duration_seconds=timeout,
            log_excerpt="TIMEOUT",
            failure_classification="timeout",
        )
    except Exception as e:
        return TestResult(
            ok=False, log_excerpt=f"sandbox error: {e}",
            failure_classification="sandbox_error",
        )


def run_ruff(repo_root: Path) -> int:
    """Return number of ruff issues (Phase 2 will detail)."""
    log.debug("[dev_sandbox] ruff Phase 2 stub")
    return 0


def run_typecheck(repo_root: Path) -> int:
    """Return number of mypy/pyright issues (Phase 2 will detail)."""
    log.debug("[dev_sandbox] typecheck Phase 2 stub")
    return 0


def full_check(repo_root: Path, paths: list[str] | None = None) -> TestResult:
    """Run pytest + ruff + typecheck → unified TestResult."""
    result = run_pytest(repo_root, paths)
    result.ruff_issues = run_ruff(repo_root)
    result.typecheck_issues = run_typecheck(repo_root)
    if result.pytest_failed > 0 or result.pytest_errors > 0:
        result.ok = False
    if result.ruff_issues > 0 or result.typecheck_issues > 0:
        result.ok = False
    return result


__all__ = ["TestResult", "run_pytest", "run_ruff", "run_typecheck", "full_check"]
