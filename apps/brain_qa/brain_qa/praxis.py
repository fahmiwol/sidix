"""
praxis.py — Sistem "mengajar SIDIX" lewat jejak eksekusi agen.

Tujuan:
- Setiap sesi ReAct menghasilkan **JSONL** (audit/debug) + **pelajaran Markdown** di
  `brain/public/praxis/lessons/` supaya `build_index` memasukkannya ke korpus BM25.
- Format pelajaran menjelaskan: konteks, keputusan bertahap, alat yang dipakai,
  cara merangkai jawaban — metafora "berpikir seperti agen coding" tanpa menyalin
  model eksternal.

Privasi: tidak menulis secret; observasi tool dipotong panjang.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import default_data_dir, workspace_root

_PRAXIS_SAFE = re.compile(r"(?i)(api[_-]?key|token|password|secret|bearer\s+)\s*[:=]\s*\S+")

_MAX_OBS_IN_LESSON = 900
_MAX_JSONL = 50_000


def praxis_data_dir() -> Path:
    d = default_data_dir() / "praxis"
    d.mkdir(parents=True, exist_ok=True)
    return d


def praxis_sessions_dir() -> Path:
    d = praxis_data_dir() / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def praxis_lessons_root() -> Path:
    """Markdown di bawah brain/public → terindeks indexer default."""
    p = workspace_root() / "brain" / "public" / "praxis"
    (p / "lessons").mkdir(parents=True, exist_ok=True)
    return p


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redact(s: str) -> str:
    return _PRAXIS_SAFE.sub(r"\1[REDACTED]", s or "")


def record_praxis_event(session_id: str, kind: str, data: dict[str, Any]) -> None:
    """Append satu event ke JSONL sesi (ringan, untuk trace + replay)."""
    sid = (session_id or "unknown").strip()[:32]
    path = praxis_sessions_dir() / f"{sid}.jsonl"
    row = {
        "ts": _utc_iso(),
        "session_id": sid,
        "kind": kind,
        "data": _sanitize_payload(data),
    }
    line = json.dumps(row, ensure_ascii=False) + "\n"
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass


def _sanitize_payload(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, str):
            out[k] = _redact(v)[:8000]
        elif isinstance(v, dict):
            out[k] = _sanitize_payload(v)
        elif isinstance(v, list):
            out[k] = v[:200]
        else:
            out[k] = v
    return out


def record_react_step(session_id: str, step: Any) -> None:
    """Panggil setelah satu ReActStep ditambahkan ke sesi (non-final atau final)."""
    record_praxis_event(session_id, "react_step", _step_to_dict(step))


def _step_to_dict(step: Any) -> dict[str, Any]:
    """Duck-type ReActStep."""
    d = {
        "step": getattr(step, "step", -1),
        "thought": _redact(getattr(step, "thought", "") or "")[:2000],
        "action_name": getattr(step, "action_name", "") or "",
        "action_args": getattr(step, "action_args", {}) or {},
        "observation_excerpt": _redact((getattr(step, "observation", "") or "")[:_MAX_OBS_IN_LESSON]),
        "is_final": bool(getattr(step, "is_final", False)),
        "final_excerpt": _redact((getattr(step, "final_answer", "") or "")[:1200]),
    }
    return d


def finalize_session_teaching(session: Any) -> Path | None:
    """
    Tulis satu file Markdown pelajaran ke brain/public/praxis/lessons/.
    Return path jika sukses; None jika tidak ada konten / error.
    """
    sid = getattr(session, "session_id", "") or "unknown"
    question = getattr(session, "question", "") or ""
    persona = getattr(session, "persona", "") or ""
    steps = getattr(session, "steps", []) or []
    final = getattr(session, "final_answer", "") or ""
    orch = getattr(session, "orchestration_digest", "") or ""

    if not question.strip() and not steps:
        return None

    date_prefix = _utc_iso()[:10].replace("-", "")
    safe_sid = re.sub(r"[^\w\-]+", "_", sid)[:24]
    lesson_path = praxis_lessons_root() / "lessons" / f"lesson_{date_prefix}_{safe_sid}.md"

    lines: list[str] = [
        "# Pelajaran Praxis — jejak agen SIDIX",
        "",
        f"**Diperbarui:** {_utc_iso()}",
        f"**session_id:** `{sid}`",
        f"**persona:** {persona}",
        "",
        "## Pertanyaan / tugas pengguna",
        "",
        question.strip() or "_(kosong)_",
        "",
        "## Rangkaian eksekusi (Thought → Action → Observation)",
        "",
    ]

    for st in steps:
        d = _step_to_dict(st)
        lines.append(f"### Langkah {d['step']}")
        lines.append("")
        lines.append(f"- **Thought:** {d['thought']}")
        if d["action_name"]:
            args_s = json.dumps(d["action_args"], ensure_ascii=False)[:600]
            lines.append(f"- **Action:** `{d['action_name']}` — args: `{args_s}`")
            lines.append(f"- **Observation (cuplikan):** {d['observation_excerpt']}")
        if d["is_final"] and d["final_excerpt"]:
            lines.append(f"- **Final (cuplikan):** {d['final_excerpt']}")
        lines.append("")

    lines.extend(
        [
            "## Jawaban akhir (ringkas)",
            "",
            (final[:4000] + ("…" if len(final) > 4000 else "")) or "_(belum ada)_",
            "",
        ]
    )

    if orch.strip():
        lines.extend(["## Cuplikan orkestrasi", "", "```text", orch[:2500], "```", ""])

    try:
        from .praxis_runtime import (
            format_case_frames_for_user,
            has_substantive_corpus_observations,
            match_case_frames,
        )

        mf = match_case_frames(question)
        has_obs = has_substantive_corpus_observations(steps)
        cf_txt = format_case_frames_for_user(mf, has_corpus_observations=has_obs)
        if cf_txt.strip():
            lines.extend(["## Kerangka kasus (runtime — niat & cabang data)", "", cf_txt, ""])
    except Exception:
        pass

    lines.extend(
        [
            "## Untuk SIDIX — cara berpikir seperti agen eksekutor",
            "",
            "1. **Rekam dulu:** salin pertanyaan, persona, dan setiap *thought* sebelum bertindak.",
            "2. **Pilah:** bedakan faktual (butuh korpus) vs meta (orkestrasi) vs implementasi (sandbox).",
            "3. **Pilih alat:** satu tool per langkah; evaluasi observasi sebelum lanjut atau final.",
            "4. **Batasi risiko:** jangan sebar secret; potong observasi panjang; hormati `corpus_only` / web fallback.",
            "5. **Tutup dengan jawaban:** rangkum sumber + langkah berikutnya; akui ketidakpastian bila perlu.",
            "",
            "_Tag: #praxis #sidix-agent #meta-learning_",
            "",
        ]
    )

    body = "\n".join(lines)
    if len(body) > _MAX_JSONL * 4:
        body = body[: _MAX_JSONL * 4] + "\n\n_(truncated)_\n"

    try:
        lesson_path.write_text(body, encoding="utf-8")
        record_praxis_event(
            sid,
            "session_end",
            {
                "lesson_path": str(lesson_path.relative_to(workspace_root())),
                "chars": len(body),
                "step_count": len(steps),
                "finished": bool(getattr(session, "finished", False)),
                "error": (getattr(session, "error", "") or "")[:500],
            },
        )
        return lesson_path
    except OSError:
        return None


def list_recent_lessons(*, limit: int = 20) -> list[dict[str, Any]]:
    root = praxis_lessons_root() / "lessons"
    if not root.exists():
        return []
    files = sorted(root.glob("lesson_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files[:limit]:
        try:
            st = p.stat()
            out.append(
                {
                    "path": str(p.relative_to(workspace_root())),
                    "mtime": st.st_mtime,
                    "size_bytes": st.st_size,
                }
            )
        except OSError:
            continue
    return out


@dataclass
class ExternalPraxisNote:
    """Catatan dari agen luar (mis. Cursor) — diserialkan ke Markdown."""

    title: str
    summary: str
    steps: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        t = _redact(self.title.strip() or "Catatan Praxis")
        s = _redact(self.summary.strip() or "")
        tag_line = " ".join(f"#{tg}" for tg in self.tags[:12])
        step_lines = [f"{i + 1}. {_redact(str(x))[:2000]}" for i, x in enumerate(self.steps[:40])]
        body = "\n".join(step_lines)
        return "\n".join(
            [
                f"# {t}",
                "",
                f"**Diperbarui:** {_utc_iso()}",
                "",
                "## Ringkasan",
                "",
                s[:8000],
                "",
                "## Langkah-langkah",
                "",
                body or "_(tidak dirinci)_",
                "",
                "## Tag",
                "",
                tag_line or "#praxis #external",
                "",
            ]
        )


def ingest_external_note(note: ExternalPraxisNote) -> Path | None:
    """Simpan catatan agen luar sebagai pelajaran terindeks."""
    slug = re.sub(r"[^\w\-]+", "_", note.title.lower())[:40] or "note"
    fn = f"note_{_utc_iso()[:10].replace('-', '')}_{slug}.md"
    out = praxis_lessons_root() / "lessons" / fn
    try:
        out.write_text(note.to_markdown(), encoding="utf-8")
        record_praxis_event("external", "external_note", {"path": str(out.relative_to(workspace_root()))})
        return out
    except OSError:
        return None
