"""
auto_lora.py — Trigger LoRA Fine-Tune Saat Corpus Cukup
========================================================

Sesuai mandate note 142 ("SIDIX entitas mandiri"):
  - Setiap jawaban mentor LLM = 1 training pair
  - Saat pair terkumpul cukup (default >=500), trigger pipeline upload
  - Target: setiap N hari, SIDIX dapat LoRA adapter baru yang lebih pintar

Modul ini TIDAK menjalankan training (butuh GPU). Tugasnya:
  1. Inventarisasi training_generated/*.jsonl
  2. Konsolidasi jadi satu dataset siap upload (Kaggle/Colab/RunPod)
  3. Generate dataset-metadata.json untuk Kaggle
  4. Mark batch sebagai 'ready_for_upload'
  5. Optional: trigger Kaggle CLI upload (kalau env KAGGLE_USERNAME/KAGGLE_KEY ada)
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import default_data_dir


# ── Config ────────────────────────────────────────────────────────────────────

LORA_TRIGGER_THRESHOLD = 500       # min pair untuk trigger
DATASET_NAME           = "sidix-mighan-corpus"


# ── Status & Inventaris ───────────────────────────────────────────────────────

def get_training_corpus_status() -> dict:
    """
    Hitung berapa training pair tersedia, cek apakah cukup untuk fine-tune baru.
    """
    pairs_dir = default_data_dir() / "training_generated"
    if not pairs_dir.exists():
        return {
            "total_pairs":       0,
            "files":             [],
            "ready_for_upload":  False,
            "threshold":         LORA_TRIGGER_THRESHOLD,
            "message":           "no training_generated/ yet",
        }

    files_info: list[dict] = []
    total = 0
    for f in sorted(pairs_dir.glob("*.jsonl")):
        try:
            count = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
            files_info.append({
                "file":      f.name,
                "pairs":     count,
                "size_kb":   round(f.stat().st_size / 1024, 1),
                "modified":  datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds"),
            })
            total += count
        except Exception as e:
            files_info.append({"file": f.name, "error": str(e)})

    last_upload = _read_last_upload_marker()
    pairs_since_last_upload = total - (last_upload.get("total_at_upload", 0) if last_upload else 0)

    return {
        "total_pairs":             total,
        "pairs_since_last_upload": pairs_since_last_upload,
        "threshold":               LORA_TRIGGER_THRESHOLD,
        "ready_for_upload":        pairs_since_last_upload >= LORA_TRIGGER_THRESHOLD,
        "files":                   files_info,
        "last_upload":             last_upload,
        "next_check_at":           f"+{LORA_TRIGGER_THRESHOLD - pairs_since_last_upload} pairs to trigger" if not (pairs_since_last_upload >= LORA_TRIGGER_THRESHOLD) else "READY",
    }


# ── Konsolidasi & Persiapan Upload ────────────────────────────────────────────

def prepare_upload_batch(force: bool = False) -> dict:
    """
    Konsolidasi semua jsonl jadi satu file batch + buat metadata Kaggle.
    Kalau belum cukup pair (dan tidak force) → return info tanpa aksi.
    """
    status = get_training_corpus_status()
    if not status["ready_for_upload"] and not force:
        return {
            "ok":       False,
            "reason":   "below threshold",
            "status":   status,
        }

    upload_dir = default_data_dir() / "lora_upload"
    upload_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d_%H%M")
    batch_id = f"sidix_lora_batch_{today}"
    batch_dir = upload_dir / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Concat all jsonl ke satu file
    out_jsonl = batch_dir / "training.jsonl"
    pairs_dir = default_data_dir() / "training_generated"
    line_count = 0
    sources: list[str] = []
    seen_ids: set = set()
    with out_jsonl.open("w", encoding="utf-8") as out:
        for f in sorted(pairs_dir.glob("*.jsonl")):
            for line in f.open(encoding="utf-8"):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                pair_id = obj.get("pair_id")
                if pair_id and pair_id in seen_ids:
                    continue
                if pair_id:
                    seen_ids.add(pair_id)
                out.write(line + "\n")
                line_count += 1
            sources.append(f.name)

    # Metadata Kaggle
    kaggle_meta = {
        "title":     f"SIDIX Mighan Corpus Batch {today}",
        "id":        f"<USERNAME>/{DATASET_NAME}-{today.lower()}",
        "licenses":  [{"name": "CC-BY-SA-4.0"}],
        "keywords":  ["llm", "fine-tuning", "indonesian", "islamic", "sidix", "mighan", "instruction-tuning"],
        "description": (
            f"SIDIX self-learning training corpus, batch {today}. "
            f"{line_count} ChatML training pairs collected via daily_growth pipeline. "
            f"Format: messages array (system/user/assistant). "
            f"Domain: multi-domain (epistemology, AI, programming, Indonesian language, etc.)."
        ),
    }
    (batch_dir / "dataset-metadata.json").write_text(
        json.dumps(kaggle_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # README.md untuk dataset
    readme = (
        f"# SIDIX Training Batch — {today}\n\n"
        f"- Total pairs: {line_count}\n"
        f"- Source files merged: {len(sources)}\n"
        f"- Format: ChatML JSONL ({{messages: [system, user, assistant]}})\n"
        f"- Generated by: SIDIX `daily_growth` pipeline\n"
        f"- License: CC-BY-SA 4.0 (corpus sintesis multi-mentor)\n\n"
        f"## Usage\n"
        f"```python\n"
        f"import json\n"
        f"with open('training.jsonl') as f:\n"
        f"    for line in f:\n"
        f"        sample = json.loads(line)\n"
        f"        # sample['messages'] = [{{role, content}}, ...]\n"
        f"```\n\n"
        f"## Lineage\n"
        f"Setiap pair di-trace ke topic_hash via field `source: \"daily_growth:<topic_hash>\"`. "
        f"Lihat sanad eksplisit di `brain/public/research_notes/<n>_<slug>.md`.\n"
    )
    (batch_dir / "README.md").write_text(readme, encoding="utf-8")

    # Tulis marker (last_upload)
    marker = {
        "batch_id":         batch_id,
        "batch_path":       str(batch_dir),
        "total_at_upload":  status["total_pairs"],
        "pairs_in_batch":   line_count,
        "prepared_at":      time.time(),
        "sources_merged":   sources,
    }
    _write_upload_marker(marker)

    return {
        "ok":              True,
        "batch_id":        batch_id,
        "batch_dir":       str(batch_dir),
        "pairs_in_batch":  line_count,
        "sources_merged":  len(sources),
        "next_step":       "kaggle datasets create -p <batch_dir> (atau upload manual)",
    }


# ── Markers (last_upload state) ───────────────────────────────────────────────

def _marker_path() -> Path:
    return default_data_dir() / "lora_upload" / ".last_upload.json"


def _read_last_upload_marker() -> Optional[dict]:
    p = _marker_path()
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_upload_marker(marker: dict) -> None:
    p = _marker_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Optional: Trigger Kaggle CLI ──────────────────────────────────────────────

def try_kaggle_upload(batch_dir: str) -> dict:
    """
    Coba upload via Kaggle CLI kalau credentials tersedia.
    Tidak wajib — user bisa upload manual via web Kaggle.
    """
    import os
    import subprocess
    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        return {
            "ok":     False,
            "reason": "KAGGLE_USERNAME / KAGGLE_KEY not set — upload manual via kaggle.com",
        }
    try:
        cmd = ["kaggle", "datasets", "create", "-p", batch_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return {
            "ok":      result.returncode == 0,
            "stdout":  result.stdout[-500:],
            "stderr":  result.stderr[-500:],
        }
    except FileNotFoundError:
        return {"ok": False, "reason": "kaggle CLI not installed (pip install kaggle)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
