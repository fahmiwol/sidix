"""
wiki_lookup.py — Fast Wikipedia lookup untuk current_events fastpath (Vol 20-fu5)
================================================================================

Bypass DDG (yang block dari VPS IP). Direct ke Wikipedia API:
- opensearch → top matching article titles
- extracts → intro paragraph (TextExtracts API, plain text)
- Multi-language: ID priority, EN fallback

Anti-pattern dihindari:
- ❌ Pakai BeautifulSoup parse HTML (heavy + slow) → opensearch+extracts return JSON
- ❌ Sync block lama → semua HTTP timeout 5-8s, fail fast
- ❌ Cache semua hit → user harus dapet info terkini, no stale cache di sini
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)

# Wikipedia public API: no auth, no rate limit (kecuali abuse), very stable
_WIKI_API_TEMPLATE = "https://{lang}.wikipedia.org/w/api.php"
_USER_AGENT = "SIDIX-Agent/2.0 (https://sidixlab.com)"
_TIMEOUT_OPENSEARCH = 5.0
_TIMEOUT_EXTRACTS = 6.0


@dataclass
class WikiResult:
    """Hasil lookup Wikipedia: title + URL + intro paragraph."""
    title: str
    url: str
    extract: str  # Intro paragraph (plain text, max ~2KB)
    lang: str
    page_id: Optional[int] = None


def _opensearch(query: str, lang: str, max_results: int = 5) -> list[tuple[str, str]]:
    """
    Wikipedia opensearch → list[(title, url)].
    Returns empty list on failure.
    """
    import httpx
    try:
        with httpx.Client(timeout=_TIMEOUT_OPENSEARCH) as client:
            r = client.get(
                _WIKI_API_TEMPLATE.format(lang=lang),
                params={
                    "action": "opensearch",
                    "search": query,
                    "limit": max_results,
                    "namespace": 0,
                    "format": "json",
                },
                headers={"User-Agent": _USER_AGENT},
            )
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and len(data) >= 4:
                titles = data[1] or []
                urls = data[3] or []
                return [(t, urls[i] if i < len(urls) else "") for i, t in enumerate(titles)]
    except Exception as e:
        log.debug("[wiki_lookup] opensearch %s/%s failed: %s", lang, query[:40], e)
    return []


def _extracts(titles: list[str], lang: str) -> dict[str, str]:
    """
    Wikipedia extracts (intro paragraph) untuk batch titles.
    Returns dict[title -> extract_text].
    """
    import httpx
    if not titles:
        return {}
    try:
        with httpx.Client(timeout=_TIMEOUT_EXTRACTS) as client:
            r = client.get(
                _WIKI_API_TEMPLATE.format(lang=lang),
                params={
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "exintro": "1",          # only intro section
                    "explaintext": "1",      # plain text, no HTML
                    "exsectionformat": "plain",
                    "titles": "|".join(titles[:5]),  # max 5 to keep response small
                    "redirects": "1",
                },
                headers={"User-Agent": _USER_AGENT},
            )
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            out = {}
            for pid, page in pages.items():
                title = page.get("title", "")
                extract = page.get("extract", "")
                if extract:
                    out[title] = extract[:2000]  # cap 2KB per article
            return out
    except Exception as e:
        log.debug("[wiki_lookup] extracts %s failed: %s", lang, e)
    return {}


_STOPWORDS_ID = {
    "siapa", "apa", "kapan", "dimana", "di mana", "bagaimana", "kenapa", "mengapa",
    "yang", "ini", "itu", "saja", "juga", "kah", "lah",
    "sekarang", "saat ini", "hari ini",
    "saya", "kamu", "dia", "mereka",
    "tolong", "mohon", "ya", "dong",
    "berapa", "manakah", "adakah",
}
_STOPWORDS_EN = {
    "who", "what", "when", "where", "why", "how", "which",
    "is", "are", "was", "were", "the", "a", "an",
    "now", "today", "currently", "current",
    "please", "tell", "me", "us",
}


def _simplify_query(query: str) -> str:
    """Strip stopwords + punctuation untuk Wikipedia opensearch.

    Wikipedia opensearch optimal dengan keyword phrase, BUKAN full sentence.
    "siapa presiden indonesia sekarang?" → "presiden indonesia"
    """
    import re
    q = query.lower().strip().rstrip("?!.,;:")
    tokens = re.findall(r"\w+", q)
    keep = [t for t in tokens if t not in _STOPWORDS_ID and t not in _STOPWORDS_EN]
    simplified = " ".join(keep) if keep else q
    return simplified


def wiki_lookup_fast(query: str, max_articles: int = 3) -> list[WikiResult]:
    """
    Fast Wikipedia lookup untuk current_events / factual queries.

    Strategy:
    1. Simplify query (strip stopwords) — Wikipedia opensearch needs keywords, not full sentence
    2. opensearch ID → top titles + URLs
    3. Kalau ID kosong, fallback opensearch EN
    4. Kalau masih kosong, retry dengan query asli (jaga-jaga simplifier terlalu agresif)
    5. Fetch extracts batch untuk top titles
    6. Return WikiResult list (ranked by opensearch order)

    Total latency: ~500ms-2s warm (2 HTTP calls dengan 5-6s timeout each).
    """
    simplified = _simplify_query(query)
    # 1. opensearch dengan simplified query, ID → fallback EN
    pairs: list[tuple[str, str]] = []
    used_lang = "id"
    queries_to_try = [simplified] if simplified != query.lower() else []
    queries_to_try.append(query)  # fallback ke original
    for q in queries_to_try:
        for lang in ("id", "en"):
            pairs = _opensearch(q, lang, max_results=max_articles)
            if pairs:
                used_lang = lang
                log.debug("[wiki_lookup] hit lang=%s query='%s'", lang, q[:50])
                break
        if pairs:
            break
    if not pairs:
        log.info("[wiki_lookup] no results for '%s' (simplified='%s') in id/en", query[:60], simplified[:40])
        return []

    # 2. Fetch extracts untuk titles
    titles = [t for t, _ in pairs]
    extracts_map = _extracts(titles, used_lang)

    # 3. Build results (preserve opensearch ranking)
    results: list[WikiResult] = []
    for title, url in pairs:
        extract = extracts_map.get(title, "")
        if not extract:
            # Some titles ambiguous; skip if no extract
            continue
        results.append(WikiResult(
            title=title,
            url=url,
            extract=extract,
            lang=used_lang,
        ))
    log.info(
        "[wiki_lookup] '%s' → %d articles (lang=%s, total %dB)",
        query[:60], len(results), used_lang,
        sum(len(r.extract) for r in results),
    )
    return results


def format_for_llm_context(results: list[WikiResult], max_chars: int = 4000) -> str:
    """Format hasil Wikipedia jadi context block untuk LLM."""
    if not results:
        return ""
    chunks = []
    used = 0
    for i, r in enumerate(results, 1):
        block = f"[Sumber {i}: {r.title} ({r.url})]\n{r.extract}\n"
        if used + len(block) > max_chars:
            block = block[:max_chars - used]
        chunks.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n".join(chunks)


def to_citations(results: list[WikiResult]) -> list[dict]:
    """Convert ke citation format SIDIX."""
    return [
        {
            "type": "web_search",
            "url": r.url,
            "title": r.title,
            "engine": f"wiki_{r.lang}",
            "snippet": r.extract[:200],
        }
        for r in results
    ]


# Alias untuk backward compatibility dengan multi_source_orchestrator
def search_wikipedia(query: str, max_results: int = 3):
    """Alias untuk wiki_lookup_fast dengan return format list[dict]."""
    results = wiki_lookup_fast(query, max_articles=max_results)
    return [
        {
            "title": r.title,
            "url": r.url,
            "snippet": r.extract[:500],
        }
        for r in results
    ]


__all__ = [
    "WikiResult",
    "wiki_lookup_fast",
    "format_for_llm_context",
    "to_citations",
    "search_wikipedia",
]
