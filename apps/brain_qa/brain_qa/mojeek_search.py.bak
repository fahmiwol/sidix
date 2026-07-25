"""
mojeek_search.py — Mojeek Search scraper for SIDIX

Mojeek = independent search engine (UK-based) with permissive scraping.
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

import logging
import time
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

            # ── Try multiple selectors (Mojeek changes layout occasionally) ──
            selectors = [
                ("li.result", "a.title", "p.s"),           # newer layout
                (".results-standard li", "a", "p"),        # original layout
                ("[data-result]", "a[data-url]", ".snippet"), # possible future
            ]

            hits = []
            for container_sel, title_sel, snippet_sel in selectors:
                results = tree.css(container_sel)
                log.debug("[mojeek] selector %s → %d results", container_sel, len(results))
                if not results:
                    continue
                for res in results[:max_results]:
                    title_el = res.css_first(title_sel)
                    if not title_el:
                        # fallback: any <a> inside result
                        title_el = res.css_first("a")
                    title_text = (title_el.text() or "").strip()
                    href = title_el.attributes.get("href", "") if title_el else ""

                    snippet_el = res.css_first(snippet_sel)
                    if not snippet_el:
                        # fallback: any <p> or .desc
                        snippet_el = res.css_first("p, .desc, .snippet")
                    snippet_text = (snippet_el.text() or "").strip() if snippet_el else ""

                    # Skip empty or URL-only titles
                    if not title_text or title_text.startswith(("http", "www.")):
                        continue

                    hits.append(MojeekHit(
                        title=title_text[:200],
                        url=href,
                        snippet=snippet_text[:400],
                    ))
                if hits:
                    break  # found working selector

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


# Debug helper — can be called from CLI
if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    q = " ".join(__import__("sys").argv[1:]) or "presiden indonesia 2024"
    hits = asyncio.run(mojeek_search_async(q, max_results=3))
    print(f"Query: {q}")
    print(f"Hits: {len(hits)}")
    for h in hits:
        print(f"  Title: {h.title}")
        print(f"  URL: {h.url}")
        print(f"  Snippet: {h.snippet[:100]}...")
        print()
