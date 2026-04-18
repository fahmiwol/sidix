"""
threads_oauth.py — Threads (Meta) OAuth 2.0 + auto-posting untuk SIDIX.

Flow:
1. User → GET /threads/auth → redirect ke Meta OAuth
2. Meta → GET /threads/callback?code=XXX → tukar code → simpan token
3. SIDIX → POST /threads/post → post konten ke Threads

Environment variables (dari .env atau PM2 env_production):
  THREADS_APP_ID
  THREADS_APP_SECRET
  THREADS_REDIRECT_URI     (default: https://ctrl.sidixlab.com/threads/callback)
  THREADS_API_BASE         (default: https://graph.threads.net/v1.0)

Token disimpan di: .data/threads_token.json
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional


# ── Config ─────────────────────────────────────────────────────────────────────

APP_ID = os.getenv("THREADS_APP_ID", "")
APP_SECRET = os.getenv("THREADS_APP_SECRET", "")
REDIRECT_URI = os.getenv("THREADS_REDIRECT_URI", "https://ctrl.sidixlab.com/threads/callback")
API_BASE = os.getenv("THREADS_API_BASE", "https://graph.threads.net/v1.0")

# Scope yang diminta
SCOPES = "threads_basic,threads_content_publish,threads_read_replies,threads_manage_replies"

# Token storage
_TOKEN_FILE = Path(__file__).parent.parent.parent / ".data" / "threads_token.json"


# ── Token Storage ──────────────────────────────────────────────────────────────

def _load_token() -> dict:
    """Load token dari file. Return {} jika tidak ada."""
    if _TOKEN_FILE.exists():
        try:
            return json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_token(data: dict) -> None:
    """Simpan token ke file."""
    _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_token() -> Optional[str]:
    """Return access_token jika ada dan belum expired."""
    data = _load_token()
    if not data:
        return None
    access_token = data.get("access_token")
    expires_at = data.get("expires_at", 0)
    if not access_token:
        return None
    # Long-lived token = 60 hari; warn jika sisa < 7 hari
    if expires_at and time.time() > expires_at:
        return None  # expired
    return access_token


def get_token_info() -> dict:
    """Return info token (tanpa secret)."""
    data = _load_token()
    if not data:
        return {"connected": False}
    expires_at = data.get("expires_at", 0)
    remaining_days = max(0, int((expires_at - time.time()) / 86400)) if expires_at else None
    return {
        "connected": bool(data.get("access_token")),
        "user_id": data.get("user_id"),
        "username": data.get("username"),
        "expires_at": expires_at,
        "remaining_days": remaining_days,
        "has_expired": bool(expires_at and time.time() > expires_at),
    }


# ── OAuth Flow ─────────────────────────────────────────────────────────────────

def build_auth_url(state: str = "sidix_oauth") -> str:
    """Generate URL untuk redirect user ke Meta OAuth."""
    import urllib.parse
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "state": state,
    }
    base = "https://threads.net/oauth/authorize"
    return base + "?" + urllib.parse.urlencode(params)


def exchange_code(code: str) -> dict:
    """
    Tukar authorization code → short-lived token → long-lived token.
    Return: {"access_token": ..., "user_id": ..., "expires_at": ...}
    """
    import urllib.request
    import urllib.parse

    # Step 1: Exchange code → short-lived token
    token_url = "https://graph.threads.net/oauth/access_token"
    payload = urllib.parse.urlencode({
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code,
    }).encode()

    req = urllib.request.Request(token_url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        short_data = json.loads(resp.read())

    short_token = short_data.get("access_token")
    user_id = short_data.get("user_id")
    if not short_token:
        raise ValueError(f"Tidak dapat short-lived token: {short_data}")

    # Step 2: Exchange → long-lived token (60 hari)
    ll_url = (
        f"{API_BASE}/access_token"
        f"?grant_type=th_exchange_token"
        f"&client_secret={APP_SECRET}"
        f"&access_token={short_token}"
    )
    req2 = urllib.request.Request(ll_url)
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        ll_data = json.loads(resp2.read())

    long_token = ll_data.get("access_token", short_token)
    expires_in = ll_data.get("expires_in", 60 * 86400)

    # Fetch username
    username = _fetch_username(long_token, user_id)

    token_record = {
        "access_token": long_token,
        "user_id": user_id,
        "username": username,
        "obtained_at": int(time.time()),
        "expires_at": int(time.time()) + expires_in,
        "expires_in": expires_in,
    }
    _save_token(token_record)
    return token_record


def _fetch_username(access_token: str, user_id: str) -> str:
    """Fetch @username dari Threads API."""
    import urllib.request
    url = f"{API_BASE}/{user_id}?fields=username&access_token={access_token}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("username", "")
    except Exception:
        return ""


# ── Posting ────────────────────────────────────────────────────────────────────

def create_text_post(text: str, access_token: Optional[str] = None) -> dict:
    """
    Buat post teks di Threads.
    Return: {"ok": True, "post_id": "...", "permalink": "..."}
    """
    import urllib.request
    import urllib.parse

    token = access_token or get_token()
    if not token:
        raise ValueError("Tidak ada access token Threads. Hubungkan akun dulu via /threads/auth")

    token_data = _load_token()
    user_id = token_data.get("user_id")
    if not user_id:
        raise ValueError("user_id tidak ditemukan di token storage")

    # Step 1: Create media container
    create_url = f"{API_BASE}/{user_id}/threads"
    payload = urllib.parse.urlencode({
        "media_type": "TEXT",
        "text": text,
        "access_token": token,
    }).encode()

    req = urllib.request.Request(create_url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        container = json.loads(resp.read())

    container_id = container.get("id")
    if not container_id:
        raise ValueError(f"Gagal create container: {container}")

    # Step 2: Publish
    publish_url = f"{API_BASE}/{user_id}/threads_publish"
    pub_payload = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": token,
    }).encode()

    req2 = urllib.request.Request(publish_url, data=pub_payload, method="POST")
    with urllib.request.urlopen(req2, timeout=15) as resp2:
        pub_data = json.loads(resp2.read())

    post_id = pub_data.get("id", "")
    username = token_data.get("username", "")
    permalink = f"https://www.threads.net/@{username}/post/{post_id}" if username and post_id else ""

    return {
        "ok": True,
        "post_id": post_id,
        "permalink": permalink,
    }


def get_recent_posts(limit: int = 5) -> list[dict]:
    """Ambil posts terbaru dari akun Threads."""
    import urllib.request

    token = get_token()
    if not token:
        return []

    token_data = _load_token()
    user_id = token_data.get("user_id", "me")

    url = (
        f"{API_BASE}/{user_id}/threads"
        f"?fields=id,text,timestamp,permalink"
        f"&limit={limit}"
        f"&access_token={token}"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("data", [])
    except Exception as e:
        return [{"error": str(e)}]


# ── SIDIX Auto-post Content Generator ─────────────────────────────────────────

SIDIX_POST_TEMPLATES = [
    "🧠 SIDIX baru belajar tentang {topic}. Mau ikut? sidixlab.com",
    "📚 Research terbaru SIDIX: {topic}. Dibangun dengan epistemologi Islam + AI modern. sidixlab.com",
    "🌐 SIDIX update: {topic}. AI lokal, bahasa Indonesia, no vendor API. sidixlab.com",
    "⚡ SIDIX milestone: {topic}. Bergabung komunitas: sidixlab.com",
    "🔬 Dari riset ke aksi: {topic}. SIDIX terus belajar. sidixlab.com",
]


def generate_sidix_post(topic: str, template_idx: int = 0) -> str:
    """Generate post text dari template SIDIX."""
    idx = template_idx % len(SIDIX_POST_TEMPLATES)
    return SIDIX_POST_TEMPLATES[idx].format(topic=topic)
