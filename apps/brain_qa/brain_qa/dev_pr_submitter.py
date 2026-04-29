"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

dev_pr_submitter.py — Sprint 40 Phase 1 (Autonomous Developer git ops)

Convert applied DiffPlan + TestResult ke git commit + push + (optional) GitHub
PR creation. Notifies founder via Telegram bot.

State transitions consumed:
  in_progress → review (after successful submit)

Phase 1 scope: subprocess wrapping git commands + return PR URL stub.
Phase 2: GitHub API for PR creation + Telegram bot notification.

Reference: docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md
"""
from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class SubmitResult:
    ok: bool = False
    branch: str = ""
    commit_sha: str = ""
    pr_url: str = ""
    error: str = ""


def _git(args: list[str], repo_root: Path, check: bool = True) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args], cwd=str(repo_root),
        capture_output=True, text=True,
    )
    if check and proc.returncode != 0:
        log.warning("[dev_pr] git %s exit=%d stderr=%s",
                    " ".join(args), proc.returncode, proc.stderr.strip())
    return proc.returncode, proc.stdout, proc.stderr


def create_branch(branch_name: str, repo_root: Path) -> bool:
    """Create branch from current HEAD. Returns True on success."""
    code, _, _ = _git(["checkout", "-b", branch_name], repo_root, check=False)
    if code != 0:
        # branch exists, checkout
        code, _, _ = _git(["checkout", branch_name], repo_root, check=False)
    return code == 0


def stage_files(paths: list[str], repo_root: Path) -> bool:
    if not paths:
        return False
    code, _, _ = _git(["add", *paths], repo_root)
    return code == 0


def commit(message: str, repo_root: Path) -> str:
    """Commit staged. Returns commit SHA, or empty string."""
    code, _, _ = _git(["commit", "-m", message], repo_root, check=False)
    if code != 0:
        return ""
    code, sha, _ = _git(["rev-parse", "HEAD"], repo_root)
    return sha.strip() if code == 0 else ""


def push_branch(branch_name: str, repo_root: Path,
                remote: str = "origin") -> bool:
    code, _, _ = _git(["push", "-u", remote, branch_name], repo_root, check=False)
    return code == 0


def submit(
    task_id: str,
    branch_name: str,
    diff_summary: str,
    test_summary: str,
    touched_paths: list[str],
    repo_root: Path,
) -> SubmitResult:
    """End-to-end: branch + stage + commit + push.

    Phase 2 will add GitHub PR creation via gh CLI + Telegram notify.
    """
    if not create_branch(branch_name, repo_root):
        return SubmitResult(ok=False, error="branch create failed")

    if not stage_files(touched_paths, repo_root):
        return SubmitResult(ok=False, error="git stage failed")

    msg = (
        f"autonomous-dev({task_id}): {diff_summary}\n"
        f"\n"
        f"{test_summary}\n"
        f"\n"
        f"Submitted by SIDIX autonomous_developer (Sprint 40).\n"
        f"Owner approval required before merge.\n"
    )
    sha = commit(msg, repo_root)
    if not sha:
        return SubmitResult(ok=False, branch=branch_name, error="commit failed")

    pushed = push_branch(branch_name, repo_root)
    if not pushed:
        return SubmitResult(
            ok=False, branch=branch_name, commit_sha=sha,
            error="push failed (commit retained locally)",
        )

    # Phase 2: gh pr create
    pr_url = f"branch:{branch_name}@{sha[:8]}"  # placeholder
    return SubmitResult(ok=True, branch=branch_name, commit_sha=sha, pr_url=pr_url)


def notify_owner(task_id: str, summary: str, pr_url: str) -> bool:
    """Telegram bot notification. Sprint 60D: real implementation.

    Requires env vars:
      TELEGRAM_BOT_TOKEN  — from @BotFather
      TELEGRAM_CHAT_ID    — founder's chat ID (integer) or group ID

    If either var is missing → falls back to log-only (silent, returns True).
    Uses stdlib only (urllib) — no extra dependencies.
    """
    import os, urllib.request, urllib.parse, json as _json

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id   = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        log.info("[dev_pr] OWNER NOTIFY (log-only — set TELEGRAM_BOT_TOKEN+TELEGRAM_CHAT_ID) "
                 "task=%s pr=%s", task_id, pr_url)
        return True

    try:
        message = (
            f"🤖 *SIDIX Autonomous Dev*\n"
            f"Task: `{task_id}`\n"
            f"Summary: {summary}\n"
            f"PR: `{pr_url}`\n\n"
            f"_Review diperlukan sebelum merge ke main._"
        )
        payload = _json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }).encode("utf-8")
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            ok = resp.status == 200
        log.info("[dev_pr] Telegram notify sent ok=%s task=%s", ok, task_id)
        return ok
    except Exception as e:
        log.warning("[dev_pr] Telegram notify failed: %s — continuing", e)
        return False  # non-fatal: PR was submitted, notification just failed


__all__ = ["SubmitResult", "create_branch", "stage_files", "commit",
           "push_branch", "submit", "notify_owner"]
