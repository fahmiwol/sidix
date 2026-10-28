"""
feedback_store — Persistent storage untuk user feedback (bug report, kritik, saran).

Schema (JSON file):
{
  "version": 1,
  "items": [
    {
      "id": "fb_<uuid8>",
      "title": "...",
      "body": "...",
      "screenshot": "filename.png" | null,  # path relative ke feedback_images/
      "user_email": "...",
      "user_id": "...",
      "session_id": "...",
      "status": "new" | "in_progress" | "resolved" | "dismissed",
      "created_at": "ISO8601",
      "updated_at": "ISO8601" | null,
    }
  ]
}

Disimpan di: apps/brain_qa/.data/feedback.json
Screenshot file: apps/brain_qa/.data/feedback_images/<uuid>.<ext>
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_LOCK = threading.Lock()
_STORE_PATH: Optional[Path] = None
_IMAGE_DIR: Optional[Path] = None
_VALID_STATUS = ("new", "in_progress", "resolved", "dismissed")
_MAX_ITEMS = 5000


def _resolve_paths() -> tuple[Path, Path]:
    global _STORE_PATH, _IMAGE_DIR
    if _STORE_PATH is not None and _IMAGE_DIR is not None:
        return _STORE_PATH, _IMAGE_DIR
    here = Path(__file__).resolve().parent  # brain_qa/
    data_dir = here.parent / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _STORE_PATH = data_dir / "feedback.json"
    _IMAGE_DIR = data_dir / "feedback_images"
    _IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    return _STORE_PATH, _IMAGE_DIR


def image_dir() -> Path:
    return _resolve_paths()[1]


def _empty_store() -> dict:
    return {"version": 1, "items": []}


def _load() -> dict:
    path, _ = _resolve_paths()
    if not path.exists():
        return _empty_store()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _empty_store()


def _save(data: dict) -> None:
    path, _ = _resolve_paths()
    with _LOCK:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _new_id() -> str:
    return f"fb_{uuid.uuid4().hex[:10]}"


# ── Public API ──────────────────────────────────────────────────────────────

def add_feedback(
    *,
    title: str,
    body: str,
    user_email: str = "",
    user_id: str = "",
    session_id: str = "",
    screenshot_filename: Optional[str] = None,
) -> dict:
    title = (title or "").strip()
    body = (body or "").strip()
    if not title or not body:
        raise ValueError("title dan body wajib diisi")
    if len(title) > 200:
        title = title[:200]
    if len(body) > 8000:
        body = body[:8000]

    item = {
        "id": _new_id(),
        "title": title,
        "body": body,
        "screenshot": screenshot_filename,
        "user_email": (user_email or "").strip().lower()[:200],
        "user_id": (user_id or "").strip()[:200],
        "session_id": (session_id or "").strip()[:80],
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None,
    }
    data = _load()
    items = data.get("items") or []
    items.append(item)
    # Prune kalau kebanyakan
    if len(items) > _MAX_ITEMS:
        items = items[-_MAX_ITEMS:]
    data["items"] = items
    _save(data)
    return item


def list_all(*, limit: int = 200, status_filter: Optional[str] = None) -> list[dict]:
    data = _load()
    items = data.get("items") or []
    if status_filter and status_filter in _VALID_STATUS:
        items = [i for i in items if i.get("status") == status_filter]
    # Newest first
    items = sorted(items, key=lambda i: i.get("created_at") or "", reverse=True)
    return items[:limit]


def get_by_id(fb_id: str) -> Optional[dict]:
    data = _load()
    for item in data.get("items") or []:
        if item.get("id") == fb_id:
            return item
    return None


def update_status(fb_id: str, status: str) -> Optional[dict]:
    if status not in _VALID_STATUS:
        raise ValueError(f"status invalid: {status}")
    data = _load()
    items = data.get("items") or []
    for item in items:
        if item.get("id") == fb_id:
            item["status"] = status
            item["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["items"] = items
            _save(data)
            return item
    return None


def delete_feedback(fb_id: str) -> bool:
    data = _load()
    items = data.get("items") or []
    new_items = [i for i in items if i.get("id") != fb_id]
    if len(new_items) == len(items):
        return False
    # Cleanup screenshot file kalau ada
    removed = next(i for i in items if i.get("id") == fb_id)
    fname = removed.get("screenshot")
    if fname:
        try:
            (image_dir() / fname).unlink(missing_ok=True)
        except Exception:
            pass
    data["items"] = new_items
    _save(data)
    return True


def stats() -> dict:
    data = _load()
    items = data.get("items") or []
    by_status = {s: 0 for s in _VALID_STATUS}
    for i in items:
        by_status[i.get("status", "new")] = by_status.get(i.get("status", "new"), 0) + 1
    return {"total": len(items), "by_status": by_status}
