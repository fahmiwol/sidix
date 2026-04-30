"""
Aql — Self-Learn System (Pilar 2) — Jariyah v2.0

Pipeline: Capture → CQF Score → Validate → Extract → Store
CQF threshold: ≥7.0 untuk disimpan, ≥9.0 untuk auto-promote ke corpus
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── CQF Rubric (10 criteria, each 0-1) ───────────────────────────────────────

CQF_CRITERIA = [
    "kejelasan",        # apakah jawaban jelas dan mudah dipahami
    "kelengkapan",      # apakah menjawab pertanyaan sepenuhnya
    "akurasi",          # apakah faktanya benar (estimasi)
    "relevansi",        # apakah relevan dengan pertanyaan
    "koherensi",        # apakah alur logis
    "sanad",            # apakah ada sumber/sanad yang bisa diverifikasi
    "bahasa",           # apakah bahasa tepat dan baku
    "originalitas",     # apakah bukan copy-paste verbatim
    "etika",            # apakah tidak melanggar nilai etika/maqashid
    "kedalaman",        # apakah ada insight mendalam, bukan permukaan saja
]


@dataclass
class InteractionRecord:
    question: str
    answer: str
    persona: str
    topic: str
    platform: str
    cqf_score: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    validated: bool = False
    promoted: bool = False
    criteria_scores: dict = field(default_factory=dict)
    entities: list[str] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)


@dataclass
class AqlStats:
    total_captured: int = 0
    total_saved: int = 0
    total_promoted: int = 0
    total_rejected: int = 0
    avg_cqf: float = 0.0


# ── AqlLearningLoop ───────────────────────────────────────────────────────────

class AqlLearningLoop:
    """
    Jariyah v2: every good interaction becomes a training pair.

    Usage (fire-and-forget):
        aql = AqlLearningLoop(storage_dir="data/jiwa_training_pairs")
        aql.capture(question=..., answer=..., persona=..., cqf_score=7.5)
    """

    SAVE_THRESHOLD = 7.0
    PROMOTE_THRESHOLD = 9.0

    def __init__(
        self,
        storage_dir: str = "data/jiwa_training_pairs",
        kg_insert_fn=None,
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.kg_insert_fn = kg_insert_fn  # optional KG integration
        self.stats = AqlStats()
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def capture(
        self,
        *,
        question: str,
        answer: str,
        persona: str = "UTZ",
        topic: str = "umum",
        platform: str = "api",
        cqf_score: float,
        blocking: bool = False,
    ) -> None:
        if blocking:
            self._process(question, answer, persona, topic, platform, cqf_score)
        else:
            t = threading.Thread(
                target=self._process,
                args=(question, answer, persona, topic, platform, cqf_score),
                daemon=True,
            )
            t.start()

    def get_stats(self) -> AqlStats:
        return self.stats

    # ── Processing pipeline ───────────────────────────────────────────────────

    def _process(
        self,
        question: str,
        answer: str,
        persona: str,
        topic: str,
        platform: str,
        cqf_score: float,
    ) -> None:
        with self._lock:
            self.stats.total_captured += 1

        if cqf_score < self.SAVE_THRESHOLD:
            with self._lock:
                self.stats.total_rejected += 1
            logger.debug("Aql: rejected (CQF %.1f < %.1f)", cqf_score, self.SAVE_THRESHOLD)
            return

        record = InteractionRecord(
            question=question,
            answer=answer,
            persona=persona,
            topic=topic,
            platform=platform,
            cqf_score=cqf_score,
            criteria_scores=self._estimate_criteria(question, answer, cqf_score),
            entities=self._extract_entities(question + " " + answer),
        )

        record.validated = self._validate(record)
        if cqf_score >= self.PROMOTE_THRESHOLD:
            record.promoted = True

        self._save(record)

        if self.kg_insert_fn and record.validated:
            try:
                self.kg_insert_fn(record)
            except Exception as e:
                logger.warning("Aql: KG insert failed: %s", e)

        with self._lock:
            self.stats.total_saved += 1
            if record.promoted:
                self.stats.total_promoted += 1
            n = self.stats.total_saved
            self.stats.avg_cqf = (
                (self.stats.avg_cqf * (n - 1) + cqf_score) / n
            )

    # ── CQF estimation ────────────────────────────────────────────────────────

    def _estimate_criteria(self, question: str, answer: str, cqf: float) -> dict[str, float]:
        base = cqf / 10.0
        return {c: round(base + (hash(c + question) % 3 - 1) * 0.05, 2) for c in CQF_CRITERIA}

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate(self, record: InteractionRecord) -> bool:
        if len(record.answer) < 30:
            return False
        if record.question.strip() == record.answer.strip():
            return False
        return True

    # ── Entity extraction (simple keyword-based) ──────────────────────────────

    def _extract_entities(self, text: str) -> list[str]:
        words = text.split()
        return [w for w in words if len(w) > 4 and w[0].isupper()][:10]

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self, record: InteractionRecord) -> None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        path = self.storage_dir / f"pairs_{date_str}.jsonl"
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.error("Aql: save failed: %s", e)

    # ── Daily summary ─────────────────────────────────────────────────────────

    def daily_summary(self) -> dict:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        path = self.storage_dir / f"pairs_{date_str}.jsonl"
        count = 0
        if path.exists():
            with open(path, encoding="utf-8") as f:
                count = sum(1 for _ in f)
        return {
            "date": date_str,
            "pairs_today": count,
            "stats": asdict(self.stats),
        }
