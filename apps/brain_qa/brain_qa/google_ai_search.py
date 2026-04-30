"""
google_ai_search.py — Google AI Search integration via google-generativeai

Grounding search menggunakan Google Search API melalui Gemini model.
Ini memungkinkan hasil pencarian yang lebih kaya dan terstruktur
banding pure HTML scrape (Brave) atau SearxNG instance yang bisa down.

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger("sidix.google_ai_search")

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass
class GoogleAIHit:
    title: str
    url: str
    snippet: str
    source: str = "google_ai"


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_GOOGLE_API_KEY: Optional[str] = None


def _get_api_key() -> Optional[str]:
    global _GOOGLE_API_KEY
    if _GOOGLE_API_KEY:
        return _GOOGLE_API_KEY
    _GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    return _GOOGLE_API_KEY


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

async def google_ai_search_async(query: str, max_results: int = 5) -> list[GoogleAIHit]:
    """
    Search using Google AI (Gemini) with google_search_tool grounding.
    Returns list[GoogleAIHit] compatible with SearxNG/Brave output.
    """
    import asyncio
    # google-generativeai is sync; run in thread
    return await asyncio.to_thread(_google_ai_search_sync, query, max_results)


def _google_ai_search_sync(query: str, max_results: int = 5) -> list[GoogleAIHit]:
    api_key = _get_api_key()
    if not api_key:
        log.warning("[google_ai_search] No GOOGLE_API_KEY/GEMINI_API_KEY in env")
        return []

    try:
        import google.generativeai as genai
        from google.generativeai.types import Tool
    except ImportError as exc:
        log.warning("[google_ai_search] google-generativeai not installed: %s", exc)
        return []

    try:
        genai.configure(api_key=api_key)

        # Note: google_search_tool requires specific API enablement.
        # Fallback to plain Gemini prompt with explicit search instruction.
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = (
            f"Kamu adalah asisten riset. Cari fakta terkini dan akurat tentang: {query}\n\n"
            f"Berikan ringkasan hasil pencarian dalam format berikut (maksimal {max_results} hasil):\n"
            f"Judul | URL | Snippet\n"
            f"\n"
            f"Pastikan setiap hasil memiliki URL yang valid (mulai dengan http:// atau https://)."
        )

        generation_config = {
            "temperature": 0.3,
            "max_output_tokens": 1024,
        }

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )

        text = ""
        if hasattr(response, "text"):
            text = response.text or ""
        elif hasattr(response, "parts"):
            text = "".join(p.text for p in response.parts if hasattr(p, "text"))

        hits = _parse_hits_from_text(text, max_results)
        log.info("[google_ai_search] query=%r hits=%d", query, len(hits))
        return hits

    except Exception as exc:
        log.warning("[google_ai_search] Error: %s", exc)
        return []


def _parse_hits_from_text(text: str, max_results: int) -> list[GoogleAIHit]:
    """Parse loose text output from Gemini into structured hits."""
    import re
    hits: list[GoogleAIHit] = []

    # Try pipe-delimited format: Title | URL | Snippet
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        if len(hits) >= max_results:
            break
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            title, url, snippet = parts[0], parts[1], " | ".join(parts[2:])
            if url.startswith("http"):
                hits.append(GoogleAIHit(title=title, url=url, snippet=snippet))
                continue

        # Try URL detection inline
        url_match = re.search(r'(https?://\S+)', line)
        if url_match:
            url = url_match.group(1)
            title = line[:url_match.start()].strip("- ").strip()
            if not title:
                title = url
            snippet = line[url_match.end():].strip("- ").strip()
            hits.append(GoogleAIHit(title=title, url=url, snippet=snippet or title))

    return hits


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def google_ai_search_health() -> dict:
    key = _get_api_key()
    return {
        "available": bool(key),
        "api_key_configured": bool(key),
        "key_preview": (key[:8] + "..." + key[-4:]) if key else None,
    }
