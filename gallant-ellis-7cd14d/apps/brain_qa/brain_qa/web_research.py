"""
web_research.py — Pencarian Sumber Eksternal untuk SIDIX (Fase 3+)
==================================================================

SIDIX tidak boleh hanya menjawab dari "isi kepala" model. Setiap riset otomatis
juga mencari sumber eksternal — logis, akademis, realistis.

Strategi (tanpa API key berbayar):
  1. DuckDuckGo HTML (html.duckduckgo.com)     — general web search
  2. Wikipedia REST API (id + en)              — akademis ringkas
  3. Filter kualitas: preferensi domain berbobot (.edu, .gov, .ac.id,
     wikipedia, arxiv, github, stackoverflow, dsb.)

Output: list[SearchResult] dengan title + url + snippet, siap diturunkan
ke webfetch untuk diambil konten lengkapnya.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import quote_plus, urlparse, parse_qs, unquote

import httpx
from bs4 import BeautifulSoup


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    title:   str
    url:     str
    snippet: str
    source:  str        # "ddg" / "wikipedia_id" / "wikipedia_en"
    score:   float = 0.5

    def to_dict(self) -> dict:
        return asdict(self)


# ── Domain Quality Scoring ────────────────────────────────────────────────────
# Bobot domain: sumber yang umumnya logis/akademis dapat skor lebih tinggi

_DOMAIN_WEIGHTS: list[tuple[str, float]] = [
    (".edu",            0.95),
    (".gov",            0.95),
    (".ac.id",          0.90),
    (".ac.",            0.88),
    ("wikipedia.org",   0.85),
    ("arxiv.org",       0.90),
    ("nature.com",      0.92),
    ("sciencedirect",   0.88),
    ("ieee.org",        0.88),
    ("springer.com",    0.85),
    ("plos.org",        0.85),
    ("biorxiv.org",     0.82),
    ("medrxiv.org",     0.82),
    ("github.com",      0.72),
    ("stackoverflow",   0.70),
    ("developer.mozilla", 0.75),
    ("docs.python.org", 0.80),
    ("fastapi.tiangolo", 0.75),
    ("pytorch.org",     0.78),
    ("huggingface.co",  0.75),
    ("anthropic.com",   0.78),
    ("openai.com",      0.70),
    ("medium.com",      0.45),
    ("quora.com",       0.35),
    ("reddit.com",      0.40),
    ("pinterest",       0.15),
    ("tiktok",          0.10),
]

_BLOCK_DOMAINS = {
    "facebook.com", "instagram.com", "twitter.com", "x.com",
    "tiktok.com", "pinterest.com",
}


def _score_url(url: str) -> float:
    host = (urlparse(url).netloc or "").lower()
    if any(b in host for b in _BLOCK_DOMAINS):
        return 0.05
    for marker, weight in _DOMAIN_WEIGHTS:
        if marker in host:
            return weight
    # default medium
    return 0.50


# ── DuckDuckGo HTML scraper ───────────────────────────────────────────────────

_DDG_URL = "https://html.duckduckgo.com/html/"
_UA = "Mozilla/5.0 (compatible; SIDIX-ResearchBot/0.1; +https://sidixlab.com)"


def search_duckduckgo(query: str, max_results: int = 8, timeout: float = 12.0) -> list[SearchResult]:
    """Scrape DuckDuckGo HTML (tidak butuh API key)."""
    results: list[SearchResult] = []
    try:
        with httpx.Client(timeout=timeout, headers={"User-Agent": _UA}, follow_redirects=True) as client:
            resp = client.post(_DDG_URL, data={"q": query, "kl": "id-id"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[web_research] DDG failed: {e}")
        return results

    for res in soup.select(".result"):
        title_tag = res.select_one(".result__title a")
        snip_tag  = res.select_one(".result__snippet")
        if not title_tag:
            continue
        raw_url = title_tag.get("href", "")
        # DDG sering membungkus URL di /l/?uddg=...
        url = _unwrap_ddg_url(raw_url)
        if not url:
            continue
        title   = title_tag.get_text(" ", strip=True)
        snippet = snip_tag.get_text(" ", strip=True) if snip_tag else ""
        score   = _score_url(url)
        if score < 0.15:
            continue  # drop domain yang masuk blocklist/sosmed
        results.append(SearchResult(
            title=title, url=url, snippet=snippet[:300],
            source="ddg", score=score,
        ))
        if len(results) >= max_results:
            break

    # Sort by score DESC (sumber kredibel duluan)
    results.sort(key=lambda r: -r.score)
    return results


def _unwrap_ddg_url(raw: str) -> str:
    if not raw:
        return ""
    # DDG redirect: //duckduckgo.com/l/?uddg=<encoded_url>
    if raw.startswith("//"):
        raw = "https:" + raw
    try:
        parsed = urlparse(raw)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            qs = parse_qs(parsed.query)
            uddg = qs.get("uddg", [""])[0]
            if uddg:
                return unquote(uddg)
    except Exception:
        pass
    return raw


# ── Wikipedia (REST API, no key) ──────────────────────────────────────────────

_WIKI_SEARCH = "https://{lang}.wikipedia.org/w/api.php"
_WIKI_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"


def search_wikipedia(query: str, lang: str = "id", max_results: int = 3, timeout: float = 10.0) -> list[SearchResult]:
    """Cari artikel Wikipedia + ambil summary (ringkas, akademis)."""
    results: list[SearchResult] = []
    try:
        with httpx.Client(timeout=timeout, headers={"User-Agent": _UA}) as client:
            r = client.get(_WIKI_SEARCH.format(lang=lang), params={
                "action": "query", "list": "search", "srsearch": query,
                "format": "json", "srlimit": max_results,
            })
            r.raise_for_status()
            hits = r.json().get("query", {}).get("search", []) or []

            for h in hits[:max_results]:
                title = h.get("title", "")
                if not title:
                    continue
                # Ambil summary singkat
                try:
                    sum_r = client.get(_WIKI_SUMMARY.format(
                        lang=lang, title=quote_plus(title.replace(" ", "_"))
                    ))
                    if sum_r.status_code == 200:
                        sj = sum_r.json()
                        extract = sj.get("extract", "")
                        page_url = sj.get("content_urls", {}).get("desktop", {}).get("page", "")
                    else:
                        extract, page_url = "", ""
                except Exception:
                    extract, page_url = "", ""

                url = page_url or f"https://{lang}.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                snippet = extract or re.sub("<.*?>", "", h.get("snippet", ""))
                # Filter relevansi minimal: judul harus punya overlap dengan query
                query_words = set(query.lower().split())
                title_words = set(title.lower().split())
                overlap = query_words & title_words
                # Minimal 1 kata non-stopword overlap, atau judul cukup panjang dan spesifik
                stopwords = {"dan", "yang", "di", "ke", "dari", "dalam", "untuk", "itu",
                             "ini", "atau", "the", "a", "an", "of", "in", "to", "for"}
                meaningful_overlap = overlap - stopwords
                if len(title) < 5:
                    continue
                # Kalau tidak ada overlap tapi snippet ada query — tetap masuk
                snippet_has_query = any(w in snippet.lower() for w in query_words - stopwords if len(w) > 3)
                if not meaningful_overlap and not snippet_has_query:
                    print(f"[web_research] wiki {lang} skip low-relevance: '{title}' for '{query}'")
                    continue

                results.append(SearchResult(
                    title=title, url=url, snippet=snippet[:400],
                    source=f"wikipedia_{lang}", score=0.85,
                ))
    except Exception as e:
        print(f"[web_research] wikipedia {lang} failed: {e}")

    return results


# ── Unified Search ────────────────────────────────────────────────────────────

def search_multi(query: str, max_total: int = 10) -> list[SearchResult]:
    """
    Unified search: Wikipedia (id+en) + DuckDuckGo, dedupe by host+title,
    sorted by score.
    """
    combined: list[SearchResult] = []

    # Wikipedia dulu (lebih terpercaya untuk definisi)
    combined += search_wikipedia(query, lang="id", max_results=2)
    combined += search_wikipedia(query, lang="en", max_results=2)

    # DDG untuk breadth
    combined += search_duckduckgo(query, max_results=6)

    # Dedupe berdasarkan URL
    seen: set[str] = set()
    unique: list[SearchResult] = []
    for r in combined:
        key = r.url.split("#")[0]
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    unique.sort(key=lambda r: -r.score)
    return unique[:max_total]


def top_urls_for_query(query: str, n: int = 4) -> list[str]:
    """Shortcut: ambil top-N URL untuk diturunkan ke webfetch."""
    return [r.url for r in search_multi(query, max_total=n * 2)[:n]]
