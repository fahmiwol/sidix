"""
merge_persona_dataset.py — Sprint 13 Phase 3a → 3b bridge.

Combine 5 persona JSONL → single Alpaca-style training dataset dengan
train/val split per persona (preserve persona balance di kedua split).

Output:
- {out_dir}/persona_qa_train.jsonl (90% per persona, shuffled)
- {out_dir}/persona_qa_val.jsonl (10% per persona, shuffled)
- {out_dir}/persona_qa_stats.json (balance + score summary)

Format kompatibel dengan HuggingFace `datasets.load_dataset("json", ...)`
dan SFTTrainer Alpaca format. Persona tag tetap di metadata (BUKAN prompt).
"""
from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


_PERSONAS = ["UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"]


def merge_and_split(
    in_dir: str = "/opt/sidix/.data/training",
    out_dir: Optional[str] = None,
    val_ratio: float = 0.10,
    seed: int = 2026,
) -> dict:
    """Merge 5 persona JSONL → train/val split + stats.

    Args:
        in_dir: dir berisi persona_qa_{PERSONA}.jsonl (output Phase 3a).
        out_dir: dir untuk output (default = in_dir).
        val_ratio: fraction holdout untuk val (default 0.10 = 10%).
        seed: random seed untuk shuffle reproducibility.

    Returns:
        dict summary {ok, train_count, val_count, per_persona, files}.
    """
    in_path = Path(in_dir)
    out_path = Path(out_dir) if out_dir else in_path
    out_path.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)

    train_rows: list[dict] = []
    val_rows: list[dict] = []
    per_persona_stats: dict = {}

    for persona in _PERSONAS:
        src = in_path / f"persona_qa_{persona}.jsonl"
        if not src.exists():
            log.warning("[merge] missing %s", src)
            per_persona_stats[persona] = {"missing": True}
            continue

        rows = []
        for line in src.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        rng.shuffle(rows)
        n_val = max(1, int(len(rows) * val_ratio))
        val_part = rows[:n_val]
        train_part = rows[n_val:]

        train_rows.extend(train_part)
        val_rows.extend(val_part)

        scores = [r.get("metadata", {}).get("signature_score", 0.0) for r in rows]
        per_persona_stats[persona] = {
            "total": len(rows),
            "train": len(train_part),
            "val": len(val_part),
            "avg_signature_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        }

    # Final shuffle untuk mix persona di setiap batch
    rng.shuffle(train_rows)
    rng.shuffle(val_rows)

    train_path = out_path / "persona_qa_train.jsonl"
    val_path = out_path / "persona_qa_val.jsonl"
    stats_path = out_path / "persona_qa_stats.json"

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for r in val_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = {
        "ok": True,
        "train_count": len(train_rows),
        "val_count": len(val_rows),
        "val_ratio": val_ratio,
        "seed": seed,
        "per_persona": per_persona_stats,
        "files": {
            "train": str(train_path),
            "val": str(val_path),
            "stats": str(stats_path),
        },
    }

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    log.info("[merge] train=%d val=%d → %s", len(train_rows), len(val_rows), out_path)
    return summary


__all__ = ["merge_and_split"]
