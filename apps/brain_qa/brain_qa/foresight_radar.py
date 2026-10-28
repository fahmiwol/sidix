"""
foresight_radar.py — Sprint L2: Foresight Radar (RSS + Weak Signal Detector)
==============================================================================

Berjalan sebagai background cron (setiap 24 jam).

Pipeline:
  1. FETCH  — RSS dari arXiv AI, HN, GitHub trending, ProductHunt AI
  2. SCORE  — relevance ke domain SIDIX (AI agent, LLM, Indonesia tech)
  3. COMPARE — bandingkan dengan corpus SIDIX topics (BM25 overlap)
  4. DETECT  — kalau topic baru + high-relevance → "weak signal"
  5. DRAFT   — generate draft research note (untuk owner review)
  6. NOTIFY  — save ke .data/radar_signals.jsonl

Filosofi: SIDIX tidak menunggu user untuk tahu tren. Seperti otak yang
terus memproses peripheral signals bahkan saat tidak diminta (default mode
network). Selalu aware, selalu update.

Public API:
    run_radar_cycle(llm_fn=None) -> dict     # jalankan 1 siklus
    get_recent_signals(n=20) -> list[dict]   # ambil sinyal terbaru
    get_pending_drafts() -> list[dict]       # draft research note belum review
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────

def _resolve_data_dir() -> Path:
    try:
        from .paths import workspace_root
        p = workspace_root() / ".data"
    except Exception:
        p = Path(__file__).resolve().parents[3] / ".data"
    p.mkdir(parents=True, exist_ok=True)
    return p

_DATA_DIR: Path | None = None

def _data_dir() -> Path:
    global _DATA_DIR
    if _DATA_DIR is None:
        _DATA_DIR = _resolve_data_dir()
    return _DATA_DIR

_SIGNALS_FILE = None
_DRAFTS_FILE = None
_lock = threading.Lock()

def _signals_path() -> Path:
    global _SIGNALS_FILE
    if _SIGNALS_FILE is None:
        _SIGNALS_FILE = _data_dir() / "radar_signals.jsonl"
    return _SIGNALS_FILE

def _drafts_path() -> Path:
    global _DRAFTS_FILE
    if _DRAFTS_FILE is None:
        _DRAFTS_FILE = _data_dir() / "radar_drafts.jsonl"
    return _DRAFTS_FILE


# ── RSS Feed Sources ───────────────────────────────────────────────────────────

RSS_FEEDS = {
    "arxiv_ai": "https://arxiv.org/rss/cs.AI",
    "arxiv_cl": "https://arxiv.org/rss/cs.CL",  # Computation and Language (LLM papers)
    "arxiv_lg": "https://arxiv.org/rss/cs.LG",  # Machine Learning
    "hn_best": "https://hnrss.org/best",
    "producthunt_ai": "https://www.producthunt.com/feed?category=artificial-intelligence",
}

# Keywords yang relevan untuk SIDIX domain
RELEVANCE_KEYWORDS = {
    "core": ["llm", "agent", "rag", "retrieval", "multi-agent", "autonomous", "self-learning",
             "fine-tuning", "lora", "dora", "instruction tuning", "mcp", "tool use"],
    "sidix_specific": ["indonesia", "malay", "bahasa", "southeast asia", "open source",
                       "self-hosted", "local llm", "qwen", "mistral"],
    "creative": ["diffusion", "image generation", "video generation", "tts", "voice",
                 "multimodal", "vision"],
    "architecture": ["memory", "episodic", "vector store", "knowledge graph", "corpus",
                     "embedding", "semantic search", "continual learning"],
}

ALL_KEYWORDS = [kw for kws in RELEVANCE_KEYWORDS.values() for kw in kws]


# ── Fetch RSS ─────────────────────────────────────────────────────────────────

def _fetch_rss(url: str, timeout: int = 10) -> list[dict]:
    """Fetch RSS feed, return list of {title, link, summary, published}."""
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SIDIXForesightRadar/1.0 (https://sidixlab.com; research)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()

        root = ET.fromstring(content)
        ns = ""
        # Detect namespace
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Standard RSS 2.0
        for item in root.findall(f".//{ns}item"):
            title = item.findtext(f"{ns}title") or item.findtext("title") or ""
            link = item.findtext(f"{ns}link") or item.findtext("link") or ""
            summary = (item.findtext(f"{ns}description") or
                       item.findtext("description") or
                       item.findtext(f"{ns}summary") or "")
            published = item.findtext(f"{ns}pubDate") or item.findtext("pubDate") or ""
            if title:
                items.append({
                    "title": title.strip()[:200],
                    "link": link.strip()[:300],
                    "summary": re.sub(r'<[^>]+>', '', summary).strip()[:400],
                    "published": published.strip(),
                })
    except Exception as e:
        log.debug("[foresight_radar] RSS fetch failed for %s: %s", url, e)
    return items[:20]  # cap per feed


# ── Score Relevance ────────────────────────────────────────────────────────────

def _score_item(item: dict) -> float:
    """Score relevance 0-1 berdasarkan keyword matching."""
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    hits = 0
    weights = {"core": 2.0, "sidix_specific": 2.5, "creative": 1.0, "architecture": 1.5}
    total_weight = 0.0
    for category, keywords in RELEVANCE_KEYWORDS.items():
        w = weights.get(category, 1.0)
        for kw in keywords:
            if kw in text:
                hits += w
        total_weight += w * len(keywords)

    return min(1.0, hits / max(total_weight * 0.1, 1.0))


# ── Compare with Corpus ───────────────────────────────────────────────────────

def _is_novel_topic(title: str) -> bool:
    """
    True if topic likely not covered in SIDIX corpus.
    Quick heuristic: try BM25 search, check top score.
    """
    try:
        from .agent_tools import _tool_search_corpus
        result = _tool_search_corpus({"query": title, "k": 1})
        output = getattr(result, "output", "") or ""
        # If corpus returns something highly relevant, topic already covered
        if len(output) > 100:
            # Topic probably covered — not novel
            return False
        return True
    except Exception:
        return True  # Default: treat as novel if corpus check fails


# ── Detect Weak Signals ───────────────────────────────────────────────────────

def detect_weak_signals(items: list[dict]) -> list[dict]:
    """
    Filter items yang:
    - Relevance score tinggi (>0.15)
    - Belum ada di corpus SIDIX (novel topic)
    """
    signals = []
    for item in items:
        score = _score_item(item)
        if score >= 0.15:
            novel = _is_novel_topic(item["title"])
            signals.append({
                **item,
                "relevance_score": round(score, 3),
                "is_novel": novel,
                "priority": "high" if score >= 0.4 and novel else "medium" if score >= 0.25 else "low",
            })
    # Sort by relevance
    signals.sort(key=lambda x: x["relevance_score"], reverse=True)
    return signals[:10]  # top 10


# ── Generate Draft Research Note ──────────────────────────────────────────────

def _generate_draft(signal: dict, llm_fn=None) -> Optional[str]:
    """Generate draft markdown untuk research note berdasarkan sinyal."""
    if llm_fn is None:
        return None

    prompt = f"""Kamu adalah SIDIX research assistant.

Berdasarkan sinyal tren berikut:
Judul: {signal['title']}
Link: {signal.get('link', '')}
Summary: {signal.get('summary', '')}

Tulis draft research note SIDIX dengan format:
---
title: [topik dalam 5-10 kata]
tags: [tag1, tag2, tag3]
date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
sanad: draft — perlu verifikasi manual
---

# [Judul]

## Apa Ini?
[2-3 kalimat tentang topik]

## Kenapa Relevan untuk SIDIX?
[2-3 kalimat relevansi ke SIDIX architecture/roadmap]

## Poin Kunci
- [poin 1]
- [poin 2]
- [poin 3]

## Adopsi Potensial
[1-2 kalimat tentang bagaimana SIDIX bisa adopt/terinspirasi]

## Link Sumber
- {signal.get('link', 'tidak tersedia')}

---
*Draft otomatis dari Foresight Radar. Perlu review sebelum publish.*"""

    try:
        draft = llm_fn(prompt)
        return draft[:3000]
    except Exception as e:
        log.warning("[foresight_radar] draft generation failed: %s", e)
        return None


# ── Persistence ───────────────────────────────────────────────────────────────

def _save_signals(signals: list[dict], source: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    with _lock:
        try:
            with open(_signals_path(), "a", encoding="utf-8") as f:
                for sig in signals:
                    entry = {"id": uuid.uuid4().hex[:10], "ts": ts, "source": source, **sig}
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            log.warning("[foresight_radar] save signals failed: %s", e)


def _save_draft(signal: dict, draft: str, note_number: Optional[int] = None) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": uuid.uuid4().hex[:10],
        "ts": ts,
        "signal_title": signal.get("title", ""),
        "signal_link": signal.get("link", ""),
        "draft": draft,
        "suggested_note_number": note_number,
        "status": "pending_review",
    }
    with _lock:
        try:
            with open(_drafts_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            log.warning("[foresight_radar] save draft failed: %s", e)


def get_recent_signals(n: int = 20) -> list[dict]:
    p = _signals_path()
    if not p.exists():
        return []
    entries = []
    with _lock:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except Exception:
                            pass
        except Exception:
            pass
    return entries[-n:]


def get_pending_drafts() -> list[dict]:
    p = _drafts_path()
    if not p.exists():
        return []
    entries = []
    with _lock:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            d = json.loads(line)
                            if d.get("status") == "pending_review":
                                entries.append(d)
                        except Exception:
                            pass
        except Exception:
            pass
    return entries


# ── Main Cycle ────────────────────────────────────────────────────────────────

def run_radar_cycle(llm_fn=None) -> dict:
    """
    Jalankan 1 siklus radar:
    1. Fetch semua RSS feeds
    2. Score + detect weak signals
    3. Draft research notes untuk high-priority novel signals
    4. Save semua ke .data/
    Returns summary dict.
    """
    log.info("[foresight_radar] starting radar cycle")
    t0 = time.time()

    all_items: list[dict] = []
    feed_results: dict[str, int] = {}

    for feed_name, feed_url in RSS_FEEDS.items():
        items = _fetch_rss(feed_url)
        feed_results[feed_name] = len(items)
        for item in items:
            item["_feed"] = feed_name
        all_items.extend(items)

    log.info("[foresight_radar] fetched %d items from %d feeds", len(all_items), len(feed_results))

    # Detect weak signals
    signals = detect_weak_signals(all_items)
    log.info("[foresight_radar] detected %d relevant signals", len(signals))

    # Save signals
    if signals:
        _save_signals(signals, source="rss_cycle")

    # Draft for high-priority novel signals
    drafts_created = 0
    high_priority = [s for s in signals if s.get("priority") == "high" and s.get("is_novel")]
    for sig in high_priority[:3]:  # max 3 drafts per cycle
        draft = _generate_draft(sig, llm_fn=llm_fn)
        if draft:
            _save_draft(sig, draft)
            drafts_created += 1

    duration = round(time.time() - t0, 2)
    result = {
        "cycle_ts": datetime.now(timezone.utc).isoformat(),
        "feeds_fetched": feed_results,
        "total_items": len(all_items),
        "signals_detected": len(signals),
        "high_priority": len(high_priority),
        "drafts_created": drafts_created,
        "duration_s": duration,
        "top_signals": [
            {"title": s["title"], "score": s["relevance_score"], "novel": s["is_novel"]}
            for s in signals[:5]
        ],
    }

    log.info("[foresight_radar] cycle done in %.1fs: %d signals, %d drafts", duration, len(signals), drafts_created)
    return result
