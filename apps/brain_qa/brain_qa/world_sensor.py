"""
world_sensor.py — SIDIX World Sensor Architecture
==================================================
Sistem deteksi tren dunia secara otonom — "mata dan telinga" SIDIX.

Arsitektur dari Growth Manifesto (42_sidix_growth_manifesto_dikw_architecture.md):
  7 sensor aktif dengan interval berbeda:
  - arXiv        : 6 jam  — paper AI/ML/NLP terbaru
  - GitHub       : 12 jam — tool/repo populer (via GitHub trending API)
  - News         : realtime (manual fetch dengan interval)
  - User feedback: per interaksi (via feedback_loop)
  - Benchmark    : mingguan (MMLU, HumanEval — tracking skor lokal)
  - Competitor   : harian  — model baru di HuggingFace leaderboard
  - Social       : 6 jam  — Twitter/X topics, Reddit r/MachineLearning

Implementasi sekarang (Phase 0 — VPS tunggal):
  - arXiv RSS scanner (tanpa API key)
  - GitHub trending scraper (tanpa API key, public API)
  - MCP Knowledge Bridge (D:\\SIDIX\\knowledge -> corpus)
  - Benchmark drift tracker (lokal, simpel)

Phase 1 (nanti): News API + HuggingFace leaderboard
Phase 2 (nanti): Social signals, competitor intelligence

Setiap sinyal yang terdeteksi masuk ke pipeline:
  signal → novelty_check (apakah sudah ada di corpus?) → ingest → reindex
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .paths import default_data_dir, workspace_root

# ── Paths ──────────────────────────────────────────────────────────────────────

_SENSOR_DIR = default_data_dir() / "world_sensor"
_SENSOR_LOG = _SENSOR_DIR / "sensor_log.jsonl"
_NOVELTY_DB = _SENSOR_DIR / "seen_ids.json"
_CORPUS_WEB = workspace_root() / "brain" / "public" / "sources" / "web_clips"
_SENSOR_DIR.mkdir(parents=True, exist_ok=True)
_CORPUS_WEB.mkdir(parents=True, exist_ok=True)

USER_AGENT = "SIDIX-WorldSensor/1.0 (educational; contact:fahmiwol@gmail.com)"
REQUEST_DELAY = 2.0  # seconds between requests

# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class SensorSignal:
    id: str = ""              # Unique ID (URL hash atau arXiv ID)
    source: str = ""          # "arxiv", "github", "mcp_bridge", "benchmark"
    title: str = ""
    url: str = ""
    summary: str = ""
    authors: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    published: str = ""
    novelty_score: float = 1.0  # 1.0 = baru, 0.0 = sudah ada
    timestamp: float = field(default_factory=time.time)
    ingested: bool = False

    def to_corpus_markdown(self) -> str:
        """Konversi ke format Markdown untuk corpus."""
        tags_str = ", ".join(self.tags) if self.tags else "research"
        authors_str = ", ".join(self.authors[:5]) if self.authors else "Unknown"
        date_str = self.published or datetime.now().strftime("%Y-%m-%d")

        return (
            f"# {self.title}\n\n"
            f"**Sumber:** {self.source}  \n"
            f"**URL:** {self.url}  \n"
            f"**Tanggal:** {date_str}  \n"
            f"**Penulis/Kontributor:** {authors_str}  \n"
            f"**Tags:** {tags_str}  \n\n"
            f"## Ringkasan\n\n{self.summary}\n\n"
            f"---\n*Diambil otomatis oleh SIDIX World Sensor*\n"
        )

    def corpus_filename(self) -> str:
        safe = re.sub(r"[^\w\-]", "_", self.title[:50])
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"sensor_{self.source}_{ts}_{safe}.md"


# ── Novelty Checker ────────────────────────────────────────────────────────────

class NoveltyChecker:
    """Track ID yang sudah pernah diingest agar tidak duplikat."""

    def __init__(self, db_path: Path = _NOVELTY_DB):
        self._path = db_path
        self._seen: set[str] = self._load()

    def _load(self) -> set[str]:
        if self._path.exists():
            try:
                return set(json.loads(self._path.read_text(encoding="utf-8")))
            except Exception:
                return set()
        return set()

    def _save(self) -> None:
        self._path.write_text(
            json.dumps(list(self._seen), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_new(self, signal_id: str) -> bool:
        return signal_id not in self._seen

    def mark_seen(self, signal_id: str) -> None:
        self._seen.add(signal_id)
        self._save()


# ── arXiv Sensor ───────────────────────────────────────────────────────────────

class ArxivSensor:
    """
    Fetch paper terbaru dari arXiv RSS.
    Kategori target: cs.AI, cs.LG, cs.CL, cs.NE, stat.ML
    """

    RSS_BASE = "https://rss.arxiv.org/rss"
    CATEGORIES = ["cs.AI", "cs.LG", "cs.CL"]
    MAX_PER_CATEGORY = 5  # ambil 5 paper per kategori per run

    RELEVANCE_KEYWORDS = [
        "language model", "llm", "fine-tun", "qlora", "lora",
        "continual learning", "federated", "distributed training",
        "retrieval", "rag", "agent", "self-play", "spin",
        "constitutional", "alignment", "reinforcement", "reward",
        "knowledge graph", "graph rag", "indonesian", "arabic",
        "islamic", "multilingual",
    ]

    def fetch(self, max_results: int = 10) -> list[SensorSignal]:
        signals = []
        for cat in self.CATEGORIES:
            try:
                url = f"{self.RSS_BASE}/{cat}"
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    xml_text = resp.read().decode("utf-8", errors="replace")

                signals.extend(self._parse_rss(xml_text, cat))
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                self._log(f"arXiv RSS error ({cat}): {e}")

        # Filter ke yang relevan saja
        relevant = [s for s in signals if self._is_relevant(s)]
        return relevant[:max_results]

    def _parse_rss(self, xml_text: str, category: str) -> list[SensorSignal]:
        signals = []
        try:
            root = ET.fromstring(xml_text)
            ns = {
                "dc": "http://purl.org/dc/elements/1.1/",
            }
            channel = root.find("channel")
            if channel is None:
                return []

            items = channel.findall("item")
            for item in items[:self.MAX_PER_CATEGORY]:
                title_el = item.find("title")
                desc_el = item.find("description")
                link_el = item.find("link")
                date_el = item.find("pubDate")

                title = title_el.text.strip() if title_el is not None else ""
                summary = desc_el.text or "" if desc_el is not None else ""
                # Strip HTML from summary
                summary = re.sub(r"<[^>]+>", "", summary).strip()[:600]
                url = link_el.text.strip() if link_el is not None else ""
                published = date_el.text.strip() if date_el is not None else ""

                # Extract arXiv ID from URL
                arxiv_id = re.search(r"arxiv\.org/abs/(.+?)$", url)
                signal_id = f"arxiv:{arxiv_id.group(1)}" if arxiv_id else f"arxiv:{hash(url)}"

                authors = []
                for creator in item.findall("dc:creator", ns):
                    if creator.text:
                        authors.append(creator.text.strip())

                signals.append(SensorSignal(
                    id=signal_id,
                    source="arxiv",
                    title=title,
                    url=url,
                    summary=summary,
                    authors=authors,
                    tags=[category, "research", "ai"],
                    published=published,
                ))
        except Exception as e:
            self._log(f"RSS parse error: {e}")
        return signals

    def _is_relevant(self, signal: SensorSignal) -> bool:
        text = (signal.title + " " + signal.summary).lower()
        return any(kw in text for kw in self.RELEVANCE_KEYWORDS)

    def _log(self, msg: str) -> None:
        print(f"[ArxivSensor] {msg}")


# ── GitHub Sensor ──────────────────────────────────────────────────────────────

class GitHubSensor:
    """
    Fetch trending GitHub repositories via GitHub Search API (public, no key needed).
    Fokus: AI/ML Python repos dengan star terbaru.
    """

    SEARCH_URL = "https://api.github.com/search/repositories"
    QUERIES = [
        "topic:llm topic:fine-tuning",
        "topic:rag topic:retrieval-augmented",
        "topic:lora topic:peft",
        "topic:continual-learning",
        "topic:ai-agent",
    ]

    def fetch(self, max_results: int = 8) -> list[SensorSignal]:
        signals = []
        # Hanya ambil 1 query per run (rate limit GitHub)
        query = self.QUERIES[int(time.time() / 3600) % len(self.QUERIES)]
        try:
            params = urllib.parse.urlencode({
                "q": query + " language:python",
                "sort": "updated",
                "order": "desc",
                "per_page": max_results,
            })
            url = f"{self.SEARCH_URL}?{params}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for repo in data.get("items", [])[:max_results]:
                repo_id = f"github:{repo['full_name']}"
                signals.append(SensorSignal(
                    id=repo_id,
                    source="github",
                    title=repo.get("full_name", ""),
                    url=repo.get("html_url", ""),
                    summary=(
                        f"{repo.get('description', 'No description')} | "
                        f"Stars: {repo.get('stargazers_count', 0)} | "
                        f"Language: {repo.get('language', 'Unknown')} | "
                        f"Updated: {repo.get('updated_at', '')[:10]}"
                    )[:500],
                    tags=repo.get("topics", [])[:5] + ["github", "tool"],
                    published=repo.get("updated_at", "")[:10],
                ))
        except Exception as e:
            print(f"[GitHubSensor] Error: {e}")
        return signals


# ── MCP Knowledge Bridge ───────────────────────────────────────────────────────

class MCPKnowledgeBridge:
    """
    Bridge dari D:\\SIDIX\\knowledge\\queue\\ ke corpus brain_qa.
    Converts MCP knowledge items -> corpus Markdown files.

    Ini menghubungkan "short-term MCP memory" dengan "long-term BM25 corpus".
    """

    MCP_DIR = Path(r"D:\SIDIX\knowledge\queue")

    def bridge(self, force_all: bool = False) -> int:
        """
        Export semua MCP knowledge items ke corpus.
        Return: jumlah item yang di-export.
        """
        if not self.MCP_DIR.exists():
            print(f"[MCPBridge] Dir tidak ada: {self.MCP_DIR}")
            return 0

        novelty = NoveltyChecker()
        exported = 0

        for json_file in sorted(self.MCP_DIR.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                item_id = f"mcp:{data.get('id', json_file.stem)}"

                if not force_all and not novelty.is_new(item_id):
                    continue

                # Convert ke Markdown corpus
                md = self._to_markdown(data)
                if not md:
                    continue

                # Simpan ke brain/public/sources/web_clips/ (terindeks oleh indexer)
                out_name = f"mcp_{data.get('id', json_file.stem)}.md"
                out_path = _CORPUS_WEB / out_name
                out_path.write_text(md, encoding="utf-8")

                novelty.mark_seen(item_id)
                exported += 1

            except Exception as e:
                print(f"[MCPBridge] Error processing {json_file.name}: {e}")

        return exported

    def _to_markdown(self, data: dict) -> str:
        topic = data.get("topic", "Unknown Topic")
        instruction = data.get("instruction", "")
        output = data.get("output", "")
        tags = ", ".join(data.get("tags", []))
        source = data.get("source", "mcp")
        ts = data.get("timestamp", "")[:10]

        if not output:
            return ""

        return (
            f"# {topic}\n\n"
            f"**Sumber:** {source}  \n"
            f"**Tanggal:** {ts}  \n"
            f"**Tags:** {tags}  \n\n"
            f"## Konteks\n\n{instruction}\n\n"
            f"## Pengetahuan\n\n{output}\n\n"
            f"---\n*Diambil dari SIDIX MCP Knowledge Base*\n"
        )


# ── Benchmark Tracker ─────────────────────────────────────────────────────────

class BenchmarkTracker:
    """
    Track benchmark sederhana lokal — bukan lm-eval-harness (terlalu berat).
    Simpan manual score + deteksi drift dari waktu ke waktu.
    """

    _BENCH_FILE = _SENSOR_DIR / "benchmarks.json"

    def record(self, metric: str, value: float, model: str = "sidix-qwen2.5-7b",
               notes: str = "") -> None:
        data = self._load()
        entry = {
            "metric": metric,
            "value": value,
            "model": model,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        data.setdefault(metric, []).append(entry)
        self._save(data)

    def get_drift(self, metric: str, window: int = 5) -> Optional[float]:
        """
        Hitung drift dari window terakhir.
        Positif = membaik, negatif = degradasi.
        """
        data = self._load()
        entries = data.get(metric, [])[-window:]
        if len(entries) < 2:
            return None
        vals = [e["value"] for e in entries]
        return vals[-1] - vals[0]

    def report(self) -> dict:
        data = self._load()
        report: dict = {}
        for metric, entries in data.items():
            if not entries:
                continue
            recent = entries[-1]["value"]
            drift = self.get_drift(metric)
            report[metric] = {
                "latest": recent,
                "drift": drift,
                "trend": "improving" if (drift or 0) > 0 else "degrading" if (drift or 0) < 0 else "stable",
                "samples": len(entries),
            }
        return report

    def _load(self) -> dict:
        if self._BENCH_FILE.exists():
            try:
                return json.loads(self._BENCH_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save(self, data: dict) -> None:
        self._BENCH_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ── World Sensor Engine ────────────────────────────────────────────────────────

class WorldSensorEngine:
    """
    Orchestrator semua sensor.
    Dijalankan periodik (startup, cron, atau manual via /sensor/run endpoint).
    """

    def __init__(self):
        self._novelty = NoveltyChecker()
        self._arxiv = ArxivSensor()
        self._github = GitHubSensor()
        self._mcp_bridge = MCPKnowledgeBridge()
        self._benchmark = BenchmarkTracker()

    def run(self, sources: Optional[list[str]] = None,
            dry_run: bool = False) -> dict:
        """
        Jalankan semua sensor (atau subset).
        Return: summary {source: count_new}.
        """
        if sources is None:
            sources = ["mcp_bridge", "arxiv", "github"]

        summary: dict = {}
        total_new = 0

        # 1. MCP Bridge (paling penting — koneksikan knowledge base ke corpus)
        if "mcp_bridge" in sources:
            count = self._mcp_bridge.bridge()
            summary["mcp_bridge"] = count
            total_new += count
            print(f"[WorldSensor] MCP Bridge: {count} items exported to corpus")

        # 2. arXiv
        if "arxiv" in sources:
            signals = self._arxiv.fetch(max_results=8)
            new_arxiv = 0
            for sig in signals:
                if self._novelty.is_new(sig.id):
                    if not dry_run:
                        self._ingest_signal(sig)
                    self._novelty.mark_seen(sig.id)
                    new_arxiv += 1
            summary["arxiv"] = new_arxiv
            total_new += new_arxiv
            print(f"[WorldSensor] arXiv: {new_arxiv} new papers")

        # 3. GitHub
        if "github" in sources:
            signals = self._github.fetch(max_results=8)
            new_gh = 0
            for sig in signals:
                if self._novelty.is_new(sig.id):
                    if not dry_run:
                        self._ingest_signal(sig)
                    self._novelty.mark_seen(sig.id)
                    new_gh += 1
            summary["github"] = new_gh
            total_new += new_gh
            print(f"[WorldSensor] GitHub: {new_gh} new repos")

        summary["total_new"] = total_new
        summary["timestamp"] = datetime.now(timezone.utc).isoformat()

        if not dry_run and total_new > 0:
            # Trigger re-index setelah ingest
            self._trigger_reindex()

        self._log_run(summary)
        return summary

    def _ingest_signal(self, signal: SensorSignal) -> None:
        """Simpan signal ke corpus sebagai Markdown."""
        try:
            out_path = _CORPUS_WEB / signal.corpus_filename()
            out_path.write_text(signal.to_corpus_markdown(), encoding="utf-8")
            signal.ingested = True
        except Exception as e:
            print(f"[WorldSensor] Ingest error: {e}")

    def _trigger_reindex(self) -> None:
        """Trigger brain_qa index rebuild (non-blocking)."""
        import subprocess
        import sys
        try:
            brain_qa_dir = workspace_root() / "apps" / "brain_qa"
            subprocess.Popen(
                [sys.executable, "-m", "brain_qa", "index"],
                cwd=str(brain_qa_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("[WorldSensor] Re-index triggered (background)")
        except Exception as e:
            print(f"[WorldSensor] Re-index trigger failed: {e}")

    def _log_run(self, summary: dict) -> None:
        try:
            with open(_SENSOR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def benchmark(self) -> BenchmarkTracker:
        return self._benchmark

    def stats(self) -> dict:
        seen_count = len(self._novelty._seen)
        return {
            "seen_signals": seen_count,
            "mcp_bridge_dir": str(MCPKnowledgeBridge.MCP_DIR),
            "corpus_dir": str(_CORPUS_WEB),
            "sensor_log": str(_SENSOR_LOG),
            "benchmarks": self._benchmark.report(),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_engine: Optional[WorldSensorEngine] = None

def get_sensor_engine() -> WorldSensorEngine:
    global _engine
    if _engine is None:
        _engine = WorldSensorEngine()
    return _engine


def run_sensors(sources: Optional[list[str]] = None, dry_run: bool = False) -> dict:
    """Shorthand untuk dipakai dari endpoints atau cron."""
    return get_sensor_engine().run(sources=sources, dry_run=dry_run)


def bridge_mcp_to_corpus() -> int:
    """Shorthand: bridge D:\\SIDIX\\knowledge -> corpus."""
    return MCPKnowledgeBridge().bridge()
