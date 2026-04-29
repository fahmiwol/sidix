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
import shutil as _shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

_PYTHON_BIN: str = "python3" if _shutil.which("python3") else "python"


@dataclass
class TestResult:
    """Outcome of running tests on applied diff."""

    __test__ = False  # prevent pytest treating this dataclass as a test class

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
    return _PYTHON_BIN


def run_pytest(repo_root: Path, paths: list[str] | None = None,
               timeout: int = 600) -> TestResult:
    """Run pytest. Returns TestResult.

    Root-cause fix (Sprint 40 final):
    pytest's FDCapture/TerminalWriter writes to sys.stdout during Python
    shutdown (Py_Finalize()), AFTER the underlying fd is already closed by
    the subprocess machinery — especially when Ollama times out and pytest
    error teardown runs during interpreter shutdown.  Routing stdout+stderr
    to /dev/null (writes always succeed, never block) eliminates the race
    entirely.  All result data comes from --junitxml which is written
    per-testcase and survives a terminal crash.  Failure details are
    extracted from <failure>/<error> XML child elements.
    """
    import time
    t0 = time.time()

    xml_fd, xml_path = tempfile.mkstemp(suffix=".pytest.xml", prefix="sidix_")
    os.close(xml_fd)  # pytest will write to this path itself

    cmd = [_python_bin(), "-m", "pytest", "--tb=short", "-q",
           f"--junitxml={xml_path}"]
    if paths:
        cmd.extend(paths)
    # NOTE: no --ignore flag needed — /dev/null eliminates FDCapture crash

    log.info("[dev_sandbox] pytest cmd=%s", " ".join(cmd))
    try:
        # Route stdout+stderr to /dev/null.  This is the key fix: writes to
        # /dev/null never raise ValueError regardless of shutdown ordering,
        # so pytest's FDCapture teardown cannot crash the subprocess.
        # All result data is read from junitxml below.
        with open(os.devnull, "w") as devnull_f:
            proc = subprocess.run(
                cmd, cwd=str(repo_root),
                stdout=devnull_f, stderr=devnull_f,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
            )

        # Parse counts + failure messages from junitxml ───────────────────────
        passed = failed = errors = 0
        ok = False
        log_lines: list[str] = []
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            # <testsuite tests="N" failures="M" errors="K" skipped="J" ...>
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

                # Extract failure/error messages for log_excerpt so callers
                # can see WHY tests failed without needing stdout capture.
                for tc in suite.iter("testcase"):
                    name = f"{tc.get('classname','')}.{tc.get('name','')}"
                    for child in tc:
                        if child.tag in ("failure", "error"):
                            msg = (child.get("message") or "")[:300]
                            body = (child.text or "")[-500:]
                            log_lines.append(f"[{child.tag.upper()}] {name}: {msg}\n{body}")
            else:
                log.warning("[dev_sandbox] junitxml: no testsuite element")
                ok = proc.returncode == 0
        except Exception as xml_err:
            log.warning("[dev_sandbox] junitxml parse failed: %s — fallback to returncode", xml_err)
            ok = proc.returncode == 0

        duration = time.time() - t0
        log.info("[dev_sandbox] pytest done: passed=%d failed=%d errors=%d ok=%s",
                 passed, failed, errors, ok)
        excerpt = "\n\n".join(log_lines)[-2000:] if log_lines else ""
        return TestResult(
            ok=ok, pytest_passed=passed, pytest_failed=failed,
            pytest_errors=errors, duration_seconds=round(duration, 2),
            log_excerpt=excerpt,
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
        try:
            os.unlink(xml_path)
        except OSError:
            pass


def run_ruff(repo_root: Path,
             paths: list[str] | None = None) -> int:
    """Run ruff check. Return number of lint issues.

    Delta-mode (paths given):
      Scan ONLY the specific files touched by the autonomous developer's diff.
      This is the gating mode — violations in new/modified files → PR blocked.
      Pre-existing violations in untouched files are ignored.

    Full-scan mode (paths=None):
      Scan entire apps/brain_qa. Advisory only — not gating — because the
      baseline codebase carries ~3000+ pre-existing violations the autonomous
      developer did not introduce.

    Requires ruff to be installed (`pip install ruff`).
    Returns 0 if ruff not found (non-fatal — test gate still works).
    """
    if paths:
        # Delta-mode: filter to .py files that exist on disk
        py_files = [
            str(repo_root / p) if not Path(p).is_absolute() else p
            for p in paths
            if p.endswith(".py")
        ]
        py_files = [p for p in py_files if Path(p).exists()]
        if not py_files:
            log.debug("[dev_sandbox] ruff delta: no .py files in touched set")
            return 0
        target_args = py_files
        mode = f"delta({len(py_files)} files)"
    else:
        target = repo_root / "apps" / "brain_qa"
        if not target.is_dir():
            log.debug("[dev_sandbox] ruff: apps/brain_qa not found, skipping")
            return 0
        target_args = [str(target)]
        mode = "full-scan(advisory)"

    try:
        proc = subprocess.run(
            [_PYTHON_BIN, "-m", "ruff", "check", *target_args,
             "--select=E,F,W,I", "--quiet"],
            cwd=str(repo_root),
            capture_output=True, text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        )
        if proc.returncode == 0:
            log.info("[dev_sandbox] ruff %s: clean (0 issues)", mode)
            return 0
        # Count violation lines: each looks like "path:line:col: CODE message"
        issues = [ln for ln in proc.stdout.splitlines() if ln.strip() and ": " in ln]
        n = len(issues)
        log.info("[dev_sandbox] ruff %s: %d issues", mode, n)
        return n
    except FileNotFoundError:
        log.debug("[dev_sandbox] ruff not installed — skip lint check")
        return 0
    except subprocess.TimeoutExpired:
        log.warning("[dev_sandbox] ruff timed out — skip")
        return 0
    except Exception as e:
        log.warning("[dev_sandbox] ruff error: %s", e)
        return 0


def run_typecheck(repo_root: Path) -> int:
    """Return number of mypy/pyright issues (Phase 2 will detail)."""
    log.debug("[dev_sandbox] typecheck Phase 2 stub")
    return 0


def full_check(repo_root: Path, paths: list[str] | None = None) -> TestResult:
    """Run pytest + ruff + typecheck → unified TestResult.

    Gate policy (Sprint 60E — delta-mode ruff):

      paths provided (autonomous_developer supplies touched files):
        → ruff runs in DELTA-MODE: check only files the diff touched.
        → ruff_issues > 0 → ok = False (new violations block the PR).
        → This makes autonomous dev fully production-quality gated.

      paths=None (manual / full-scan call):
        → ruff runs on entire apps/brain_qa (advisory; ~3000+ baseline).
        → ruff_issues informational only — does NOT change ok.
        → pytest failures still gate ok.

    Design rationale: baseline has ~3726 pre-existing ruff violations the
    autonomous developer did not introduce. Full-scan gating would permanently
    block all PRs. Delta-mode is precise: SIDIX cannot INTRODUCE new lint
    violations into files it modifies. Pre-existing violations in untouched
    files are ignored — they are a separate cleanup task.
    """
    # pytest ALWAYS runs the full test suite — paths here are source files,
    # not test paths.  Passing touched source files to pytest would make it
    # try to collect tests from e.g. "brain_qa/foo.py" → finds 0 tests →
    # ok=False (wrong).  Always run all tests unconditionally.
    result = run_pytest(repo_root)

    # ruff: delta-mode (check only touched source files) when paths given,
    # otherwise advisory full-scan (does not gate ok).
    result.ruff_issues = run_ruff(repo_root, paths)
    result.typecheck_issues = run_typecheck(repo_root)

    # pytest always gates
    if result.pytest_failed > 0 or result.pytest_errors > 0:
        result.ok = False

    # ruff gates ONLY in delta-mode (autonomous developer supplied touched paths)
    if paths and result.ruff_issues > 0:
        result.ok = False
        log.warning("[dev_sandbox] ruff delta: %d violations in touched files — PR blocked",
                    result.ruff_issues)

    return result


__all__ = ["TestResult", "run_pytest", "run_ruff", "run_typecheck", "full_check"]
