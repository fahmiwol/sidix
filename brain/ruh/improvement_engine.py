"""
Ruh — Self-Improve System (Pilar 4)

Weekly benchmark + gap analysis + improvement planning.
Evaluasi mingguan performa SIDIX berdasarkan training pairs yang tersimpan.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class TopicStat:
    topic: str
    count: int
    avg_cqf: float
    thumbs_up_count: int
    error_count: int

    @property
    def thumbs_up_ratio(self) -> float:
        if self.count == 0:
            return 0.0
        return round(self.thumbs_up_count / self.count, 3)

    @property
    def error_rate(self) -> float:
        if self.count == 0:
            return 0.0
        return round(self.error_count / self.count, 3)


@dataclass
class WeeklyReport:
    week_label: str          # e.g. "2026-W17"
    start_date: str
    end_date: str
    total_pairs: int
    avg_cqf: float
    thumbs_up_ratio: float
    error_rate: float
    by_topic: list[TopicStat] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Gap:
    topic: str
    avg_cqf: float
    severity: str            # "low" | "medium" | "high"
    pair_count: int

    @property
    def is_critical(self) -> bool:
        return self.avg_cqf < 5.0


@dataclass
class ImprovementAction:
    topic: str
    action_type: str         # more_training_data | prompt_tuning | corpus_update | model_upgrade
    priority: int            # 1 = highest
    rationale: str
    estimated_impact: str    # "low" | "medium" | "high"


@dataclass
class ImprovementPlan:
    week_label: str
    gaps_found: int
    actions: list[ImprovementAction] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: str = ""


# ── RuhImprovementEngine ──────────────────────────────────────────────────────

class RuhImprovementEngine:
    """
    Weekly self-improvement engine untuk SIDIX.

    Membaca JSONL training pairs dari 7 hari terakhir, menghitung CQF rata-rata
    per topik, mendeteksi gap, dan menghasilkan rencana perbaikan.

    Usage:
        ruh = RuhImprovementEngine()
        plan = ruh.run_weekly_eval("data/jiwa_training_pairs")
    """

    CQF_GAP_THRESHOLD = 7.0      # topic below this = gap
    MIN_PAIRS_FOR_EVAL = 5       # minimum pairs before a topic is evaluated
    PLANS_DIR = "data/ruh_plans"

    def __init__(self, plans_dir: str = PLANS_DIR):
        self.plans_dir = Path(plans_dir)
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate_week(self, pairs_dir: str) -> WeeklyReport:
        """
        Load JSONL pairs dari 7 hari terakhir, hitung statistik.

        Args:
            pairs_dir: direktori berisi files pairs_YYYY-MM-DD.jsonl

        Returns:
            WeeklyReport dengan avg CQF, thumbs_up_ratio, by_topic stats
        """
        pairs_path = Path(pairs_dir)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        week_label = now.strftime("%Y-W%W")
        start_date = week_ago.strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        # Load pairs from last 7 days
        all_pairs: list[dict] = []
        for i in range(8):  # 0..7 inclusive
            date = (week_ago + timedelta(days=i)).strftime("%Y-%m-%d")
            f = pairs_path / f"pairs_{date}.jsonl"
            if f.exists():
                pairs = self._load_jsonl(f)
                all_pairs.extend(pairs)

        if not all_pairs:
            logger.info("Ruh: no pairs found for week %s", week_label)
            return WeeklyReport(
                week_label=week_label,
                start_date=start_date,
                end_date=end_date,
                total_pairs=0,
                avg_cqf=0.0,
                thumbs_up_ratio=0.0,
                error_rate=0.0,
            )

        # Aggregate global stats
        total = len(all_pairs)
        sum_cqf = sum(p.get("cqf_score", 0.0) for p in all_pairs)
        thumbs_up = sum(1 for p in all_pairs if p.get("thumbs_up", False))
        errors = sum(1 for p in all_pairs if p.get("is_error", False))

        avg_cqf = round(sum_cqf / total, 3) if total else 0.0
        thumbs_up_ratio = round(thumbs_up / total, 3) if total else 0.0
        error_rate = round(errors / total, 3) if total else 0.0

        # Aggregate by topic
        topic_buckets: dict[str, list[dict]] = {}
        for p in all_pairs:
            topic = p.get("topic", "umum")
            topic_buckets.setdefault(topic, []).append(p)

        by_topic: list[TopicStat] = []
        for topic, pairs in topic_buckets.items():
            count = len(pairs)
            t_avg_cqf = round(sum(p.get("cqf_score", 0.0) for p in pairs) / count, 3)
            t_thumbs = sum(1 for p in pairs if p.get("thumbs_up", False))
            t_errors = sum(1 for p in pairs if p.get("is_error", False))
            by_topic.append(TopicStat(
                topic=topic,
                count=count,
                avg_cqf=t_avg_cqf,
                thumbs_up_count=t_thumbs,
                error_count=t_errors,
            ))

        by_topic.sort(key=lambda s: s.avg_cqf)

        return WeeklyReport(
            week_label=week_label,
            start_date=start_date,
            end_date=end_date,
            total_pairs=total,
            avg_cqf=avg_cqf,
            thumbs_up_ratio=thumbs_up_ratio,
            error_rate=error_rate,
            by_topic=by_topic,
        )

    def detect_gaps(self, report: WeeklyReport) -> list[Gap]:
        """
        Deteksi topic dengan avg CQF < 7.0 sebagai gap.

        Args:
            report: WeeklyReport dari evaluate_week

        Returns:
            list of Gap, sorted by severity (critical first)
        """
        gaps: list[Gap] = []
        for stat in report.by_topic:
            if stat.count < self.MIN_PAIRS_FOR_EVAL:
                continue  # tidak cukup data untuk evaluasi
            if stat.avg_cqf < self.CQF_GAP_THRESHOLD:
                if stat.avg_cqf < 5.0:
                    severity = "high"
                elif stat.avg_cqf < 6.0:
                    severity = "medium"
                else:
                    severity = "low"
                gaps.append(Gap(
                    topic=stat.topic,
                    avg_cqf=stat.avg_cqf,
                    severity=severity,
                    pair_count=stat.count,
                ))

        gaps.sort(key=lambda g: g.avg_cqf)  # worst first
        return gaps

    def generate_improvement_plan(self, gaps: list[Gap]) -> ImprovementPlan:
        """
        Untuk tiap gap, generate action yang sesuai.

        Logika:
        - avg_cqf < 5.0 → model_upgrade (sangat butuh retrain)
        - avg_cqf 5.0-5.9 → more_training_data (butuh lebih banyak contoh)
        - avg_cqf 6.0-6.4 → corpus_update (butuh dokumen referensi lebih baik)
        - avg_cqf 6.5-6.9 → prompt_tuning (perlu penyesuaian system prompt/persona)
        """
        week_label = datetime.utcnow().strftime("%Y-W%W")
        actions: list[ImprovementAction] = []
        priority = 1

        for gap in gaps:
            action_type, rationale, impact = self._decide_action(gap)
            actions.append(ImprovementAction(
                topic=gap.topic,
                action_type=action_type,
                priority=priority,
                rationale=rationale,
                estimated_impact=impact,
            ))
            priority += 1

        notes = (
            f"Total gaps detected: {len(gaps)}. "
            f"Generated: {datetime.utcnow().isoformat()}"
        )

        return ImprovementPlan(
            week_label=week_label,
            gaps_found=len(gaps),
            actions=actions,
            notes=notes,
        )

    def run_weekly_eval(self, pairs_dir: str) -> ImprovementPlan:
        """
        Full pipeline: evaluate → detect gaps → generate plan → save.

        Args:
            pairs_dir: direktori berisi JSONL pairs

        Returns:
            ImprovementPlan yang sudah disimpan
        """
        logger.info("Ruh: starting weekly evaluation from %s", pairs_dir)

        report = self.evaluate_week(pairs_dir)
        logger.info(
            "Ruh: week %s — %d pairs, avg CQF %.2f, error_rate %.3f",
            report.week_label, report.total_pairs, report.avg_cqf, report.error_rate,
        )

        gaps = self.detect_gaps(report)
        logger.info("Ruh: %d gap(s) detected", len(gaps))

        plan = self.generate_improvement_plan(gaps)
        self._save_plan(plan)

        return plan

    # ── Private helpers ───────────────────────────────────────────────────────

    def _decide_action(self, gap: Gap) -> tuple[str, str, str]:
        """Return (action_type, rationale, estimated_impact)."""
        cqf = gap.avg_cqf
        topic = gap.topic

        if cqf < 5.0:
            return (
                "model_upgrade",
                f"Topic '{topic}' memiliki CQF {cqf:.1f} — sangat rendah. "
                "Diperlukan LoRA retrain dengan data yang lebih berkualitas.",
                "high",
            )
        elif cqf < 6.0:
            return (
                "more_training_data",
                f"Topic '{topic}' memiliki CQF {cqf:.1f}. "
                "Perlu lebih banyak training pairs berkualitas tinggi.",
                "high",
            )
        elif cqf < 6.5:
            return (
                "corpus_update",
                f"Topic '{topic}' memiliki CQF {cqf:.1f}. "
                "Update corpus dengan dokumen referensi yang lebih akurat.",
                "medium",
            )
        else:
            return (
                "prompt_tuning",
                f"Topic '{topic}' memiliki CQF {cqf:.1f}. "
                "Penyesuaian system prompt atau persona untuk topik ini.",
                "low",
            )

    def _load_jsonl(self, path: Path) -> list[dict]:
        """Load JSONL file, skip invalid lines."""
        records = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning("Ruh: invalid JSON line in %s", path)
        except OSError as e:
            logger.warning("Ruh: cannot read %s: %s", path, e)
        return records

    def _save_plan(self, plan: ImprovementPlan) -> None:
        """Save improvement plan ke data/ruh_plans/plan_YYYY-WW.json."""
        filename = f"plan_{plan.week_label.replace('-', '_')}.json"
        path = self.plans_dir / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(plan), f, ensure_ascii=False, indent=2)
            logger.info("Ruh: plan saved to %s", path)
        except OSError as e:
            logger.error("Ruh: cannot save plan: %s", e)

    def load_latest_plan(self) -> Optional[ImprovementPlan]:
        """Load rencana perbaikan terbaru jika ada."""
        plans = sorted(self.plans_dir.glob("plan_*.json"))
        if not plans:
            return None
        latest = plans[-1]
        try:
            with open(latest, encoding="utf-8") as f:
                data = json.load(f)
            actions = [ImprovementAction(**a) for a in data.get("actions", [])]
            return ImprovementPlan(
                week_label=data["week_label"],
                gaps_found=data["gaps_found"],
                actions=actions,
                generated_at=data.get("generated_at", ""),
                notes=data.get("notes", ""),
            )
        except Exception as e:
            logger.warning("Ruh: cannot load latest plan: %s", e)
            return None
