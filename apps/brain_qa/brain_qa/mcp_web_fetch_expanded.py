"""
mcp_web_fetch_expanded.py — SIDIX Web Fetch Expansion
=====================================================
Expand web fetch capabilities: Reddit, YouTube (transcript), GitHub, arXiv,
HackerNews, ProductHunt. All standing-alone, no API keys required for basic use.

Research notes:
  - 318 cognitive expansion (MCP web fetch)
"""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Optional


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0"
TIMEOUT = 15


def _http_get(url: str, headers: Optional[dict] = None) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="ignore")


# ── Reddit ───────────────────────────────────────────────────────────────────

def fetch_reddit(query: str, subreddit: str = "", max_results: int = 5) -> dict:
    """Cari Reddit via JSON API (no auth)."""
    try:
        if subreddit:
            url = f"https://www.reddit.com/r/{subreddit}/search.json?q={urllib.parse.quote(query)}&limit={max_results}&sort=relevance"
        else:
            url = f"https://www.reddit.com/search.json?q={urllib.parse.quote(query)}&limit={max_results}&sort=relevance"

        data = json.loads(_http_get(url, headers={"Accept": "application/json"}))
        posts = data.get("data", {}).get("children", [])
        results = []
        for p in posts[:max_results]:
            d = p.get("data", {})
            results.append({
                "title": d.get("title", ""),
                "subreddit": d.get("subreddit", ""),
                "author": d.get("author", ""),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "selftext": d.get("selftext", "")[:500],
            })
        return _ok({
            "platform": "reddit",
            "query": query,
            "results": results,
            "count": len(results),
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"Reddit fetch gagal: {exc}")


# ── YouTube (transcript + metadata) ──────────────────────────────────────────

def fetch_youtube_transcript(video_id: str) -> dict:
    """Ambil transcript YouTube via timedtext (no API key)."""
    try:
        # Try multiple caption sources
        urls = [
            f"https://www.youtube.com/api/timedtext?v={video_id}&lang=id",
            f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en",
            f"https://video.google.com/timedtext?v={video_id}&lang=id",
        ]
        for url in urls:
            try:
                text = _http_get(url)
                if text and len(text) > 100:
                    # Simple XML strip
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(text)
                    lines = [elem.text or "" for elem in root.iter() if elem.text]
                    transcript = " ".join(lines)
                    return _ok({
                        "platform": "youtube",
                        "video_id": video_id,
                        "transcript": transcript[:3000],
                        "char_count": len(transcript),
                        "source_url": url,
                    })
            except Exception:  # noqa: BLE001
                continue
        return _fallback(
            "Transcript tidak tersedia (private video atau tidak ada caption). "
            "Coba: pip install youtube-transcript-api untuk fallback.",
            data={"video_id": video_id},
        )
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"YouTube fetch gagal: {exc}")


def fetch_youtube_search(query: str, max_results: int = 5) -> dict:
    """Cari YouTube via scrape (no API)."""
    try:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = _http_get(url)
        # Extract video IDs from initial data
        matches = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        ids = list(dict.fromkeys(matches))[:max_results]
        results = []
        for vid in ids:
            # Extract title from ytInitialData
            title_match = re.search(rf'"videoId":"{vid}".*?"title":\{{"runs":\[\{{"text":"([^"]+)"', html)
            title = title_match.group(1) if title_match else "Unknown"
            results.append({
                "video_id": vid,
                "title": title,
                "url": f"https://youtube.com/watch?v={vid}",
            })
        return _ok({
            "platform": "youtube",
            "query": query,
            "results": results,
            "count": len(results),
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"YouTube search gagal: {exc}")


# ── GitHub ───────────────────────────────────────────────────────────────────

def fetch_github_repo(owner: str, repo: str) -> dict:
    """Ambil metadata repo GitHub via API (no auth untuk public repos)."""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        data = json.loads(_http_get(url, headers={"Accept": "application/vnd.github.v3+json"}))
        return _ok({
            "platform": "github",
            "owner": owner,
            "repo": repo,
            "description": data.get("description", ""),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "language": data.get("language", ""),
            "topics": data.get("topics", []),
            "license": data.get("license", {}).get("name", ""),
            "updated_at": data.get("updated_at", ""),
            "url": data.get("html_url", ""),
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"GitHub fetch gagal: {exc}")


def fetch_github_search(query: str, language: str = "", max_results: int = 5) -> dict:
    """Cari repo GitHub via API."""
    try:
        q = urllib.parse.quote(query)
        if language:
            q += f"+language:{language}"
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={max_results}"
        data = json.loads(_http_get(url, headers={"Accept": "application/vnd.github.v3+json"}))
        items = data.get("items", [])
        results = []
        for item in items[:max_results]:
            results.append({
                "name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "url": item.get("html_url", ""),
            })
        return _ok({
            "platform": "github",
            "query": query,
            "total_count": data.get("total_count", 0),
            "results": results,
            "count": len(results),
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"GitHub search gagal: {exc}")


# ── arXiv ────────────────────────────────────────────────────────────────────

def fetch_arxiv(query: str, max_results: int = 5) -> dict:
    """Cari arXiv via API."""
    try:
        import xml.etree.ElementTree as ET
        url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        xml_text = _http_get(url)
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        entries = root.findall("atom:entry", ns)
        results = []
        for entry in entries:
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
            link = entry.find("atom:link[@rel='alternate']", ns)
            pdf_link = entry.find("atom:link[@title='pdf']", ns)
            published = entry.find("atom:published", ns)
            results.append({
                "title": (title.text or "").replace("\n", " ").strip() if title is not None else "",
                "summary": (summary.text or "").strip()[:500] if summary is not None else "",
                "authors": authors,
                "url": link.get("href") if link is not None else "",
                "pdf_url": pdf_link.get("href") if pdf_link is not None else "",
                "published": published.text if published is not None else "",
            })
        return _ok({
            "platform": "arxiv",
            "query": query,
            "results": results,
            "count": len(results),
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"arXiv fetch gagal: {exc}")


# ── HackerNews ───────────────────────────────────────────────────────────────

def fetch_hackernews(query: str = "", max_results: int = 5) -> dict:
    """Ambil top stories HackerNews + search via Algolia (no auth)."""
    try:
        if query:
            url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(query)}&tags=story&hitsPerPage={max_results}"
            data = json.loads(_http_get(url))
            hits = data.get("hits", [])
        else:
            # Top stories
            top_ids = json.loads(_http_get("https://hacker-news.firebaseio.com/v0/topstories.json"))
            hits = []
            for story_id in top_ids[:max_results]:
                try:
                    story = json.loads(_http_get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"))
                    if story:
                        hits.append(story)
                except Exception:  # noqa: BLE001
                    continue

        results = []
        for h in hits[:max_results]:
            results.append({
                "title": h.get("title", h.get("story_title", "")),
                "url": h.get("url", f"https://news.ycombinator.com/item?id={h.get('objectID', h.get('id', ''))}"),
                "score": h.get("points", h.get("score", 0)),
                "comments": h.get("num_comments", 0),
                "author": h.get("author", h.get("by", "")),
            })
        return _ok({
            "platform": "hackernews",
            "query": query or "top",
            "results": results,
            "count": len(results),
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"HackerNews fetch gagal: {exc}")


# ── Unified router ───────────────────────────────────────────────────────────

def fetch_web_unified(platform: str, query: str, **kwargs) -> dict:
    """Router untuk semua web fetch expanded."""
    platform = platform.lower()
    if platform == "reddit":
        return fetch_reddit(query, kwargs.get("subreddit", ""), kwargs.get("max_results", 5))
    if platform == "youtube":
        if kwargs.get("transcript"):
            return fetch_youtube_transcript(query)
        return fetch_youtube_search(query, kwargs.get("max_results", 5))
    if platform == "github":
        if kwargs.get("owner") and kwargs.get("repo"):
            return fetch_github_repo(kwargs["owner"], kwargs["repo"])
        return fetch_github_search(query, kwargs.get("language", ""), kwargs.get("max_results", 5))
    if platform == "arxiv":
        return fetch_arxiv(query, kwargs.get("max_results", 5))
    if platform == "hackernews":
        return fetch_hackernews(query, kwargs.get("max_results", 5))
    return _fallback(f"Platform '{platform}' tidak didukung. Supported: reddit, youtube, github, arxiv, hackernews")
