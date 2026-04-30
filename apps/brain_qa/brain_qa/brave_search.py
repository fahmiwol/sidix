"""
brave_search.py — Brave Search HTML scraper (Vol 20-fu6)

Built by SIDIX in sandbox 2026-04-26 night. Production-graded version of
.sandbox/lite_browser/v02_search.py result.

Why: DDG blocked from VPS, Wikipedia article body sometimes stale (pre-2024
election). Brave Search returns FRESH results no API key needed.

Usage:
    from brain_qa.brave_search import brave_search_async
    hits = await brave_search_async("siapa presiden indonesia 2024", max_results=5)

Fallback chain (used by sanad web branch):
    Wikipedia direct  →  Brave search  →  DDG (last resort)

License: this scraper respects robots.txt-style rate limits (max 1 req/sec).
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx
from selectolax.parser import HTMLParser

log = logging.getLogger(__name__)

_BRAVE_URL = "https://search.brave.com/search?q={q}"
_USER_AGENT = "SIDIX-LiteBrowser/0.2 (https://sidixlab.com)"
_TIMEOUT = 8.0
_MIN_INTERVAL = 3.0  # min sec between requests (more polite, less 429)

_last_request_at: float = 0.0
_rate_lock = asyncio.Lock()

# 429 backoff: when rate-limited, skip all brave calls for N seconds
_429_until: float = 0.0
_429_backoff_seconds: float = 300.0
_CACHE_TTL = 300.0  # cache results 5 min to avoid repeat brave calls
_result_cache: dict = {}  # query -> (timestamp, BraveHit list)


@dataclass
class BraveHit:
    title: str
    url: str
    snippet: str


async def brave_search_async(query: str, max_results: int = 5) -> list[BraveHit]:
    """
    Brave Search via HTML scrape. Returns top-N hits.

    Rate-limit aware:
    - Min 3s between requests (asyncio.Lock)
    - 5-min cache per query (avoid repeat 429)
    - 60s global backoff after 429
    """
    global _last_request_at, _429_until

    # 1. Check cache first
    now = time.time()
    cached = _result_cache.get(query)
    if cached:
        ts, hits = cached
        if now - ts < _CACHE_TTL:
            log.debug("[brave_search] cache hit query=%r", query[:60])
            return hits

    # 2. Check 429 backoff
    if now < _429_until:
        log.debug("[brave_search] in 429 backoff for %.1fs more, skip", _429_until - now)
        return []

    async with _rate_lock:
        elapsed = time.time() - _last_request_at
        if elapsed < _MIN_INTERVAL:
            await asyncio.sleep(_MIN_INTERVAL - elapsed)

        url = _BRAVE_URL.format(q=quote_plus(query))
        try:
            async with httpx.AsyncClient(
                http2=True,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept-Encoding": "gzip, deflate",  # FIX: disable brotli (decoder fails)
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                },
                timeout=_TIMEOUT,
            ) as c:
                r = await c.get(url, follow_redirects=True)
            _last_request_at = time.time()

            if r.status_code == 429:
                # Rate-limited: backoff 60s, return empty
                _429_until = time.time() + _429_backoff_seconds
                log.warning("[brave_search] 429 — backing off 60s")
                return []
            if r.status_code != 200:
                log.warning("[brave_search] status %d for query=%r", r.status_code, query[:60])
                return []

            tree = HTMLParser(r.text)
            hits: list[BraveHit] = []

            # Brave puts results in div.snippet[data-type=web]
            for node in tree.css("div.snippet[data-type=web]"):
                # Title: usually in .title or first h-tag
                title_el = node.css_first(".title") or node.css_first("h4") or node.css_first("a")
                title = title_el.text(strip=True)[:200] if title_el else ""

                # URL: first <a href> with http(s)
                link_el = node.css_first("a[href]")
                href = link_el.attributes.get("href", "") if link_el else ""
                if not href.startswith("http"):
                    continue

                # Snippet: .snippet-content or full text minus title
                snip_el = node.css_first(".snippet-content") or node.css_first(".description")
                snippet = snip_el.text(strip=True, separator=" ")[:400] if snip_el else ""
                if not snippet:
                    # Fallback: take node text minus title
                    full_text = node.text(strip=True, separator=" ")
                    snippet = full_text.replace(title, "").strip()[:400]

                if title and href:
                    hits.append(BraveHit(title=title, url=href, snippet=snippet))
                    if len(hits) >= max_results:
                        break

            log.info("[brave_search] '%s' -> %d hits", query[:60], len(hits))
            # Cache result (even empty, to avoid repeat hits)
            _result_cache[query] = (time.time(), hits)
            # Bound cache size (drop oldest if >100 entries)
            if len(_result_cache) > 100:
                oldest = min(_result_cache.items(), key=lambda kv: kv[1][0])
                _result_cache.pop(oldest[0], None)
            return hits

        except Exception as e:
            log.warning("[brave_search] error for query=%r: %s", query[:60], e)
            return []


def brave_search_sync(query: str, max_results: int = 5) -> list[BraveHit]:
    """Sync wrapper untuk legacy callers (run in thread)."""
    return asyncio.run(brave_search_async(query, max_results))


def to_citations(hits: list[BraveHit]) -> list[dict]:
    return [
        {"type": "web_search", "url": h.url, "title": h.title,
         "snippet": h.snippet[:200], "engine": "brave"}
        for h in hits
    ]


def format_for_llm_context(hits: list[BraveHit], max_chars: int = 4000) -> str:
    if not hits:
        return ""
    chunks = []
    used = 0
    for i, h in enumerate(hits, 1):
        block = f"[Sumber {i}: {h.title}]\nURL: {h.url}\n{h.snippet}\n"
        if used + len(block) > max_chars:
            block = block[: max_chars - used]
        chunks.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n".join(chunks)


__all__ = ["BraveHit", "brave_search_async", "brave_search_sync",
           "to_citations", "format_for_llm_context"]
