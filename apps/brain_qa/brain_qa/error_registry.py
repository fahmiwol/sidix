"""
error_registry.py — Sprint L: Error Registry + Root Cause Tracking
====================================================================

Setiap kali SIDIX gagal (low confidence, exception, timeout, hallucination
detected), log masuk ke sini. Secara periodik, LLM analisis pola error →
propose fix ke admin untuk review.

Ini adalah fondasi dari "self-modifying" capability — SIDIX tidak hanya
tahu dia salah, tapi tahu KENAPA dan BAGAIMANA memperbaiki.

Analogi: dokter yang mencatat setiap kasus gagal + belajar dari pola.

Public API:
    log_error(error_type, message, context, root_cause) -> str  # returns entry_id
    get_recent_errors(n=50, error_type=None) -> list[dict]
    get_error_stats() -> dict
    analyze_patterns(llm_fn) -> dict  # LLM synthesis of error patterns
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# ── Storage ────────────────────────────────────────────────────────────────────

def _resolve_registry_path() -> Path:
    try:
        from .paths import workspace_root
        p = workspace_root() / ".data" / "error_registry.jsonl"
    except Exception:
        p = Path(__file__).resolve().parents[3] / ".data" / "error_registry.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

_REGISTRY_PATH: Path | None = None
_lock = threading.Lock()

def _registry_path() -> Path:
    global _REGISTRY_PATH
    if _REGISTRY_PATH is None:
        _REGISTRY_PATH = _resolve_registry_path()
    return _REGISTRY_PATH


# ── Known error types ──────────────────────────────────────────────────────────

class ErrorType:
    LOW_CONFIDENCE = "low_confidence"        # sanad score < 4.0
    OMNYX_EXCEPTION = "omnyx_exception"      # OMNYX raised exception
    TOOL_FAILURE = "tool_failure"            # tool execution failed
    LLM_TIMEOUT = "llm_timeout"             # LLM took too long
    INTENT_MISMATCH = "intent_mismatch"     # intent classified wrong
    MEMORY_FAIL = "memory_fail"             # conversation memory error
    HARVEST_FAIL = "harvest_fail"           # auto-harvest pipeline failed
    SYNTHESIS_EMPTY = "synthesis_empty"     # synthesizer returned empty answer
    RATE_LIMIT = "rate_limit"               # user hit rate limit
    UNKNOWN = "unknown"


# ── Core Functions ─────────────────────────────────────────────────────────────

def log_error(
    error_type: str,
    message: str,
    context: Optional[dict] = None,
    root_cause: str = "",
    fix_applied: str = "",
    session_id: str = "",
) -> str:
    """Log satu error entry. Returns entry_id."""
    entry_id = uuid.uuid4().hex[:12]
    entry = {
        "id": entry_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "error_type": error_type,
        "message": str(message)[:500],
        "context": _sanitize_context(context or {}),
        "root_cause": root_cause[:300],
        "fix_applied": fix_applied[:200],
        "session_id": session_id or "",
        "reviewed": False,
    }
    _append_entry(entry)
    log.debug("[error_registry] logged %s: %s", error_type, message[:80])
    return entry_id


def _sanitize_context(ctx: dict) -> dict:
    """Remove PII-like fields sebelum simpan."""
    safe = {}
    for k, v in ctx.items():
        if k.lower() in {"password", "token", "api_key", "email", "user_id"}:
            continue
        safe[k] = str(v)[:200] if not isinstance(v, (int, float, bool)) else v
    return safe


def _append_entry(entry: dict) -> None:
    with _lock:
        try:
            with open(_registry_path(), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            log.warning("[error_registry] write failed: %s", e)


def _load_all() -> list[dict]:
    p = _registry_path()
    if not p.exists():
        return []
    entries = []
    with _lock:
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            log.warning("[error_registry] read failed: %s", e)
    return entries


def get_recent_errors(n: int = 50, error_type: Optional[str] = None) -> list[dict]:
    """Return N most recent errors, optionally filtered by type."""
    all_e = _load_all()
    if error_type:
        all_e = [e for e in all_e if e.get("error_type") == error_type]
    return all_e[-n:]


def get_error_stats() -> dict:
    """Summary statistics — type counts, most common root causes, trend."""
    all_e = _load_all()
    if not all_e:
        return {"total": 0, "by_type": {}, "top_messages": [], "recent_7d": 0}

    type_counts = Counter(e.get("error_type", "unknown") for e in all_e)

    from datetime import timedelta
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    recent = [
        e for e in all_e
        if e.get("ts", "") >= week_ago.isoformat()
    ]

    # Most common short messages
    msg_counts = Counter(e.get("message", "")[:80] for e in all_e[-200:])
    top_msgs = [{"msg": m, "count": c} for m, c in msg_counts.most_common(5)]

    return {
        "total": len(all_e),
        "by_type": dict(type_counts),
        "top_messages": top_msgs,
        "recent_7d": len(recent),
        "last_error_ts": all_e[-1].get("ts", "") if all_e else "",
    }


def analyze_patterns(llm_fn=None) -> dict:
    """
    LLM analisis pola error terbaru → propose improvement.
    llm_fn: callable(prompt) -> str. Jika None, return raw stats only.
    """
    stats = get_error_stats()
    recent = get_recent_errors(n=30)

    if not recent:
        return {"stats": stats, "proposal": None, "message": "belum cukup data error"}

    if llm_fn is None:
        return {
            "stats": stats,
            "proposal": None,
            "message": "llm_fn tidak disediakan — hanya stats",
        }

    # Format error summary untuk LLM
    summary_lines = []
    for e in recent[-20:]:
        summary_lines.append(
            f"[{e.get('error_type')}] {e.get('message','')[:80]} | root: {e.get('root_cause','')[:60]}"
        )
    summary = "\n".join(summary_lines)

    prompt = f"""Kamu adalah SIDIX self-improvement analyst.

Berikut adalah 20 error terbaru dari SIDIX:
{summary}

Statistik:
- Total error: {stats['total']}
- Distribusi tipe: {stats['by_type']}
- Error 7 hari terakhir: {stats['recent_7d']}

Tugas kamu:
1. Identifikasi POLA utama (bukan per-error, tapi common root cause)
2. Prioritas: 3 perbaikan yang paling impactful
3. Untuk tiap perbaikan: apa yang perlu diubah (file, behavior, config)
4. Format JSON:

{{
  "patterns": ["pattern 1", "pattern 2"],
  "proposals": [
    {{
      "priority": 1,
      "title": "nama perbaikan",
      "problem": "akar masalah",
      "solution": "apa yang perlu diubah",
      "affected_files": ["file1.py"],
      "effort": "low/medium/high"
    }}
  ]
}}

Jawab JSON saja."""

    try:
        raw = llm_fn(prompt)
        # Extract JSON
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            proposal = json.loads(m.group())
        else:
            proposal = {"raw": raw}
    except Exception as e:
        proposal = {"error": str(e)}

    return {
        "stats": stats,
        "proposal": proposal,
        "based_on_n_errors": len(recent),
    }
