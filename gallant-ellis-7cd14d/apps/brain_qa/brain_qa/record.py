from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RecordEntry:
    ts: str
    question: str
    answer_text: str
    mode: str  # "corpus" | "system_clock" | "other"
    citations: list[dict[str, Any]]
    persona: str | None = None
    persona_reason: str | None = None


def append_record(*, index_dir: Path, entry: RecordEntry) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    path = index_dir / "records.jsonl"
    line = json.dumps(asdict(entry), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

