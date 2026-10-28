"""
public_hygiene.py - final user-facing answer sanitizer.

This is the last defensive layer before text is shown to users or reused as
conversation memory. It must stay deterministic and dependency-light.
"""

from __future__ import annotations

import re


_CUT_MARKERS = (
    "\n---",
    "**ATRIBUSI**",
    "**RESPONS NATURAL**",
    "[AKHIR KONTEKS]",
    "[PERTANYAAN SAAT INI]",
    "[KONTEKS PERCAKAPAN SEBELUMNYA]",
    "Konteks Memori",
    "KONTEKS DARI SUMBER PARALEL",
    "=== KONTEKS DARI SUMBER PARALEL ===",
    "[CORPUS SEARCH]",
    "[WEB SEARCH]",
    "[DENSE SEARCH]",
)


def _strip_autotune_review(text: str) -> str:
    if "Auto-Tune Review" not in text:
        return text
    match = re.search(r"(?m)^\s*-{3,}\s*$", text)
    if not match:
        return text
    return text[match.end():].lstrip(" \t\r\n-")


def sanitize_public_answer(text: str) -> str:
    """Remove internal prompt/debug/source sections from public chat answers."""
    if not text:
        return text

    cleaned = _strip_autotune_review(str(text))

    cut_positions = [
        cleaned.find(marker)
        for marker in _CUT_MARKERS
        if cleaned.find(marker) > 0
    ]
    if cut_positions:
        candidate = cleaned[:min(cut_positions)].strip()
        if len(candidate) >= 12:
            cleaned = candidate

    cleaned = re.sub(r"(?im)^\s*\*\*(ATRIBUSI|RESPONS NATURAL)\*\*\s*$", "", cleaned)
    cleaned = re.sub(
        r"(?im)^\s*-\s*(Web Search|Corpus|Semantic Index|Persona)\s*:.*$",
        "",
        cleaned,
    )
    cleaned = re.sub(r"(?im)^\s*\[(CORPUS|WEB|DENSE)\s+SEARCH\]\s*$", "", cleaned)
    cleaned = re.sub(r"(?im)^\s*={3,}\s*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
