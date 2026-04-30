"""
mojeek_search.py — Mojeek Search scraper for SIDIX

Mojeek = independent search engine (UK-based) with permisive scraping.
No rate limits detected from VPS IP. Returns 200 with HTML results.

Why Mojeek:
- No 403/429 from VPS IP (tested 2026-04-30)
- Independent index (not Google/Bing proxy)
- Pure HTML, no JavaScript required
- Free, no API key needed

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

log = logging.getLogger("sidix.mojeek")

_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_TIMEOUT = 10.0
_CACHE_TTL = 300.0
_result_cache: dict = {}


@dataclass
class MojeekHit:
    title: str
    url: str
    snippet: str
    engine: str = "mojeek"


async def mojeek_search_async(query: str, max_results: int = 5) -> list[MojeekHit]:
    """Search Mojeek and return hits."""
    if not query.strip():
        return []

    # Cache check
    import time
    cached = _result_cache.get(query)
    if cached:
        ts, hits = cached
        if time.time() - ts < _CACHE_TTL:
            return hits[:max_results]

    url = f"https://www.mojeek.com/search?q={quote_plus(query)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Accept-Encoding": "gzip, deflate",
            })
            if r.status_code != 200:
                log.warning("[mojeek] status %d for query=%r", r.status_code, query[:60])
                return []

            from selectolax.parser import HTMLParser
            tree = HTMLParser(r.text)
            results = tree.css(".results-standard li")
            hits = []
            for res in results[:max_results]:
                title_a = res.css_first("a")
                title_text = ""
                if title_a:
                    title_text = title_a.text() or ""
                    # If text is just URL, try to get href as fallback
                    if title_text.startswith("http"):
                        title_text = title_a.attributes.get("href", "")[:80]
                
                snippet_p = res.css_first("p")
                snippet_text = snippet_p.text() if snippet_p else ""
                
                # Skip if both title and snippet are empty/URL-only
                if not title_text or title_text.startswith("http"):
                    continue

                hits.append(MojeekHit(
                    title=title_text[:200],
                    url=title_a.attributes.get("href", "") if title_a else "",
                    snippet=snippet_text[:400],
                ))

            log.info("[mojeek] '%s' → %d hits", query[:60], len(hits))
            sliced = hits[:max_results]
            _result_cache[query] = (time.time(), sliced)
            if len(_result_cache) > 100:
                oldest = min(_result_cache.items(), key=lambda kv: kv[1][0])
                _result_cache.pop(oldest[0], None)
            return sliced

    except Exception as e:
        log.warning("[mojeek] error for query='%s': %s", query[:60], e)
        return []


def to_citations(hits: list[MojeekHit]) -> list[dict]:
    return [
        {
            "type": "web_search",
            "url": h.url,
            "title": h.title,
            "engine": h.engine,
            "snippet": h.snippet,
        }
        for h in hits
    ]
