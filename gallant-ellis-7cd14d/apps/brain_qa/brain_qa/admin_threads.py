"""
admin_threads.py — SIDIX Admin Threads Integration
===================================================
Endpoint admin untuk connect/disconnect akun Threads dan trigger
auto-content post. Dibuat terpisah dari social_agent.py agar concern
admin (credentials, status, one-click post) tidak bercampur dengan
autonomous learning engine.

Pattern:
  POST /admin/threads/connect      → validasi token + simpan ke .env
  GET  /admin/threads/status       → status koneksi + posts hari ini
  POST /admin/threads/disconnect   → hapus token dari .env
  POST /admin/threads/auto-content → generate + post 1 konten sekarang

.env handling: append/update key tanpa menyentuh key lain. File .env
berada di apps/brain_qa/.env dan TIDAK di-commit (lihat .gitignore).
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from fastapi import APIRouter, HTTPException
except Exception:  # pragma: no cover
    APIRouter = None  # type: ignore

from .paths import workspace_root

# ── Konstanta ──────────────────────────────────────────────────────────────────

THREADS_API_BASE = "https://graph.threads.net/v1.0"
ENV_PATH = workspace_root() / "apps" / "brain_qa" / ".env"
POSTS_LOG = workspace_root() / "apps" / "brain_qa" / ".data" / "threads" / "posts_log.jsonl"
POSTS_LOG.parent.mkdir(parents=True, exist_ok=True)

MAX_POSTS_PER_DAY = 3
ENV_KEYS = ("THREADS_ACCESS_TOKEN", "THREADS_USER_ID", "THREADS_USERNAME")


# ── .env helpers ───────────────────────────────────────────────────────────────

def _read_env_file() -> dict[str, str]:
    """Baca file .env → dict. File tidak wajib ada."""
    out: dict[str, str] = {}
    if not ENV_PATH.exists():
        return out
    for line in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _write_env_updates(updates: dict[str, str | None]) -> None:
    """
    Update file .env: set keys in updates. Nilai None berarti hapus key.
    Preserve urutan dan baris komentar yang ada.
    """
    lines: list[str] = []
    seen: set[str] = set()

    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = raw.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                lines.append(raw)
                continue
            key, _, _old = stripped.partition("=")
            key = key.strip()
            if key in updates:
                seen.add(key)
                new_val = updates[key]
                if new_val is None:
                    # drop line
                    continue
                lines.append(f'{key}={_quote_env(new_val)}')
            else:
                lines.append(raw)

    # Append keys yang belum ada
    for key, val in updates.items():
        if key in seen or val is None:
            continue
        lines.append(f'{key}={_quote_env(val)}')

    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Refresh os.environ untuk proses berjalan
    for k, v in updates.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _quote_env(val: str) -> str:
    """Quote nilai .env kalau ada whitespace/special char."""
    if re.search(r'[\s#"\'=]', val):
        escaped = val.replace('"', '\\"')
        return f'"{escaped}"'
    return val


# ── Threads API helpers ───────────────────────────────────────────────────────

def _threads_get(path: str, access_token: str, extra: dict[str, Any] | None = None) -> dict:
    params = {"access_token": access_token}
    if extra:
        params.update(extra)
    url = f"{THREADS_API_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SIDIX/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _validate_token(access_token: str, user_id: str) -> dict:
    """
    Panggil /me untuk validasi. Return {ok, username, id, error?}.
    """
    try:
        data = _threads_get(
            f"/me",
            access_token,
            extra={"fields": "id,username,threads_profile_picture_url"},
        )
        returned_id = str(data.get("id", ""))
        username = data.get("username", "")
        if user_id and returned_id and returned_id != str(user_id):
            return {
                "ok": False,
                "error": f"user_id mismatch: token milik id={returned_id}, bukan {user_id}",
            }
        return {
            "ok": True,
            "id": returned_id or user_id,
            "username": username,
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:240]
        return {"ok": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Posts log ─────────────────────────────────────────────────────────────────

def append_post_log(entry: dict) -> None:
    entry.setdefault("created_at", time.time())
    with open(POSTS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def posts_today_count() -> int:
    if not POSTS_LOG.exists():
        return 0
    today = datetime.now().strftime("%Y-%m-%d")
    count = 0
    for line in POSTS_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("created_at", 0)
            if datetime.fromtimestamp(ts).strftime("%Y-%m-%d") == today:
                count += 1
        except Exception:
            continue
    return count


def last_post_at() -> float | None:
    if not POSTS_LOG.exists():
        return None
    last: float | None = None
    for line in POSTS_LOG.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            ts = rec.get("created_at")
            if ts and (last is None or ts > last):
                last = ts
        except Exception:
            continue
    return last


# ── Router ────────────────────────────────────────────────────────────────────

def build_router() -> "APIRouter":
    if APIRouter is None:
        raise RuntimeError("FastAPI tidak terinstall. pip install fastapi uvicorn")

    router = APIRouter(prefix="/admin/threads", tags=["admin-threads"])

    @router.post("/connect")
    def connect(body: dict[str, Any]):
        """
        Body: {"access_token": "...", "user_id": "..."}
        Validasi token lewat graph.threads.net/me, lalu simpan ke .env.
        """
        access_token = str(body.get("access_token", "")).strip()
        user_id = str(body.get("user_id", "")).strip()
        if not access_token or not user_id:
            raise HTTPException(status_code=400, detail="access_token dan user_id wajib diisi")

        check = _validate_token(access_token, user_id)
        if not check.get("ok"):
            return {"ok": False, "error": check.get("error", "validasi gagal")}

        username = check.get("username", "")
        _write_env_updates({
            "THREADS_ACCESS_TOKEN": access_token,
            "THREADS_USER_ID": user_id,
            "THREADS_USERNAME": username,
        })

        return {
            "ok": True,
            "connected": True,
            "username": username,
            "user_id": user_id,
        }

    @router.get("/status")
    def status():
        """Status koneksi Threads untuk admin UI."""
        env = _read_env_file()
        token = env.get("THREADS_ACCESS_TOKEN") or os.getenv("THREADS_ACCESS_TOKEN", "")
        user_id = env.get("THREADS_USER_ID") or os.getenv("THREADS_USER_ID", "")
        username = env.get("THREADS_USERNAME") or os.getenv("THREADS_USERNAME", "")

        connected = bool(token and user_id)
        result: dict[str, Any] = {
            "connected": connected,
            "username": username,
            "user_id": user_id if connected else "",
            "posts_today": posts_today_count(),
            "posts_remaining": max(0, MAX_POSTS_PER_DAY - posts_today_count()),
            "last_post_at": last_post_at(),
            "daily_limit": MAX_POSTS_PER_DAY,
        }

        # Note: kita tidak panggil /me tiap status untuk hindari rate cost.
        # Validasi terjadi saat connect dan saat auto-content gagal.
        return result

    @router.post("/disconnect")
    def disconnect():
        """Hapus kredensial Threads dari .env."""
        _write_env_updates({k: None for k in ENV_KEYS})
        return {"ok": True, "connected": False}

    @router.post("/auto-content")
    def auto_content(body: dict[str, Any] | None = None):
        """
        Generate 1 konten (via persona INAN/MIGHAN) dan langsung post ke Threads.
        Body opsional: {"topic_seed": "...", "persona": "inan|mighan", "dry_run": false}
        """
        body = body or {}
        topic_seed = str(body.get("topic_seed", "")).strip() or None
        persona = str(body.get("persona", "mighan")).strip() or "mighan"
        dry_run = bool(body.get("dry_run", False))

        # Rate limit harian
        if posts_today_count() >= MAX_POSTS_PER_DAY and not dry_run:
            return {
                "ok": False,
                "error": f"Daily post limit tercapai ({MAX_POSTS_PER_DAY}/hari)",
            }

        try:
            from .threads_autopost import generate_content, post_to_threads
        except Exception as e:
            return {"ok": False, "error": f"autopost module error: {e}"}

        try:
            text = generate_content(topic_seed=topic_seed, persona=persona)
        except Exception as e:
            return {"ok": False, "error": f"generate gagal: {e}"}

        if dry_run:
            return {"ok": True, "dry_run": True, "content": text, "char_count": len(text)}

        try:
            result = post_to_threads(text)
        except Exception as e:
            return {"ok": False, "error": f"post gagal: {e}"}

        if result.get("ok"):
            append_post_log({
                "platform": "threads",
                "content": text,
                "post_id_remote": result.get("id", ""),
                "persona": persona,
                "topic_seed": topic_seed,
            })
        return {"content": text, **result}

    return router
