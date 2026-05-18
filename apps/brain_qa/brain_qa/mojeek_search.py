"""
mojeek_search.py — Web Search with Mojeek + DuckDuckGo fallback

Primary: Mojeek (independent UK search, no API key needed).
Fallback: DuckDuckGo HTML (when Mojeek returns 403 or 0 hits).
Both scrapers share the same MojeekHit dataclass interface.

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from urllib.parse import quote_plus, unquote

import httpx

log = logging.getLogger("sidix.mojeek")

_TIMEOUT = 5.0   # short — VPS IP often blocked by DDG/Mojeek, fail fast to Wikipedia
_CACHE_TTL = 300.0
_result_cache: dict = {}

_UA_CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_UA_FIREFOX = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"


@dataclass
class MojeekHit:
    title: str
    url: str
    snippet: str
    engine: str = "mojeek"


# ── DuckDuckGo HTML fallback ──────────────────────────────────────────────────

async def _ddg_search_async(query: str, max_results: int = 5) -> list[MojeekHit]:
    """DuckDuckGo HTML scraper — used when Mojeek returns 403 or 0 hits."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers={
                "User-Agent": _UA_FIREFOX,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            })
            if r.status_code != 200:
                log.warning("[ddg] status %d", r.status_code)
                return []

            from selectolax.parser import HTMLParser
            tree = HTMLParser(r.text)
            hits: list[MojeekHit] = []

            for item in tree.css(".result"):
                title_el = item.css_first(".result__a")
                if not title_el:
                    continue
                title = title_el.text().strip()
                href = title_el.attributes.get("href", "")

                # DDG wraps URLs: extract real URL from uddg= param
                m = re.search(r"uddg=([^&]+)", href)
                real_url = unquote(m.group(1)) if m else href

                snippet_el = item.css_first(".result__snippet")
                snippet = snippet_el.text().strip() if snippet_el else ""

                if title and real_url:
                    hits.append(MojeekHit(
                        title=title[:200],
                        url=real_url,
                        snippet=snippet[:400],
                        engine="duckduckgo",
                    ))
                if len(hits) >= max_results:
                    break

            log.info("[ddg] '%s' -> %d hits", query[:60], len(hits))
            return hits
    except Exception as e:
        log.warning("[ddg] error for query='%s': %s", query[:60], e)
        return []


# ── Mojeek primary ────────────────────────────────────────────────────────────

async def mojeek_search_async(query: str, max_results: int = 5) -> list[MojeekHit]:
    """Search web. Primary: Mojeek. Fallback: DuckDuckGo HTML."""
    if not query.strip():
        return []

    # Cache check
    cached = _result_cache.get(query)
    if cached:
        ts, hits = cached
        if time.time() - ts < _CACHE_TTL:
            return hits[:max_results]

    url = f"https://www.mojeek.com/search?q={quote_plus(query)}"
    hits: list[MojeekHit] = []
    use_fallback = False

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as c:
            r = await c.get(url, headers={
                "User-Agent": _UA_CHROME,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Accept-Encoding": "gzip, deflate",
            })
            if r.status_code != 200:
                log.warning("[mojeek] status %d — switching to DDG fallback", r.status_code)
                use_fallback = True
            else:
                from selectolax.parser import HTMLParser
                tree = HTMLParser(r.text)

                selectors = [
                    ("li.result", "a.title", "p.s"),
                    (".results-standard li", "a", "p"),
                    ("ul.results li", "a", "p.s"),
                ]

                for container_sel, title_sel, snippet_sel in selectors:
                    results = tree.css(container_sel)
                    if not results:
                        continue
                    for res in results[:max_results]:
                        title_el = res.css_first(title_sel) or res.css_first("a")
                        if not title_el:
                            continue
                        title_text = (title_el.text() or "").strip()
                        href = title_el.attributes.get("href", "")
                        snippet_el = res.css_first(snippet_sel) or res.css_first("p, .desc, .snippet")
                        snippet_text = (snippet_el.text() or "").strip() if snippet_el else ""
                        if not title_text or title_text.startswith(("http", "www.")):
                            continue
                        hits.append(MojeekHit(title=title_text[:200], url=href, snippet=snippet_text[:400]))
                    if hits:
                        break

                if not hits:
                    log.info("[mojeek] 0 hits parsed — switching to DDG fallback")
                    use_fallback = True

    except Exception as e:
        log.warning("[mojeek] error: %s — switching to DDG fallback", e)
        use_fallback = True

    if use_fallback:
        hits = await _ddg_search_async(query, max_results=max_results)

    # Third fallback: Wikipedia (always reachable from VPS — DDG/Mojeek often blocked)
    if not hits:
        hits = await _wikipedia_search_async(query, max_results=max_results)

    log.info("[mojeek/web] '%s' -> %d hits (engine=%s)",
             query[:60], len(hits), hits[0].engine if hits else "none")

    sliced = hits[:max_results]
    _result_cache[query] = (time.time(), sliced)
    if len(_result_cache) > 100:
        oldest = min(_result_cache.items(), key=lambda kv: kv[1][0])
        _result_cache.pop(oldest[0], None)
    return sliced


async def _wikipedia_search_async(query: str, max_results: int = 5) -> list[MojeekHit]:
    """Wikipedia API fallback — used when Mojeek + DDG both fail from VPS IP."""
    import asyncio, json, urllib.parse, urllib.request

    # Wikipedia blocks Python default UA — use RFC bot UA
    _wiki_ua = "SIDIXKnowledgeSearch/1.0 (https://sidixlab.com; contact@sidixlab.com) Python-urllib"

    def _wiki_get(url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": _wiki_ua})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read()

    def _sync_search() -> list[MojeekHit]:
        # Search for article titles
        params = urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max_results,
            "format": "json",
        })
        try:
            data = json.loads(_wiki_get(f"https://id.wikipedia.org/w/api.php?{params}"))
        except Exception as e:
            log.warning("[wikipedia] search error: %s", e)
            return []

        titles = [r["title"] for r in data.get("query", {}).get("search", [])]
        if not titles:
            # Try English Wikipedia
            try:
                data = json.loads(_wiki_get(f"https://en.wikipedia.org/w/api.php?{params}"))
                titles = [r["title"] for r in data.get("query", {}).get("search", [])]
            except Exception:
                return []

        extracts: dict[str, str] = {}
        if titles:
            try:
                extract_params = urllib.parse.urlencode({
                    "action": "query",
                    "prop": "extracts",
                    "exintro": 1,
                    "explaintext": 1,
                    "redirects": 1,
                    "format": "json",
                    "titles": "|".join(titles[:max_results]),
                })
                extract_data = json.loads(
                    _wiki_get(f"https://id.wikipedia.org/w/api.php?{extract_params}")
                )
                for page in extract_data.get("query", {}).get("pages", {}).values():
                    title = page.get("title", "")
                    extract = (page.get("extract") or "").strip()
                    if title and extract:
                        extracts[title] = extract
            except Exception as e:
                log.debug("[wikipedia] extract enrichment skipped: %s", e)

        hits = []
        for title in titles[:max_results]:
            snippet = extracts.get(title) or f"Wikipedia: {title}"
            hits.append(MojeekHit(
                title=title,
                url=f"https://id.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                snippet=snippet[:900],
                engine="wikipedia",
            ))
        return hits

    try:
        hits = await asyncio.to_thread(_sync_search)
        log.info("[wikipedia] '%s' -> %d hits", query[:60], len(hits))
        return hits
    except Exception as e:
        log.warning("[wikipedia] async error: %s", e)
        return []


def to_citations(hits: list[MojeekHit]) -> list[dict]:
    return [{"type": "web_search", "url": h.url, "title": h.title,
             "engine": h.engine, "snippet": h.snippet} for h in hits]


if __name__ == "__main__":
    import asyncio, sys
    logging.basicConfig(level=logging.DEBUG)
    q = " ".join(sys.argv[1:]) or "presiden indonesia 2024"
    hits = asyncio.run(mojeek_search_async(q, max_results=3))
    print(f"Query: {q}\nHits: {len(hits)}")
    for h in hits:
        print(f"  [{h.engine}] {h.title}")
        print(f"  URL: {h.url}")
        print(f"  Snippet: {h.snippet[:100]}...")
        print()
