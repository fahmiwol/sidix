# -*- coding: utf-8 -*-
"""Unit tests: sandbox workspace tools untuk mode agen SIDIX."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.agent_tools import call_tool, get_agent_workspace_root
from brain_qa.agent_react import run_react


def test_get_agent_workspace_root_env(monkeypatch, tmp_path):
    monkeypatch.setenv("BRAIN_QA_AGENT_WORKSPACE", str(tmp_path))
    assert get_agent_workspace_root() == tmp_path.resolve()


def test_workspace_read_rejects_dotdot(monkeypatch, tmp_path):
    monkeypatch.setenv("BRAIN_QA_AGENT_WORKSPACE", str(tmp_path))
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    r = call_tool(
        tool_name="workspace_read",
        args={"path": "../a.txt"},
        session_id="t",
        step=0,
    )
    assert not r.success


def test_workspace_write_requires_allow_restricted(monkeypatch, tmp_path):
    monkeypatch.setenv("BRAIN_QA_AGENT_WORKSPACE", str(tmp_path))
    r = call_tool(
        tool_name="workspace_write",
        args={"path": "w.txt", "content": "hi"},
        session_id="t",
        step=0,
        allow_restricted=False,
    )
    assert not r.success

    r2 = call_tool(
        tool_name="workspace_write",
        args={"path": "w.txt", "content": "hi"},
        session_id="t",
        step=1,
        allow_restricted=True,
    )
    assert r2.success
    assert (tmp_path / "w.txt").read_text(encoding="utf-8") == "hi"


def test_run_react_build_intent_includes_workspace_list(monkeypatch, tmp_path):
    monkeypatch.setenv("BRAIN_QA_AGENT_WORKSPACE", str(tmp_path))
    (tmp_path / "README.md").write_text("# stub", encoding="utf-8")
    session = run_react(
        question="Buatkan aplikasi kalkulator sederhana dalam Python",
        persona="INAN",
        corpus_only=True,
        allow_web_fallback=False,
        max_steps=8,
    )
    names = [s.action_name for s in session.steps if s.action_name]
    # Build intent terdeteksi → langsung workspace_list (bypass corpus)
    assert "workspace_list" in names
    # search_corpus mungkin tidak muncul kalau build intent kuat
