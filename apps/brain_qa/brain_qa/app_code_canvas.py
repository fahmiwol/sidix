"""
app_code_canvas.py — Code Canvas MVP for SIDIX

In-memory code artifact store + execution wrapper around code_sandbox tool.
All inference is self-hosted (generate_sidix from local_llm module).
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel

from .agent_tools import call_tool
from .local_llm import generate_sidix


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
    artifact_id: str
    code: str
    language: str
    output: str
    error: str = ""
    created_at: float
    duration_ms: int


# ── In-memory store ───────────────────────────────────────────────────────────

_CODE_ARTIFACTS: dict[str, CodeArtifact] = {}
_MAX_ARTIFACTS = 200


def _prune_artifacts() -> None:
    """Keep store under _MAX_ARTIFACTS by removing oldest entries."""
    global _CODE_ARTIFACTS
    if len(_CODE_ARTIFACTS) <= _MAX_ARTIFACTS:
        return
    # Sort by created_at ascending, drop oldest
    sorted_ids = sorted(_CODE_ARTIFACTS.keys(), key=lambda k: _CODE_ARTIFACTS[k].created_at)
    for old_id in sorted_ids[: len(_CODE_ARTIFACTS) - _MAX_ARTIFACTS]:
        del _CODE_ARTIFACTS[old_id]


def _sanitize_output(text: str, max_len: int = 8_000) -> str:
    if len(text) > max_len:
        return text[:max_len] + "\n\n... [truncated]"
    return text


# ── Core functions ────────────────────────────────────────────────────────────

def run_code(code: str, language: str = "python") -> CodeRunResponse:
    """
    Execute code via the code_sandbox tool.
    Only Python is fully supported; other languages return a placeholder.
    """
    start = time.time()

    if language.lower() != "python":
        duration_ms = int((time.time() - start) * 1000)
        artifact_id = str(uuid.uuid4())
        artifact = CodeArtifact(
            artifact_id=artifact_id,
            code=code,
            language=language,
            output="",
            error=f"Language '{language}' not yet supported in Code Canvas MVP. Use Python.",
            created_at=time.time(),
            duration_ms=duration_ms,
        )
        _CODE_ARTIFACTS[artifact_id] = artifact
        _prune_artifacts()
        return CodeRunResponse(
            artifact_id=artifact_id,
            output="",
            error=artifact.error,
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
    artifact_id = str(uuid.uuid4())

    output = result.output if result.success else ""
    error = result.error if not result.success else ""

    artifact = CodeArtifact(
        artifact_id=artifact_id,
        code=code,
        language=language,
        output=_sanitize_output(output),
        error=error,
        created_at=time.time(),
        duration_ms=duration_ms,
    )
    _CODE_ARTIFACTS[artifact_id] = artifact
    _prune_artifacts()

    return CodeRunResponse(
        artifact_id=artifact_id,
        output=artifact.output,
        error=artifact.error,
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

    # Extract fixed code from ```python ... ``` block
    import re
    code_match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if code_match:
        fixed_code = code_match.group(1).strip()

    # Extract bullet suggestions (lines starting with - or * or numbered)
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("*") or re.match(r"^\d+\.", stripped):
            suggestions.append(stripped.lstrip("-*0123456789. ").strip())

    # Fallback: if no bullets found, use non-code paragraphs as suggestions
    if not suggestions:
        for para in text.split("\n\n"):
            para = para.strip()
            if para and "```" not in para:
                suggestions.append(para)

    # Deduplicate and cap
    seen: set[str] = set()
    unique: list[str] = []
    for s in suggestions:
        if s not in seen and len(s) > 5:
            seen.add(s)
            unique.append(s)
    suggestions = unique[:5]

    return CodeDebugResponse(suggestions=suggestions, fixed_code=fixed_code)


def get_artifact(artifact_id: str) -> CodeArtifact | None:
    return _CODE_ARTIFACTS.get(artifact_id)


def list_artifacts() -> list[CodeArtifact]:
    """Return artifacts sorted by newest first."""
    return sorted(_CODE_ARTIFACTS.values(), key=lambda a: a.created_at, reverse=True)
