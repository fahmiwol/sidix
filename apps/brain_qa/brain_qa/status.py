from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .curation import format_curation_events, list_recent_curation_events
from .ledger import ledger_status, verify_latest_snapshot
from .paths import default_index_dir, load_manifest_paths


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _latest_mtime_under(root: Path, *, suffix: str) -> float | None:
    if not root.exists():
        return None
    latest: float | None = None
    for p in root.rglob(f"*{suffix}"):
        if not p.is_file():
            continue
        try:
            mt = p.stat().st_mtime
        except Exception:
            continue
        if latest is None or mt > latest:
            latest = mt
    return latest


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@dataclass(frozen=True)
class BrainQaStatus:
    at: str
    index: dict[str, Any]
    ledger: dict[str, Any]
    recent_events: dict[str, Any]


def compute_status(index_dir_override: str | None = None) -> BrainQaStatus:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()

    # Index status
    ready = index_dir / "READY"
    meta_path = index_dir / "index_meta.json"
    meta = _safe_read_json(meta_path) if meta_path.exists() else None

    manifest = load_manifest_paths()
    public_root = manifest.public_markdown_root
    latest_corpus_mtime = _latest_mtime_under(public_root, suffix=".md")
    index_mtime = meta_path.stat().st_mtime if meta_path.exists() else None

    indexed = bool(ready.exists() and meta_path.exists())
    out_of_date = bool(indexed and latest_corpus_mtime is not None and index_mtime is not None and latest_corpus_mtime > index_mtime)

    index_status = "ready" if indexed and not out_of_date else ("out_of_date" if indexed and out_of_date else "missing")

    index_info: dict[str, Any] = {
        "status": index_status,
        "index_dir": str(index_dir),
        "ready_file": str(ready),
        "meta_file": str(meta_path),
        "meta": meta,
        "public_root": str(public_root),
        "out_of_date": out_of_date,
    }

    if index_status == "missing":
        index_info["ui_message"] = "Index belum ada. Jalankan `python -m brain_qa index`."
    elif index_status == "out_of_date":
        index_info["ui_message"] = "Index perlu di-refresh (corpus berubah). Jalankan `python -m brain_qa index`."
    else:
        index_info["ui_message"] = "Index siap dipakai."

    # Ledger status
    led_stat = ledger_status(index_dir_override)
    ver = verify_latest_snapshot(index_dir_override=index_dir_override)
    ledger_info: dict[str, Any] = {
        "paths": led_stat,
        "verify": {
            "ok": ver.ok,
            "message": ver.message,
            "chain_ok": ver.chain_ok,
            "latest_snapshot_root": ver.latest_snapshot_root,
            "recomputed_root": ver.recomputed_root,
        },
        "ui_message": "Ledger OK (chain valid, root match)." if ver.ok else f"Ledger warning: {ver.message}",
    }

    # Recent events
    events = list_recent_curation_events(index_dir_override=index_dir_override, limit=10)
    events_block = format_curation_events(events)
    recent_info: dict[str, Any] = {
        "count": len(events),
        "tail": events,
        "text": events_block,
        "ui_message": "Belum ada event publish." if not events else "Event publish terbaru tersedia.",
    }

    return BrainQaStatus(
        at=_now_utc_iso(),
        index=index_info,
        ledger=ledger_info,
        recent_events=recent_info,
    )

