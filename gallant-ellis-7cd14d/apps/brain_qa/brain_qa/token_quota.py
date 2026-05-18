"""
token_quota.py — SIDIX User Token Quota System.

Setiap user punya batas harian berdasarkan tier:
  guest     → 3 pesan/hari  (IP-based)
  free      → 10 pesan/hari (Supabase user_id)
  sponsored → 100 pesan/hari + Sonnet access
  admin     → unlimited

Cara kerja:
  1. Request masuk → check_quota(user_id_or_ip) → ok/limit_hit
  2. Jika ok → proses chat
  3. Setelah selesai → record_usage(...)
  4. Response menyertakan quota info: {used, limit, remaining, tier}

Storage: .data/quota/ per hari (JSON sederhana, cepat)
Untuk prod scale → ganti ke Supabase usage_logs table
"""

from __future__ import annotations

import json
import datetime
import hashlib
from pathlib import Path
from typing import Optional, Literal

# ── Config ─────────────────────────────────────────────────────────────────────

QuotaTier = Literal["guest", "free", "sponsored", "whitelist", "admin"]

# Pivot 2026-04-26: limits naik supaya UX free tier lebih enak.
# Strategy: guest cukup buat try, login dapat substantial value, whitelist/admin unlimited.
QUOTA_LIMITS: dict[QuotaTier, int] = {
    "guest":     5,    # IP-based, tanpa login (was 3, naik 5 supaya bisa try lebih)
    "free":      30,   # login gratis (was 10, naik 30 supaya casual user puas)
    "sponsored": 200,  # sudah top up (was 100, naik 200 untuk power user)
    "whitelist": 9999, # owner / dev / sponsor / researcher / contributor (admin-managed)
    "admin":     9999, # unlimited efektif
}

# Model per tier — semua tier pakai local LLM (Ollama/LoRA/Mock)
# Standing Alone: tidak ada vendor cloud API di inference pipeline
TIER_MODELS: dict[QuotaTier, str] = {
    "guest":     "local",
    "free":      "local",
    "sponsored": "local",
    "whitelist": "local",
    "admin":     "local",
}

# Trakteer/Saweria link untuk top up
TOPUP_URL = "https://trakteer.id/sidixlab"  # update ke URL asli
TOPUP_WA  = "https://wa.me/6281234567890"   # update ke nomor WA resmi

_BASE = Path(__file__).parent.parent.parent
_QUOTA_DIR = _BASE / ".data" / "quota"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _today() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _quota_file() -> Path:
    _QUOTA_DIR.mkdir(parents=True, exist_ok=True)
    return _QUOTA_DIR / f"quota_{_today()}.json"


def _load_today() -> dict:
    f = _quota_file()
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_today(data: dict) -> None:
    _quota_file().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _user_key(user_id: Optional[str], ip: str) -> str:
    """Buat key unik per user. Jika belum login, hash IP."""
    if user_id:
        return f"user:{user_id}"
    # Hash IP agar tidak expose raw IP
    return f"ip:{hashlib.sha256(ip.encode()).hexdigest()[:16]}"


def _load_sponsored_users() -> set[str]:
    """Load daftar user_id yang sudah top up (sponsored tier)."""
    f = _BASE / ".data" / "sponsored_users.json"
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            return set(data.get("user_ids", []))
        except Exception:
            pass
    return set()


def _get_tier(user_id: Optional[str], is_admin: bool = False) -> QuotaTier:
    """Tentukan tier user berdasarkan login status dan sponsored list."""
    if is_admin:
        return "admin"
    if not user_id:
        return "guest"
    if user_id in _load_sponsored_users():
        return "sponsored"
    return "free"


def _is_whitelisted_user(user_id: Optional[str], email: Optional[str] = None) -> bool:
    """
    Pivot 2026-04-26: cek whitelist 2-layer (env + JSON store).

    Email > user_id checking. Owner/dev/sponsor/researcher/contributor di whitelist
    bypass quota limits.
    """
    import os
    raw_emails = os.environ.get("SIDIX_WHITELIST_EMAILS", "").strip().lower()
    raw_uids = os.environ.get("SIDIX_WHITELIST_USER_IDS", "").strip()
    if email:
        em = email.strip().lower()
        if em and raw_emails:
            env_emails = {e.strip() for e in raw_emails.split(",") if e.strip()}
            if em in env_emails:
                return True
    if user_id and raw_uids:
        env_uids = {u.strip() for u in raw_uids.split(",") if u.strip()}
        if user_id in env_uids:
            return True
    # JSON store layer
    try:
        from . import whitelist_store
        if email and whitelist_store.is_email_whitelisted(email):
            return True
        if user_id and whitelist_store.is_user_id_whitelisted(user_id):
            return True
    except Exception:
        pass
    return False


# ── Core Functions ─────────────────────────────────────────────────────────────

def check_quota(
    user_id: Optional[str],
    ip: str = "unknown",
    is_admin: bool = False,
    email: Optional[str] = None,
) -> dict:
    """
    Cek apakah user masih punya quota.

    Pivot 2026-04-26: tambah `email` param + cek whitelist (2-layer env+JSON).
    Whitelist user → tier 'whitelist' (unlimited efektif).

    Returns:
    {
      "ok": True/False,
      "tier": "guest"|"free"|"sponsored"|"whitelist"|"admin",
      "used": int,
      "limit": int,
      "remaining": int,
      "model": str,          ← model yang boleh dipakai
      "reset_at": str,       ← kapan quota reset (UTC midnight)
      "topup_url": str,      ← jika limit, link untuk top up
      "message": str,        ← pesan untuk user
      "unlimited": bool,     ← True untuk whitelist/admin (frontend hide counter)
    }
    """
    # Whitelist check pertama (tertinggi prioritas)
    if _is_whitelisted_user(user_id, email):
        tier: QuotaTier = "whitelist"
    else:
        tier = _get_tier(user_id, is_admin)
    limit = QUOTA_LIMITS[tier]
    model = TIER_MODELS[tier]
    key = _user_key(user_id, ip)

    data = _load_today()
    used = data.get(key, {}).get("count", 0)
    remaining = max(0, limit - used)

    # Hitung reset time (UTC midnight)
    now = datetime.datetime.utcnow()
    tomorrow = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    if remaining <= 0:
        return {
            "ok": False,
            "tier": tier,
            "used": used,
            "limit": limit,
            "remaining": 0,
            "model": model,
            "reset_at": tomorrow.isoformat() + "Z",
            "topup_url": TOPUP_URL,
            "topup_wa": TOPUP_WA,
            "message": _limit_message(tier, used, limit, tomorrow),
        }

    return {
        "ok": True,
        "tier": tier,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "model": model,
        "reset_at": tomorrow.isoformat() + "Z",
        "topup_url": TOPUP_URL,
        "topup_wa": TOPUP_WA,
        "message": "",
    }


def record_usage(
    user_id: Optional[str],
    ip: str = "unknown",
    tokens_in: int = 0,
    tokens_out: int = 0,
    model: str = "unknown",
    session_id: str = "",
) -> dict:
    """
    Catat 1 pesan ke quota harian.
    Dipanggil SETELAH chat selesai.
    """
    key = _user_key(user_id, ip)
    data = _load_today()

    entry = data.get(key, {"count": 0, "tokens_in": 0, "tokens_out": 0, "sessions": []})
    entry["count"] += 1
    entry["tokens_in"] = entry.get("tokens_in", 0) + tokens_in
    entry["tokens_out"] = entry.get("tokens_out", 0) + tokens_out

    if session_id and len(entry.get("sessions", [])) < 50:
        entry["sessions"] = entry.get("sessions", []) + [session_id]

    data[key] = entry
    _save_today(data)

    tier = _get_tier(user_id)
    limit = QUOTA_LIMITS[tier]
    used = entry["count"]

    return {
        "ok": True,
        "used": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "tier": tier,
    }


def add_sponsored_user(user_id: str) -> bool:
    """Tambahkan user ke daftar sponsored (setelah top up). Dipanggil manual oleh admin."""
    f = _BASE / ".data" / "sponsored_users.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    data = {"user_ids": []}
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    if user_id not in data["user_ids"]:
        data["user_ids"].append(user_id)
    f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def remove_sponsored_user(user_id: str) -> bool:
    """Hapus dari sponsored (opsional)."""
    f = _BASE / ".data" / "sponsored_users.json"
    if not f.exists():
        return False
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        data["user_ids"] = [uid for uid in data["user_ids"] if uid != user_id]
        f.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False


def get_quota_stats(date: Optional[str] = None) -> dict:
    """Statistik quota usage untuk tanggal tertentu (default: hari ini)."""
    target = date or _today()
    f = _QUOTA_DIR / f"quota_{target}.json"
    if not f.exists():
        return {"date": target, "total_users": 0, "total_messages": 0, "breakdown": {}}

    data = json.loads(f.read_text(encoding="utf-8"))
    total_msgs = sum(v.get("count", 0) for v in data.values())
    guest_count = sum(1 for k in data if k.startswith("ip:"))
    user_count = sum(1 for k in data if k.startswith("user:"))

    return {
        "date": target,
        "total_users": len(data),
        "guest_sessions": guest_count,
        "member_sessions": user_count,
        "total_messages": total_msgs,
        "total_tokens_in": sum(v.get("tokens_in", 0) for v in data.values()),
        "total_tokens_out": sum(v.get("tokens_out", 0) for v in data.values()),
    }


def _limit_message(tier: QuotaTier, used: int, limit: int, reset_at: datetime.datetime) -> str:
    """Pesan saat limit tercapai."""
    hrs = int((reset_at - datetime.datetime.utcnow()).total_seconds() / 3600)
    if tier == "guest":
        return (
            f"Kamu sudah menggunakan {used} dari {limit} pesan gratis hari ini. "
            f"Login untuk dapat 10 pesan/hari, atau top up untuk akses lebih. "
            f"Reset dalam ~{hrs} jam."
        )
    elif tier == "free":
        return (
            f"Kamu sudah menggunakan semua {limit} pesan gratis hari ini. "
            f"Top up untuk melanjutkan sekarang, atau tunggu reset dalam ~{hrs} jam."
        )
    return f"Quota habis. Reset dalam ~{hrs} jam."
