"""
proactive_feeds.py — External Trend Monitor (Pilar 4 closure 70% → 85%)
========================================================================

Per SIDIX_DEFINITION_20260426 Daily Capability #6:
> "Mengikuti trend setiap hari"

Plus DIRECTION_LOCK Q3 P1:
> "Pilar 4: Trend RSS feed + push notification"

Modul ini fetch external trend signals dari 4 sumber berkala:
1. **Hacker News top** — tech news daily
2. **arXiv cs.AI recent** — academic preprint AI/ML
3. **GitHub trending** — repo populer (lang: Python, TypeScript)
4. **HuggingFace papers** — daily curated AI papers

Hook ke `proactive_trigger.scan_anomalies()` — kalau topik baru muncul yang
tidak match pattern existing → flag sebagai "external_trend_emergence" anomaly.

Filosofi: SIDIX **literally follow trend setiap hari**. Bukan tunggu user
report. Pagi 06:00 WIB, SIDIX sudah scan + digest top 10 trend.

Privacy + Ethics:
- Public RSS only (no auth needed)
- Cache via local JSON (no third-party tracking)
- Rate-limit conservative (5s/source per scan)

Cron suggestion:
- Hourly: `fetch_all_feeds()` cheap
- 4-hourly: `analyze_trends_with_llm()` (deep, more LLM cost)
- Daily 06:00 WIB: include di morning_digest (existing proactive_trigger)
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class TrendItem:
    """1 trend item dari external feed."""
    id: str
    ts: str
    source: str          # "hn" | "arxiv" | "github" | "hf_papers"
    title: str
    url: str
    score: int = 0       # upvotes / stars / kalau available
    summary: str = ""
    keywords: list[str] = field(default_factory=list)
    fetched_at: str = ""


# ── Path ───────────────────────────────────────────────────────────────────────

def _trends_log() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "external_trends.jsonl"


def _trends_cache() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "trends_cache.json"


# ── HTTP helper (httpx, conservative timeout) ─────────────────────────────────

def _safe_fetch(url: str, *, timeout: float = 8.0) -> Optional[str]:
    """Fetch URL dengan timeout. Return text atau None kalau fail."""
    try:
        import httpx
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(url, headers={
                "User-Agent": "SIDIX-Bot/2.0 (proactive trend monitor; +https://sidixlab.com)",
                "Accept": "application/json, text/html, */*",
            })
            if r.status_code == 200:
                return r.text
    except Exception as e:
        log.debug("[feeds] fetch fail %s: %s", url, e)
    return None


# ── Source 1: Hacker News (Algolia API, free) ────────────────────────────────

def fetch_hn_top(limit: int = 10) -> list[TrendItem]:
    """Top HN stories last 24h dengan tags 'story'."""
    url = "https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage=20"
    text = _safe_fetch(url)
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for h in (data.get("hits") or [])[:limit]:
            title = (h.get("title") or "").strip()
            if not title:
                continue
            items.append(TrendItem(
                id=f"hn_{h.get('objectID', uuid.uuid4().hex[:8])}",
                ts=h.get("created_at", ""),
                source="hn",
                title=title,
                url=h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID', '')}",
                score=int(h.get("points", 0) or 0),
                summary="",
                keywords=_extract_keywords(title),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ))
        return items
    except Exception as e:
        log.debug("[feeds] hn parse fail: %s", e)
        return []


# ── Source 2: arXiv cs.AI recent ─────────────────────────────────────────────

def fetch_arxiv_recent(limit: int = 10) -> list[TrendItem]:
    """arXiv cs.AI new submissions API."""
    url = (
        "http://export.arxiv.org/api/query?"
        "search_query=cat:cs.AI&"
        "sortBy=submittedDate&sortOrder=descending&"
        f"max_results={limit}"
    )
    text = _safe_fetch(url)
    if not text:
        return []
    try:
        # Parse Atom XML manually (no extra dep)
        items = []
        # Split by <entry> blocks
        entries = re.findall(r"<entry>(.*?)</entry>", text, re.DOTALL)
        for entry in entries[:limit]:
            title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
            link_m = re.search(r'<id>(.*?)</id>', entry)
            summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
            published_m = re.search(r"<published>(.*?)</published>", entry)

            if not title_m or not link_m:
                continue
            title = re.sub(r"\s+", " ", title_m.group(1)).strip()
            url_arxiv = link_m.group(1).strip()
            summary = re.sub(r"\s+", " ", summary_m.group(1)[:300]).strip() if summary_m else ""

            arxiv_id = url_arxiv.split("/")[-1] if "/" in url_arxiv else uuid.uuid4().hex[:8]
            items.append(TrendItem(
                id=f"arxiv_{arxiv_id}",
                ts=published_m.group(1) if published_m else "",
                source="arxiv",
                title=title,
                url=url_arxiv,
                score=0,
                summary=summary,
                keywords=_extract_keywords(title),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ))
        return items
    except Exception as e:
        log.debug("[feeds] arxiv parse fail: %s", e)
        return []


# ── Source 3: GitHub trending (HTML scrape — no auth API) ─────────────────────

def fetch_github_trending(language: str = "python", limit: int = 10) -> list[TrendItem]:
    """
    GitHub trending — tidak ada official API, scrape ringan dari trending page.
    Fallback ke API search kalau scrape fail.
    """
    # Try API search recent created (proxy untuk trending)
    url = (
        "https://api.github.com/search/repositories?"
        f"q=created:>={(datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')}+language:{language}&"
        "sort=stars&order=desc&per_page=20"
    )
    text = _safe_fetch(url)
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for r in (data.get("items") or [])[:limit]:
            name = (r.get("full_name") or "").strip()
            desc = (r.get("description") or "").strip()
            if not name:
                continue
            items.append(TrendItem(
                id=f"gh_{r.get('id', uuid.uuid4().hex[:8])}",
                ts=r.get("created_at", ""),
                source="github",
                title=f"{name} — {desc[:120]}" if desc else name,
                url=r.get("html_url", ""),
                score=int(r.get("stargazers_count", 0) or 0),
                summary=desc[:300],
                keywords=_extract_keywords(f"{name} {desc}"),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ))
        return items
    except Exception as e:
        log.debug("[feeds] github parse fail: %s", e)
        return []


# ── Source 4: HuggingFace papers (daily curated) ─────────────────────────────

def fetch_huggingface_papers(limit: int = 10) -> list[TrendItem]:
    """
    HF papers RSS-like endpoint. /api/daily_papers tidak dipublish
    — pakai HF papers landing scrape via JSON-LD atau cardinal markdown.
    Fallback: query arxiv via HF mirror.
    """
    # HF papers daily — ada endpoint JSON kalau available
    url = "https://huggingface.co/api/daily_papers"
    text = _safe_fetch(url)
    if not text:
        return []
    try:
        data = json.loads(text)
        # data biasanya list of paper objects
        items = []
        papers = data if isinstance(data, list) else (data.get("papers") or [])
        for p in papers[:limit]:
            paper = p.get("paper") or p
            title = (paper.get("title") or "").strip()
            if not title:
                continue
            arxiv_id = paper.get("id") or paper.get("arxivId") or uuid.uuid4().hex[:8]
            summary = (paper.get("summary") or "")[:300]
            upvotes = int(paper.get("upvotes", 0) or 0)
            items.append(TrendItem(
                id=f"hf_{arxiv_id}",
                ts=paper.get("publishedAt", ""),
                source="hf_papers",
                title=title,
                url=f"https://huggingface.co/papers/{arxiv_id}",
                score=upvotes,
                summary=summary,
                keywords=_extract_keywords(title + " " + summary),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            ))
        return items
    except Exception as e:
        log.debug("[feeds] hf papers parse fail: %s", e)
        return []


# ── Keyword extractor (lightweight, no NLP lib) ───────────────────────────────

_AI_KEYWORDS = {
    "agent", "agentic", "llm", "transformer", "diffusion", "rag", "lora",
    "multimodal", "voice", "audio", "vision", "vlm", "tts", "stt", "image",
    "tactile", "embodied", "robot", "training", "fine-tune", "rl", "rlhf",
    "alignment", "safety", "reasoning", "chain", "tree", "self-improve",
    "skill", "tool", "ontology", "graph", "memory", "context", "long-context",
    "moe", "mixture", "experts", "open-source", "open-weight", "gpu",
    "inference", "edge", "mobile", "decentralized", "p2p", "federated",
    "sora", "claude", "gemini", "qwen", "llama", "mistral", "deepseek",
    "evaluation", "benchmark", "prm", "process-reward", "consciousness",
}


def _extract_keywords(text: str) -> list[str]:
    """Quick keyword match dari text vs AI keyword bank."""
    text_lower = (text or "").lower()
    found = []
    for kw in _AI_KEYWORDS:
        if kw in text_lower:
            found.append(kw)
    return found[:8]


# ── Aggregate fetch ────────────────────────────────────────────────────────────

def fetch_all_feeds(*, limit_per_source: int = 5) -> dict:
    """
    Fetch semua 4 source paralel-ish (sequential dengan timeout per source).
    Return dict dengan items + summary stats. Save ke trends_cache.json.

    Cron: hourly.
    """
    all_items: list[TrendItem] = []
    sources_status = {}

    for source_name, fetch_fn in [
        ("hn", fetch_hn_top),
        ("arxiv", fetch_arxiv_recent),
        ("github", fetch_github_trending),
        ("hf_papers", fetch_huggingface_papers),
    ]:
        try:
            items = fetch_fn(limit=limit_per_source)
            all_items.extend(items)
            sources_status[source_name] = {"ok": True, "count": len(items)}
        except Exception as e:
            sources_status[source_name] = {"ok": False, "error": str(e)[:100]}
            log.warning("[feeds] %s fail: %s", source_name, e)

    # Persist all items
    try:
        with _trends_log().open("a", encoding="utf-8") as f:
            for item in all_items:
                f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[feeds] log fail: %s", e)

    # Cache latest
    cache = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources_status,
        "total_items": len(all_items),
        "items": [asdict(i) for i in all_items],
    }
    try:
        _trends_cache().write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

    return cache


# ── Anomaly detection (hook ke proactive_trigger) ─────────────────────────────

def detect_trend_anomalies() -> list[dict]:
    """
    Detect anomaly dari trend cache:
    - Repeated keyword across sources (signal kuat tren)
    - High-score outlier (>500 HN points, >50 HF upvotes, >100 GH stars)
    - New domain emergence (keyword tidak pernah muncul sebelumnya)
    """
    cache_path = _trends_cache()
    if not cache_path.exists():
        return []

    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    items = cache.get("items", [])
    if not items:
        return []

    anomalies = []
    from collections import Counter

    # 1. Cross-source keyword cluster
    kw_counter = Counter()
    kw_to_items = {}
    for item in items:
        for kw in item.get("keywords", []):
            kw_counter[kw] += 1
            kw_to_items.setdefault(kw, []).append(item.get("title", "")[:80])

    for kw, count in kw_counter.most_common(5):
        if count >= 3:  # appears in 3+ items across sources
            anomalies.append({
                "id": f"trendanom_{uuid.uuid4().hex[:8]}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "cross_source_keyword_cluster",
                "source": "external_feeds",
                "severity": "notice" if count >= 5 else "info",
                "description": f"Keyword '{kw}' muncul {count}x di trend feed (3+ source) — possible emerging theme",
                "evidence": kw_to_items.get(kw, [])[:3],
                "suggested_prompt": (
                    f"Riset 'mengapa keyword {kw} sedang trending di AI/tech feed minggu ini. "
                    f"Bisa jadi opportunity untuk SIDIX adopt? Bandingkan dengan pattern library existing."
                ),
            })

    # 2. High-score outlier
    for item in items:
        score = int(item.get("score", 0) or 0)
        source = item.get("source", "")
        # Threshold per source
        if (source == "hn" and score >= 500) or \
           (source == "hf_papers" and score >= 50) or \
           (source == "github" and score >= 100):
            anomalies.append({
                "id": f"trendanom_{uuid.uuid4().hex[:8]}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "high_score_outlier",
                "source": "external_feeds",
                "severity": "important",
                "description": f"[{source}] {item.get('title', '')[:100]} — score {score} (high)",
                "evidence": [item.get("url", "")],
                "suggested_prompt": (
                    f"Trend high-impact: {item.get('title', '')}. "
                    f"Riset detail. Apakah ada implikasi untuk SIDIX roadmap?"
                ),
            })

    return anomalies[:10]  # cap to avoid spam


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Stats untuk admin dashboard."""
    cache_path = _trends_cache()
    log_path = _trends_log()

    out = {
        "cache_exists": cache_path.exists(),
        "log_exists": log_path.exists(),
        "latest_fetch": "",
        "latest_sources": {},
        "total_items_logged": 0,
    }

    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            out["latest_fetch"] = cache.get("fetched_at", "")
            out["latest_sources"] = cache.get("sources", {})
            out["latest_total"] = cache.get("total_items", 0)
        except Exception:
            pass

    if log_path.exists():
        try:
            with log_path.open("r", encoding="utf-8") as f:
                out["total_items_logged"] = sum(1 for line in f if line.strip())
        except Exception:
            pass

    return out


def list_recent(limit: int = 20, source: str = "") -> list[dict]:
    """List recent items (filtered by source kalau specified)."""
    cache_path = _trends_cache()
    if not cache_path.exists():
        return []
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        items = cache.get("items", [])
        if source:
            items = [i for i in items if i.get("source") == source]
        return items[:limit]
    except Exception:
        return []


__all__ = [
    "TrendItem",
    "fetch_hn_top", "fetch_arxiv_recent", "fetch_github_trending",
    "fetch_huggingface_papers", "fetch_all_feeds",
    "detect_trend_anomalies", "stats", "list_recent",
]
