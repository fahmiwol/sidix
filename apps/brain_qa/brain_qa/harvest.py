"""
harvest.py — SIDIX Conversation Harvester

Tujuan: Tangkap setiap Q&A yang dilakukan SIDIX → konversi ke training pairs.
Ini adalah "feedback loop penutup" dari siklus belajar SIDIX:

    User tanya → SIDIX jawab → harvest.py simpan → corpus_to_training.py
    → fine-tune batch → LoRA adapter baru → SIDIX lebih pintar

Pipeline:
    1. `harvest_session(session)` — dipanggil otomatis dari agent_serve.py setelah setiap jawaban
    2. Simpan ke .data/harvest/sessions.jsonl
    3. `export_training_pairs(min_quality=0.6)` → generate Alpaca/ShareGPT format
    4. Batch upload ke Kaggle tiap 7 hari

Format harvest record:
    {
      "id": "uuid",
      "timestamp": "ISO8601",
      "question": "...",
      "answer": "...",
      "persona": "...",
      "confidence_score": 0.85,
      "answer_type": "fakta|opini|spekulasi",
      "citations": [...],
      "quality_score": 0.0-1.0,  # computed
      "flagged": false,           # manual review flag
      "used_for_training": false  # sudah dipakai?
    }

Quality scoring:
    - confidence_score > 0.7: +0.3
    - answer_type == "fakta": +0.2
    - len(answer) > 200: +0.2
    - ada citations: +0.2
    - len(question) > 20: +0.1
    - Total max: 1.0
"""

from __future__ import annotations

import json
import uuid
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .paths import BRAIN_QA_DATA_DIR

logger = logging.getLogger("sidix.harvest")

# ── Paths ─────────────────────────────────────────────────────────────────────
HARVEST_DIR = BRAIN_QA_DATA_DIR / "harvest"
HARVEST_SESSIONS_FILE = HARVEST_DIR / "sessions.jsonl"
HARVEST_TRAINING_DIR = HARVEST_DIR / "training_pairs"

HARVEST_DIR.mkdir(parents=True, exist_ok=True)
HARVEST_TRAINING_DIR.mkdir(parents=True, exist_ok=True)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class HarvestRecord:
    id: str
    timestamp: str
    question: str
    answer: str
    persona: str
    confidence_score: float
    answer_type: str          # fakta | opini | spekulasi
    citations: list
    quality_score: float
    flagged: bool = False
    used_for_training: bool = False
    session_id: str = ""
    user_language: str = ""
    user_literacy: str = ""
    epistemic_tier: str = ""
    maqashid_score: float = 0.0
    steps_count: int = 0
    tags: list = field(default_factory=list)


# ── Quality scoring ───────────────────────────────────────────────────────────

def compute_quality_score(
    question: str,
    answer: str,
    confidence_score: float,
    answer_type: str,
    citations: list,
) -> float:
    """Hitung quality score 0.0-1.0 untuk sebuah Q&A pair."""
    score = 0.0

    # Confidence dari agent
    if confidence_score >= 0.8:
        score += 0.3
    elif confidence_score >= 0.6:
        score += 0.2
    elif confidence_score >= 0.4:
        score += 0.1

    # Answer type
    if answer_type == "fakta":
        score += 0.2
    elif answer_type == "opini":
        score += 0.1

    # Panjang jawaban
    answer_len = len(answer.strip())
    if answer_len >= 300:
        score += 0.2
    elif answer_len >= 100:
        score += 0.1

    # Ada citations
    if citations and len(citations) > 0:
        score += 0.2

    # Panjang pertanyaan (bukan junk)
    if len(question.strip()) >= 20:
        score += 0.1

    return min(1.0, round(score, 3))


# ── Core harvester ────────────────────────────────────────────────────────────

class ConversationHarvester:
    """
    Tangkap setiap session SIDIX → simpan → export training pairs.

    Singleton via get_harvester().
    """

    def __init__(self):
        self._count: int = 0
        self._high_quality: int = 0

    def harvest_session(self, session_data: dict) -> Optional[HarvestRecord]:
        """
        Tangkap satu AgentSession sebagai HarvestRecord.

        `session_data` adalah dict dari AgentSession (via asdict atau .to_dict()).
        Return None jika tidak layak disimpan.
        """
        question = (session_data.get("question") or "").strip()
        answer = (session_data.get("final_answer") or "").strip()

        # Filter: skip kosong / blocked
        if not question or not answer:
            return None
        if len(answer) < 20:
            return None
        if "diblokir" in (session_data.get("confidence") or ""):
            return None
        # Skip cache hits (bukan interaksi baru)
        if session_data.get("confidence") == "cache singkat":
            return None

        confidence_score = float(session_data.get("confidence_score") or 0.0)
        answer_type = session_data.get("answer_type") or "fakta"
        citations = session_data.get("citations") or []
        persona = session_data.get("persona") or "INAN"

        quality = compute_quality_score(
            question=question,
            answer=answer,
            confidence_score=confidence_score,
            answer_type=answer_type,
            citations=citations,
        )

        record = HarvestRecord(
            id=str(uuid.uuid4())[:12],
            timestamp=datetime.now(timezone.utc).isoformat(),
            question=question,
            answer=answer,
            persona=persona,
            confidence_score=confidence_score,
            answer_type=answer_type,
            citations=citations[:5],  # max 5 citations
            quality_score=quality,
            session_id=session_data.get("session_id") or "",
            user_language=session_data.get("user_language") or "",
            user_literacy=session_data.get("user_literacy") or "",
            epistemic_tier=session_data.get("epistemic_tier") or "",
            maqashid_score=float(session_data.get("maqashid_score") or 0.0),
            steps_count=len(session_data.get("steps") or []),
            tags=_auto_tag(question, answer, persona),
        )

        # Simpan ke JSONL
        self._append_record(record)
        self._count += 1
        if quality >= 0.6:
            self._high_quality += 1

        logger.debug(
            f"[Harvest] {record.id} | Q: {question[:50]!r} | "
            f"quality={quality:.2f} | type={answer_type}"
        )
        return record

    def _append_record(self, record: HarvestRecord) -> None:
        """Append satu record ke sessions.jsonl."""
        d = asdict(record)
        with open(HARVEST_SESSIONS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    def load_records(
        self,
        min_quality: float = 0.0,
        unused_only: bool = False,
        limit: int = 0,
    ) -> list[HarvestRecord]:
        """Load records dari JSONL dengan filter."""
        records: list[HarvestRecord] = []
        if not HARVEST_SESSIONS_FILE.exists():
            return records

        with open(HARVEST_SESSIONS_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    r = HarvestRecord(**{k: d.get(k, v) for k, v in asdict(HarvestRecord(
                        id="", timestamp="", question="", answer="",
                        persona="", confidence_score=0.0, answer_type="",
                        citations=[], quality_score=0.0,
                    )).items()})
                    if r.quality_score < min_quality:
                        continue
                    if unused_only and r.used_for_training:
                        continue
                    records.append(r)
                except Exception:
                    continue

        if limit > 0:
            records = records[-limit:]
        return records

    def export_training_pairs(
        self,
        min_quality: float = 0.6,
        format: str = "alpaca",  # "alpaca" | "sharegpt" | "plain"
        output_file: Optional[str] = None,
    ) -> dict:
        """
        Export records sebagai training pairs untuk fine-tuning.

        Alpaca format:
            {"instruction": Q, "input": "", "output": A}

        ShareGPT format:
            {"conversations": [{"from": "human", "value": Q}, {"from": "gpt", "value": A}]}

        Plain format:
            {"question": Q, "answer": A, "persona": P}
        """
        records = self.load_records(min_quality=min_quality, unused_only=True)
        if not records:
            return {"exported": 0, "file": None, "message": "Tidak ada record baru yang layak"}

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        if output_file is None:
            fname = f"training_{format}_{timestamp}.jsonl"
            out_path = HARVEST_TRAINING_DIR / fname
        else:
            out_path = Path(output_file)

        exported = 0
        with open(out_path, "w", encoding="utf-8") as f:
            for r in records:
                if format == "alpaca":
                    row = {
                        "instruction": r.question,
                        "input": "",
                        "output": r.answer,
                        "persona": r.persona,
                        "quality": r.quality_score,
                    }
                elif format == "sharegpt":
                    row = {
                        "conversations": [
                            {"from": "human", "value": r.question},
                            {"from": "gpt", "value": r.answer},
                        ],
                        "persona": r.persona,
                    }
                else:
                    row = {
                        "question": r.question,
                        "answer": r.answer,
                        "persona": r.persona,
                        "quality": r.quality_score,
                    }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                exported += 1

        # Mark as used
        self._mark_used(records)

        logger.info(f"[Harvest] Exported {exported} pairs → {out_path}")
        return {
            "exported": exported,
            "file": str(out_path),
            "format": format,
            "min_quality": min_quality,
        }

    def _mark_used(self, records: list[HarvestRecord]) -> None:
        """Tandai records sebagai sudah dipakai untuk training."""
        ids_to_mark = {r.id for r in records}
        all_lines: list[str] = []

        if HARVEST_SESSIONS_FILE.exists():
            with open(HARVEST_SESSIONS_FILE, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get("id") in ids_to_mark:
                            d["used_for_training"] = True
                        all_lines.append(json.dumps(d, ensure_ascii=False))
                    except Exception:
                        all_lines.append(line)

        with open(HARVEST_SESSIONS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(all_lines) + "\n")

    def flag_record(self, record_id: str, reason: str = "") -> bool:
        """Flag record untuk manual review (jawaban buruk / berbahaya)."""
        lines: list[str] = []
        found = False
        if not HARVEST_SESSIONS_FILE.exists():
            return False

        with open(HARVEST_SESSIONS_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if d.get("id") == record_id:
                        d["flagged"] = True
                        if reason:
                            d["flag_reason"] = reason
                        found = True
                    lines.append(json.dumps(d, ensure_ascii=False))
                except Exception:
                    lines.append(line)

        if found:
            with open(HARVEST_SESSIONS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        return found

    def stats(self) -> dict:
        """Statistik harvest."""
        total = 0
        high_q = 0
        unused = 0
        flagged = 0
        by_persona: dict[str, int] = {}

        if HARVEST_SESSIONS_FILE.exists():
            with open(HARVEST_SESSIONS_FILE, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        total += 1
                        q = d.get("quality_score", 0.0)
                        if q >= 0.6:
                            high_q += 1
                        if not d.get("used_for_training"):
                            unused += 1
                        if d.get("flagged"):
                            flagged += 1
                        p = d.get("persona", "INAN")
                        by_persona[p] = by_persona.get(p, 0) + 1
                    except Exception:
                        continue

        training_files = list(HARVEST_TRAINING_DIR.glob("training_*.jsonl"))

        return {
            "total_harvested": total,
            "high_quality": high_q,
            "unused_for_training": unused,
            "flagged": flagged,
            "by_persona": by_persona,
            "training_files": len(training_files),
            "harvest_file": str(HARVEST_SESSIONS_FILE),
        }

    def recent(self, n: int = 10) -> list[dict]:
        """N records terbaru."""
        records = self.load_records(limit=n)
        return [asdict(r) for r in records[-n:]]


# ── Auto-tagging ──────────────────────────────────────────────────────────────

_TAG_KEYWORDS: dict[str, list[str]] = {
    "programming": ["python", "code", "bug", "error", "function", "class", "import"],
    "ai-ml": ["model", "llm", "fine-tune", "training", "dataset", "neural", "transformer"],
    "islamic": ["islam", "quran", "hadis", "fiqh", "aqidah", "maqashid", "halal", "haram"],
    "epistemology": ["epistemic", "sanad", "tabayyun", "yaqin", "mutawatir", "ihos"],
    "indonesia": ["indonesia", "surabaya", "jakarta", "bahasa", "nusantara"],
    "deployment": ["deploy", "vps", "server", "docker", "pm2", "nginx", "supabase"],
    "math": ["hitung", "calculate", "+", "-", "*", "/", "persen", "integral"],
    "question-answer": ["apa", "bagaimana", "mengapa", "kapan", "siapa", "jelaskan"],
}


def _auto_tag(question: str, answer: str, persona: str) -> list[str]:
    """Auto-detect tags dari konten Q&A."""
    text = (question + " " + answer).lower()
    tags: list[str] = [persona.lower()]

    for tag, keywords in _TAG_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)

    return list(set(tags))


# ── Singleton ─────────────────────────────────────────────────────────────────

_harvester_instance: Optional[ConversationHarvester] = None


def get_harvester() -> ConversationHarvester:
    global _harvester_instance
    if _harvester_instance is None:
        _harvester_instance = ConversationHarvester()
    return _harvester_instance


# ── Shorthand API ─────────────────────────────────────────────────────────────

def harvest_session(session_data: dict) -> Optional[HarvestRecord]:
    """Shorthand: harvest satu session. Panggil dari agent_serve.py."""
    return get_harvester().harvest_session(session_data)


def export_training(
    min_quality: float = 0.6,
    format: str = "alpaca",
) -> dict:
    """Shorthand: export training pairs."""
    return get_harvester().export_training_pairs(min_quality=min_quality, format=format)
