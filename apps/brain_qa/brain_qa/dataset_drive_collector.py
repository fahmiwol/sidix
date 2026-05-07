"""
dataset_drive_collector.py — SIDIX Google Drive Dataset Collector
=================================================================
Collect image metadata dari Google Drive folder (agency assets).

Autentikasi:
  1. OAuth2 Web Flow (recommended untuk user)
     - Daftar app di Google Cloud Console
     - Dapatkan CLIENT_ID dan CLIENT_SECRET
     - Jalankan auth flow → dapatkan ACCESS_TOKEN + REFRESH_TOKEN
  2. Service Account (untuk server-side automation)
     - Butuh service_account.json (di-download dari GCP)

Env vars:
  GOOGLE_DRIVE_ACCESS_TOKEN   — OAuth2 access token (expires ~1 jam)
  GOOGLE_DRIVE_REFRESH_TOKEN  — OAuth2 refresh token (persistent)
  GOOGLE_DRIVE_CLIENT_ID      — OAuth2 client ID
  GOOGLE_DRIVE_CLIENT_SECRET  — OAuth2 client secret

Usage:
  1. Dapatkan folder ID dari URL Google Drive:
     https://drive.google.com/drive/folders/FOLDER_ID
  2. Set env vars atau pass access_token ke function
  3. Panggil collect_drive_dataset(folder_id, access_token)

Image MIME types yang di-support:
  image/jpeg, image/png, image/gif, image/webp, image/bmp, image/tiff, image/svg+xml

Output:
  - JSONL dengan fields: id, name, mimeType, size, width, height, folder_path,
    thumbnail_url, web_view_url, created_at, modified_at, tags, source

Legal:
  - Gambar dari agency sendiri = 100% legal untuk training
  - No copyright risk, no ToS violation
  - Data tetap di Google Drive, hanya metadata yang di-collect

Research notes:
  - 320 Google Drive dataset collection
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
OAUTH2_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN_URL = "https://oauth2.googleapis.com/token"

IMAGE_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/bmp", "image/tiff", "image/svg+xml",
}

SAFETY_MAX_FILES = 5000


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


def _http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    data: dict | None = None,
    timeout: int = 30,
) -> dict:
    """Simple HTTP request with JSON response."""
    req_headers = headers or {}
    body = None
    if data:
        body = json.dumps(data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, method=method, headers=req_headers, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_access_token() -> str | None:
    """Get access token from env var."""
    return os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN") or None


def _get_refresh_token() -> str | None:
    return os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN") or None


def _get_client_credentials() -> tuple[str | None, str | None]:
    return (
        os.environ.get("GOOGLE_DRIVE_CLIENT_ID"),
        os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET"),
    )


# ── 1. OAuth2 Helpers ─────────────────────────────────────────────────────────


def get_auth_url(
    client_id: str | None = None,
    redirect_uri: str = "http://localhost:8080",
    scope: str = "https://www.googleapis.com/auth/drive.readonly",
) -> dict:
    """Generate Google OAuth2 authorization URL.

    User buka URL ini di browser → authorize → Google redirect ke redirect_uri
    dengan ?code=AUTH_CODE.
    """
    if not client_id:
        client_id = _get_client_credentials()[0]
    if not client_id:
        return _fallback(
            "GOOGLE_DRIVE_CLIENT_ID tidak di-set. Daftar di https://console.cloud.google.com/ "
            "→ APIs & Services → Credentials → OAuth 2.0 Client IDs"
        )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"{OAUTH2_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return _ok({
        "auth_url": url,
        "redirect_uri": redirect_uri,
        "instructions": (
            "1. Buka auth_url di browser\n"
            "2. Login & authorize access ke Google Drive\n"
            "3. Copy ?code=... dari URL redirect\n"
            "4. Panggil exchange_auth_code(code) untuk dapatkan access_token + refresh_token"
        ),
    })


def exchange_auth_code(
    code: str,
    redirect_uri: str = "http://localhost:8080",
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict:
    """Exchange authorization code for access token + refresh token."""
    if not client_id:
        client_id = _get_client_credentials()[0]
    if not client_secret:
        client_secret = _get_client_credentials()[1]
    if not client_id or not client_secret:
        return _fallback("GOOGLE_DRIVE_CLIENT_ID dan CLIENT_SECRET wajib di-set")

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        result = _http_request(OAUTH2_TOKEN_URL, method="POST", data=data)
        return _ok({
            "access_token": result.get("access_token"),
            "refresh_token": result.get("refresh_token"),
            "expires_in": result.get("expires_in"),
            "token_type": result.get("token_type"),
            "scope": result.get("scope"),
            "instructions": (
                "Simpan ke environment variable:\n"
                f"GOOGLE_DRIVE_ACCESS_TOKEN={result.get('access_token')}\n"
                f"GOOGLE_DRIVE_REFRESH_TOKEN={result.get('refresh_token')}\n"
                "GOOGLE_DRIVE_CLIENT_ID=...\n"
                "GOOGLE_DRIVE_CLIENT_SECRET=..."
            ),
        })
    except Exception as exc:
        return _fallback(f"OAuth2 exchange error: {exc}")


def refresh_access_token(
    refresh_token: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict:
    """Refresh expired access token using refresh token."""
    if not refresh_token:
        refresh_token = _get_refresh_token()
    if not refresh_token:
        return _fallback("refresh_token wajib di-set (env var GOOGLE_DRIVE_REFRESH_TOKEN)")
    if not client_id:
        client_id = _get_client_credentials()[0]
    if not client_secret:
        client_secret = _get_client_credentials()[1]
    if not client_id or not client_secret:
        return _fallback("GOOGLE_DRIVE_CLIENT_ID dan CLIENT_SECRET wajib di-set")

    data = {
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    }
    try:
        result = _http_request(OAUTH2_TOKEN_URL, method="POST", data=data)
        return _ok({
            "access_token": result.get("access_token"),
            "expires_in": result.get("expires_in"),
            "token_type": result.get("token_type"),
            "scope": result.get("scope"),
            "note": "GOOGLE_DRIVE_ACCESS_TOKEN perlu di-update dengan token baru",
        })
    except Exception as exc:
        return _fallback(f"Token refresh error: {exc}")


# ── 2. Drive API Functions ────────────────────────────────────────────────────


def _drive_api_get(endpoint: str, access_token: str | None = None, params: dict | None = None) -> dict:
    """Internal helper untuk call Drive API."""
    if not access_token:
        access_token = _get_access_token()
    if not access_token:
        raise ValueError("Access token tidak tersedia. Set GOOGLE_DRIVE_ACCESS_TOKEN atau jalankan auth flow.")

    url = f"{DRIVE_API_BASE}/{endpoint}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"

    headers = {"Authorization": f"Bearer {access_token}"}
    return _http_request(url, headers=headers)


def list_drive_images(
    folder_id: str | None = None,
    access_token: str | None = None,
    page_size: int = 100,
    max_files: int = SAFETY_MAX_FILES,
) -> dict:
    """List semua gambar di Google Drive folder (atau root jika folder_id=None).

    Returns metadata: id, name, mimeType, size, createdTime, modifiedTime,
    thumbnailLink, webViewLink, imageMediaMetadata (width, height).
    """
    if not access_token:
        access_token = _get_access_token()
    if not access_token:
        return _fallback(
            "GOOGLE_DRIVE_ACCESS_TOKEN tidak di-set.\n"
            "Cara setup:\n"
            "1. Daftar app di https://console.cloud.google.com/ → APIs & Services → Credentials\n"
            "2. Enable Google Drive API\n"
            "3. Buat OAuth 2.0 Client ID (Desktop app)\n"
            "4. Jalankan get_auth_url() → buka URL → authorize → copy code\n"
            "5. Jalankan exchange_auth_code(code) → simpan access_token & refresh_token\n"
            "6. Set GOOGLE_DRIVE_ACCESS_TOKEN dan GOOGLE_DRIVE_REFRESH_TOKEN sebagai env var"
        )

    # Build query
    query_parts = ["trashed = false", "mimeType contains 'image/'"]
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")
    q = " and ".join(query_parts)

    fields = (
        "nextPageToken,files("
        "id,name,mimeType,size,createdTime,modifiedTime,"
        "parents,thumbnailLink,webViewLink,imageMediaMetadata"
        ")"
    )

    all_files = []
    page_token = None
    total_fetched = 0

    try:
        while total_fetched < max_files:
            params = {
                "q": q,
                "fields": fields,
                "pageSize": min(page_size, max_files - total_fetched),
                "orderBy": "createdTime desc",
            }
            if page_token:
                params["pageToken"] = page_token

            result = _drive_api_get("files", access_token=access_token, params=params)
            files = result.get("files", [])
            all_files.extend(files)
            total_fetched += len(files)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        # Build folder name cache untuk path resolution
        folder_names = {}

        # Enrich with dimensions dari imageMediaMetadata
        enriched = []
        for f in all_files:
            meta = f.get("imageMediaMetadata", {})
            width = meta.get("width")
            height = meta.get("height")

            # Resolve folder path
            parent_ids = f.get("parents", [])
            folder_path = ""
            if parent_ids:
                # Lazy load folder names
                for pid in parent_ids:
                    if pid not in folder_names:
                        try:
                            p = _drive_api_get(f"files/{pid}", access_token=access_token, params={"fields": "name"})
                            folder_names[pid] = p.get("name", "unknown")
                        except Exception:
                            folder_names[pid] = "unknown"
                folder_path = "/".join(folder_names.get(pid, "unknown") for pid in parent_ids)

            # Auto-tag berdasarkan folder name + file name
            tags = _auto_tag_from_path(folder_path, f["name"])

            size_bytes = int(f.get("size", 0)) if f.get("size") else None

            enriched.append({
                "id": f["id"],
                "name": f["name"],
                "mime_type": f["mimeType"],
                "size_bytes": size_bytes,
                "width": width,
                "height": height,
                "folder_id": parent_ids[0] if parent_ids else None,
                "folder_path": folder_path,
                "thumbnail_url": f.get("thumbnailLink"),
                "web_view_url": f.get("webViewLink"),
                "created_at": f.get("createdTime"),
                "modified_at": f.get("modifiedTime"),
                "source": "google_drive",
                "license": "agency_owned",
                "tags": tags,
            })

        return _ok({
            "folder_id": folder_id or "root",
            "total_files": len(enriched),
            "files": enriched,
            "note": "Gambar dari agency = 100% legal untuk training. Hanya metadata yang di-collect, gambar tetap di Drive.",
        })

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        if e.code == 401:
            return _fallback(
                f"Access token expired atau invalid. Status: {e.code}\n"
                f"Response: {body[:200]}\n"
                f"Solusi: jalankan refresh_access_token() atau ulangi auth flow.",
                data={"needs_refresh": True},
            )
        return _fallback(f"Drive API error {e.code}: {body[:200]}")
    except Exception as exc:
        return _fallback(f"Drive list error: {exc}")


def _auto_tag_from_path(folder_path: str, file_name: str) -> list[str]:
    """Auto-tag berdasarkan folder path dan file name."""
    tags = []
    path_lower = (folder_path + " " + file_name).lower()

    # Folder-based tags
    folder_tags = {
        "npc": ["npc", "character", "portrait"],
        "agent": ["agent", "character", "avatar"],
        "sprite": ["sprite", "game", "2d"],
        "texture": ["texture", "material", "3d"],
        "design": ["design", "ui", "graphic"],
        "logo": ["logo", "brand", "identity"],
        "photo": ["photo", "photography"],
        "product": ["product", "catalog", "ecommerce"],
        "banner": ["banner", "ads", "marketing"],
        "social": ["social", "instagram", "content"],
        "web": ["web", "website", "landing"],
        "mobile": ["mobile", "app", "ui"],
        "icon": ["icon", "ui", "small"],
        "background": ["background", "wallpaper", "texture"],
        "mockup": ["mockup", "presentation", "template"],
    }

    for keyword, tag_list in folder_tags.items():
        if keyword in path_lower:
            tags.extend(tag_list)

    # File extension tag
    if file_name.lower().endswith(".png"):
        tags.append("png")
        tags.append("transparent")
    elif file_name.lower().endswith(".jpg") or file_name.lower().endswith(".jpeg"):
        tags.append("jpg")
        tags.append("photograph")
    elif file_name.lower().endswith(".svg"):
        tags.append("svg")
        tags.append("vector")
    elif file_name.lower().endswith(".webp"):
        tags.append("webp")

    # Dimension-based tags
    # (will be added by caller if width/height known)

    return list(set(tags)) if tags else ["agency"]


def get_drive_file(file_id: str, access_token: str | None = None) -> dict:
    """Get detailed metadata untuk single file."""
    if not access_token:
        access_token = _get_access_token()
    if not access_token:
        return _fallback("GOOGLE_DRIVE_ACCESS_TOKEN tidak di-set")

    try:
        result = _drive_api_get(
            f"files/{file_id}",
            access_token=access_token,
            params={"fields": "id,name,mimeType,size,createdTime,modifiedTime,parents,thumbnailLink,webViewLink,imageMediaMetadata,description"},
        )
        meta = result.get("imageMediaMetadata", {})
        return _ok({
            "id": result["id"],
            "name": result["name"],
            "mime_type": result["mimeType"],
            "size_bytes": int(result["size"]) if result.get("size") else None,
            "width": meta.get("width"),
            "height": meta.get("height"),
            "description": result.get("description"),
            "thumbnail_url": result.get("thumbnailLink"),
            "web_view_url": result.get("webViewLink"),
            "created_at": result.get("createdTime"),
            "modified_at": result.get("modifiedTime"),
        })
    except Exception as exc:
        return _fallback(f"Get file error: {exc}")


def collect_drive_dataset(
    folder_id: str | None = None,
    access_token: str | None = None,
    max_files: int = SAFETY_MAX_FILES,
) -> dict:
    """Collect dataset dari Google Drive (metadata only, gambar tetap di Drive).

    Ini adalah primary entry point untuk collect dataset dari Drive agency.
    """
    result = list_drive_images(folder_id, access_token, max_files=max_files)
    if not result.get("ok"):
        return result

    data = result["data"]
    files = data.get("files", [])

    # Add dimension-based tags
    for f in files:
        w = f.get("width")
        h = f.get("height")
        if w and h:
            if w >= 1024 and h >= 1024:
                f["tags"].append("high_res")
            if w >= 2048 and h >= 2048:
                f["tags"].append("ultra_high_res")
            ratio = w / h if h else 0
            if 0.9 <= ratio <= 1.1:
                f["tags"].append("square")
            elif ratio > 1.1:
                f["tags"].append("landscape")
            else:
                f["tags"].append("portrait")
        f["tags"] = list(set(f["tags"]))

    return _ok({
        "folder_id": data["folder_id"],
        "total_files": len(files),
        "total_size_mb": round(sum(f.get("size_bytes", 0) or 0 for f in files) / (1024 * 1024), 2),
        "files": files,
        "license_note": "100% agency-owned content. No copyright risk.",
        "next_steps": [
            "1. Pilih gambar yang relevan untuk training",
            "2. Download via thumbnail_url atau web_view_url (manual atau via tool)",
            "3. Combine dengan local dataset via collect_dataset",
            "4. Run analyze_dataset_dna untuk cek LoRA suitability",
        ],
    })


def export_drive_dataset_jsonl(files: list[dict], output_path: str) -> dict:
    """Export Drive dataset ke JSONL format untuk training pipeline."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in files:
                record = {
                    "id": entry["id"],
                    "file_name": entry["name"],
                    "source": "google_drive",
                    "source_url": entry.get("web_view_url"),
                    "thumbnail_url": entry.get("thumbnail_url"),
                    "width": entry.get("width"),
                    "height": entry.get("height"),
                    "mime_type": entry.get("mime_type"),
                    "size_bytes": entry.get("size_bytes"),
                    "folder_path": entry.get("folder_path"),
                    "tags": entry.get("tags", []),
                    "license": entry.get("license", "agency_owned"),
                    "created_at": entry.get("created_at"),
                    "modified_at": entry.get("modified_at"),
                    "caption": f"{entry['name']} — {', '.join(entry.get('tags', []))}",
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return _ok({"output_path": output_path, "count": len(files)})
    except Exception as exc:
        return _fallback(f"Export error: {exc}")


# ── 3. Health Check ───────────────────────────────────────────────────────────


def drive_health_check(access_token: str | None = None) -> dict:
    """Check Google Drive API connectivity dan token validity."""
    if not access_token:
        access_token = _get_access_token()
    if not access_token:
        return _fallback(
            "GOOGLE_DRIVE_ACCESS_TOKEN tidak di-set.\n"
            "Jalankan get_auth_url() untuk mulai auth flow."
        )

    try:
        # Call about API untuk cek user info
        result = _drive_api_get("about", access_token=access_token, params={"fields": "user,storageQuota"})
        user = result.get("user", {})
        quota = result.get("storageQuota", {})
        return _ok({
            "connected": True,
            "user_email": user.get("emailAddress"),
            "user_name": user.get("displayName"),
            "total_storage": quota.get("limit"),
            "used_storage": quota.get("usage"),
            "token_valid": True,
        })
    except Exception as exc:
        return _fallback(f"Drive health check error: {exc}", data={"connected": False, "token_valid": False})
