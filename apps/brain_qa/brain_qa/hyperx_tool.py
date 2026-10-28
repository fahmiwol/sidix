"""
hyperx_tool.py — SIDIX subprocess wrapper for HYPERX Browser

HYPERX Browser is at /opt/sidix/tools/hyperx-browser/
Pure Node.js, anonymous-first, multi-engine search, scrape-friendly.

This wrapper exposes HYPERX as Python-callable functions, so SIDIX can use it
from agent_tools.py without spawning a long-running process.

Why HYPERX vs httpx-only:
- UA rotation built-in (8 user agents in pool)
- Tracker param stripping (UTM/fbclid/etc auto-removed)
- Cookie-less by default (true anonymous)
- Multi-source search aggregator (HN + GitHub + Wiby)
- Markdown extraction via turndown (cleaner than trafilatura for some sites)
- Cheerio CSS selectors (more flexible than regex)

Usage:
    from brain_qa.hyperx_tool import hyperx_get, hyperx_search_multi
    page = hyperx_get("https://example.com")
    hits = hyperx_search_multi("AI agent open source")
"""
from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_HYPERX_DIR = Path("/opt/sidix/tools/hyperx-browser")
_HYPERX_CLI = _HYPERX_DIR / "bin" / "hyperx.js"
_TIMEOUT_DEFAULT = 20  # seconds


@dataclass
class HyperXPage:
    url: str
    title: str
    text: str
    status: int
    duration_ms: int
    error: str = ""


@dataclass
class HyperXSearchHit:
    title: str
    url: str
    snippet: str
    source: str  # "hn" / "github" / "wiby" / "brave" / etc


def _run_hyperx(args: list[str], timeout: int = _TIMEOUT_DEFAULT) -> tuple[int, str, str]:
    """Run HYPERX CLI subprocess, return (exit_code, stdout, stderr)."""
    if not _HYPERX_CLI.exists():
        return 127, "", f"HYPERX not installed at {_HYPERX_CLI}"
    try:
        proc = subprocess.run(
            ["node", str(_HYPERX_CLI), *args],
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    except Exception as e:
        return 1, "", str(e)[:300]


def hyperx_get(url: str, raw: bool = False, timeout: int = _TIMEOUT_DEFAULT) -> HyperXPage:
    """
    Anonymous fetch via HYPERX. Returns rendered text + metadata.

    Slower than direct httpx (subprocess overhead ~50ms) but anonymity-grade.
    Use for sensitive scraping where UA rotation + tracker stripping matters.
    """
    import time
    t0 = time.time()
    args = [url]
    if raw:
        args.append("--raw")
    code, stdout, stderr = _run_hyperx(args, timeout=timeout)
    duration = int((time.time() - t0) * 1000)
    if code != 0:
        return HyperXPage(url=url, title="", text="", status=0,
                          duration_ms=duration, error=stderr[:300])
    # HYPERX outputs banner header + content; parse loosely
    lines = stdout.split("\n")
    title = ""
    text_lines = []
    in_content = False
    for line in lines:
        if "━━━" in line:
            in_content = not in_content
            continue
        if not in_content and " " in line and not title and len(line.strip()) < 200:
            stripped = line.strip()
            if stripped and not stripped.startswith("HTTP") and not stripped.startswith("hyperx"):
                title = stripped
                continue
        if in_content:
            continue  # banner section
        text_lines.append(line)
    text = "\n".join(text_lines).strip()
    return HyperXPage(
        url=url, title=title, text=text[:5000],
        status=200 if code == 0 else 0,
        duration_ms=duration,
    )


def hyperx_search_multi(query: str, timeout: int = 20) -> list[HyperXSearchHit]:
    """
    Multi-source search via HYPERX aggregator (HN + GitHub + Wiby).
    These sources don't IP-block VPS like DDG/Google do.
    """
    args = ["--engine=multi", "--json", query]
    code, stdout, stderr = _run_hyperx(args, timeout=timeout)
    if code != 0:
        log.warning("[hyperx] search failed: %s", stderr[:200])
        return []
    try:
        # HYPERX --json should output JSON array
        # If banner contamination, find the JSON line
        for line in stdout.split("\n"):
            line = line.strip()
            if line.startswith("[") or line.startswith("{"):
                data = json.loads(line)
                if isinstance(data, dict) and "results" in data:
                    data = data["results"]
                hits = []
                for h in (data or [])[:10]:
                    hits.append(HyperXSearchHit(
                        title=h.get("title", "")[:200],
                        url=h.get("url", ""),
                        snippet=h.get("snippet", "")[:300],
                        source=h.get("source", "?"),
                    ))
                return hits
    except Exception as e:
        log.debug("[hyperx] search JSON parse: %s", e)
    return []


def hyperx_links(url: str, timeout: int = _TIMEOUT_DEFAULT) -> list[str]:
    """Extract all outbound links from URL."""
    args = ["--links", url]
    code, stdout, _ = _run_hyperx(args, timeout=timeout)
    if code != 0:
        return []
    return [l.strip() for l in stdout.split("\n") if l.strip().startswith("http")][:50]


def hyperx_available() -> bool:
    """Check if HYPERX is installed and functional."""
    return _HYPERX_CLI.exists()


__all__ = [
    "HyperXPage", "HyperXSearchHit",
    "hyperx_get", "hyperx_search_multi", "hyperx_links",
    "hyperx_available",
]
