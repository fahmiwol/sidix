"""
Ilm — Self-Crawl System (Pilar 6)

Knowledge gap detection → web crawl → corpus queue.
Mengisi celah pengetahuan SIDIX secara otomatis dari sumber terbuka.

Sumber yang digunakan (tidak perlu API key):
- Wikipedia REST API (free, no auth)
- arXiv API (free, no auth)
"""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
WIKIPEDIA_ID_API = "https://id.wikipedia.org/api/rest_v1/page/summary/{title}"
ARXIV_API = "https://export.arxiv.org/api/query?search_query=all:{query}&max_results=3"

REQUEST_TIMEOUT = 15  # seconds
MAX_CONTENT_CHARS = 3000  # truncate long content
USER_AGENT = "SIDIX-Ilm-Crawler/1.0 (https://sidixlab.com; educational-bot)"


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class CrawlResult:
    topic: str
    source: str          # "wikipedia_en" | "wikipedia_id" | "arxiv" | "error"
    title: str
    content: str
    url: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    word_count: int = 0

    def __post_init__(self):
        if not self.word_count:
            self.word_count = len(self.content.split())


# ── IlmCrawlingEngine ─────────────────────────────────────────────────────────

class IlmCrawlingEngine:
    """
    Self-crawl engine SIDIX untuk mengisi celah pengetahuan.

    Usage:
        ilm = IlmCrawlingEngine()
        ilm.run_crawl_cycle(
            pairs_dir="data/jiwa_training_pairs",
            corpus_queue_dir="data/corpus_queue",
        )
    """

    CQF_GAP_THRESHOLD = 7.0
    MIN_PAIRS_FOR_GAP = 3

    def __init__(self, corpus_queue_dir: str = "data/corpus_queue"):
        self.corpus_queue_dir = Path(corpus_queue_dir)
        self.corpus_queue_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_gaps_from_pairs(self, pairs_dir: str) -> list[str]:
        """
        Deteksi topic dengan avg CQF < 7.0 dari JSONL training pairs.

        Args:
            pairs_dir: direktori berisi files pairs_*.jsonl

        Returns:
            list of topic strings yang perlu diperkuat
        """
        pairs_path = Path(pairs_dir)
        topic_cqf: dict[str, list[float]] = {}

        for jsonl_file in sorted(pairs_path.glob("pairs_*.jsonl")):
            try:
                with open(jsonl_file, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            topic = record.get("topic", "umum")
                            cqf = float(record.get("cqf_score", 0.0))
                            topic_cqf.setdefault(topic, []).append(cqf)
                        except (json.JSONDecodeError, ValueError):
                            pass
            except OSError:
                pass

        gaps: list[str] = []
        for topic, scores in topic_cqf.items():
            if len(scores) < self.MIN_PAIRS_FOR_GAP:
                continue
            avg = sum(scores) / len(scores)
            if avg < self.CQF_GAP_THRESHOLD:
                logger.debug("Ilm: gap detected — topic='%s' avg_cqf=%.2f", topic, avg)
                gaps.append(topic)

        return gaps

    def crawl_topic(self, topic: str) -> list[CrawlResult]:
        """
        Crawl informasi dari Wikipedia (ID & EN) dan arXiv untuk topik ini.

        Args:
            topic: nama topik yang akan di-crawl

        Returns:
            list CrawlResult dari berbagai sumber
        """
        results: list[CrawlResult] = []

        # Wikipedia Indonesia
        wiki_id = self._fetch_wikipedia(topic, lang="id")
        if wiki_id:
            results.append(wiki_id)
            time.sleep(0.5)

        # Wikipedia English
        wiki_en = self._fetch_wikipedia(topic, lang="en")
        if wiki_en:
            results.append(wiki_en)
            time.sleep(0.5)

        # arXiv (cocok untuk topik teknis/ilmiah)
        if self._is_technical_topic(topic):
            arxiv_results = self._fetch_arxiv(topic)
            results.extend(arxiv_results)

        logger.info("Ilm: crawled topic='%s' → %d result(s)", topic, len(results))
        return results

    def queue_for_corpus(self, results: list[CrawlResult], output_dir: Optional[str] = None) -> None:
        """
        Simpan CrawlResult ke corpus queue JSONL untuk diproses lebih lanjut.

        Args:
            results: list CrawlResult dari crawl_topic
            output_dir: override direktori output (optional)
        """
        out_dir = Path(output_dir) if output_dir else self.corpus_queue_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        output_path = out_dir / f"crawl_queue_{date_str}.jsonl"

        saved = 0
        try:
            with open(output_path, "a", encoding="utf-8") as f:
                for result in results:
                    if not result.content.strip():
                        continue
                    f.write(json.dumps(asdict(result), ensure_ascii=False) + "\n")
                    saved += 1
        except OSError as e:
            logger.error("Ilm: cannot write queue: %s", e)
            return

        logger.info("Ilm: queued %d/%d results to %s", saved, len(results), output_path)

    def run_crawl_cycle(self, pairs_dir: str, corpus_queue_dir: Optional[str] = None) -> None:
        """
        Full pipeline: detect gaps → crawl → queue.

        Args:
            pairs_dir: direktori berisi JSONL pairs training
            corpus_queue_dir: direktori untuk menyimpan hasil crawl
        """
        logger.info("Ilm: starting crawl cycle")

        gaps = self.detect_gaps_from_pairs(pairs_dir)
        logger.info("Ilm: %d gap topic(s) to crawl: %s", len(gaps), gaps)

        if not gaps:
            logger.info("Ilm: no gaps detected, crawl cycle done")
            return

        all_results: list[CrawlResult] = []
        for topic in gaps:
            results = self.crawl_topic(topic)
            all_results.extend(results)
            time.sleep(1.0)  # polite crawl delay

        self.queue_for_corpus(all_results, corpus_queue_dir)
        logger.info("Ilm: crawl cycle complete — %d results queued", len(all_results))

    # ── Private: Wikipedia fetch ──────────────────────────────────────────────

    def _fetch_wikipedia(self, topic: str, lang: str = "en") -> Optional[CrawlResult]:
        """Fetch Wikipedia summary via REST API."""
        # Normalize topic to Wikipedia title format
        title = topic.replace(" ", "_").capitalize()

        if lang == "id":
            url = WIKIPEDIA_ID_API.format(title=urllib.parse.quote(title))
            source = "wikipedia_id"
        else:
            url = WIKIPEDIA_API.format(title=urllib.parse.quote(title))
            source = "wikipedia_en"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))

            title_found = data.get("title", topic)
            extract = data.get("extract", "").strip()

            if not extract:
                return None

            content = extract[:MAX_CONTENT_CHARS]
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page", url)

            return CrawlResult(
                topic=topic,
                source=source,
                title=title_found,
                content=content,
                url=page_url,
            )

        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug("Ilm: Wikipedia %s not found for '%s'", lang, topic)
            else:
                logger.warning("Ilm: Wikipedia %s error %d for '%s'", lang, e.code, topic)
            return None
        except Exception as e:
            logger.warning("Ilm: Wikipedia %s fetch failed for '%s': %s", lang, topic, e)
            return None

    # ── Private: arXiv fetch ──────────────────────────────────────────────────

    def _fetch_arxiv(self, topic: str) -> list[CrawlResult]:
        """Fetch arXiv paper summaries via Atom API."""
        query = urllib.parse.quote(topic)
        url = ARXIV_API.format(query=query)
        results: list[CrawlResult] = []

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                xml_data = response.read().decode("utf-8")

            # Simple XML parsing without external libraries
            entries = self._parse_arxiv_xml(xml_data, topic)
            results.extend(entries)

        except Exception as e:
            logger.warning("Ilm: arXiv fetch failed for '%s': %s", topic, e)

        return results

    def _parse_arxiv_xml(self, xml: str, topic: str) -> list[CrawlResult]:
        """Parse arXiv Atom XML — simple regex-based, no lxml needed."""
        import re
        results = []

        entries = re.findall(r"<entry>(.*?)</entry>", xml, re.DOTALL)
        for entry in entries:
            title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
            summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
            id_m = re.search(r"<id>(.*?)</id>", entry)

            if not (title_m and summary_m):
                continue

            title = title_m.group(1).strip()
            summary = summary_m.group(1).strip()[:MAX_CONTENT_CHARS]
            arxiv_url = id_m.group(1).strip() if id_m else "https://arxiv.org"

            results.append(CrawlResult(
                topic=topic,
                source="arxiv",
                title=title,
                content=summary,
                url=arxiv_url,
            ))

        return results

    @staticmethod
    def _is_technical_topic(topic: str) -> bool:
        """Tentukan apakah topik cocok untuk crawl arXiv."""
        technical_keywords = {
            "koding", "coding", "machine learning", "deep learning", "neural",
            "nlp", "llm", "transformers", "python", "algorithm", "data science",
            "computer vision", "reinforcement", "ai", "artificial intelligence",
        }
        topic_lower = topic.lower()
        return any(kw in topic_lower for kw in technical_keywords)
