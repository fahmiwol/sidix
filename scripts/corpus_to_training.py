#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
corpus_to_training.py — SIDIX Self-Train Fase 1 (Weekly Cron)

Standalone script untuk weekly cron:
  - Load corpus docs via curator agent
  - Score all docs
  - Generate instruction-tuning JSONL format
  - Output to: brain/public/training_data/YYYY-MM-DD/corpus_pairs.jsonl
  - Also generate summary: brain/public/training_data/YYYY-MM-DD/_summary.json

Cara pakai:
    python scripts/corpus_to_training.py

Cron (weekly Senin 03:00 UTC):
    0 3 * * 1 cd /opt/sidix && python scripts/corpus_to_training.py >> /var/log/sidix_training.log 2>&1
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add apps/brain_qa to path so we can import curator_agent
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "brain_qa"))

from brain_qa.curator_agent import (
    load_corpus_docs,
    curate_batch,
    _build_training_pair,
    MIN_PAIRS_TARGET,
    MAX_PAIRS_PER_RUN,
    MIN_SCORE,
    PREMIUM_SCORE,
)


def main():
    start = time.time()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = ROOT / "brain" / "public" / "training_data" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[corpus_to_training] start {today}")

    # 1. Load corpus docs
    docs = load_corpus_docs(limit=MAX_PAIRS_PER_RUN * 3)
    print(f"[corpus_to_training] loaded {len(docs)} docs")

    if len(docs) < 10:
        print("[corpus_to_training] WARNING: corpus too small, skipping")
        sys.exit(0)

    # 2. Score and curate
    approved, rejected = curate_batch(docs, threshold=MIN_SCORE)
    print(f"[corpus_to_training] approved={len(approved)} rejected={len(rejected)}")

    # 3. Build training pairs
    pairs = []
    for doc in approved[:MAX_PAIRS_PER_RUN]:
        pair = _build_training_pair(doc)
        pairs.append({
            "instruction": pair.instruction,
            "input": pair.input,
            "output": pair.output,
            "source": pair.source,
            "score": pair.score,
            "sanad_tier": pair.sanad_tier,
            "maqashid_passed": pair.maqashid_passed,
            "collected_at": pair.collected_at,
        })

    premium_pairs = [p for p in pairs if p["score"] >= PREMIUM_SCORE]

    # 4. Write JSONL
    corpus_path = out_dir / "corpus_pairs.jsonl"
    with open(corpus_path, "w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    premium_path = out_dir / "corpus_pairs_premium.jsonl"
    if premium_pairs:
        with open(premium_path, "w", encoding="utf-8") as f:
            for p in premium_pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")

    # 5. Write summary
    summary = {
        "date": today,
        "total_corpus_docs": len(docs),
        "total_approved": len(approved),
        "total_rejected": len(rejected),
        "total_premium": len(premium_pairs),
        "pairs_written": len(pairs),
        "output_file": str(corpus_path),
        "premium_file": str(premium_path) if premium_pairs else "",
        "elapsed_s": round(time.time() - start, 2),
        "threshold": MIN_SCORE,
        "premium_threshold": PREMIUM_SCORE,
        "warnings": [],
    }

    if len(pairs) < MIN_PAIRS_TARGET:
        msg = f"Pairs generated ({len(pairs)}) < target ({MIN_PAIRS_TARGET}). Tambah corpus atau turunkan threshold."
        summary["warnings"].append(msg)
        print(f"[corpus_to_training] WARNING: {msg}")

    summary_path = out_dir / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[corpus_to_training] done: {len(pairs)} pairs → {corpus_path}")
    print(f"[corpus_to_training] summary → {summary_path}")

    # 6. Also append to aggregate files in .data
    data_dir = ROOT / "apps" / "brain_qa" / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    all_pairs_file = data_dir / "lora_all_pairs.jsonl"
    with open(all_pairs_file, "a", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    if premium_pairs:
        premium_file = data_dir / "lora_premium_pairs.jsonl"
        with open(premium_file, "a", encoding="utf-8") as f:
            for p in premium_pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
