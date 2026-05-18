"""
whitelist_store — Persistent whitelist untuk bypass rate limit + daily quota.

Store: JSON file di .data/whitelist.json. Categori: sponsor, researcher,
contributor, owner, dev, beta_tester. Bisa di-manage via admin UI.

Schema:
{
  "version": 1,
  "emails": [
    {"email": "fahmiwol@gmail.com", "category": "owner", "note": "...", "added_at": "..."},
    {"email": "researcher@univ.edu", "category": "researcher", "note": "PhD AI", "added_at": "..."},
  ],
  "user_ids": [
    {"id": "user_xxx", "category": "sponsor", "note": "Patreon Tier 3", "added_at": "..."},
  ]
}

Combined dengan env var SIDIX_WHITELIST_EMAILS / USER_IDS (immutable
default) — JSON store adalah admin-managed dynamic layer.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


_LOCK = threading.Lock()
_STORE_PATH: Optional[Path] = None
_CACHE: Optional[dict] = None
_CACHE_MTIME: float = 0.0


_VALID_CATEGORIES = (
    "owner", "dev", "sponsor", "researcher", "contributor", "beta_tester", "vip", "other",
)


def _resolve_path() -> Path:
    global _STORE_PATH
    if _STORE_PATH is not None:
        return _STORE_PATH
    base_dir = os.environ.get("SIDIX_WHITELIST_DIR", "")
    if base_dir:
        p = Path(base_dir)
    else:
        # Default: relative ke apps/brain_qa/.data/
        here = Path(__file__).resolve().parent  # brain_qa/
        p = here.parent / ".data"
    p.mkdir(parents=True, exist_ok=True)
    _STORE_PATH = p / "whitelist.json"
    return _STORE_PATH


def _empty_store() -> dict:
    return {"version": 1, "emails": [], "user_ids": []}


def _load_raw() -> dict:
    path = _resolve_path()
    if not path.exists():
        return _empty_store()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _empty_store()


def _load_cached() -> dict:
    global _CACHE, _CACHE_MTIME
    path = _resolve_path()
    try:
        mtime = path.stat().st_mtime if path.exists() else 0.0
    except Exception:
        mtime = 0.0
    if _CACHE is not None and mtime == _CACHE_MTIME:
        return _CACHE
    with _LOCK:
        _CACHE = _load_raw()
        _CACHE_MTIME = mtime
    return _CACHE


def _save(data: dict) -> None:
    global _CACHE, _CACHE_MTIME
    path = _resolve_path()
    with _LOCK:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        _CACHE = data
        try:
            _CACHE_MTIME = path.stat().st_mtime
        except Exception:
            _CACHE_MTIME = 0.0


# ── Public API ──────────────────────────────────────────────────────────────

def list_all() -> dict:
    """Return seluruh whitelist (untuk admin GET)."""
    return _load_cached()


def is_email_whitelisted(email: str) -> bool:
    if not email:
        return False
    em = email.strip().lower()
    if not em:
        return False
    data = _load_cached()
    for entry in data.get("emails") or []:
        if (entry.get("email") or "").strip().lower() == em:
            return True
    return False


def is_user_id_whitelisted(uid: str) -> bool:
    if not uid:
        return False
    u = uid.strip()
    if not u:
        return False
    data = _load_cached()
    for entry in data.get("user_ids") or []:
        if (entry.get("id") or "").strip() == u:
            return True
    return False


def add_email(email: str, *, category: str = "other", note: str = "") -> dict:
    em = (email or "").strip().lower()
    if not em or "@" not in em:
        raise ValueError("email tidak valid")
    cat = category.strip().lower() if category else "other"
    if cat not in _VALID_CATEGORIES:
        cat = "other"
    data = _load_cached()
    emails = data.get("emails") or []
    # Dedup
    for entry in emails:
        if (entry.get("email") or "").strip().lower() == em:
            entry["category"] = cat
            entry["note"] = note[:240]
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["emails"] = emails
            _save(data)
            return entry
    new_entry = {
        "email": em,
        "category": cat,
        "note": note[:240],
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    emails.append(new_entry)
    data["emails"] = emails
    _save(data)
    return new_entry


def remove_email(email: str) -> bool:
    em = (email or "").strip().lower()
    if not em:
        return False
    data = _load_cached()
    emails = data.get("emails") or []
    new_emails = [e for e in emails if (e.get("email") or "").strip().lower() != em]
    if len(new_emails) == len(emails):
        return False
    data["emails"] = new_emails
    _save(data)
    return True


def add_user_id(uid: str, *, category: str = "other", note: str = "") -> dict:
    u = (uid or "").strip()
    if not u:
        raise ValueError("user_id tidak valid")
    cat = category.strip().lower() if category else "other"
    if cat not in _VALID_CATEGORIES:
        cat = "other"
    data = _load_cached()
    uids = data.get("user_ids") or []
    for entry in uids:
        if (entry.get("id") or "").strip() == u:
            entry["category"] = cat
            entry["note"] = note[:240]
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            data["user_ids"] = uids
            _save(data)
            return entry
    new_entry = {
        "id": u,
        "category": cat,
        "note": note[:240],
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    uids.append(new_entry)
    data["user_ids"] = uids
    _save(data)
    return new_entry


def remove_user_id(uid: str) -> bool:
    u = (uid or "").strip()
    if not u:
        return False
    data = _load_cached()
    uids = data.get("user_ids") or []
    new_uids = [e for e in uids if (e.get("id") or "").strip() != u]
    if len(new_uids) == len(uids):
        return False
    data["user_ids"] = new_uids
    _save(data)
    return True


def stats() -> dict:
    data = _load_cached()
    return {
        "total_emails": len(data.get("emails") or []),
        "total_user_ids": len(data.get("user_ids") or []),
        "categories": {
            cat: sum(
                1 for e in (data.get("emails") or []) + (data.get("user_ids") or [])
                if (e.get("category") or "other") == cat
            )
            for cat in _VALID_CATEGORIES
        },
    }
