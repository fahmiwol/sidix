from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from .paths import workspace_root


_WS_RE = re.compile(r"\s+")
_BAD_CHARS_RE = re.compile(r"[^a-zA-Z0-9\-_.]+")


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slugify(s: str, max_len: int = 80) -> str:
    s = s.strip().lower()
    s = s.replace(" ", "-")
    s = _BAD_CHARS_RE.sub("-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    if not s:
        s = "clip"
    return s[:max_len].rstrip("-")


def _extract_text_and_title(html: str) -> tuple[str, str]:
    # Use stdlib parser to avoid native deps on Windows (no lxml build needed).
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = _WS_RE.sub(" ", text).strip()
    return text, title


def _default_out_dir() -> Path:
    return workspace_root() / "brain" / "private" / "web_clips"


def fetch_urls_to_private_clips(urls: list[str], *, out_dir_override: str | None) -> list[Path]:
    out_dir = Path(out_dir_override) if out_dir_override else _default_out_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    with httpx.Client(follow_redirects=True, timeout=30.0, headers={"User-Agent": "mighan-brain-qa/0.1"}) as client:
        for url in urls:
            r = client.get(url)
            r.raise_for_status()
            text, title = _extract_text_and_title(r.text)
            host = urlparse(url).netloc.replace(":", "_") or "site"
            slug = _slugify(title)
            filename = f"{host}__{slug}.md"
            path = out_dir / filename
            safe_title = title.replace('"', "'")
            md = "\n".join(
                [
                    "---",
                    f'title: "{safe_title}"',
                    f'url: "{url}"',
                    f'fetched_at: "{_now_utc()}"',
                    "visibility: private",
                    "---",
                    "",
                    "# Source",
                    "",
                    f"- Title: {title}",
                    f"- URL: {url}",
                    f"- Fetched at (UTC): {_now_utc()}",
                    "",
                    "# Extracted text (clean)",
                    "",
                    text,
                    "",
                ]
            )
            path.write_text(md, encoding="utf-8")
            written.append(path)

    return written

