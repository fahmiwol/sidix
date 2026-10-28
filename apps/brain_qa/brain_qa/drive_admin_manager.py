"""
drive_admin_manager.py — Admin Google Drive Token Manager
==========================================================
Manage OAuth2 tokens untuk multiple Google Drive accounts via admin panel.

Features:
  - Store tokens di JSON file (runtime-reloadable, tanpa restart)
  - CRUD operations (add, list, delete, refresh)
  - Account status check (connected / expired / invalid)
  - Generate OAuth2 auth URL untuk new account
  - Exchange auth code → tokens

Security:
  - Hanya callable dari admin endpoints (gated by _admin_ok)
  - Token file di .data/ (gitignored)
  - No client_secret di frontend — exchange via backend only

Usage (admin endpoints):
  GET  /admin/drive/accounts      → list all accounts + status
  POST /admin/drive/connect       → start OAuth (return auth_url)
  POST /admin/drive/exchange      → exchange code → store token
  POST /admin/drive/refresh       → refresh access token
  DELETE /admin/drive/account/{name} → revoke & delete
"""
from __future__ import annotations

import json
import os
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dataset_drive_collector import (
    exchange_auth_code,
    refresh_access_token,
    OAUTH2_AUTH_URL,
    list_drive_images,
)

TOKEN_FILE = Path(__file__).resolve().parent / ".data" / "drive_tokens.json"


def _load_tokens() -> dict:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    return {}


def _save_tokens(data: dict) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_accounts() -> dict:
    """List all configured Drive accounts with connection status."""
    tokens = _load_tokens()
    accounts = []
    for name, cfg in tokens.get("accounts", {}).items():
        status = "unknown"
        try:
            result = list_drive_images(folder_id="root", account=name, max_files=1)
            status = "connected" if result.get("ok") else "error"
        except Exception:
            status = "disconnected"
        accounts.append({
            "name": name,
            "email": cfg.get("email", ""),
            "status": status,
            "created_at": cfg.get("created_at", ""),
            "last_refresh": cfg.get("last_refresh", ""),
            "scopes": cfg.get("scope", ""),
        })
    return {"ok": True, "accounts": accounts, "total": len(accounts)}


def generate_auth_url(
    account_name: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    redirect_uri: str = "https://sidixlab.com/admin/drive/callback",
    scope: str = "https://www.googleapis.com/auth/drive.readonly",
) -> dict:
    """Generate OAuth2 auth URL untuk account baru."""
    if not client_id:
        client_id = os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "").strip()
    if not client_secret:
        client_secret = os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "").strip()
    if not client_id:
        return {"ok": False, "error": "GOOGLE_DRIVE_CLIENT_ID belum di-set di .env"}

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": account_name,
    }
    url = f"{OAUTH2_AUTH_URL}?{urllib.parse.urlencode(params)}"

    # Simpan pending connection metadata
    tokens = _load_tokens()
    tokens.setdefault("pending", {})[account_name] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_tokens(tokens)

    return {"ok": True, "auth_url": url, "account": account_name, "redirect_uri": redirect_uri}


def exchange_and_store(
    account_name: str,
    code: str,
) -> dict:
    """Exchange auth code dan store refresh_token untuk account."""
    tokens = _load_tokens()
    pending = tokens.get("pending", {}).get(account_name)
    if not pending:
        return {"ok": False, "error": f"Tidak ada pending connection untuk '{account_name}'. Generate auth URL dulu."}

    client_id = pending.get("client_id") or os.environ.get("GOOGLE_DRIVE_CLIENT_ID", "")
    client_secret = pending.get("client_secret") or os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", "")
    redirect_uri = pending.get("redirect_uri", "https://sidixlab.com/admin/drive/callback")

    if not client_id or not client_secret:
        return {"ok": False, "error": "client_id dan client_secret wajib di-set"}

    result = exchange_auth_code(
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
    )

    if not result.get("ok"):
        return {"ok": False, "error": result.get("fallback_instructions", "Exchange gagal")}

    data = result.get("data", {})
    refresh_token = data.get("refresh_token")
    access_token = data.get("access_token")

    if not refresh_token:
        return {"ok": False, "error": "Google tidak mengembalikan refresh_token. Pastikan access_type=offline dan prompt=consent."}

    # Store securely
    tokens.setdefault("accounts", {})[account_name] = {
        "refresh_token": refresh_token,
        "access_token": access_token,
        "scope": data.get("scope", ""),
        "token_type": data.get("token_type", "Bearer"),
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_refresh": datetime.now(timezone.utc).isoformat(),
    }
    # Clean pending
    tokens.get("pending", {}).pop(account_name, None)
    _save_tokens(tokens)

    # Also set env var for immediate use
    os.environ[f"GOOGLE_DRIVE_REFRESH_TOKEN_{account_name.upper()}"] = refresh_token
    os.environ[f"GOOGLE_DRIVE_ACCESS_TOKEN_{account_name.upper()}"] = access_token

    return {
        "ok": True,
        "account": account_name,
        "access_token": access_token,
        "expires_in": data.get("expires_in"),
        "note": f"Token tersimpan. Env var GOOGLE_DRIVE_REFRESH_TOKEN_{account_name.upper()} di-set.",
    }


def refresh_account_token(account_name: str) -> dict:
    """Refresh access token untuk account."""
    tokens = _load_tokens()
    cfg = tokens.get("accounts", {}).get(account_name)
    if not cfg:
        return {"ok": False, "error": f"Account '{account_name}' tidak ditemukan."}

    result = refresh_access_token(
        refresh_token=cfg.get("refresh_token"),
        client_id=cfg.get("client_id") or os.environ.get("GOOGLE_DRIVE_CLIENT_ID", ""),
        client_secret=cfg.get("client_secret") or os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET", ""),
    )

    if not result.get("ok"):
        return {"ok": False, "error": result.get("fallback_instructions", "Refresh gagal")}

    data = result.get("data", {})
    access_token = data.get("access_token")
    cfg["access_token"] = access_token
    cfg["last_refresh"] = datetime.now(timezone.utc).isoformat()
    _save_tokens(tokens)

    os.environ[f"GOOGLE_DRIVE_ACCESS_TOKEN_{account_name.upper()}"] = access_token
    return {"ok": True, "account": account_name, "access_token": access_token}


def delete_account(account_name: str) -> dict:
    """Hapus account dari token store."""
    tokens = _load_tokens()
    accounts = tokens.get("accounts", {})
    if account_name not in accounts:
        return {"ok": False, "error": f"Account '{account_name}' tidak ditemukan."}
    del accounts[account_name]
    _save_tokens(tokens)

    # Clear env var
    for prefix in ["GOOGLE_DRIVE_ACCESS_TOKEN_", "GOOGLE_DRIVE_REFRESH_TOKEN_"]:
        key = f"{prefix}{account_name.upper()}"
        if key in os.environ:
            del os.environ[key]

    return {"ok": True, "message": f"Account '{account_name}' dihapus."}


def get_account_token(account_name: str) -> dict:
    """Get stored token info (tanpa expose secret) untuk admin UI."""
    tokens = _load_tokens()
    cfg = tokens.get("accounts", {}).get(account_name)
    if not cfg:
        return {"ok": False, "error": f"Account '{account_name}' tidak ditemukan."}
    return {
        "ok": True,
        "account": account_name,
        "email": cfg.get("email", ""),
        "scope": cfg.get("scope", ""),
        "created_at": cfg.get("created_at", ""),
        "last_refresh": cfg.get("last_refresh", ""),
        "has_refresh_token": bool(cfg.get("refresh_token")),
        "has_access_token": bool(cfg.get("access_token")),
    }
