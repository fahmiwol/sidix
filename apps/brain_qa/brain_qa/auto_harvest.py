"""
auto_harvest.py — Sprint Auto-Harvest Pipeline

Setiap 6 jam, cron job otomatis:
1. Ambil trending topics (Google Trends RSS Indonesia / hardcoded fallback)
2. Search via Wikipedia API (DDG blocked dari VPS)
3. Fetch artikel content via trafilatura (no Playwright needed)
4. Generate markdown note dengan YAML frontmatter
5. Save ke brain/public/omnyx_knowledge/YYYY-MM-DD/
6. Auto-reindex BM25 via /corpus/reindex endpoint

Knowledge flywheel: auto-harvest → corpus growth → more passthrough → faster answers.

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger("sidix.auto_harvest")

# ── Paths (resolved at import time using paths.py workspace_root) ─────────────
def _resolve_knowledge_root() -> Path:
    try:
        from .paths import workspace_root
        return workspace_root() / "brain" / "public" / "omnyx_knowledge"
    except Exception:
        # Fallback: resolve from this file's location (brain_qa/ → apps/brain_qa → apps → workspace)
        return Path(__file__).resolve().parents[3] / "brain" / "public" / "omnyx_knowledge"

KNOWLEDGE_ROOT = _resolve_knowledge_root()
HARVEST_LOG_FILE = KNOWLEDGE_ROOT / ".harvest_log.jsonl"

# ── Static fallback topics (when Google Trends unavailable) ───────────────────
FALLBACK_TOPICS_ID = [
    "kecerdasan buatan Indonesia",
    "Prabowo Subianto 2024",
    "teknologi AI terbaru",
    "startup Indonesia 2024",
    "ekonomi Indonesia 2025",
    "ibu kota nusantara IKN",
    "pendidikan digital Indonesia",
    "UMKM digital Indonesia",
    "kesehatan digital telemedicine",
    "energi terbarukan Indonesia",
]


# ── Google Trends RSS (optional, may not work from VPS) ───────────────────────

def _fetch_google_trends_id(n: int = 10) -> list[str]:
    """Fetch trending topics from Google Trends RSS for Indonesia."""
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=ID"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _WIKI_UA})
        with urllib.request.urlopen(req, timeout=10) as resp:
            import xml.etree.ElementTree as ET
            tree = ET.parse(resp)
            root = tree.getroot()
            topics = []
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    topics.append(title_el.text.strip())
                if len(topics) >= n:
                    break
            log.info("[harvest] Google Trends: %d topics", len(topics))
            return topics
    except Exception as e:
        log.warning("[harvest] Google Trends unavailable: %s", e)
        return []


# ── Wikipedia content fetch ────────────────────────────────────────────────────

_WIKI_UA = "SIDIXKnowledgeHarvest/1.0 (https://sidixlab.com; contact@sidixlab.com) Python-urllib"


def _wiki_get(url: str, timeout: int = 10) -> bytes:
    """GET request to Wikipedia with proper User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": _WIKI_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _wikipedia_search(query: str, limit: int = 3, lang: str = "id") -> list[dict]:
    """Search Wikipedia and return list of {title, extract, url}."""
    base = f"https://{lang}.wikipedia.org/w/api.php"

    # Step 1: search for relevant titles
    search_params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
    })
    try:
        data = json.loads(_wiki_get(f"{base}?{search_params}"))
        titles = [r["title"] for r in data.get("query", {}).get("search", [])]
    except Exception as e:
        log.warning("[harvest] Wikipedia search error: %s", e)
        return []

    if not titles and lang == "id":
        # Retry with English
        return _wikipedia_search(query, limit=limit, lang="en")

    results = []
    for title in titles[:limit]:
        content_params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts|info",
            "exintro": 1,
            "explaintext": 1,
            "inprop": "url",
            "titles": title,
            "format": "json",
            "redirects": 1,
        })
        try:
            cdata = json.loads(_wiki_get(f"{base}?{content_params}"))
            pages = cdata.get("query", {}).get("pages", {})
            for page in pages.values():
                if "missing" in page:
                    continue
                extract = page.get("extract", "").strip()
                if len(extract) < 300:
                    continue
                results.append({
                    "title": page.get("title", title),
                    "text": extract,
                    "url": page.get("fullurl", f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"),
                    "source": "wikipedia",
                })
            time.sleep(0.3)  # polite rate limiting
        except Exception as e:
            log.warning("[harvest] Wikipedia fetch error for '%s': %s", title, e)
    return results


# ── URL content fetch via trafilatura (no Playwright) ─────────────────────────

def _fetch_url_trafilatura(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch URL content via trafilatura (no browser needed)."""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return text
    except ImportError:
        log.warning("[harvest] trafilatura not installed; skipping URL fetch")
        return None
    except Exception as e:
        log.warning("[harvest] trafilatura fetch error for %s: %s", url, e)
        return None


# ── Note generation ────────────────────────────────────────────────────────────

def _make_note_id(topic: str, url: str) -> str:
    h = hashlib.md5(f"{topic}:{url}".encode()).hexdigest()[:8]
    return f"harvest_{h}"


def _generate_note(topic: str, content_item: dict, date_str: str) -> str:
    """Generate markdown note with YAML frontmatter."""
    title = content_item.get("title", topic)
    url = content_item.get("url", "")
    text = content_item.get("text", "")
    source = content_item.get("source", "web")
    note_id = _make_note_id(topic, url)

    # Trim text to reasonable size
    text_trimmed = text[:3000].strip()
    if len(text) > 3000:
        text_trimmed += "\n\n[...terpotong...]"

    tags = _extract_tags(topic, title)
    tags_yaml = ", ".join(f'"{t}"' for t in tags[:5])

    return f"""---
title: "{title.replace('"', "'")}"
date: "{date_str}"
source: "{url}"
topic: "{topic.replace('"', "'")}"
engine: "auto_harvest"
source_type: "{source}"
tags: [{tags_yaml}]
note_id: "{note_id}"
---

# {title}

**Topik:** {topic}
**Sumber:** {url}
**Tanggal harvest:** {date_str}

---

{text_trimmed}
"""


def _extract_tags(topic: str, title: str) -> list[str]:
    """Extract simple tags from topic + title."""
    words = (topic + " " + title).lower().split()
    stopwords = {"dan", "atau", "yang", "di", "ke", "dari", "untuk", "dengan", "adalah", "ini", "itu", "the", "a", "of", "in", "and", "to", "for"}
    tags = []
    seen = set()
    for w in words:
        w = w.strip(".,;:!?()")
        if len(w) > 3 and w not in stopwords and w not in seen:
            tags.append(w)
            seen.add(w)
    return tags[:8]


# ── BM25 reindex trigger ───────────────────────────────────────────────────────

def _trigger_reindex(backend_url: str = "http://localhost:8765") -> bool:
    """Trigger BM25 reindex via backend API (requires X-Admin-Token from env)."""
    admin_token = os.environ.get("BRAIN_QA_ADMIN_TOKEN", "")
    if not admin_token:
        log.warning("[harvest] BRAIN_QA_ADMIN_TOKEN not set — cannot trigger reindex")
        return False
    try:
        req = urllib.request.Request(
            f"{backend_url}/corpus/reindex",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Admin-Token": admin_token,
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            log.info("[harvest] Reindex triggered: %s", result)
            return True
    except Exception as e:
        log.warning("[harvest] Reindex trigger failed: %s", e)
        return False


# ── Duplicate check ────────────────────────────────────────────────────────────

def _already_harvested(note_id: str) -> bool:
    """Check if note_id already in harvest log."""
    if not HARVEST_LOG_FILE.exists():
        return False
    try:
        with open(HARVEST_LOG_FILE) as f:
            for line in f:
                entry = json.loads(line.strip())
                if entry.get("note_id") == note_id:
                    return True
    except Exception:
        pass
    return False


def _log_harvest(note_id: str, topic: str, path: str) -> None:
    HARVEST_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HARVEST_LOG_FILE, "a") as f:
        f.write(json.dumps({
            "note_id": note_id,
            "topic": topic,
            "path": path,
            "ts": datetime.now(timezone.utc).isoformat(),
        }) + "\n")


# ── Main AutoHarvest class ─────────────────────────────────────────────────────

class AutoHarvest:
    """Sprint Auto-Harvest pipeline — runs every 6 hours via cron."""

    def __init__(
        self,
        knowledge_root: Path = KNOWLEDGE_ROOT,
        backend_url: str = "http://localhost:8765",
        max_topics: int = 5,
        max_articles_per_topic: int = 2,
    ):
        self.knowledge_root = knowledge_root
        self.backend_url = backend_url
        self.max_topics = max_topics
        self.max_articles_per_topic = max_articles_per_topic

    async def run(self, topics: Optional[list[str]] = None) -> dict:
        """Main harvest run. Returns stats dict."""
        t0 = time.monotonic()
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_dir = self.knowledge_root / date_str
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Get topics
        if not topics:
            topics = await asyncio.to_thread(_fetch_google_trends_id, self.max_topics + 5)
        if not topics:
            topics = FALLBACK_TOPICS_ID[:]
            log.info("[harvest] Using %d fallback topics", len(topics))

        topics = topics[:self.max_topics]
        log.info("[harvest] Starting with %d topics: %s", len(topics), topics[:3])

        # 2. For each topic: Wikipedia search → content → note → save
        notes_saved = 0
        notes_skipped = 0
        errors = 0

        for topic in topics:
            try:
                articles = await asyncio.to_thread(
                    _wikipedia_search, topic, self.max_articles_per_topic
                )
                if not articles:
                    log.warning("[harvest] No articles for topic: %s", topic)
                    errors += 1
                    continue

                for article in articles:
                    note_id = _make_note_id(topic, article.get("url", ""))
                    if _already_harvested(note_id):
                        notes_skipped += 1
                        continue

                    if len(article.get("text", "")) < 300:
                        continue

                    note_content = _generate_note(topic, article, date_str)
                    note_filename = f"{note_id}.md"
                    note_path = out_dir / note_filename

                    note_path.write_text(note_content, encoding="utf-8")
                    _log_harvest(note_id, topic, str(note_path))
                    notes_saved += 1
                    log.info("[harvest] Saved: %s (%s)", note_filename, topic[:40])

            except Exception as e:
                log.error("[harvest] Error on topic '%s': %s", topic, e)
                errors += 1

        # 3. Auto-reindex if new notes added
        reindexed = False
        if notes_saved > 0:
            reindexed = await asyncio.to_thread(_trigger_reindex, self.backend_url)

        elapsed_s = time.monotonic() - t0
        stats = {
            "topics_processed": len(topics),
            "notes_saved": notes_saved,
            "notes_skipped": notes_skipped,
            "errors": errors,
            "reindexed": reindexed,
            "elapsed_s": round(elapsed_s, 1),
            "date": date_str,
        }
        log.info("[harvest] Done: %s", stats)
        return stats


# ── Standalone run ─────────────────────────────────────────────────────────────

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    harvester = AutoHarvest()
    stats = await harvester.run()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
