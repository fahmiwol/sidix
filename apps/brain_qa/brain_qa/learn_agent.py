"""
learn_agent.py — SIDIX LearnAgent: Belajar Mandiri dari 50+ Sumber Eksternal.

Filosofi: "Ilmu itu dicari, bukan ditunggu." SIDIX secara otonom mengambil
pengetahuan dari API publik, mengindeks ke corpus, dan mendokumentasikan
dalam research note.

Pipeline:
  pick_source() → fetch() → deduplicate() → index_corpus() → write_note() → log()

Sub-sources yang didukung (fase 1):
  - arXiv: paper AI/ML/CS terbaru
  - Wikipedia: factual knowledge base
  - MusicBrainz: music theory + metadata
  - GitHub Trending: coding best practices
  - Quran.com: Islamic epistemology corpus

Fase 2 (TODO):
  - Spotify audio features
  - Unsplash/Pexels visual metadata
  - Papers With Code benchmarks
  - World Bank data
  - NASA APOD
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .paths import default_data_dir, workspace_root
from .connectors import (
    ArxivConnector,
    WikipediaConnector,
    MusicBrainzConnector,
    GitHubTrendingConnector,
    QuranConnector,
)

logger = logging.getLogger(__name__)

_STATE_FILE = default_data_dir() / "learn_agent" / "state.json"
_NOTE_DIR = workspace_root() / "brain" / "public" / "research_notes"


# ── State management ───────────────────────────────────────────────────────────

def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_state(state: dict):
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _content_hash(content: str) -> str:
    return hashlib.sha256(content[:500].encode()).hexdigest()[:16]


def _topic_slug(title: str) -> str:
    s = (title or "untitled").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "untitled"


_VALID_SANAD = frozenset({"primer", "ulama", "peer_review", "aggregator"})


def _normalize_sanad_tier(raw: str | None) -> str:
    v = (raw or "aggregator").lower().replace(" ", "_").replace("-", "_")
    if v in ("peerreviewed", "peer_reviewed", "peerreview"):
        v = "peer_review"
    return v if v in _VALID_SANAD else "aggregator"


def _extract_sanad_tier_from_md(text: str) -> str:
    for line in (text or "").splitlines()[:40]:
        if line.lower().startswith("sanad-tier:"):
            return _normalize_sanad_tier(line.split(":", 1)[1].strip())
    return "aggregator"


# ── Deduplication ──────────────────────────────────────────────────────────────

def _load_seen_hashes() -> set[str]:
    hashes_file = _STATE_FILE.parent / "seen_hashes.json"
    if hashes_file.exists():
        try:
            return set(json.loads(hashes_file.read_text()))
        except Exception:
            pass
    return set()


def _save_seen_hashes(hashes: set[str]):
    hashes_file = _STATE_FILE.parent / "seen_hashes.json"
    hashes_file.parent.mkdir(parents=True, exist_ok=True)
    hashes_file.write_text(json.dumps(list(hashes)), encoding="utf-8")


def deduplicate(items: list[dict]) -> list[dict]:
    """Remove items whose content hash already exists in corpus."""
    seen = _load_seen_hashes()
    new_items = []
    for item in items:
        h = _content_hash(item.get("content", ""))
        if h not in seen:
            seen.add(h)
            new_items.append(item)
    _save_seen_hashes(seen)
    return new_items


# ── Corpus writer ──────────────────────────────────────────────────────────────

def _write_to_corpus_queue(items: list[dict], source_id: str):
    """
    Simpan items ke antrian corpus (JSON lines) untuk diproses indexer.
    Tidak langsung call indexer — hindari import circular.
    """
    queue_file = default_data_dir() / "learn_agent" / "corpus_queue.jsonl"
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    with queue_file.open("a", encoding="utf-8") as f:
        for item in items:
            item["_source_id"] = source_id
            item["_queued_at"] = datetime.now(timezone.utc).isoformat()
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ── Research note generator ────────────────────────────────────────────────────

def _next_note_number() -> int:
    existing = list(_NOTE_DIR.glob("[0-9]*.md"))
    if not existing:
        return 154
    nums = []
    for p in existing:
        try:
            nums.append(int(p.stem.split("_")[0]))
        except ValueError:
            pass
    return max(nums) + 1 if nums else 154


def _auto_research_note(items: list[dict], source_id: str, source_label: str) -> Path | None:
    """Generate a minimal research note from fetched items."""
    if not items:
        return None

    num = _next_note_number()
    slug = source_id.replace("/", "_").replace("-", "_")
    filename = f"{num}_auto_learn_{slug}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
    path = _NOTE_DIR / filename

    lines = [
        f"# {num}. Auto-Learn: {source_label} ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
        "",
        f"> **Domain**: {items[0].get('domain', 'general')}",
        f"> **Status**: `[FACT]` (auto-fetched, belum direview manual)",
        f"> **Source**: {source_id}",
        f"> **Items**: {len(items)} dokumen",
        "",
        "---",
        "",
        "## Ringkasan Item Terfetch",
        "",
    ]

    for i, item in enumerate(items[:10], 1):
        lines.append(f"### {i}. {item.get('title', 'Untitled')}")
        content_preview = item.get("content", "")[:300].replace("\n", " ")
        lines.append(f"{content_preview}...")
        if item.get("url"):
            lines.append(f"*Source: {item['url']}*")
        lines.append("")

    if len(items) > 10:
        lines.append(f"*... dan {len(items) - 10} item lainnya (tidak ditampilkan)*")
        lines.append("")

    lines += [
        "---",
        "",
        "## Catatan",
        "",
        "Note ini di-generate otomatis oleh `LearnAgent`. Perlu review manual",
        "sebelum dijadikan corpus training.",
        "",
        f"**Total item baru**: {len(items)}",
        f"**Waktu fetch**: {datetime.now(timezone.utc).isoformat()}",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ── Source definitions ─────────────────────────────────────────────────────────

def _source_arxiv(limit: int = 15) -> list[dict]:
    return ArxivConnector().fetch_latest(max_results=limit)


def _source_wikipedia_ai(limit: int = 10) -> list[dict]:
    topics = [
        "Artificial intelligence", "Machine learning", "Neural network",
        "Natural language processing", "Epistemology", "Islamic philosophy",
        "Knowledge graph", "Reinforcement learning", "Transformer model",
        "Bayesian inference",
    ]
    return WikipediaConnector().fetch_topics(topics[:limit])


def _source_musicbrainz(limit: int = 10) -> list[dict]:
    genres = ["jazz", "electronic", "classical", "hip hop", "ambient",
              "indie rock", "folk", "blues", "soul", "world music"]
    return MusicBrainzConnector().fetch_genre_overview(genres[:limit])


def _source_github(limit: int = 15) -> list[dict]:
    return GitHubTrendingConnector().fetch_ai_ml_trending(limit=limit)


def _source_quran(chapters: list[int] | None = None) -> list[dict]:
    if chapters is None:
        chapters = [1, 2, 3, 18, 36, 55, 67, 78, 112, 113, 114]  # prioritas
    results = []
    connector = QuranConnector()
    for ch in chapters[:5]:  # max 5 per run
        item = connector.fetch_chapter_as_corpus(ch)
        if item:
            results.append(item)
    return results


SOURCES: dict[str, Callable[[], list[dict]]] = {
    "arxiv": _source_arxiv,
    "wikipedia/ai": _source_wikipedia_ai,
    "musicbrainz": _source_musicbrainz,
    "github/trending": _source_github,
    "islamic/quran": _source_quran,
}


# ── Main LearnAgent ────────────────────────────────────────────────────────────

class LearnAgent:
    """
    SIDIX autonomous learning agent.

    Usage:
        agent = LearnAgent()
        result = agent.run(domain="arxiv")
        result = agent.run(domain="all", limit=10)
    """

    MIN_INTERVAL_SEC = 3600  # satu source tidak boleh di-fetch < 1 jam

    def run(self, domain: str = "all", limit: int = 20, force: bool = False) -> dict:
        """
        Run learning cycle untuk domain tertentu atau semua.

        Returns summary dict: {source: count_new_items, ...}
        """
        state = _load_state()
        now = time.time()
        summary: dict[str, int] = {}

        sources_to_run = (
            list(SOURCES.keys()) if domain == "all"
            else [k for k in SOURCES if k.startswith(domain)]
        )

        for source_id in sources_to_run:
            last_run = state.get(source_id, {}).get("last_run", 0)
            if not force and (now - last_run) < self.MIN_INTERVAL_SEC:
                logger.info("skip %s (last run %.0f min ago)", source_id,
                            (now - last_run) / 60)
                summary[source_id] = 0
                continue

            logger.info("fetching %s ...", source_id)
            try:
                raw_items = SOURCES[source_id]()
                new_items = deduplicate(raw_items)
                if new_items:
                    _write_to_corpus_queue(new_items, source_id)
                    note_path = _auto_research_note(
                        new_items, source_id,
                        source_id.replace("/", " ").replace("_", " ").title()
                    )
                    logger.info("%s → %d new items, note: %s",
                                source_id, len(new_items),
                                note_path.name if note_path else "none")
                state[source_id] = {"last_run": now, "last_count": len(new_items)}
                summary[source_id] = len(new_items)
            except Exception as exc:
                logger.error("learn_agent error for %s: %s", source_id, exc)
                summary[source_id] = -1

        _save_state(state)
        return summary

    def status(self) -> dict:
        """Return last-run info per source."""
        state = _load_state()
        now = time.time()
        result = {}
        for source_id in SOURCES:
            info = state.get(source_id, {})
            last_run = info.get("last_run", 0)
            result[source_id] = {
                "last_run": datetime.fromtimestamp(last_run, tz=timezone.utc).isoformat() if last_run else None,
                "minutes_ago": int((now - last_run) / 60) if last_run else None,
                "last_count": info.get("last_count", 0),
            }
        return result

    def process_corpus_queue(self) -> int:
        """
        Proses antrian corpus_queue.jsonl → panggil indexer.
        Return jumlah item yang berhasil diproses.
        """
        queue_file = default_data_dir() / "learn_agent" / "corpus_queue.jsonl"
        if not queue_file.exists():
            return 0

        lines = queue_file.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return 0

        try:
            from .indexer import build_index
            from .naskh_handler import NaskhHandler, note_to_knowledge_item

            auto_dir = workspace_root() / "brain" / "public" / "auto_learn"
            auto_dir.mkdir(parents=True, exist_ok=True)
            handler = NaskhHandler()
            for line in lines:
                try:
                    item = json.loads(line)
                    title = item.get("title", "Untitled")
                    topic = _topic_slug(title)
                    sanad = _normalize_sanad_tier(item.get("sanad_tier"))
                    content_body = item.get("content", "") or ""
                    full_md_body = (
                        f"# {title}\n\n"
                        f"Source: {item.get('url', '')}\n"
                        f"Domain: {item.get('domain', '')}\n"
                        f"License: {item.get('license', '')}\n"
                        f"Sanad-Tier: {sanad}\n\n"
                        f"{content_body}"
                    )
                    md_path = auto_dir / f"{topic}.md"
                    src_new = item.get("url") or item.get("_source_id", "learn_queue")
                    new_ki = note_to_knowledge_item(
                        full_md_body,
                        str(src_new),
                        topic,
                        sanad_tier=sanad,
                        confidence=float(item.get("confidence", 0.75)),
                    )
                    if md_path.exists():
                        old_text = md_path.read_text(encoding="utf-8")
                        old_stat = md_path.stat()
                        old_ki = note_to_knowledge_item(
                            old_text,
                            str(md_path),
                            topic,
                            sanad_tier=_extract_sanad_tier_from_md(old_text),
                            confidence=0.72,
                            date_added=datetime.fromtimestamp(old_stat.st_mtime, tz=timezone.utc),
                        )
                        winner, status, _reason = handler.resolve(old_ki, new_ki)
                        if status == "retained":
                            continue
                        md_path.write_text(winner.content, encoding="utf-8")
                    else:
                        md_path.write_text(full_md_body, encoding="utf-8")
                except Exception:
                    pass
            build_index()
            queue_file.write_text("", encoding="utf-8")
            return len(lines)
        except ImportError:
            logger.warning("indexer not available; queue items preserved")
            return 0
