from __future__ import annotations

import re
from dataclasses import dataclass


_WS_RE = re.compile(r"\s+")
_MD_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_MD_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def normalize_text_for_search(s: str) -> str:
    # Remove code blocks to reduce false positives for retrieval.
    s = _MD_CODE_FENCE_RE.sub(" ", s)
    s = _MD_INLINE_CODE_RE.sub(" ", s)
    s = _MD_LINK_RE.sub(r"\1", s)
    s = s.replace("\u00a0", " ")
    s = _WS_RE.sub(" ", s).strip()
    return s


def tokenize(s: str) -> list[str]:
    s = normalize_text_for_search(s).lower()
    # Keep basic latin + digits; split everything else.
    tokens = re.findall(r"[a-z0-9_]+", s)
    return tokens


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_path: str
    source_title: str
    start_char: int
    end_char: int
    text: str
    sanad_tier: str = "unknown"


def chunk_text(text: str, *, chunk_chars: int, chunk_overlap: int) -> list[tuple[int, int, str]]:
    if chunk_chars <= 200:
        raise ValueError("chunk_chars too small; use >= 200")
    if chunk_overlap < 0 or chunk_overlap >= chunk_chars:
        raise ValueError("chunk_overlap must be >=0 and < chunk_chars")

    n = len(text)
    out: list[tuple[int, int, str]] = []
    i = 0
    while i < n:
        j = min(n, i + chunk_chars)
        chunk = text[i:j]
        out.append((i, j, chunk))
        if j >= n:
            break
        i = max(0, j - chunk_overlap)
    return out

