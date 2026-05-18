"""
harvest_drive_d_datasets.py — One-shot adopt brain/datasets/*.jsonl

Jalankan sekali untuk import 4 dataset existing dari Drive D ke training pipeline:
  - corpus_qa.jsonl
  - finetune_sft.jsonl
  - memory_cards.jsonl
  - qa_pairs.jsonl

Output: training_generated/harvest_<name>.jsonl (ChatML format)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from brain_qa.skill_builder import harvest_dataset_jsonl


def main() -> None:
    root = Path(__file__).resolve().parents[3]   # repo root (dinamis)
    datasets = [
        root / "brain" / "datasets" / "corpus_qa.jsonl",
        root / "brain" / "datasets" / "finetune_sft.jsonl",
        root / "brain" / "datasets" / "memory_cards.jsonl",
        root / "brain" / "datasets" / "qa_pairs.jsonl",
    ]
    total_pairs = 0
    for ds in datasets:
        if not ds.exists():
            print(f"SKIP (not found): {ds}")
            continue
        result = harvest_dataset_jsonl(str(ds), max_samples=10_000)
        if result.get("ok"):
            n = result.get("harvested", 0)
            print(f"OK    {ds.name:25s} -> {result['output']} ({n} pairs)")
            total_pairs += n
        else:
            print(f"FAIL  {ds.name:25s} -> {result.get('error')}")
    print(f"\nTOTAL HARVESTED: {total_pairs} pairs")


if __name__ == "__main__":
    main()
