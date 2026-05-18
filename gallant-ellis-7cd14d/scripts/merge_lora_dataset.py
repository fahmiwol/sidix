# -*- coding: utf-8 -*-
"""
merge_lora_dataset.py — Merge & filter LoRA training datasets (Kimi)

Combine:
- lora_starter_dataset_*.jsonl (benchmark + C3oT + augmented)
- corpus_qa_pairs_*.jsonl (corpus-derived)

Filter:
- Remove duplicates by user query
- Balance categories (cap corpus-derived to avoid dominance)
- Ensure minimum reasoning trace length

Output: output/lora_training_dataset_v1_YYYYMMDD.jsonl
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "apps" / "output"


def load_jsonl(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def merge_and_filter() -> Path:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"lora_training_dataset_v1_{date_str}.jsonl"

    # Load sources
    starter_files = sorted(OUTPUT_DIR.glob("lora_starter_dataset_*.jsonl"))
    corpus_files = sorted(OUTPUT_DIR.glob("corpus_qa_pairs_*.jsonl"))

    starter_records = []
    for f in starter_files:
        starter_records.extend(load_jsonl(f))

    corpus_records = []
    for f in corpus_files:
        corpus_records.extend(load_jsonl(f))

    print(f"Loaded: {len(starter_records)} starter + {len(corpus_records)} corpus")

    # Deduplicate by query
    seen = set()
    deduped = []

    # Prioritize starter records (higher quality reasoning)
    for r in starter_records:
        q = r["messages"][1]["content"].strip().lower()[:100]
        if q not in seen:
            seen.add(q)
            deduped.append(r)

    # Add corpus records, cap to avoid overwhelming starter
    corpus_cap = max(500, len(starter_records) * 3)  # max 3x starter
    corpus_added = 0
    for r in corpus_records:
        q = r["messages"][1]["content"].strip().lower()[:100]
        if q not in seen and corpus_added < corpus_cap:
            seen.add(q)
            deduped.append(r)
            corpus_added += 1

    # Filter: minimum reasoning trace length (in assistant content)
    filtered = []
    for r in deduped:
        assistant = r["messages"][2]["content"] if len(r["messages"]) > 2 else ""
        if len(assistant) > 50:  # At least 50 chars
            filtered.append(r)

    # Write
    with output_path.open("w", encoding="utf-8") as f:
        for r in filtered:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[OK] Final dataset: {len(filtered)} records -> {output_path}")
    print(f"    Starter: {len(starter_records)}, Corpus added: {corpus_added}")
    print(f"    Ready for LoRA training: {'YES' if len(filtered) >= 500 else 'NO'}")

    return output_path


if __name__ == "__main__":
    print("=== LoRA Dataset Merger ===\n")
    merge_and_filter()
    print("\n[OK] Done")
