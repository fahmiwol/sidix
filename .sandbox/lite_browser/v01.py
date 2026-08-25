"""
SIDIX Lite Browser v0.1 — first self-built tool
Built in sandbox by SIDIX agent (with Claude as teacher), 2026-04-26 night.

Goal: Replace heavy headless Chromium for 90% of scrape needs.
Stack: httpx (HTTP/2 async) + selectolax (10x faster parser) + trafilatura (text extract)

Test target: kompas.com, tempo.co, github.com, wikipedia, arxiv abstract.
Success metric: 5 URLs fetched + extracted in <5s wall-clock total.
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass

import httpx
import trafilatura
from selectolax.parser import HTMLParser


@dataclass
class ScrapeResult:
    url: str
    status: int
    title: str
    text: str             # cleaned main content (trafilatura)
    headings: list[str]   # h1+h2 (selectolax — for outline)
    links: list[str]      # outbound links (first 20)
    duration_ms: int
    error: str = ""


async def fetch_one(client: httpx.AsyncClient, url: str) -> ScrapeResult:
    t0 = time.time()
    try:
        r = await client.get(url, follow_redirects=True, timeout=12.0)
        html = r.text

        # Tier 1a: trafilatura main-content extract
        text = trafilatura.extract(html) or ""

        # Tier 1b: selectolax for structured peek (title, h1, h2, links)
        tree = HTMLParser(html)
        title = (tree.css_first("title").text() if tree.css_first("title") else "").strip()
        headings = []
        for tag in ("h1", "h2"):
            for n in tree.css(tag)[:5]:
                t = n.text().strip()
                if t and len(t) < 200:
                    headings.append(f"{tag}: {t}")
        links = []
        for a in tree.css("a[href]")[:50]:
            href = a.attributes.get("href", "")
            if href.startswith("http") and "sidixlab" not in href:
                links.append(href)
                if len(links) >= 20:
                    break

        return ScrapeResult(
            url=url, status=r.status_code, title=title[:200],
            text=text[:3000], headings=headings, links=links,
            duration_ms=int((time.time() - t0) * 1000),
        )
    except Exception as e:
        return ScrapeResult(
            url=url, status=0, title="", text="",
            headings=[], links=[],
            duration_ms=int((time.time() - t0) * 1000),
            error=str(e)[:200],
        )


async def fetch_multi(urls: list[str]) -> list[ScrapeResult]:
    """Multi-tab parallel fetch via asyncio.gather."""
    async with httpx.AsyncClient(http2=True,
                                 headers={"User-Agent": "SIDIX-LiteBrowser/0.1"}) as c:
        return await asyncio.gather(*[fetch_one(c, u) for u in urls])


# Smoke test: 5 diverse sources
TEST_URLS = [
    "https://en.wikipedia.org/wiki/Indonesia",
    "https://github.com/fahmiwol/sidix",
    "https://arxiv.org/abs/2210.03629",   # ReAct paper
    "https://www.kompas.com/",
    "https://news.ycombinator.com/",
]


if __name__ == "__main__":
    t_start = time.time()
    results = asyncio.run(fetch_multi(TEST_URLS))
    total_ms = int((time.time() - t_start) * 1000)
    print(f"\n=== 5-URL parallel fetch: {total_ms}ms wall-clock ===\n")
    for r in results:
        marker = "OK" if not r.error else "ERR"
        print(f"[{marker}] {r.status} {r.duration_ms}ms | {r.url}")
        if r.error:
            print(f"      err: {r.error}")
        else:
            print(f"      title: {r.title[:80]}")
            print(f"      text len: {len(r.text)} | headings: {len(r.headings)} | links: {len(r.links)}")
        print()
