"""
searxng_search.py — Vol 24a-mini: SearxNG meta-search via public instances

DDG blocked from VPS IP. Brave hits 429 burst. Solution:
SearxNG = open-source meta-search aggregating Google/Bing/etc results.
Many public instances exist with no rate limits.

Strategy: try multiple public instances in parallel, return first non-empty.
Instances rotate (avoid hammering single one).

Future Vol 24a-full: self-host SearxNG via docker (no public dependency).
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

log = logging.getLogger(__name__)

# Public SearxNG instances (community-maintained list)
# Rotated randomly to spread load. Add/remove via env SEARXNG_INSTANCES.
_DEFAULT_INSTANCES = [
    "https://searx.be",
    "https://searx.tiekoetter.com",
    "https://search.bus-hit.me",
    "https://baresearch.org",
    "https://search.sapti.me",
    "https://priv.au",
    "https://search.privacyguides.net",
]

_USER_AGENT = "SIDIX-LiteBrowser/0.3 (https://sidixlab.com)"
_TIMEOUT = 8.0
_MAX_INSTANCES_TRY = 3  # parallel race


@dataclass
class SearxHit:
    title: str
    url: str
    snippet: str
    engine: str  # which underlying search engine (google/bing/etc)


# Cache to avoid repeated calls per query (5min TTL)
_cache: dict = {}
_CACHE_TTL = 300.0


async def _try_instance(client: httpx.AsyncClient, instance: str, query: str) -> list[SearxHit]:
    """Try one SearxNG instance. Returns hits or [] on fail."""
    url = f"{instance}/search?q={quote_plus(query)}&format=json"
    try:
        r = await client.get(url, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            log.debug("[searxng] %s status %d", instance, r.status_code)
            return []
        data = r.json()
        results = data.get("results", []) or []
        hits = []
        for x in results[:10]:
            hits.append(SearxHit(
                title=(x.get("title") or "")[:200],
                url=x.get("url", ""),
                snippet=(x.get("content") or "")[:400],
                engine=x.get("engine", "?"),
            ))
        return hits
    except Exception as e:
        log.debug("[searxng] %s error: %s", instance, e)
        return []


async def searxng_search_async(query: str, max_results: int = 5) -> list[SearxHit]:
    """
    Multi-instance race. Returns first non-empty result, sliced to max_results.
    Cached 5min per query (avoid repeat hits).
    """
    if not query.strip():
        return []
    # 1. Cache check
    now = time.time()
    cached = _cache.get(query)
    if cached:
        ts, hits = cached
        if now - ts < _CACHE_TTL:
            return hits[:max_results]

    # 2. Pick random subset of instances
    import os
    instance_list = os.environ.get("SEARXNG_INSTANCES", "").strip()
    if instance_list:
        instances = [i.strip() for i in instance_list.split(",") if i.strip()]
    else:
        instances = _DEFAULT_INSTANCES.copy()
        random.shuffle(instances)

    selected = instances[:_MAX_INSTANCES_TRY]
    log.debug("[searxng] trying %d instances for %r", len(selected), query[:60])

    async with httpx.AsyncClient(
        http2=True, headers={"User-Agent": _USER_AGENT}, timeout=_TIMEOUT,
    ) as c:
        tasks = [_try_instance(c, inst, query) for inst in selected]
        results_lists = await asyncio.gather(*tasks, return_exceptions=False)

    # Pick first non-empty list (race winner)
    for result in results_lists:
        if result:
            log.info("[searxng] '%s' → %d hits", query[:60], len(result))
            sliced = result[:max_results]
            _cache[query] = (time.time(), sliced)
            # Bound cache
            if len(_cache) > 100:
                oldest = min(_cache.items(), key=lambda kv: kv[1][0])
                _cache.pop(oldest[0], None)
            return sliced

    log.warning("[searxng] all %d instances returned empty for '%s'",
                len(selected), query[:60])
    return []


def to_citations(hits: list[SearxHit]) -> list[dict]:
    return [
        {"type": "web_search", "url": h.url, "title": h.title,
         "snippet": h.snippet[:200], "engine": f"searxng_{h.engine}"}
        for h in hits
    ]


def format_for_llm_context(hits: list[SearxHit], max_chars: int = 4000) -> str:
    if not hits:
        return ""
    chunks = []
    used = 0
    for i, h in enumerate(hits, 1):
        block = f"[Sumber {i} ({h.engine}): {h.title}]\nURL: {h.url}\n{h.snippet}\n"
        if used + len(block) > max_chars:
            block = block[: max_chars - used]
        chunks.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n".join(chunks)


__all__ = ["SearxHit", "searxng_search_async", "to_citations", "format_for_llm_context"]
