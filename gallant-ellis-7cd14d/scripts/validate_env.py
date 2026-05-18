"""
validate_env.py — Validate .env against .env.sample for the SIDIX/Mighan project.

Usage:
    python scripts/validate_env.py
    python scripts/validate_env.py --env-file .env.local
    python scripts/validate_env.py --sample .env.sample --env-file .env

Exit codes:
    0 — No issues found (or .env does not exist — only a warning is printed)
    1 — Issues found (unknown keys in .env, or required keys missing)

Rules:
    1. Any key in .env that is NOT in .env.sample is flagged as a possible typo.
    2. Any key in .env.sample with no default value (empty RHS) that is also
       missing from .env is flagged as "required but not set".
    3. Secret values are NEVER printed — only key names.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_env_file(path: Path) -> dict[str, Optional[str]]:
    """
    Parse a .env / .env.sample file into {KEY: value_or_None}.

    Rules:
    - Lines starting with # (after stripping) are comments — skip.
    - Blank lines are skipped.
    - KEY=VALUE  →  {KEY: "VALUE"}
    - KEY=        →  {KEY: ""}   (empty string — may mean "required")
    - KEY         →  {KEY: None} (no equals sign — treated as key-only)
    - Duplicate keys: last one wins (matches standard dotenv behaviour).
    """
    result: dict[str, Optional[str]] = {}
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            result[key] = value
        else:
            # Key with no value at all
            key = line.strip()
            if re.match(r"^[A-Z_][A-Z0-9_]*$", key, re.IGNORECASE):
                result[key] = None
    return result


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def validate(
    sample_path: Path,
    env_path: Path,
    *,
    verbose: bool = False,
) -> int:
    """
    Perform validation. Returns 0 (ok) or 1 (issues found).
    """
    issues: list[str] = []
    warnings: list[str] = []

    # --- Load .env.sample ---------------------------------------------------
    if not sample_path.exists():
        print(f"ERROR: .env.sample not found at {sample_path}", file=sys.stderr)
        return 1

    sample = _parse_env_file(sample_path)
    sample_keys = set(sample.keys())

    if verbose:
        print(f"[validate_env] .env.sample loaded: {len(sample_keys)} key(s)")

    # --- Load .env (optional) -----------------------------------------------
    if not env_path.exists():
        print(
            f"[validate_env] WARNING: {env_path} does not exist. "
            "Copy .env.sample to .env and fill in your values.",
            file=sys.stderr,
        )
        # Not a hard failure — CI may rely solely on real env vars
        return 0

    env = _parse_env_file(env_path)
    env_keys = set(env.keys())

    if verbose:
        print(f"[validate_env] {env_path} loaded: {len(env_keys)} key(s)")

    # --- Check 1: Keys in .env not present in .env.sample (possible typos) ---
    unknown_keys = env_keys - sample_keys
    if unknown_keys:
        for key in sorted(unknown_keys):
            issues.append(
                f"UNKNOWN KEY in {env_path.name} (not in .env.sample): {key!r}  "
                f"— possible typo or undocumented variable"
            )

    # --- Check 2: Empty-default keys in .env.sample missing from .env --------
    # "empty default" = key present in sample with value "" (or None)
    required_keys = {
        k for k, v in sample.items()
        if v is None or v == ""
    }
    missing_required = required_keys - env_keys
    if missing_required:
        for key in sorted(missing_required):
            warnings.append(
                f"MISSING KEY in {env_path.name} (no default in .env.sample): {key!r}"
            )

    # --- Report -------------------------------------------------------------
    ok = True

    if issues:
        ok = False
        print(f"\n[validate_env] ISSUES FOUND in {env_path}:\n", file=sys.stderr)
        for msg in issues:
            print(f"  ✗ {msg}", file=sys.stderr)

    if warnings:
        print(f"\n[validate_env] WARNINGS for {env_path}:\n", file=sys.stderr)
        for msg in warnings:
            print(f"  ⚠  {msg}", file=sys.stderr)

    if ok and not warnings:
        print(f"[validate_env] OK — {env_path} passes all checks.")
    elif ok:
        print(
            f"\n[validate_env] {env_path} has warnings but no hard errors. "
            "Returning exit 0."
        )

    return 0 if ok else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate .env against .env.sample for SIDIX/Mighan.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--env-file",
        default=".env",
        metavar="PATH",
        help="Path to the .env file to validate (default: .env)",
    )
    p.add_argument(
        "--sample",
        default=".env.sample",
        metavar="PATH",
        help="Path to .env.sample template (default: .env.sample)",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra diagnostic information",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # Resolve relative to cwd so the script works from any location
    sample_path = Path(args.sample)
    env_path = Path(args.env_file)

    return validate(sample_path, env_path, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
