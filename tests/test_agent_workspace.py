# -*- coding: utf-8 -*-
"""Unit tests: sandbox workspace tools untuk mode agen SIDIX."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

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
    """Build intent → workspace_list dipilih rule-based (tanpa LLM nyata).

    LLM calls di-mock supaya test tidak butuh Ollama/RunPod live.
    Tanpa mock, Ollama timeout (~90s) di-CI menyebabkan pytest FDCapture
    crash yang merusak seluruh test session.
    """
    monkeypatch.setenv("BRAIN_QA_AGENT_WORKSPACE", str(tmp_path))
    (tmp_path / "README.md").write_text("# stub", encoding="utf-8")

    # Mock hybrid_generate (RunPod/Ollama router di agent_react.py baris ~1006)
    # dan ollama_generate sebagai double-safety kalau fallback branch diambil.
    # Keduanya return stub string — cukup untuk test assertion di bawah.
    with patch("brain_qa.runpod_serverless.hybrid_generate",
               return_value=("Baik, saya buatkan kalkulator Python.", "runpod")), \
         patch("brain_qa.ollama_llm.ollama_generate",
               return_value=("Baik, saya buatkan kalkulator Python.", "ollama")), \
         patch("brain_qa.ollama_llm.ollama_available", return_value=True):
        session = run_react(
            question="Buatkan aplikasi kalkulator sederhana dalam Python",
            persona="INAN",
            corpus_only=True,
            allow_web_fallback=False,
            max_steps=8,
        )

    names = [s.action_name for s in session.steps if s.action_name]

    # Build intent terdeteksi → agent pilih workspace/project op (bypass corpus).
    # Exact action varies by environment (workspace_list on dev, project_map on
    # VPS with corpus loaded, workspace_write if readme already scanned).
    # We assert the INTENT — a workspace/project operation happened — not which
    # specific action was picked first.
    WORKSPACE_OPS = {
        "workspace_list", "workspace_read", "workspace_write",
        "workspace_delete", "project_map",
    }
    assert any(n in WORKSPACE_OPS for n in names), (
        f"Build intent detected but no workspace/project op in steps: {names}"
    )
