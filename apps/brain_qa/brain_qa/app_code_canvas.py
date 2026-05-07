"""
app_code_canvas.py — Code Canvas MVP for SIDIX

In-memory code artifact store + execution wrapper around code_sandbox tool.
Semua inference self-hosted (generate_sidix dari local_llm module).

Refactored Sprint 28b: sekarang menggunakan app_framework untuk unified
artifact lifecycle. CodeArtifact lama tetap backward-compatible via migrasi
lazy on first access.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel

from .agent_tools import call_tool
from .local_llm import generate_sidix
from .app_framework import (
    Artifact,
    ArtifactCreateRequest,
    create_artifact as _framework_create_artifact,
    get_artifact as _framework_get_artifact,
    list_artifacts as _framework_list_artifacts,
    migrate_legacy_code_artifact,
)


# ── Pydantic models ───────────────────────────────────────────────────────────

class CodeRunRequest(BaseModel):
    code: str
    language: str = "python"


class CodeRunResponse(BaseModel):
    artifact_id: str
    output: str
    error: str = ""
    duration_ms: int


class CodeDebugRequest(BaseModel):
    code: str
    error: str


class CodeDebugResponse(BaseModel):
    suggestions: list[str]
    fixed_code: str | None = None


class CodeArtifact(BaseModel):
    """Model lama — tetap dipertahankan untuk backward compat API response."""
    artifact_id: str
    code: str
    language: str
    output: str
    error: str = ""
    created_at: float
    duration_ms: int


# ── Legacy in-memory store (backward compat) ──────────────────────────────────

_CODE_ARTIFACTS: dict[str, CodeArtifact] = {}
_MAX_ARTIFACTS = 200
_LEGACY_MIGRATED = False


def _prune_artifacts() -> None:
    """Keep store under _MAX_ARTIFACTS by removing oldest entries."""
    global _CODE_ARTIFACTS
    if len(_CODE_ARTIFACTS) <= _MAX_ARTIFACTS:
        return
    sorted_ids = sorted(_CODE_ARTIFACTS.keys(), key=lambda k: _CODE_ARTIFACTS[k].created_at)
    for old_id in sorted_ids[: len(_CODE_ARTIFACTS) - _MAX_ARTIFACTS]:
        del _CODE_ARTIFACTS[old_id]


def _sanitize_output(text: str, max_len: int = 8_000) -> str:
    if len(text) > max_len:
        return text[:max_len] + "\n\n... [truncated]"
    return text


def _ensure_legacy_migrated() -> None:
    """Lazy migration: CodeArtifact lama → Artifact framework on first access."""
    global _LEGACY_MIGRATED
    if _LEGACY_MIGRATED:
        return
    _LEGACY_MIGRATED = True
    for artifact_id, old in list(_CODE_ARTIFACTS.items()):
        migrate_legacy_code_artifact(
            artifact_id=old.artifact_id,
            code=old.code,
            language=old.language,
            output=old.output,
            error=old.error,
            created_at=old.created_at,
            duration_ms=old.duration_ms,
        )


def _artifact_to_code_response(artifact: Artifact) -> CodeRunResponse:
    """Konversi Artifact unified → CodeRunResponse lama."""
    meta = artifact.metadata or {}
    return CodeRunResponse(
        artifact_id=artifact.id,
        output=meta.get("output", ""),
        error=meta.get("error", ""),
        duration_ms=meta.get("duration_ms", 0),
    )


def _artifact_to_legacy(artifact: Artifact) -> CodeArtifact:
    """Konversi Artifact unified → CodeArtifact lama untuk API history."""
    meta = artifact.metadata or {}
    return CodeArtifact(
        artifact_id=artifact.id,
        code=artifact.content,
        language=meta.get("language", "python"),
        output=meta.get("output", ""),
        error=meta.get("error", ""),
        created_at=artifact.created_at,
        duration_ms=meta.get("duration_ms", 0),
    )


# ── Core functions ────────────────────────────────────────────────────────────

def run_code(code: str, language: str = "python") -> CodeRunResponse:
    """
    Execute code via the code_sandbox tool.
    Only Python is fully supported; other languages return a placeholder.
    """
    start = time.time()

    if language.lower() != "python":
        duration_ms = int((time.time() - start) * 1000)
        error_msg = f"Language '{language}' not yet supported in Code Canvas MVP. Use Python."
        # Simpan ke framework unified store
        artifact = _framework_create_artifact(
            ArtifactCreateRequest(
                type="CODE",
                title=f"Code Canvas — {language}",
                content=code,
                metadata={
                    "language": language,
                    "output": "",
                    "error": error_msg,
                    "duration_ms": duration_ms,
                },
            )
        )
        # Simpan juga ke legacy store untuk backward compat
        legacy = CodeArtifact(
            artifact_id=artifact.id,
            code=code,
            language=language,
            output="",
            error=error_msg,
            created_at=time.time(),
            duration_ms=duration_ms,
        )
        _CODE_ARTIFACTS[artifact.id] = legacy
        _prune_artifacts()
        return CodeRunResponse(
            artifact_id=artifact.id,
            output="",
            error=error_msg,
            duration_ms=duration_ms,
        )

    result = call_tool(
        tool_name="code_sandbox",
        args={"code": code},
        session_id=f"canvas_{uuid.uuid4().hex[:8]}",
        step=0,
        allow_restricted=False,
    )

    duration_ms = int((time.time() - start) * 1000)

    output = result.output if result.success else ""
    error = result.error if not result.success else ""

    # Simpan ke framework unified store
    artifact = _framework_create_artifact(
        ArtifactCreateRequest(
            type="CODE",
            title=f"Code Canvas — {language}",
            content=code,
            metadata={
                "language": language,
                "output": _sanitize_output(output),
                "error": error,
                "duration_ms": duration_ms,
            },
        )
    )

    # Simpan juga ke legacy store untuk backward compat
    legacy = CodeArtifact(
        artifact_id=artifact.id,
        code=code,
        language=language,
        output=_sanitize_output(output),
        error=error,
        created_at=time.time(),
        duration_ms=duration_ms,
    )
    _CODE_ARTIFACTS[artifact.id] = legacy
    _prune_artifacts()

    return CodeRunResponse(
        artifact_id=artifact.id,
        output=_sanitize_output(output),
        error=error,
        duration_ms=duration_ms,
    )


def debug_code(code: str, error: str) -> CodeDebugResponse:
    """
    Analyze a code error using the local LLM (self-hosted inference only).
    Returns suggestions and optionally a fixed code snippet.
    """
    system = (
        "Kamu adalah SIDIX, AI assistant yang jujur dan teliti. "
        "Analisis error kode Python berikut dan berikan saran perbaikan. "
        "Jawab dalam bahasa Indonesia. "
        "Format: 1) Penjelasan singkat penyebab error. 2) Saran perbaikan (bullet). "
        "3) Blok kode yang sudah diperbaiki dalam format ```python ... ```."
    )
    prompt = (
        f"Kode:\n```python\n{code[:4000]}\n```\n\n"
        f"Error:\n{error[:2000]}\n\n"
        "Tolong analisis dan berikan saran perbaikan."
    )

    try:
        text = generate_sidix(prompt, system=system, max_tokens=600, temperature=0.3)
    except Exception as e:
        return CodeDebugResponse(
            suggestions=[f"Gagal memanggil model lokal: {e}"],
            fixed_code=None,
        )

    suggestions: list[str] = []
    fixed_code: str | None = None

    import re
    code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if code_match:
        fixed_code = code_match.group(1).strip()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("*") or re.match(r"^\d+\.", stripped):
            suggestions.append(stripped.lstrip("-*0123456789. ").strip())

    if not suggestions:
        for para in text.split("\n\n"):
            para = para.strip()
            if para and "```" not in para:
                suggestions.append(para)

    seen: set[str] = set()
    unique: list[str] = []
    for s in suggestions:
        if s not in seen and len(s) > 5:
            seen.add(s)
            unique.append(s)
    suggestions = unique[:5]

    return CodeDebugResponse(suggestions=suggestions, fixed_code=fixed_code)


def get_artifact(artifact_id: str) -> CodeArtifact | None:
    """Backward-compat getter: coba framework dulu, fallback legacy."""
    _ensure_legacy_migrated()
    unified = _framework_get_artifact(artifact_id)
    if unified:
        return _artifact_to_legacy(unified)
    return _CODE_ARTIFACTS.get(artifact_id)


def list_artifacts() -> list[CodeArtifact]:
    """Return artifacts sorted by newest first (backward-compat)."""
    _ensure_legacy_migrated()
    # Ambil dari framework (CODE type only, exclude DELETED)
    unified_list = _framework_list_artifacts(artifact_type="CODE")
    # Merge dengan legacy yang belum bermigrasi
    legacy_ids = {a.id for a in unified_list}
    for old_id, old in _CODE_ARTIFACTS.items():
        if old_id not in legacy_ids:
            unified_list.append(
                migrate_legacy_code_artifact(
                    artifact_id=old.artifact_id,
                    code=old.code,
                    language=old.language,
                    output=old.output,
                    error=old.error,
                    created_at=old.created_at,
                    duration_ms=old.duration_ms,
                )
            )
    # Konversi ke CodeArtifact lama
    result = [_artifact_to_legacy(a) for a in unified_list]
    return sorted(result, key=lambda a: a.created_at, reverse=True)
