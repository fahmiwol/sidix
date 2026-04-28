"""
claude_sessions.py — Sprint 41 v1.2 (Claude Code Session Discovery & Batch Synthesizer)

Auto-discover semua Claude Code sessions di ~/.claude/projects/* dan batch-feed
ke Conversation Synthesizer.

Founder mandate (LOCK 2026-04-29): *"setiap percakapan kita juga harus bisa
di sintesis sama sidix, kamu sebagai guru."*

Usage flow:
  1. List all sessions across projects:
       python -m brain_qa claude_sessions list

  2. Synthesize one session:
       python -m brain_qa claude_sessions synthesize --uuid=<UUID>

  3. Batch synthesize (filter by project / since-date / min-turns):
       python -m brain_qa claude_sessions batch \\
           --project="Mighan-3D" --since="2026-04-01" --min-turns=20

Discovery scope:
  Default: ~/.claude/projects/<project-folder>/<session-uuid>.jsonl
  Project folder pattern: encoded path (slashes → dashes, etc.)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


def _claude_projects_root() -> Path:
    """Locate ~/.claude/projects/ across OS."""
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~")
    return home.expanduser() / ".claude" / "projects"


@dataclass
class SessionInfo:
    """Quick summary of a Claude Code session JSONL file."""
    uuid: str = ""
    project_folder: str = ""        # raw folder name e.g. "C--SIDIX-AI-pedantic-banach-c8232d"
    project_label: str = ""         # human-readable e.g. "SIDIX-AI/pedantic-banach-c8232d"
    jsonl_path: str = ""
    size_bytes: int = 0
    line_count: int = 0
    user_turns: int = 0
    assistant_turns: int = 0
    first_timestamp: str = ""
    last_timestamp: str = ""
    note_synthesized_path: str = "" # filled after batch synthesize


def decode_project_folder(folder: str) -> str:
    """Convert Claude Code's encoded folder name → readable path.

    Example: 'C--SIDIX-AI-pedantic-banach-c8232d' →
             'C:/SIDIX-AI/pedantic-banach-c8232d'

    Heuristic: 'C--' prefix → 'C:/'. Subsequent '-' separators → '/'.
    Best-effort, fallback returns folder as-is.
    """
    s = folder
    if s.startswith("C--"):
        s = "C:/" + s[3:]
    # Replace remaining double-dash with slash (project boundaries)
    # then single-dash with slash (path separators)
    # Actually Claude Code uses '-' for both '/' and '_' chars; can't disambiguate
    # perfectly. Just return raw with prefix decoded.
    return s


def quick_summarize_jsonl(path: Path) -> SessionInfo:
    """Read JSONL, extract counts + timestamps without full parse."""
    info = SessionInfo(
        jsonl_path=str(path),
        uuid=path.stem,
        size_bytes=path.stat().st_size,
        project_folder=path.parent.name,
        project_label=decode_project_folder(path.parent.name),
    )
    user_turns = assistant_turns = line_count = 0
    first_ts = last_ts = ""
    try:
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                line_count += 1
                try:
                    d = json.loads(raw)
                except Exception:
                    continue
                ts = d.get("timestamp", "")
                if ts and not first_ts:
                    first_ts = ts
                if ts:
                    last_ts = ts
                msg = d.get("message", {})
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    if role == "user":
                        user_turns += 1
                    elif role == "assistant":
                        assistant_turns += 1
    except Exception as e:
        log.debug("[claude_sessions] read error %s: %s", path, e)

    info.line_count = line_count
    info.user_turns = user_turns
    info.assistant_turns = assistant_turns
    info.first_timestamp = first_ts
    info.last_timestamp = last_ts
    return info


def list_all_sessions(
    projects_root: Optional[Path] = None,
    project_filter: Optional[str] = None,
    min_turns: int = 0,
    since: Optional[str] = None,
) -> list[SessionInfo]:
    """Scan ~/.claude/projects/ → list of SessionInfo, filtered.

    Args:
        projects_root: override default ~/.claude/projects/
        project_filter: substring match against project_folder (e.g. "Mighan")
        min_turns: skip sessions with user_turns + assistant_turns < this
        since: ISO date string, skip sessions with last_timestamp < this
    """
    root = projects_root or _claude_projects_root()
    if not root.exists():
        log.warning("[claude_sessions] projects root not found: %s", root)
        return []

    out: list[SessionInfo] = []
    for proj_dir in sorted(root.iterdir()):
        if not proj_dir.is_dir():
            continue
        if project_filter and project_filter.lower() not in proj_dir.name.lower():
            continue
        for f in proj_dir.iterdir():
            if not f.is_file() or f.suffix != ".jsonl":
                continue
            info = quick_summarize_jsonl(f)
            total_turns = info.user_turns + info.assistant_turns
            if total_turns < min_turns:
                continue
            if since and info.last_timestamp and info.last_timestamp < since:
                continue
            out.append(info)
    # Sort by last_timestamp desc (most recent first)
    out.sort(key=lambda s: s.last_timestamp, reverse=True)
    return out


def synthesize_session(
    info: SessionInfo,
    notes_dir: Optional[Path] = None,
    persona_fanout: bool = False,
    source_label_prefix: str = "claude_session",
) -> dict:
    """Run conversation_synthesizer on a single session JSONL."""
    from .conversation_synthesizer import synthesize, claude_jsonl_to_markdown

    transcript = claude_jsonl_to_markdown(Path(info.jsonl_path))
    if not transcript.strip():
        return {
            "ok": False,
            "uuid": info.uuid,
            "error": "empty transcript after parse",
        }

    label = f"{source_label_prefix}_{info.project_folder}_{info.uuid[:8]}"
    result = synthesize(
        transcript=transcript,
        source_label=label,
        notes_dir=notes_dir,
        write_note=True,
        persona_fanout=persona_fanout,
    )
    info.note_synthesized_path = result.note_path
    return {
        "ok": True,
        "uuid": info.uuid,
        "project": info.project_label,
        "topic": result.topic,
        "domain": result.domain,
        "turn_count": result.turn_count,
        "qa_pairs": len(result.qa_pairs),
        "decisions": len(result.decisions),
        "facts": len(result.facts),
        "open_questions": len(result.open_questions),
        "note_number": result.note_number,
        "note_path": result.note_path,
    }


def batch_synthesize(
    sessions: list[SessionInfo],
    notes_dir: Optional[Path] = None,
    persona_fanout: bool = False,
    max_count: int = 50,
    source_label_prefix: str = "claude_session",
) -> list[dict]:
    """Synthesize multiple sessions sequentially. Returns per-session results."""
    results: list[dict] = []
    for i, info in enumerate(sessions[:max_count], 1):
        log.info("[claude_sessions] %d/%d synthesizing %s (%s, %d turns)",
                 i, len(sessions), info.uuid[:8], info.project_label,
                 info.user_turns + info.assistant_turns)
        try:
            r = synthesize_session(info, notes_dir, persona_fanout,
                                   source_label_prefix)
            results.append(r)
        except Exception as e:
            log.exception("[claude_sessions] synth error %s", info.uuid[:8])
            results.append({"ok": False, "uuid": info.uuid, "error": str(e)})
    return results


def format_list_table(sessions: list[SessionInfo]) -> str:
    """Pretty-print session list as a table for CLI output."""
    if not sessions:
        return "(no sessions found)"
    lines = []
    lines.append(f"{'UUID':<10} {'Turns':>7} {'Bytes':>10} {'Last':<22} Project")
    lines.append("-" * 90)
    for s in sessions:
        turns = s.user_turns + s.assistant_turns
        last = s.last_timestamp[:19] if s.last_timestamp else "?"
        proj = s.project_label[:48]
        lines.append(
            f"{s.uuid[:8]:<10} {turns:>7} {s.size_bytes:>10} {last:<22} {proj}"
        )
    return "\n".join(lines)


__all__ = [
    "SessionInfo", "decode_project_folder",
    "quick_summarize_jsonl", "list_all_sessions",
    "synthesize_session", "batch_synthesize", "format_list_table",
]
