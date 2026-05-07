"""
app_framework.py — Unified Artifact Lifecycle Framework for SIDIX Built-in Apps.

Foundation untuk semua built-in apps (Code Canvas, Document Studio, Data Notebook, dll).
Menyediakan in-memory artifact store dengan threading-safe operations,
versioning, export, dan lifecycle management (DRAFT → ACTIVE → PINNED → ARCHIVED → DELETED).

All inference is self-hosted. No external API calls.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel


# ── Enums ─────────────────────────────────────────────────────────────────────

class ArtifactType(str, Enum):
    CODE = "CODE"
    DOCUMENT = "DOCUMENT"
    NOTEBOOK = "NOTEBOOK"
    IMAGE = "IMAGE"
    WEB_PREVIEW = "WEB_PREVIEW"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    THREED = "THREED"


class ArtifactStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PINNED = "PINNED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


# ── Pydantic models ───────────────────────────────────────────────────────────

class Artifact(BaseModel):
    id: str
    type: ArtifactType
    status: ArtifactStatus
    title: str
    content: str
    metadata: dict[str, Any] = {}
    created_at: float
    updated_at: float
    user_id: str = "anon"
    conversation_id: str = ""
    version: int = 1
    parent_id: str = ""  # untuk versioning chain


class ArtifactCreateRequest(BaseModel):
    type: str  # ArtifactType value as string untuk fleksibilitas
    title: str
    content: str
    metadata: dict[str, Any] = {}
    user_id: str = "anon"
    conversation_id: str = ""


class ArtifactUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    metadata: dict[str, Any] | None = None
    status: str | None = None


class ArtifactExportRequest(BaseModel):
    format: str = "md"  # md | json | html


class ArtifactListResponse(BaseModel):
    artifacts: list[Artifact]
    total: int


class ArtifactExportResponse(BaseModel):
    artifact_id: str
    format: str
    data: str


# ── In-memory store ───────────────────────────────────────────────────────────

_ARTIFACTS: dict[str, Artifact] = {}
_ARTIFACT_LOCK = threading.Lock()
_MAX_ARTIFACTS_PER_USER = 500


def _prune_oldest_for_user(user_id: str) -> None:
    """Hapus artifact tertua (bukan PINNED) kalau user melebihi batas."""
    with _ARTIFACT_LOCK:
        user_artifacts = [
            a for a in _ARTIFACTS.values()
            if a.user_id == user_id and a.status != ArtifactStatus.PINNED
        ]
        if len(user_artifacts) <= _MAX_ARTIFACTS_PER_USER:
            return
        # Urutkan berdasarkan updated_at ascending, hapus yang paling tua
        sorted_artifacts = sorted(user_artifacts, key=lambda a: a.updated_at)
        to_remove = len(sorted_artifacts) - _MAX_ARTIFACTS_PER_USER
        for a in sorted_artifacts[:to_remove]:
            del _ARTIFACTS[a.id]


def _resolve_artifact_type(type_str: str) -> ArtifactType:
    """Parse string ke ArtifactType; default CODE bila tidak dikenali."""
    try:
        return ArtifactType(type_str.upper())
    except ValueError:
        return ArtifactType.CODE


def _resolve_artifact_status(status_str: str) -> ArtifactStatus:
    """Parse string ke ArtifactStatus; default ACTIVE bila tidak dikenali."""
    try:
        return ArtifactStatus(status_str.upper())
    except ValueError:
        return ArtifactStatus.ACTIVE


# ── Core functions ────────────────────────────────────────────────────────────

def create_artifact(req: ArtifactCreateRequest) -> Artifact:
    """Buat artifact baru dan simpan ke store."""
    artifact = Artifact(
        id=str(uuid.uuid4()),
        type=_resolve_artifact_type(req.type),
        status=ArtifactStatus.ACTIVE,
        title=req.title,
        content=req.content,
        metadata=dict(req.metadata),
        created_at=time.time(),
        updated_at=time.time(),
        user_id=req.user_id or "anon",
        conversation_id=req.conversation_id or "",
        version=1,
        parent_id="",
    )
    with _ARTIFACT_LOCK:
        _ARTIFACTS[artifact.id] = artifact
    _prune_oldest_for_user(artifact.user_id)
    return artifact


def get_artifact(artifact_id: str) -> Artifact | None:
    """Ambil artifact berdasarkan ID."""
    with _ARTIFACT_LOCK:
        artifact = _ARTIFACTS.get(artifact_id)
        if artifact and artifact.status == ArtifactStatus.DELETED:
            return None
        return artifact


def update_artifact(artifact_id: str, req: ArtifactUpdateRequest) -> Artifact | None:
    """Update field artifact; return None kalau tidak ditemukan."""
    with _ARTIFACT_LOCK:
        artifact = _ARTIFACTS.get(artifact_id)
        if not artifact or artifact.status == ArtifactStatus.DELETED:
            return None
        if req.title is not None:
            artifact.title = req.title
        if req.content is not None:
            artifact.content = req.content
        if req.metadata is not None:
            artifact.metadata = dict(req.metadata)
        if req.status is not None:
            artifact.status = _resolve_artifact_status(req.status)
        artifact.updated_at = time.time()
        _ARTIFACTS[artifact_id] = artifact
        return artifact


def delete_artifact(artifact_id: str) -> bool:
    """Soft delete — set status ke DELETED."""
    with _ARTIFACT_LOCK:
        artifact = _ARTIFACTS.get(artifact_id)
        if not artifact:
            return False
        artifact.status = ArtifactStatus.DELETED
        artifact.updated_at = time.time()
        _ARTIFACTS[artifact_id] = artifact
        return True


def pin_artifact(artifact_id: str) -> Artifact | None:
    """Pin artifact — set status ke PINNED."""
    with _ARTIFACT_LOCK:
        artifact = _ARTIFACTS.get(artifact_id)
        if not artifact or artifact.status == ArtifactStatus.DELETED:
            return None
        artifact.status = ArtifactStatus.PINNED
        artifact.updated_at = time.time()
        _ARTIFACTS[artifact_id] = artifact
        return artifact


def unpin_artifact(artifact_id: str) -> Artifact | None:
    """Unpin artifact — set status ke ACTIVE."""
    with _ARTIFACT_LOCK:
        artifact = _ARTIFACTS.get(artifact_id)
        if not artifact or artifact.status == ArtifactStatus.DELETED:
            return None
        artifact.status = ArtifactStatus.ACTIVE
        artifact.updated_at = time.time()
        _ARTIFACTS[artifact_id] = artifact
        return artifact


def list_artifacts(
    user_id: str = "",
    artifact_type: str = "",
    status: str = "",
) -> list[Artifact]:
    """
    Return artifacts yang difilter.
    Default: exclude DELETED; urutkan PINNED dulu lalu updated_at desc.
    """
    with _ARTIFACT_LOCK:
        items = list(_ARTIFACTS.values())

    # Exclude DELETED secara default kecuali status eksplisit diminta
    if status:
        target_status = _resolve_artifact_status(status)
        items = [a for a in items if a.status == target_status]
    else:
        items = [a for a in items if a.status != ArtifactStatus.DELETED]

    if user_id:
        items = [a for a in items if a.user_id == user_id]
    if artifact_type:
        target_type = _resolve_artifact_type(artifact_type)
        items = [a for a in items if a.type == target_type]

    # Urutkan: PINNED dulu, lalu updated_at desc
    def _sort_key(a: Artifact) -> tuple:
        is_pinned = 0 if a.status == ArtifactStatus.PINNED else 1
        return (is_pinned, -a.updated_at)

    return sorted(items, key=_sort_key)


def export_artifact(artifact_id: str, fmt: str) -> str:
    """Export artifact ke format md/json/html."""
    artifact = get_artifact(artifact_id)
    if not artifact:
        raise ValueError(f"Artifact tidak ditemukan: {artifact_id}")

    fmt_lower = fmt.lower()
    if fmt_lower == "json":
        return json.dumps(artifact.model_dump(), ensure_ascii=False, indent=2)
    if fmt_lower == "html":
        return _export_html(artifact)
    # default markdown
    return _export_markdown(artifact)


def _export_markdown(a: Artifact) -> str:
    lines = [
        f"# {a.title}",
        "",
        f"- **ID**: {a.id}",
        f"- **Type**: {a.type.value}",
        f"- **Status**: {a.status.value}",
        f"- **Version**: {a.version}",
        f"- **Created**: {time.ctime(a.created_at)}",
        f"- **Updated**: {time.ctime(a.updated_at)}",
        "",
        "## Content",
        "",
        f"```\n{a.content}\n```" if a.type == ArtifactType.CODE else a.content,
        "",
    ]
    if a.metadata:
        lines.extend(["## Metadata", ""])
        for k, v in a.metadata.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    return "\n".join(lines)


def _export_html(a: Artifact) -> str:
    import html
    content_escaped = html.escape(a.content)
    if a.type == ArtifactType.CODE:
        content_html = f"<pre><code>{content_escaped}</code></pre>"
    else:
        content_html = f"<p>{content_escaped.replace(chr(10), '<br>')}</p>"
    meta_items = ""
    if a.metadata:
        meta_items = "\n".join(
            f'<li><strong>{html.escape(k)}</strong>: {html.escape(str(v))}</li>'
            for k, v in a.metadata.items()
        )
        meta_items = f"<h2>Metadata</h2>\n<ul>\n{meta_items}\n</ul>"
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>{html.escape(a.title)}</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; line-height: 1.6; }}
h1 {{ border-bottom: 2px solid #d4a853; padding-bottom: 8px; }}
pre {{ background: #f5f5f5; padding: 12px; border-radius: 8px; overflow-x: auto; }}
</style>
</head>
<body>
<h1>{html.escape(a.title)}</h1>
<p><strong>ID:</strong> {a.id}<br>
<strong>Type:</strong> {a.type.value}<br>
<strong>Status:</strong> {a.status.value}<br>
<strong>Version:</strong> {a.version}<br>
<strong>Created:</strong> {time.ctime(a.created_at)}<br>
<strong>Updated:</strong> {time.ctime(a.updated_at)}</p>
<h2>Content</h2>
{content_html}
{meta_items}
</body>
</html>"""


def create_version(parent_id: str) -> Artifact | None:
    """Clone artifact dengan version+1."""
    with _ARTIFACT_LOCK:
        parent = _ARTIFACTS.get(parent_id)
        if not parent or parent.status == ArtifactStatus.DELETED:
            return None
        new_artifact = Artifact(
            id=str(uuid.uuid4()),
            type=parent.type,
            status=ArtifactStatus.ACTIVE,
            title=f"{parent.title} (v{parent.version + 1})",
            content=parent.content,
            metadata=dict(parent.metadata),
            created_at=time.time(),
            updated_at=time.time(),
            user_id=parent.user_id,
            conversation_id=parent.conversation_id,
            version=parent.version + 1,
            parent_id=parent.id,
        )
        _ARTIFACTS[new_artifact.id] = new_artifact
        return new_artifact


# ── Backward-compat migration helper ──────────────────────────────────────────

def migrate_legacy_code_artifact(
    artifact_id: str,
    code: str,
    language: str,
    output: str,
    error: str,
    created_at: float,
    duration_ms: int,
) -> Artifact:
    """Konversi CodeArtifact lama ke Artifact unified framework."""
    metadata = {
        "language": language,
        "output": output,
        "error": error,
        "duration_ms": duration_ms,
    }
    artifact = Artifact(
        id=artifact_id,
        type=ArtifactType.CODE,
        status=ArtifactStatus.ACTIVE,
        title=f"Code Canvas — {language}",
        content=code,
        metadata=metadata,
        created_at=created_at,
        updated_at=created_at,
        user_id="anon",
        conversation_id="",
        version=1,
        parent_id="",
    )
    with _ARTIFACT_LOCK:
        _ARTIFACTS[artifact_id] = artifact
    return artifact
