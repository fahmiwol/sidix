"""
lite_browser.py — SIDIX Lite Browser Service

Headless browser service untuk fetch web pages dengan JavaScript rendering
dan extract clean text menggunakan trafilatura.

Use cases:
1. Fetch pages yang render JS (SPAs, dynamic content)
2. Extract clean article text dari news sites
3. Bypass simple bot detection (real browser fingerprint)
4. Auto-harvest: fetch URLs dari search results → extract text → save to corpus

Architecture:
  - Single shared browser instance (Chromium headless)
  - Reuse context/tab untuk efficiency
  - trafilatura untuk clean text extraction
  - Rate limiting: max 1 req/sec polite

Resource: Chromium headless ~200-300MB RAM

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger("sidix.lite_browser")

# Singleton browser instance
_browser = None
_context = None
_lock = asyncio.Lock()
_last_fetch_at = 0.0
_MIN_INTERVAL = 1.0  # polite 1 sec between requests


@dataclass
class FetchResult:
    url: str
    title: str
    text: str  # clean extracted text
    html: str  # raw HTML
    success: bool
    error: Optional[str] = None
    latency_ms: int = 0


async def _ensure_browser():
    """Lazy-init Playwright browser."""
    global _browser, _context
    if _browser is None:
        from playwright.async_api import async_playwright
        pw = await async_playwright().start()
        _browser = await pw.chromium.launch(headless=True)
        _context = await _browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="id-ID",
        )
        log.info("[lite_browser] Chromium headless launched")
    return _context


async def fetch_url(
    url: str,
    *,
    wait_for: Optional[str] = None,
    timeout: int = 15,
    extract_text: bool = True,
) -> FetchResult:
    """Fetch URL via headless browser and extract clean text.

    Args:
        url: Target URL
        wait_for: CSS selector to wait for before extraction
        timeout: Page load timeout in seconds
        extract_text: Use trafilatura to extract article text

    Returns:
        FetchResult with clean text + metadata
    """
    global _last_fetch_at
    t0 = time.monotonic()

    # Polite rate limiting
    async with _lock:
        elapsed = time.time() - _last_fetch_at
        if elapsed < _MIN_INTERVAL:
            await asyncio.sleep(_MIN_INTERVAL - elapsed)
        _last_fetch_at = time.time()

    try:
        context = await _ensure_browser()
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=5000)
                except Exception:
                    pass  # Continue even if selector not found
            
            # Wait a bit for dynamic content
            await asyncio.sleep(1.0)
            
            title = await page.title()
            html = await page.content()
            
            # Extract clean text with trafilatura
            text = ""
            if extract_text:
                try:
                    from trafilatura import extract
                    text = extract(html, url=url, include_comments=False, include_tables=False) or ""
                except Exception as e:
                    log.debug("[lite_browser] trafilatura failed: %s", e)
                    # Fallback: simple text extraction
                    text = await page.evaluate("() => document.body.innerText")
            
            await page.close()
            
            latency = int((time.monotonic() - t0) * 1000)
            log.info("[lite_browser] fetched %s in %dms", url[:60], latency)
            return FetchResult(
                url=url,
                title=title,
                text=text[:8000],  # cap 8KB
                html=html[:5000],  # cap 5KB for debug
                success=True,
                latency_ms=latency,
            )
        except Exception as e:
            await page.close()
            raise
    except Exception as e:
        latency = int((time.monotonic() - t0) * 1000)
        log.warning("[lite_browser] failed %s: %s", url[:60], e)
        return FetchResult(
            url=url,
            title="",
            text="",
            html="",
            success=False,
            error=f"{type(e).__name__}: {e}",
            latency_ms=latency,
        )


async def fetch_urls(
    urls: list[str],
    *,
    max_concurrent: int = 2,
    timeout: int = 15,
) -> list[FetchResult]:
    """Batch fetch multiple URLs with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _fetch_one(url: str) -> FetchResult:
        async with semaphore:
            return await fetch_url(url, timeout=timeout)
    
    results = await asyncio.gather(*[_fetch_one(u) for u in urls])
    return list(results)


async def search_and_fetch(
    query: str,
    *,
    search_engine: str = "mojeek",
    max_results: int = 3,
) -> list[FetchResult]:
    """Search → get URLs → fetch each page → return clean text.

    This is the "deep fetch" pattern: not just search snippets,
    but actual page content for richer context.
    """
    urls = []
    if search_engine == "mojeek":
        from .mojeek_search import mojeek_search_async
        hits = await mojeek_search_async(query, max_results=max_results)
        urls = [h.url for h in hits if h.url]
    elif search_engine == "wikipedia":
        from .wiki_lookup import wiki_lookup_fast
        results = wiki_lookup_fast(query, max_articles=max_results)
        urls = [r.url for r in results if r.url]
    
    if not urls:
        return []
    
    return await fetch_urls(urls, max_concurrent=2)


async def close_browser():
    """Close browser instance (cleanup)."""
    global _browser, _context
    if _browser:
        await _browser.close()
        _browser = None
        _context = None
        log.info("[lite_browser] browser closed")
