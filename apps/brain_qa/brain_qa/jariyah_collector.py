"""
Jariyah Collector — SIDIX Sprint 8c
Capture feedback user → JSONL training pairs untuk LoRA retrain.

Rating convention:
  1  = thumbs up (positive)
 -1  = thumbs down (negative)
  0  = no rating
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

PAIRS_PATH = Path("data/jariyah_pairs.jsonl")
PREMIUM_THRESHOLD = 0.85


def capture_feedback(
    query: str,
    response: str,
    rating: int,
    persona: str = "UTZ",
    session_id: str = "",
    score: float | None = None,
) -> dict:
    """
    Append satu training pair ke JSONL.

    Returns dict dengan status dan path file.
    Rating: 1 = thumbs_up, -1 = thumbs_down, 0 = none.
    """
    query = (query or "").strip()
    response = (response or "").strip()
    if not query or not response:
        return {"ok": False, "reason": "query/response kosong"}

    pair = {
        "query": query,
        "response": response,
        "rating": rating,
        "persona": persona,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if score is not None:
        pair["score"] = round(float(score), 4)

    PAIRS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PAIRS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    logger.info("Jariyah pair captured — rating=%s session=%s", rating, session_id or "-")
    return {"ok": True, "path": str(PAIRS_PATH), "rating": rating}


def get_pairs_count() -> int:
    """Hitung jumlah training pair yang sudah terkumpul."""
    if not PAIRS_PATH.exists():
        return 0
    try:
        with open(PAIRS_PATH, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


def get_pairs_stats() -> dict:
    """Statistik training pairs: total, thumbs_up, thumbs_down, no_rating."""
    if not PAIRS_PATH.exists():
        return {"total": 0, "thumbs_up": 0, "thumbs_down": 0, "no_rating": 0}

    total = thumbs_up = thumbs_down = no_rating = 0
    try:
        with open(PAIRS_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    pair = json.loads(line)
                    total += 1
                    r = pair.get("rating", 0)
                    if r == 1:
                        thumbs_up += 1
                    elif r == -1:
                        thumbs_down += 1
                    else:
                        no_rating += 1
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass

    return {
        "total": total,
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "no_rating": no_rating,
        "path": str(PAIRS_PATH),
    }
