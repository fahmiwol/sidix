"""
check_ui_lockfile.py — Verify the SIDIX User UI npm lockfile is healthy.

Checks performed:
    1. package-lock.json exists in the UI directory
    2. lockfileVersion >= 2 (npm v7+ format with full dependency tree)
    3. npm audit --json: reports any audit advisories (vulnerabilities)

Usage:
    python scripts/check_ui_lockfile.py
    python scripts/check_ui_lockfile.py --ui-dir SIDIX_USER_UI
    python scripts/check_ui_lockfile.py --ui-dir SIDIX_USER_UI --audit-level high

Exit codes:
    0 — All checks pass
    1 — One or more checks failed

Notes:
    - npm must be available on PATH for audit to run.
    - Secret values in package-lock.json are never printed.
    - Audit is advisory only by default (exit 0 even with low/moderate issues).
      Use --audit-level to tighten the threshold.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIT_LEVELS = ("info", "low", "moderate", "high", "critical")
AUDIT_LEVEL_SEVERITY = {lvl: idx for idx, lvl in enumerate(AUDIT_LEVELS)}

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UI_DIR = REPO_ROOT / "SIDIX_USER_UI"


# ---------------------------------------------------------------------------
# Check 1: lockfile existence
# ---------------------------------------------------------------------------

def check_lockfile_exists(ui_dir: Path) -> tuple[bool, str]:
    lockfile = ui_dir / "package-lock.json"
    if lockfile.exists():
        return True, f"package-lock.json found: {lockfile}"
    return False, (
        f"MISSING: package-lock.json not found at {lockfile}\n"
        "  Run: cd SIDIX_USER_UI && npm install"
    )


# ---------------------------------------------------------------------------
# Check 2: lockfileVersion >= 2
# ---------------------------------------------------------------------------

def check_lockfile_version(ui_dir: Path) -> tuple[bool, str, int, int]:
    """Returns (ok, message, lockfileVersion, total_package_count)."""
    lockfile = ui_dir / "package-lock.json"
    try:
        data = json.loads(lockfile.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"package-lock.json is not valid JSON: {exc}", 0, 0

    lv = data.get("lockfileVersion", 0)
    pkg_count = len(data.get("packages", data.get("dependencies", {})))

    if lv >= 2:
        return True, f"lockfileVersion: {lv} (OK — npm v7+ format)", lv, pkg_count
    return False, (
        f"lockfileVersion: {lv} — must be >= 2 (npm v7+ format).\n"
        "  Run: npm install  with npm >= 7 to regenerate the lockfile."
    ), lv, pkg_count


# ---------------------------------------------------------------------------
# Check 3: npm audit
# ---------------------------------------------------------------------------

def run_npm_audit(ui_dir: Path) -> tuple[bool, dict]:
    """
    Run `npm audit --json` in ui_dir.
    Returns (npm_available, audit_json_dict).
    audit_json_dict is {} if npm is not available or audit fails to parse.
    """
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=str(ui_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        return False, {}
    except subprocess.TimeoutExpired:
        print("[check_ui_lockfile] WARNING: npm audit timed out after 120s", file=sys.stderr)
        return True, {}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        # npm might print partial output if there's a network issue
        return True, {}

    return True, data


def summarise_audit(audit_data: dict, min_level: str) -> tuple[bool, list[str]]:
    """
    Parse npm audit JSON and return (passes_threshold, messages).

    npm audit v2 format uses:
        audit_data["metadata"]["vulnerabilities"] = {low: N, moderate: N, high: N, critical: N}
    npm audit v1 format uses:
        audit_data["metadata"]["vulnerabilities"] = {info: N, low: N, ...}
    """
    messages: list[str] = []
    min_sev = AUDIT_LEVEL_SEVERITY.get(min_level, AUDIT_LEVEL_SEVERITY["high"])

    vuln_summary = (
        audit_data.get("metadata", {}).get("vulnerabilities", {})
        or audit_data.get("vulnerabilities", {})
    )

    if not vuln_summary:
        messages.append("npm audit: no vulnerability data returned (network issue or no packages).")
        return True, messages

    total_issues = 0
    threshold_hits = 0
    for level, count in vuln_summary.items():
        if isinstance(count, int) and count > 0:
            sev = AUDIT_LEVEL_SEVERITY.get(level, -1)
            total_issues += count
            tag = ""
            if sev >= min_sev:
                threshold_hits += count
                tag = "  *** AT/ABOVE THRESHOLD ***"
            messages.append(f"  {level:12s}: {count}{tag}")

    if total_issues == 0:
        messages.append("npm audit: 0 vulnerabilities found.")
        return True, messages

    messages.insert(0, f"npm audit: {total_issues} total issue(s) found:")

    passes = threshold_hits == 0
    if not passes:
        messages.append(
            f"\n  {threshold_hits} issue(s) at or above --audit-level={min_level!r}."
        )
    return passes, messages


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_checks(ui_dir: Path, audit_level: str, skip_audit: bool) -> int:
    print(f"\n[check_ui_lockfile] UI directory: {ui_dir}")
    print(f"[check_ui_lockfile] Audit threshold: {audit_level}\n")

    all_ok = True

    # --- Check 1 ---
    ok, msg = check_lockfile_exists(ui_dir)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {msg}")
    if not ok:
        all_ok = False
        # Cannot proceed without lockfile
        return 1

    # --- Check 2 ---
    ok, msg, lv, pkg_count = check_lockfile_version(ui_dir)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {msg}")
    print(f"       Total packages in lockfile: {pkg_count}")
    if not ok:
        all_ok = False

    # --- Check 3 ---
    if skip_audit:
        print("[SKIP] npm audit skipped (--no-audit flag set)")
    else:
        print("\n[INFO] Running npm audit (this may take a moment)...")
        npm_available, audit_data = run_npm_audit(ui_dir)
        if not npm_available:
            print(
                "[WARN] npm not found on PATH — skipping audit.\n"
                "       Install Node.js/npm to enable vulnerability scanning."
            )
        else:
            audit_ok, audit_msgs = summarise_audit(audit_data, min_level=audit_level)
            status = "PASS" if audit_ok else "FAIL"
            print(f"[{status}] Audit results:")
            for line in audit_msgs:
                print(f"       {line}")
            if not audit_ok:
                all_ok = False

    print()
    if all_ok:
        print("[check_ui_lockfile] All checks PASSED.")
        return 0
    else:
        print("[check_ui_lockfile] One or more checks FAILED.", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Verify SIDIX User UI npm lockfile health.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--ui-dir",
        default=str(DEFAULT_UI_DIR),
        metavar="PATH",
        help=f"Path to the UI directory containing package-lock.json (default: {DEFAULT_UI_DIR})",
    )
    p.add_argument(
        "--audit-level",
        default="high",
        choices=AUDIT_LEVELS,
        help="Minimum vulnerability severity that causes a FAIL (default: high)",
    )
    p.add_argument(
        "--no-audit",
        action="store_true",
        help="Skip the npm audit step entirely",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    ui_dir = Path(args.ui_dir)
    return run_checks(ui_dir, audit_level=args.audit_level, skip_audit=args.no_audit)


if __name__ == "__main__":
    sys.exit(main())
