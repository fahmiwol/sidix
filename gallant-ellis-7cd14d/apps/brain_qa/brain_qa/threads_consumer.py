"""
threads_consumer.py — Konsumsi growth_queue.jsonl ke Threads
============================================================

daily_growth menulis post ke `.data/threads/growth_queue.jsonl`.
Modul ini mengambil 1 post berikutnya yang belum di-publish, dan post-nya
via existing threads infrastructure.

Strategi konservatif:
  - Post 1 per panggilan (rate-limit alami)
  - Tandai status: queued -> publishing -> published / failed
  - Audit trail: tetap simpan semua entry, hanya update status field
  - Optional dry-run untuk testing
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import default_data_dir


QUEUE_FILE = default_data_dir() / "threads" / "growth_queue.jsonl"


def get_queue_status() -> dict:
    """Inventarisasi queue."""
    if not QUEUE_FILE.exists():
        return {"queued": 0, "published": 0, "failed": 0, "total": 0}
    counts = {"queued": 0, "published": 0, "failed": 0, "total": 0}
    for line in QUEUE_FILE.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            status = entry.get("status", "queued")
            counts[status] = counts.get(status, 0) + 1
            counts["total"] += 1
        except Exception:
            continue
    return counts


def consume_one(dry_run: bool = False) -> dict:
    """
    Ambil 1 post terlama yang status=queued, kirim ke Threads, update statusnya.
    Returns dict info hasil eksekusi.
    """
    if not QUEUE_FILE.exists():
        return {"ok": False, "reason": "no queue file yet"}

    # Read all lines, find first queued
    all_entries: list[dict] = []
    target_idx: Optional[int] = None
    for i, line in enumerate(QUEUE_FILE.open(encoding="utf-8")):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        all_entries.append(entry)
        if target_idx is None and entry.get("status") == "queued":
            target_idx = len(all_entries) - 1

    if target_idx is None:
        return {"ok": True, "reason": "no queued items", "stats": get_queue_status()}

    target = all_entries[target_idx]
    post_text = target.get("post", "")
    if not post_text:
        target["status"] = "failed"
        target["error"]  = "empty post text"
        _rewrite_queue(all_entries)
        return {"ok": False, "reason": "empty post text"}

    if dry_run:
        return {
            "ok":          True,
            "dry_run":     True,
            "would_post":  post_text[:300],
            "topic_hash":  target.get("topic_hash"),
            "domain":      target.get("domain"),
        }

    # Update to publishing first (audit)
    target["status"]         = "publishing"
    target["publishing_at"]  = time.time()
    _rewrite_queue(all_entries)

    # Try post via threads_oauth (existing infra)
    try:
        from .threads_oauth import create_text_post
        result = create_text_post(post_text)
        target["status"]      = "published" if result.get("ok") else "failed"
        target["published_at"] = time.time() if result.get("ok") else None
        target["thread_id"]    = result.get("post_id") or result.get("id") or ""
        target["raw_response"] = {
            "ok":     result.get("ok"),
            "error":  result.get("error", "")[:200] if result.get("error") else "",
        }
    except ImportError:
        target["status"] = "failed"
        target["error"]  = "threads_oauth.create_text_post not available"
    except Exception as e:
        target["status"] = "failed"
        target["error"]  = str(e)[:300]

    _rewrite_queue(all_entries)

    return {
        "ok":         target["status"] == "published",
        "status":     target["status"],
        "topic_hash": target.get("topic_hash"),
        "thread_id":  target.get("thread_id", ""),
        "preview":    post_text[:200],
        "stats":      get_queue_status(),
    }


def _rewrite_queue(entries: list[dict]) -> None:
    """Tulis ulang seluruh queue (ganti file). Async-safe untuk single writer."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_FILE.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    tmp.replace(QUEUE_FILE)


def consume_batch(max_posts: int = 3) -> dict:
    """Eksekusi beberapa post sekaligus dengan jeda kecil."""
    results = []
    for i in range(max_posts):
        r = consume_one()
        results.append(r)
        if r.get("reason") == "no queued items":
            break
        time.sleep(2)  # be nice to Threads API
    return {
        "ok":       True,
        "executed": len(results),
        "results":  results,
        "stats":    get_queue_status(),
    }
