"""
tag_release.py — Automatic git release tagging from SIDIX version string.

Usage:
    python scripts/tag_release.py
    python scripts/tag_release.py --version 0.3.0
    python scripts/tag_release.py --dry-run
    python scripts/tag_release.py --version 0.3.0 --push
    python scripts/tag_release.py --version 0.3.0 --force --push

Version resolution order:
    1. --version CLI argument
    2. apps/brain_qa/brain_qa/__init__.py  (__version__ = "x.y.z")
    3. VERSION file in repo root
    4. Interactive prompt

Exit codes:
    0 — Tag created (or dry-run printed) successfully
    1 — Error (dirty tree, tag exists, version not found, git error)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repo root (scripts/ lives one level below root)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Version resolution
# ---------------------------------------------------------------------------

def _read_version_from_init() -> str | None:
    """Read __version__ from apps/brain_qa/brain_qa/__init__.py."""
    init_path = REPO_ROOT / "apps" / "brain_qa" / "brain_qa" / "__init__.py"
    if not init_path.exists():
        return None
    text = init_path.read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    return m.group(1) if m else None


def _read_version_from_file() -> str | None:
    """Read VERSION file from repo root."""
    version_path = REPO_ROOT / "VERSION"
    if not version_path.exists():
        return None
    content = version_path.read_text(encoding="utf-8").strip()
    if re.match(r'^\d+\.\d+\.\d+', content):
        return content
    return None


def _prompt_version() -> str:
    """Interactively prompt the user for a version string."""
    while True:
        version = input("Enter version (e.g. 0.2.0): ").strip()
        if re.match(r'^\d+\.\d+\.\d+', version):
            return version
        print(f"Invalid semver format: {version!r}. Expected X.Y.Z", file=sys.stderr)


def resolve_version(cli_version: str | None) -> str:
    """Return the version string from the first available source."""
    if cli_version:
        if not re.match(r'^\d+\.\d+\.\d+', cli_version):
            print(f"ERROR: --version {cli_version!r} is not a valid semver string.", file=sys.stderr)
            sys.exit(1)
        return cli_version

    v = _read_version_from_init()
    if v:
        print(f"[tag_release] Version from __init__.py: {v}")
        return v

    v = _read_version_from_file()
    if v:
        print(f"[tag_release] Version from VERSION file: {v}")
        return v

    print("[tag_release] Version not found automatically. Prompting...", file=sys.stderr)
    return _prompt_version()


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _run_git(*args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *args]
    return subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        check=check,
        capture_output=capture,
        text=True,
    )


def check_working_tree_clean(force: bool) -> None:
    """Abort if the working tree has uncommitted changes (unless --force)."""
    result = _run_git("status", "--porcelain")
    if result.stdout.strip():
        msg = (
            "ERROR: Working tree is dirty. Commit or stash your changes before tagging.\n"
            "Dirty files:\n" + result.stdout.rstrip()
        )
        if force:
            print(f"[tag_release] WARNING: --force passed, ignoring dirty tree.\n{msg}", file=sys.stderr)
        else:
            print(msg, file=sys.stderr)
            sys.exit(1)


def tag_exists(tag: str) -> bool:
    """Return True if *tag* already exists in the local repo."""
    result = _run_git("tag", "--list", tag, check=False)
    return bool(result.stdout.strip())


def create_tag(tag: str, version: str, dry_run: bool) -> None:
    """Create an annotated git tag."""
    message = f"Release {version}\n\nSIDIX/Mighan brain_qa v{version}"
    if dry_run:
        print(f"[tag_release] DRY-RUN: would create annotated tag {tag!r}")
        print(f"              Message: {message!r}")
        return
    _run_git("tag", "-a", tag, "-m", message, capture=False)
    print(f"[tag_release] Created annotated tag: {tag}")


def push_tag(tag: str, dry_run: bool) -> None:
    """Push the tag to origin."""
    if dry_run:
        print(f"[tag_release] DRY-RUN: would run: git push origin {tag}")
        return
    print(f"[tag_release] Pushing {tag} to origin...")
    _run_git("push", "origin", tag, capture=False)
    print(f"[tag_release] Pushed: {tag}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Create an annotated git release tag from the SIDIX version.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--version",
        metavar="X.Y.Z",
        help="Override the version (default: read from __init__.py / VERSION file)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without creating any tag",
    )
    p.add_argument(
        "--push",
        action="store_true",
        help="After creating the tag, push it to origin",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Allow tagging even when the working tree is dirty",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    # 1. Resolve version
    version = resolve_version(args.version)
    tag = f"v{version}"

    print(f"[tag_release] Target tag: {tag}")

    # 2. Dirty-tree guard
    check_working_tree_clean(force=args.force)

    # 3. Tag collision guard
    if tag_exists(tag):
        print(
            f"ERROR: Tag {tag!r} already exists. "
            "Bump the version or delete the existing tag manually.",
            file=sys.stderr,
        )
        return 1

    # 4. Create tag
    create_tag(tag, version, dry_run=args.dry_run)

    # 5. Optionally push
    if args.push:
        push_tag(tag, dry_run=args.dry_run)
    else:
        if not args.dry_run:
            print(f"[tag_release] Tag created locally. Run with --push to push to origin.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
