"""
Jariyah Exporter — konversi feedback pairs ke format LoRA training.

Export dari data/jariyah_pairs.jsonl → output/jariyah_lora_YYYYMMDD.jsonl
Format LoRA output: {"messages": [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}

Filter: hanya pairs dengan rating thumbs_up atau score >= 0.7
"""
from __future__ import annotations

import json
import datetime
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PAIRS_PATH = Path("data/jariyah_pairs.jsonl")
OUTPUT_DIR = Path("output")
LORA_READY_THRESHOLD = 500

SIDIX_SYSTEM_MESSAGE = (
    "Kamu adalah SIDIX, AI generative agent berbasis Qwen2.5-7B dengan LoRA adapter. "
    "Kamu menjawab dengan jujur, bersumber, dan bisa diverifikasi. "
    "Gunakan label epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN] bila relevan. "
    "Bahasa default: Bahasa Indonesia, kecuali user pakai bahasa lain."
)


def get_exportable_pairs(
    min_score: float = 0.7,
    rating_filter: str = "thumbs_up",
) -> list[dict]:
    """
    Baca data/jariyah_pairs.jsonl dan filter pair yang layak untuk LoRA training.

    Filter: rating == 1 (thumbs_up) ATAU score >= min_score.
    Pair dengan query/response kosong selalu di-skip.

    Args:
        min_score: Minimum score threshold (default 0.7).
        rating_filter: Tipe rating yang diterima (default "thumbs_up" = rating 1).

    Returns:
        List dict pair yang lolos filter.
    """
    if not PAIRS_PATH.exists():
        logger.info("Jariyah pairs file tidak ada: %s", PAIRS_PATH)
        return []

    exportable: list[dict] = []
    try:
        with open(PAIRS_PATH, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    pair = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Baris %d: JSON tidak valid, dilewati", lineno)
                    continue

                # Validasi field wajib
                query = (pair.get("query") or "").strip()
                response = (pair.get("response") or "").strip()
                if not query or not response:
                    continue

                rating = pair.get("rating", 0)
                score = pair.get("score")

                # Filter: thumbs_up (rating==1) ATAU score >= threshold
                is_thumbs_up = (rating == 1)
                is_high_score = (score is not None and float(score) >= min_score)

                if is_thumbs_up or is_high_score:
                    exportable.append(pair)

    except OSError as e:
        logger.error("Gagal membaca %s: %s", PAIRS_PATH, e)

    return exportable


def export_to_lora_jsonl(
    output_path: Optional[Path] = None,
    min_score: float = 0.7,
) -> dict:
    """
    Export pairs ke format LoRA JSONL.

    Setiap entry output:
    {
      "messages": [
        {"role": "system",    "content": "<SIDIX system prompt>"},
        {"role": "user",      "content": "<query>"},
        {"role": "assistant", "content": "<response>"}
      ]
    }

    Args:
        output_path: Path output (opsional). Default: output/jariyah_lora_YYYYMMDD.jsonl
        min_score: Threshold score minimum untuk export (default 0.7).

    Returns:
        Dict: {"exported": N, "skipped": N, "output_path": str, "ready_for_lora": bool}
    """
    pairs = get_exportable_pairs(min_score=min_score)

    # Hitung total pairs (termasuk yang tidak lolos filter)
    total_in_file = _count_all_pairs()
    skipped = total_in_file - len(pairs)

    if not pairs:
        logger.info("Tidak ada pair yang bisa diekspor.")
        return {
            "exported": 0,
            "skipped": skipped,
            "output_path": None,
            "ready_for_lora": False,
        }

    # Tentukan output path
    if output_path is None:
        date_str = datetime.date.today().strftime("%Y%m%d")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"jariyah_lora_{date_str}.jsonl"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    exported = 0
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                entry = {
                    "messages": [
                        {"role": "system", "content": SIDIX_SYSTEM_MESSAGE},
                        {"role": "user", "content": pair["query"]},
                        {"role": "assistant", "content": pair["response"]},
                    ]
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                exported += 1
    except OSError as e:
        logger.error("Gagal menulis output LoRA: %s", e)
        return {
            "exported": 0,
            "skipped": total_in_file,
            "output_path": None,
            "ready_for_lora": False,
            "error": str(e),
        }

    ready = exported >= LORA_READY_THRESHOLD
    logger.info(
        "Jariyah export selesai: %d pairs → %s (ready_for_lora=%s)",
        exported, output_path, ready,
    )
    return {
        "exported": exported,
        "skipped": skipped,
        "output_path": str(output_path),
        "ready_for_lora": ready,
    }


def get_export_stats() -> dict:
    """
    Statistik export: total pairs, exportable, skipped, threshold.

    Returns:
        Dict dengan keys: total, exportable, skipped, threshold, ready_for_lora.
    """
    total = _count_all_pairs()
    exportable_pairs = get_exportable_pairs()
    exportable = len(exportable_pairs)
    skipped = total - exportable

    return {
        "total": total,
        "exportable": exportable,
        "skipped": skipped,
        "threshold": LORA_READY_THRESHOLD,
        "ready_for_lora": exportable >= LORA_READY_THRESHOLD,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _count_all_pairs() -> int:
    """Hitung semua baris valid di JSONL (tanpa filter)."""
    if not PAIRS_PATH.exists():
        return 0
    try:
        with open(PAIRS_PATH, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0
