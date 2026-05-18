# -*- coding: utf-8 -*-
"""Unit tests: modul praxis (mengajar SIDIX dari jejak agen)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.praxis import (
    ExternalPraxisNote,
    finalize_session_teaching,
    ingest_external_note,
    list_recent_lessons,
    praxis_sessions_dir,
    record_praxis_event,
)


class _FakeSession:
    def __init__(self) -> None:
        self.session_id = "test01"
        self.question = "Apa itu Praxis?"
        self.persona = "INAN"
        self.steps = []
        self.final_answer = "Praxis adalah jejak eksekusi untuk pembelajaran."
        self.finished = True
        self.error = ""
        self.orchestration_digest = ""


def test_record_and_finalize(monkeypatch, tmp_path):
    from brain_qa import praxis as praxis_mod

    monkeypatch.setattr(praxis_mod, "default_data_dir", lambda: tmp_path)
    monkeypatch.setattr(praxis_mod, "workspace_root", lambda: tmp_path)

    lessons = tmp_path / "brain" / "public" / "praxis" / "lessons"
    lessons.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(praxis_mod, "praxis_lessons_root", lambda: tmp_path / "brain" / "public" / "praxis")

    sid = "abc12345"
    record_praxis_event(sid, "session_start", {"question": "q"})
    p = praxis_sessions_dir() / f"{sid}.jsonl"
    assert p.exists()

    s = _FakeSession()
    s.session_id = sid
    out = finalize_session_teaching(s)
    assert out is not None
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "Praxis" in text or "praxis" in text.lower()
    assert "Thought" in text or "eksekusi" in text.lower()


def test_external_note(monkeypatch, tmp_path):
    from brain_qa import praxis as praxis_mod

    monkeypatch.setattr(praxis_mod, "default_data_dir", lambda: tmp_path)
    monkeypatch.setattr(praxis_mod, "workspace_root", lambda: tmp_path)
    (tmp_path / "brain" / "public" / "praxis" / "lessons").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(praxis_mod, "praxis_lessons_root", lambda: tmp_path / "brain" / "public" / "praxis")

    p = ingest_external_note(
        ExternalPraxisNote(
            title="Fix typo",
            summary="Ganti string di CLI.",
            steps=["Buka __main__.py", "Simpan"],
            tags=["test"],
        )
    )
    assert p is not None
    assert "Fix typo" in p.read_text(encoding="utf-8")


def test_list_recent_lessons(monkeypatch, tmp_path):
    from brain_qa import praxis as praxis_mod

    monkeypatch.setattr(praxis_mod, "workspace_root", lambda: tmp_path)
    root = tmp_path / "brain" / "public" / "praxis" / "lessons"
    root.mkdir(parents=True, exist_ok=True)
    (root / "lesson_20990101_x.md").write_text("# x\n", encoding="utf-8")
    monkeypatch.setattr(praxis_mod, "praxis_lessons_root", lambda: tmp_path / "brain" / "public" / "praxis")

    items = list_recent_lessons(limit=5)
    assert len(items) >= 1
