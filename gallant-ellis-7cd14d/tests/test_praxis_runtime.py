# -*- coding: utf-8 -*-
"""Unit tests: praxis_runtime (kerangka kasus)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.praxis_runtime import (
    format_case_frames_for_user,
    implement_frame_matches,
    match_case_frames,
    planner_step0_suggestion,
)
from brain_qa.agent_react import ReActStep, _rule_based_plan


def test_match_orchestration_question():
    m = match_case_frames("Tolong rencana orkestrasi multi-agent untuk pipeline ETL")
    ids = [x.frame_id for x in m]
    assert "orchestration_meta" in ids


def test_match_implement():
    m = match_case_frames("Buatkan aplikasi login dengan Python")
    ids = [x.frame_id for x in m]
    assert "implement_or_automate" in ids


def test_format_block():
    m = match_case_frames("Apa itu sidq dalam konteks SIDIX?")
    txt = format_case_frames_for_user(m, has_corpus_observations=True)
    assert "Niat" in txt or "niat" in txt.lower()


def test_planner_step0_orchestration():
    sug = planner_step0_suggestion("Tolong orkestrasi multi-agent untuk ETL", "INAN")
    assert sug is not None
    assert sug[1] == "orchestration_plan"


def test_implement_frame():
    assert implement_frame_matches("Buatkan script Python untuk parsing CSV")


def test_rule_based_workspace_after_corpus_with_frame_only():
    """Tanpa regex agent_build_intent, frame implement cukup untuk workspace_list."""
    hist = [
        ReActStep(
            step=0,
            thought="t",
            action_name="search_corpus",
            action_args={},
            observation="ringkasan " + ("x" * 500),
        )
    ]
    thought, action, args = _rule_based_plan(
        "Buatkan script hello world Python sederhana",
        "INAN",
        hist,
        1,
        corpus_only=False,
        allow_web_fallback=True,
    )
    assert action == "workspace_list"
