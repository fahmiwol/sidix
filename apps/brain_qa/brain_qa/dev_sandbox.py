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
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
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


def _python_bin() -> str:
    """Return 'python3' if available, else 'python'. VPS fix (Sprint 40 E2E)."""
    import shutil
    return "python3" if shutil.which("python3") else "python"


def run_pytest(repo_root: Path, paths: list[str] | None = None,
               timeout: int = 600) -> TestResult:
    """Run pytest. Returns TestResult.

    Phase 1: minimal subprocess invocation.
    """
    import time
    t0 = time.time()
    # Strategy: --junitxml for reliable machine-readable results + tempfile for
    # terminal output. pytest's FDCapture/TerminalWriter can raise ValueError
    # ("I/O operation on closed file") when run as subprocess, making returncode
    # and stdout parsing unreliable. junitxml is written per-test (not at end)
    # so it survives a terminal crash.  We read counts from XML, not stdout.
    xml_fd, xml_path = tempfile.mkstemp(suffix=".pytest.xml", prefix="sidix_")
    log_fd, log_path = tempfile.mkstemp(suffix=".pytest.log", prefix="sidix_")
    os.close(xml_fd)  # will be written by pytest, not us
    cmd = [_python_bin(), "-m", "pytest", "--tb=short", "-q",
           f"--junitxml={xml_path}"]
    if paths:
        cmd.extend(paths)

    log.info("[dev_sandbox] pytest cmd=%s", " ".join(cmd))
    try:
        with os.fdopen(log_fd, "w", errors="replace") as log_f:
            proc = subprocess.run(
                cmd, cwd=str(repo_root),
                stdout=log_f, stderr=log_f,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )
        # Read terminal log (best-effort — may be incomplete if pytest crashed)
        try:
            with open(log_path, errors="replace") as f:
                out = f.read()
        except OSError:
            out = ""

        # Parse counts from junitxml (authoritative) —────────────────────────
        passed = failed = errors = 0
        ok = False
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            # <testsuite tests="N" failures="M" errors="K" ...>
            suite = root if root.tag == "testsuite" else root.find("testsuite")
            if suite is not None:
                tests  = int(suite.get("tests",  "0"))
                fails  = int(suite.get("failures", "0"))
                errs   = int(suite.get("errors",   "0"))
                skips  = int(suite.get("skipped",  "0"))
                passed = tests - fails - errs - skips
                failed = fails
                errors = errs
                ok = (fails == 0 and errs == 0 and tests > 0)
            else:
                log.warning("[dev_sandbox] junitxml: no testsuite element")
                ok = proc.returncode == 0
        except Exception as xml_err:
            log.warning("[dev_sandbox] junitxml parse failed: %s — fallback to returncode", xml_err)
            ok = proc.returncode == 0
            # Crude text parsing as fallback
            for line in out.splitlines()[-20:]:
                if " passed" in line or " failed" in line or " error" in line:
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
        log.info("[dev_sandbox] pytest done: passed=%d failed=%d errors=%d ok=%s",
                 passed, failed, errors, ok)
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
    finally:
        for p in (xml_path, log_path):
            try:
                os.unlink(p)
            except OSError:
                pass


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
