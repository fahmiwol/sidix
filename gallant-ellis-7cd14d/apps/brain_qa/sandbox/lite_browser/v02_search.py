"""
SIDIX Lite Browser v0.2 — Multi-Search Wrapper

Goal: replace DDG (blocked from VPS IP). Try multiple FREE no-key engines.

Backends to test:
1. searx.be (public SearxNG instance) — meta-search, free
2. searx.tiekoetter.com — alt SearxNG instance
3. brave.com search HTML scrape — fallback
4. wikipedia.org direct — already proven, factual
5. ecosia.org — meta-search, free

Discovery: try each, log latency + success, pick winners.
"""
from __future__ import annotations
import asyncio
import time
from urllib.parse import quote_plus

import httpx
from selectolax.parser import HTMLParser


SEARCH_BACKENDS = [
    {
        "name": "searx.be",
        "url": "https://searx.be/search?q={q}&format=json",
        "type": "json",
        "result_path": "results",  # JSON path
    },
    {
        "name": "searxng.online",
        "url": "https://searxng.online/search?q={q}&format=json",
        "type": "json",
        "result_path": "results",
    },
    {
        "name": "search.brave.com",
        "url": "https://search.brave.com/search?q={q}",
        "type": "html",
        "selector": "div.snippet[data-type=web]",
    },
    {
        "name": "ecosia.org",
        "url": "https://www.ecosia.org/search?q={q}",
        "type": "html",
        "selector": "div.result",
    },
]


async def try_backend(client: httpx.AsyncClient, backend: dict, query: str) -> dict:
    t0 = time.time()
    url = backend["url"].format(q=quote_plus(query))
    try:
        r = await client.get(url, timeout=10.0, follow_redirects=True)
        if r.status_code != 200:
            return {"name": backend["name"], "ok": False,
                    "status": r.status_code, "duration_ms": int((time.time()-t0)*1000)}

        if backend["type"] == "json":
            try:
                data = r.json()
                results = data.get(backend["result_path"], [])
                titles = [it.get("title", "")[:80] for it in results[:5]]
                return {"name": backend["name"], "ok": True, "type": "json",
                        "result_count": len(results), "top_titles": titles,
                        "duration_ms": int((time.time()-t0)*1000)}
            except Exception as e:
                return {"name": backend["name"], "ok": False,
                        "error": f"json parse: {e}",
                        "duration_ms": int((time.time()-t0)*1000)}
        else:  # html
            tree = HTMLParser(r.text)
            nodes = tree.css(backend["selector"])
            titles = []
            for n in nodes[:5]:
                t = n.text(strip=True, separator=" ")[:80]
                if t:
                    titles.append(t)
            return {"name": backend["name"], "ok": True, "type": "html",
                    "result_count": len(nodes), "top_titles": titles,
                    "duration_ms": int((time.time()-t0)*1000)}

    except Exception as e:
        return {"name": backend["name"], "ok": False,
                "error": str(e)[:200],
                "duration_ms": int((time.time()-t0)*1000)}


async def discovery_test(query: str = "presiden indonesia 2024"):
    async with httpx.AsyncClient(http2=True,
                                 headers={"User-Agent": "SIDIX-LiteBrowser/0.2"}) as c:
        return await asyncio.gather(*[try_backend(c, b, query) for b in SEARCH_BACKENDS])


if __name__ == "__main__":
    print("=== SIDIX Search Backend Discovery ===\n")
    print("Query: presiden indonesia 2024\n")
    t0 = time.time()
    results = asyncio.run(discovery_test())
    total_ms = int((time.time()-t0)*1000)
    print(f"All 4 backends tested in {total_ms}ms parallel.\n")

    for r in sorted(results, key=lambda x: (not x["ok"], x.get("duration_ms", 99999))):
        name = r["name"]
        dur = r["duration_ms"]
        marker_str = "OK " if r["ok"] else "FAIL"
        if r["ok"]:
            rcount = r.get("result_count", 0)
            rtype = r.get("type", "?")
            print(f"[{marker_str}] {name:30s} {dur:>5}ms | {rcount} results | type={rtype}")
            for t in r.get("top_titles", [])[:3]:
                print(f"        > {t}")
        else:
            err = r.get("error", "status " + str(r.get("status", "?")))
            print(f"[{marker_str}] {name:30s} {dur:>5}ms | ERROR: {err[:120]}")
        print()
