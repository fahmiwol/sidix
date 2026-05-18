"""
kimi_code_tool.py — Subprocess wrapper for Kimi Code CLI

Kimi Code is a full coding agent CLI by Moonshot AI (similar to Claude Code).
Installed via: curl -L code.kimi.com/install.sh | bash
Binary: /root/.local/bin/kimi (or ~/.local/bin/kimi)

Different from external_llm_pool — Kimi Code is a multi-step CODING agent,
not a single-shot Q&A. SIDIX delegates coding tasks to it.

Use case:
- Refactor file: kimi --headless "refactor this Python file..."
- Generate script: kimi --headless "write a script that..."
- Review code: kimi --headless "review apps/brain_qa/.../foo.py"
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

_KIMI_BIN = Path(os.path.expanduser("~/.local/bin/kimi"))


@dataclass
class KimiCodeResult:
    success: bool
    output: str
    duration_ms: int
    error: str = ""


def kimi_available() -> bool:
    return _KIMI_BIN.exists() and os.access(_KIMI_BIN, os.X_OK)


def kimi_ask(prompt: str, cwd: str = "/opt/sidix", timeout: int = 60) -> KimiCodeResult:
    """
    Run Kimi Code CLI in headless mode.
    Note: Kimi Code may need interactive auth on first run. Set up via:
        ~/.local/bin/kimi (interactive) — login once.

    Args:
        prompt: natural-language task / question
        cwd: working dir (Kimi reads files relative here)
        timeout: max seconds
    """
    import time
    if not kimi_available():
        return KimiCodeResult(success=False, output="", duration_ms=0,
                              error="Kimi Code not installed. Run: curl -L code.kimi.com/install.sh | bash")
    t0 = time.time()
    try:
        # Try common headless flags
        proc = subprocess.run(
            [str(_KIMI_BIN), "--headless", "--no-confirm", prompt],
            capture_output=True, text=True, timeout=timeout,
            cwd=cwd, encoding="utf-8", errors="replace",
        )
        duration = int((time.time() - t0) * 1000)
        if proc.returncode != 0:
            return KimiCodeResult(success=False,
                                  output=proc.stdout[:2000],
                                  duration_ms=duration,
                                  error=proc.stderr[:500])
        return KimiCodeResult(success=True,
                              output=proc.stdout[:5000],
                              duration_ms=duration)
    except subprocess.TimeoutExpired:
        return KimiCodeResult(success=False, output="",
                              duration_ms=int((time.time() - t0) * 1000),
                              error=f"timeout after {timeout}s")
    except Exception as e:
        return KimiCodeResult(success=False, output="",
                              duration_ms=int((time.time() - t0) * 1000),
                              error=str(e)[:300])


__all__ = ["KimiCodeResult", "kimi_available", "kimi_ask"]
