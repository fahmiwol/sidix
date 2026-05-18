"""
auth_google.py — SIDIX Own Auth dengan Google Identity Services.

Migrasi dari Supabase Auth ke own auth (Pivot 2026-04-26):
- Lebih ringan, no third-party dependency untuk auth
- Full control data user
- Activity log per-user
- Database user di SIDIX sendiri

Flow:
  1. Frontend: Google Sign-In button → OAuth → ID token JWT
  2. POST /auth/google {credential: <id_token>} ke backend
  3. Backend verify token via Google public keys
  4. Backend create/update user di local store
  5. Backend issue session JWT (HMAC-signed)
  6. Frontend simpan JWT di localStorage
  7. Subsequent requests: Authorization: Bearer <session_jwt>

Storage:
- User database: apps/brain_qa/.data/users.json (atau SQLite)
- Activity log: apps/brain_qa/.data/activity_log.jsonl

Env:
- GOOGLE_OAUTH_CLIENT_ID (publik, di-embed frontend)
- SIDIX_JWT_SECRET (rahasia, sign session JWT)
"""

from __future__ import annotations

import hmac
import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


_USER_STORE_PATH: Optional[Path] = None
_ACTIVITY_LOG_PATH: Optional[Path] = None
_LOCK = threading.Lock()


def _resolve_paths() -> tuple[Path, Path]:
    global _USER_STORE_PATH, _ACTIVITY_LOG_PATH
    if _USER_STORE_PATH is not None and _ACTIVITY_LOG_PATH is not None:
        return _USER_STORE_PATH, _ACTIVITY_LOG_PATH
    here = Path(__file__).resolve().parent
    data_dir = here.parent / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _USER_STORE_PATH = data_dir / "users.json"
    _ACTIVITY_LOG_PATH = data_dir / "activity_log.jsonl"
    return _USER_STORE_PATH, _ACTIVITY_LOG_PATH


# ─── Google ID Token verification ──────────────────────────────────────────

def verify_google_id_token(id_token: str) -> Optional[dict]:
    """
    Verify Google ID token JWT via Google's public keys (tokeninfo endpoint
    untuk simplicity, tanpa dependency google-auth lib heavy).

    Returns user info dict kalau valid:
        {sub, email, email_verified, name, picture, given_name, family_name, ...}
    Returns None kalau invalid/expired.
    """
    if not id_token or not id_token.strip():
        return None
    try:
        import httpx
        with httpx.Client(timeout=10.0) as client:
            r = client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": id_token},
            )
        if r.status_code != 200:
            return None
        data = r.json()
        # Validate audience (client ID)
        client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
        if client_id and data.get("aud") != client_id:
            import logging
            logging.warning(f"[auth_google] aud mismatch: {data.get('aud')} != {client_id}")
            return None
        # Validate not expired
        exp = int(data.get("exp", 0))
        if exp and exp < time.time():
            return None
        # Validate email verified
        if data.get("email_verified") not in (True, "true"):
            return None
        return data
    except Exception as e:
        import logging
        logging.warning(f"[auth_google] verify fail: {e}")
        return None


# ─── User store (JSON file, simple) ────────────────────────────────────────

def _load_users() -> dict:
    path, _ = _resolve_paths()
    if not path.exists():
        return {"version": 1, "users": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "users": {}}


def _save_users(data: dict) -> None:
    path, _ = _resolve_paths()
    with _LOCK:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def upsert_user(google_info: dict) -> dict:
    """Insert or update user dari Google ID token info."""
    sub = google_info.get("sub", "")
    email = (google_info.get("email") or "").strip().lower()
    if not sub or not email:
        raise ValueError("invalid google info: missing sub or email")

    data = _load_users()
    users = data.get("users") or {}
    now = datetime.now(timezone.utc).isoformat()
    existing = users.get(sub)

    if existing:
        existing.update({
            "email": email,
            "name": google_info.get("name", existing.get("name", "")),
            "picture": google_info.get("picture", existing.get("picture", "")),
            "given_name": google_info.get("given_name", existing.get("given_name", "")),
            "family_name": google_info.get("family_name", existing.get("family_name", "")),
            "last_login_at": now,
            "login_count": (existing.get("login_count", 0) + 1),
        })
        user = existing
    else:
        user = {
            "id": f"u_{uuid.uuid4().hex[:12]}",
            "google_sub": sub,
            "email": email,
            "name": google_info.get("name", ""),
            "picture": google_info.get("picture", ""),
            "given_name": google_info.get("given_name", ""),
            "family_name": google_info.get("family_name", ""),
            "created_at": now,
            "last_login_at": now,
            "login_count": 1,
            "tier": "free",
            "is_admin": False,
        }
        users[sub] = user

    data["users"] = users
    _save_users(data)
    return user


def get_user_by_id(user_id: str) -> Optional[dict]:
    """Lookup by SIDIX user_id (u_xxx)."""
    data = _load_users()
    for user in (data.get("users") or {}).values():
        if user.get("id") == user_id:
            return user
    return None


def get_user_by_email(email: str) -> Optional[dict]:
    em = (email or "").strip().lower()
    if not em:
        return None
    data = _load_users()
    for user in (data.get("users") or {}).values():
        if user.get("email") == em:
            return user
    return None


def list_users(limit: int = 200) -> list[dict]:
    data = _load_users()
    users = list((data.get("users") or {}).values())
    users.sort(key=lambda u: u.get("last_login_at") or "", reverse=True)
    return users[:limit]


def stats() -> dict:
    data = _load_users()
    users = list((data.get("users") or {}).values())
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    active_today = sum(1 for u in users if (u.get("last_login_at") or "")[:10] == today)
    return {
        "total_users": len(users),
        "active_today": active_today,
        "by_tier": {
            tier: sum(1 for u in users if u.get("tier") == tier)
            for tier in ("free", "sponsored", "whitelist", "admin")
        },
    }


# ─── Session JWT (HMAC-signed) ─────────────────────────────────────────────

def _b64url_encode(b: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    import base64
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _jwt_secret() -> bytes:
    secret = os.environ.get("SIDIX_JWT_SECRET", "").strip()
    if not secret:
        # Auto-generate weak fallback (warn) — production HARUS set env
        secret = "sidix-dev-jwt-not-secure-change-in-prod"
        import logging
        logging.warning("[auth_google] SIDIX_JWT_SECRET not set, using insecure default")
    return secret.encode("utf-8")


def issue_session_jwt(user_id: str, email: str, *, ttl_seconds: int = 30 * 24 * 3600) -> str:
    """Issue HMAC-SHA256 signed JWT session token. Default TTL 30 hari."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + ttl_seconds,
        "iss": "sidix",
    }
    h = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing = f"{h}.{p}".encode("utf-8")
    sig = hmac.new(_jwt_secret(), signing, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url_encode(sig)}"


def verify_session_jwt(token: str) -> Optional[dict]:
    """Verify HMAC JWT, return payload kalau valid + not expired."""
    if not token:
        return None
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        h, p, s = parts
        signing = f"{h}.{p}".encode("utf-8")
        expected_sig = hmac.new(_jwt_secret(), signing, hashlib.sha256).digest()
        actual_sig = _b64url_decode(s)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(p).decode("utf-8"))
        # Check expiry
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        if payload.get("iss") != "sidix":
            return None
        return payload
    except Exception:
        return None


def extract_user_from_request(request: Any) -> Optional[dict]:
    """
    Extract user payload dari request Authorization header.
    Returns {sub, email, ...} kalau valid JWT, None kalau tidak.
    """
    auth = ""
    try:
        auth = request.headers.get("authorization", "") or ""
    except Exception:
        return None
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    return verify_session_jwt(token)


# ─── Activity log (per-user) ───────────────────────────────────────────────

def log_activity(
    user_id: str,
    email: str,
    *,
    action: str,           # "ask" / "agent/burst" / "agent/foresight" / dll
    question: str = "",
    answer_preview: str = "",
    persona: str = "",
    mode: str = "",
    citations_count: int = 0,
    latency_ms: int = 0,
    ip: str = "",
    error: str = "",
) -> None:
    """Append activity log entry sebagai JSONL line. Non-blocking, best-effort."""
    try:
        _, log_path = _resolve_paths()
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "email": email,
            "action": action,
            "question": (question or "")[:200],
            "answer_preview": (answer_preview or "")[:160],
            "persona": persona,
            "mode": mode,
            "citations": citations_count,
            "latency_ms": latency_ms,
            "ip": ip[:32],
            "error": (error or "")[:200] if error else "",
        }
        with _LOCK:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # never block main flow


def list_activity(*, limit: int = 200, user_id: Optional[str] = None) -> list[dict]:
    """Read tail dari activity_log.jsonl. Filter optional by user_id."""
    _, log_path = _resolve_paths()
    if not log_path.exists():
        return []
    try:
        # Read last N lines (simple, OK untuk file < 100MB)
        with log_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        entries = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                if user_id and e.get("user_id") != user_id:
                    continue
                entries.append(e)
                if len(entries) >= limit:
                    break
            except Exception:
                continue
        return entries
    except Exception:
        return []
