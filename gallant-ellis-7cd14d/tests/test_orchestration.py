# -*- coding: utf-8 -*-
"""Unit tests: modul orchestration + tool orchestration_plan."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.agent_tools import call_tool
from brain_qa.agent_react import _rule_based_plan, ReActStep
from brain_qa.orchestration import (
    ARCHETYPE_ORDER,
    agent_build_intent,
    build_orchestration_plan,
    format_plan_text,
    score_archetypes,
)


def test_score_archetypes_has_all_keys():
    s = score_archetypes("verifikasi bukti dan integrasi API")
    for k in ARCHETYPE_ORDER:
        assert k in s


def test_build_orchestration_plan_stable_shape():
    plan = build_orchestration_plan("multi-agent pipeline untuk ETL", request_persona="INAN")
    assert plan.request_persona == "INAN"
    assert plan.router_persona
    assert len(plan.phases) >= 1
    txt = format_plan_text(plan)
    assert "OrchestrationPlan" in txt
    assert "deduce" in txt or "synthesize" in txt


def test_agent_build_intent_matches_implement_language():
    assert agent_build_intent("buatkan aplikasi login")
    assert not agent_build_intent("apa itu maqashid syariah")


def test_tool_orchestration_plan():
    r = call_tool(
        tool_name="orchestration_plan",
        args={"question": "orkestrasi multi-agent", "persona": "FACH"},
        session_id="t",
        step=0,
    )
    assert r.success
    assert "OrchestrationPlan" in r.output
    assert r.citations and r.citations[0].get("type") == "orchestration_plan"


def test_rule_based_plan_step0_orchestration_meta():
    thought, action, args = _rule_based_plan(
        "Tolong rencana orkestrasi untuk tugas ini",
        "INAN",
        [],
        0,
        corpus_only=False,
        allow_web_fallback=True,
    )
    assert action == "orchestration_plan"
    assert args.get("question")


def test_rule_based_plan_after_orchestration_plan_final():
    hist = [
        ReActStep(
            step=0,
            thought="t",
            action_name="orchestration_plan",
            action_args={},
            observation="SIDIX OrchestrationPlan",
        )
    ]
    thought, action, args = _rule_based_plan(
        "rencana orkestrasi",
        "INAN",
        hist,
        1,
        corpus_only=False,
        allow_web_fallback=True,
    )
    assert action == ""
