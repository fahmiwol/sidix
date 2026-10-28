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


def _get_access_token(account: str | None = None) -> str | None:
    """Get access token from env var or admin token store. Support multi-account.
    
    Priority: env var → admin token file (runtime-managed by drive_admin_manager)
    """
    key = "GOOGLE_DRIVE_ACCESS_TOKEN"
    if account:
        key += f"_{account.upper()}"
    token = os.environ.get(key) or os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
    if token:
        return token
    # Fallback: read from admin token store
    try:
        from drive_admin_manager import _load_tokens
        data = _load_tokens()
        cfg = data.get("accounts", {}).get(account or "", {})
        return cfg.get("access_token")
    except Exception:
        return None


def _get_refresh_token(account: str | None = None) -> str | None:
    key = "GOOGLE_DRIVE_REFRESH_TOKEN"
    if account:
        key += f"_{account.upper()}"
    token = os.environ.get(key) or os.environ.get("GOOGLE_DRIVE_REFRESH_TOKEN")
    if token:
        return token
    # Fallback: read from admin token store
    try:
        from drive_admin_manager import _load_tokens
        data = _load_tokens()
        cfg = data.get("accounts", {}).get(account or "", {})
        return cfg.get("refresh_token")
    except Exception:
        return None


def _get_client_credentials() -> tuple[str | None, str | None]:
    return (
        os.environ.get("GOOGLE_DRIVE_CLIENT_ID"),
        os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET"),
    )


def list_configured_accounts() -> list[str]:
    """Detect all configured Google Drive accounts from env vars.
    
    Looks for GOOGLE_DRIVE_ACCESS_TOKEN_* patterns.
    """
    accounts = set()
    for key in os.environ:
        if key.startswith("GOOGLE_DRIVE_ACCESS_TOKEN_"):
            account = key.replace("GOOGLE_DRIVE_ACCESS_TOKEN_", "").lower()
            accounts.add(account)
    # Also check default (no suffix)
    if os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN"):
        accounts.add("default")
    return sorted(accounts)


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


def _drive_api_get(endpoint: str, access_token: str | None = None, params: dict | None = None, account: str | None = None) -> dict:
    """Internal helper untuk call Drive API."""
    if not access_token:
        access_token = _get_access_token(account)
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
    account: str | None = None,
) -> dict:
    """List semua gambar di Google Drive folder (atau root jika folder_id=None).

    Returns metadata: id, name, mimeType, size, createdTime, modifiedTime,
    thumbnailLink, webViewLink, imageMediaMetadata (width, height).
    """
    if not access_token:
        access_token = _get_access_token(account)
    if not access_token:
        return _fallback(
            f"GOOGLE_DRIVE_ACCESS_TOKEN{'_' + account.upper() if account else ''} tidak di-set.\n"
            "Cara setup:\n"
            "1. Daftar app di https://console.cloud.google.com/ → APIs & Services → Credentials\n"
            "2. Enable Google Drive API\n"
            "3. Buat OAuth 2.0 Client ID (Desktop app)\n"
            "4. Jalankan get_auth_url() → buka URL → authorize → copy code\n"
            "5. Jalankan exchange_auth_code(code) → simpan access_token & refresh_token\n"
            f"6. Set GOOGLE_DRIVE_ACCESS_TOKEN{'_' + account.upper() if account else ''} sebagai env var"
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


def get_drive_file(file_id: str, access_token: str | None = None, account: str | None = None) -> dict:
    """Get detailed metadata untuk single file."""
    if not access_token:
        access_token = _get_access_token(account)
    if not access_token:
        return _fallback(f"GOOGLE_DRIVE_ACCESS_TOKEN{'_' + account.upper() if account else ''} tidak di-set")

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
    account: str | None = None,
) -> dict:
    """Collect dataset dari Google Drive (metadata only, gambar tetap di Drive).

    Ini adalah primary entry point untuk collect dataset dari Drive agency.
    """
    result = list_drive_images(folder_id, access_token, max_files=max_files, account=account)
    if not result.get("ok"):
        return result

    data = result["data"]
    files = data.get("files", [])

    # Add dimension-based tags + account tag
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
        if account:
            f["tags"].append(account.lower())
            f["account"] = account.lower()
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


def drive_health_check(access_token: str | None = None, account: str | None = None) -> dict:
    """Check Google Drive API connectivity dan token validity."""
    if not access_token:
        access_token = _get_access_token(account)
    if not access_token:
        return _fallback(
            f"GOOGLE_DRIVE_ACCESS_TOKEN{'_' + account.upper() if account else ''} tidak di-set.\n"
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



# ── 4. Multi-Account & Batch Functions ─────────────────────────────────────────


def explore_drive_structure(
    folder_id: str | None = None,
    access_token: str | None = None,
    account: str | None = None,
    max_depth: int = 3,
    current_depth: int = 0,
) -> dict:
    """Explore Google Drive folder structure recursively (folder tree + image count per folder).

    Returns tree dengan image count per folder untuk membantu bos memutuskan
    folder mana yang paling berharga untuk training.
    """
    if not access_token:
        access_token = _get_access_token(account)
    if not access_token:
        return _fallback(
            f"GOOGLE_DRIVE_ACCESS_TOKEN{'_' + account.upper() if account else ''} tidak di-set. "
            "Jalankan get_auth_url() dan exchange_auth_code() dulu."
        )

    if current_depth >= max_depth:
        return _ok({"name": "...", "truncated": True, "image_count": 0, "folders": []})

    # Get folder info
    try:
        if folder_id:
            folder_info = _drive_api_get(
                f"files/{folder_id}",
                access_token=access_token,
                params={"fields": "id,name,mimeType"},
            )
            folder_name = folder_info.get("name", "unknown")
        else:
            folder_id = "root"
            folder_name = "My Drive"
    except Exception as exc:
        return _fallback(f"Folder info error: {exc}")

    # Count images in this folder
    try:
        q = f"trashed = false and mimeType contains 'image/' and '{folder_id}' in parents"
        img_result = _drive_api_get(
            "files",
            access_token=access_token,
            params={"q": q, "fields": "files(id)", "pageSize": 1000},
        )
        image_count = len(img_result.get("files", []))
    except Exception:
        image_count = 0

    # Count subfolders
    try:
        q = f"trashed = false and mimeType = 'application/vnd.google-apps.folder' and '{folder_id}' in parents"
        folder_result = _drive_api_get(
            "files",
            access_token=access_token,
            params={"q": q, "fields": "files(id,name)", "pageSize": 1000},
        )
        subfolders = folder_result.get("files", [])
    except Exception:
        subfolders = []

    # Recurse into subfolders
    children = []
    for sf in subfolders:
        child = explore_drive_structure(
            folder_id=sf["id"],
            access_token=access_token,
            account=account,
            max_depth=max_depth,
            current_depth=current_depth + 1,
        )
        if child.get("ok"):
            children.append(child["data"])
        else:
            children.append({
                "id": sf["id"],
                "name": sf["name"],
                "image_count": 0,
                "error": child.get("fallback_instructions", "?"),
            })

    return _ok({
        "id": folder_id,
        "name": folder_name,
        "image_count": image_count,
        "subfolder_count": len(subfolders),
        "folders": children,
        "depth": current_depth,
    })


def get_account_overview(account: str | None = None, access_token: str | None = None) -> dict:
    """Get overview untuk satu Google Drive account.

    Returns: user info, storage, total images, top folders by image count.
    """
    if not access_token:
        access_token = _get_access_token(account)
    if not access_token:
        return _fallback(
            f"GOOGLE_DRIVE_ACCESS_TOKEN{'_' + account.upper() if account else ''} tidak di-set."
        )

    try:
        # User info + storage
        about = _drive_api_get("about", access_token=access_token, params={"fields": "user,storageQuota"})
        user = about.get("user", {})
        quota = about.get("storageQuota", {})

        # Count total images in drive
        total_images = 0
        try:
            q = "trashed = false and mimeType contains 'image/'"
            result = _drive_api_get(
                "files",
                access_token=access_token,
                params={"q": q, "fields": "files(id,name,parents,size,imageMediaMetadata)", "pageSize": 1000},
            )
            total_images = len(result.get("files", []))
        except Exception:
            pass

        # Top-level folders with image count
        top_folders = []
        try:
            q = "trashed = false and mimeType = 'application/vnd.google-apps.folder' and 'root' in parents"
            folders = _drive_api_get(
                "files",
                access_token=access_token,
                params={"q": q, "fields": "files(id,name)"},
            )
            for f in folders.get("files", [])[:20]:
                # Count images in each top folder
                img_q = f"trashed = false and mimeType contains 'image/' and '{f['id']}' in parents"
                try:
                    img_res = _drive_api_get(
                        "files",
                        access_token=access_token,
                        params={"q": img_q, "fields": "files(id)"},
                    )
                    img_count = len(img_res.get("files", []))
                except Exception:
                    img_count = 0
                top_folders.append({"id": f["id"], "name": f["name"], "image_count": img_count})
            top_folders.sort(key=lambda x: x["image_count"], reverse=True)
        except Exception:
            pass

        return _ok({
            "account": account or "default",
            "user_email": user.get("emailAddress"),
            "user_name": user.get("displayName"),
            "total_storage": quota.get("limit"),
            "used_storage": quota.get("usage"),
            "total_images": total_images,
            "top_folders": top_folders,
            "configured": True,
        })
    except Exception as exc:
        return _fallback(f"Account overview error: {exc}")


def batch_collect_drive_datasets(
    accounts: list[str] | None = None,
    max_files_per_account: int = 1000,
) -> dict:
    """Collect image metadata dari multiple Google Drive accounts.

    If accounts=None, auto-detect dari env vars.
    """
    if accounts is None:
        accounts = list_configured_accounts()

    if not accounts:
        return _fallback(
            "Tidak ada Google Drive account yang dikonfigurasi.\n"
            "Set minimal satu dari:\n"
            "  GOOGLE_DRIVE_ACCESS_TOKEN (default)\n"
            "  GOOGLE_DRIVE_ACCESS_TOKEN_FAHMIWOL\n"
            "  GOOGLE_DRIVE_ACCESS_TOKEN_TIRANYX\n"
            "  GOOGLE_DRIVE_ACCESS_TOKEN_OPERATIONALNYX\n"
            "  GOOGLE_DRIVE_ACCESS_TOKEN_NIRMANANYX\n"
            "Cara: jalankan get_auth_url() per akun, lalu exchange_auth_code()."
        )

    results = {}
    total_images = 0
    errors = []

    for acc in accounts:
        try:
            # Get overview
            overview = get_account_overview(account=acc)
            if not overview.get("ok"):
                errors.append(f"{acc}: {overview.get('fallback_instructions', '?')}")
                results[acc] = overview
                continue

            # Collect images from root
            collection = collect_drive_dataset(
                folder_id=None,
                access_token=_get_access_token(acc),
                max_files=max_files_per_account,
            )
            if collection.get("ok"):
                data = collection["data"]
                total_images += data.get("total_files", 0)
                results[acc] = _ok({
                    "overview": overview["data"],
                    "collection": data,
                })
            else:
                errors.append(f"{acc}: {collection.get('fallback_instructions', '?')}")
                results[acc] = collection
        except Exception as exc:
            errors.append(f"{acc}: {exc}")
            results[acc] = _fallback(str(exc))

    return _ok({
        "accounts": accounts,
        "results": results,
        "total_images_across_accounts": total_images,
        "errors": errors if errors else None,
        "license_note": "Semua gambar dari agency = 100% legal untuk training.",
    })


# ── 5. Account Configuration Helpers ───────────────────────────────────────────


def get_account_config_instructions() -> dict:
    """Return step-by-step instructions untuk setup 4 Google Drive accounts."""
    return _ok({
        "title": "Setup 4 Google Drive Accounts untuk Training Dataset",
        "accounts": ["fahmiwol", "tiranyx", "operationalnyx", "nirmananyx"],
        "steps": [
            {
                "step": 1,
                "title": "Daftar Google Cloud Console",
                "url": "https://console.cloud.google.com/",
                "instructions": (
                    "Buat project baru → APIs & Services → Enable Google Drive API → "
                    "Credentials → Create OAuth 2.0 Client ID (Desktop app) → "
                    "Copy Client ID & Client Secret"
                ),
            },
            {
                "step": 2,
                "title": "Set Client Credentials",
                "instructions": (
                    "Set env var (satu kali untuk semua akun):\n"
                    "set GOOGLE_DRIVE_CLIENT_ID=your_client_id\n"
                    "set GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret"
                ),
            },
            {
                "step": 3,
                "title": "Auth per Akun",
                "instructions": (
                    "Ulangi untuk masing-masing 4 akun:\n"
                    "a. Jalankan get_auth_url() → buka URL di browser\n"
                    "b. Login dengan akun Google yang sesuai\n"
                    "c. Copy authorization code dari redirect URL\n"
                    "d. Jalankan exchange_auth_code(code)\n"
                    "e. Simpan token:\n"
                    "   set GOOGLE_DRIVE_ACCESS_TOKEN_FAHMIWOL=...\n"
                    "   set GOOGLE_DRIVE_REFRESH_TOKEN_FAHMIWOL=...\n"
                    "   set GOOGLE_DRIVE_ACCESS_TOKEN_TIRANYX=...\n"
                    "   set GOOGLE_DRIVE_REFRESH_TOKEN_TIRANYX=...\n"
                    "   set GOOGLE_DRIVE_ACCESS_TOKEN_OPERATIONALNYX=...\n"
                    "   set GOOGLE_DRIVE_REFRESH_TOKEN_OPERATIONALNYX=...\n"
                    "   set GOOGLE_DRIVE_ACCESS_TOKEN_NIRMANANYX=...\n"
                    "   set GOOGLE_DRIVE_REFRESH_TOKEN_NIRMANANYX=..."
                ),
            },
            {
                "step": 4,
                "title": "Explore Drive Structure",
                "instructions": (
                    "Jalankan explore_drive_structure() atau batch_collect_drive_datasets() "
                    "untuk lihat semua folder dan hitung gambar per folder."
                ),
            },
            {
                "step": 5,
                "title": "Collect Dataset",
                "instructions": (
                    "Pilih folder yang paling banyak gambar dan relevan untuk training, "
                    "lalu jalankan collect_drive_dataset(folder_id=..., account='nama_akun')."
                ),
            },
        ],
        "env_vars_template": {
            "GOOGLE_DRIVE_CLIENT_ID": "your_client_id",
            "GOOGLE_DRIVE_CLIENT_SECRET": "your_client_secret",
            "GOOGLE_DRIVE_ACCESS_TOKEN_FAHMIWOL": "token1",
            "GOOGLE_DRIVE_REFRESH_TOKEN_FAHMIWOL": "refresh1",
            "GOOGLE_DRIVE_ACCESS_TOKEN_TIRANYX": "token2",
            "GOOGLE_DRIVE_REFRESH_TOKEN_TIRANYX": "refresh2",
            "GOOGLE_DRIVE_ACCESS_TOKEN_OPERATIONALNYX": "token3",
            "GOOGLE_DRIVE_REFRESH_TOKEN_OPERATIONALNYX": "refresh3",
            "GOOGLE_DRIVE_ACCESS_TOKEN_NIRMANANYX": "token4",
            "GOOGLE_DRIVE_REFRESH_TOKEN_NIRMANANYX": "refresh4",
        },
    })
