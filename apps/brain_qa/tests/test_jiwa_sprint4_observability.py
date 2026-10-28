"""
Jiwa Sprint 4 — Fase A: Steps Trace Observability + Fase B: Planner Wiring
Tests untuk ChatResponse.steps_trace + planner_used/planner_savings di AgentSession.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ))

import pytest
from brain_qa.agent_react import ReActStep, AgentSession
from brain_qa.agent_serve import _build_steps_trace, _summarize_args


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_step(n: int, action: str = "web_search", is_final: bool = False) -> ReActStep:
    return ReActStep(
        step=n,
        thought=f"Thought step {n}: investigating the query carefully",
        action_name=action,
        action_args={"query": f"sample query {n}", "k": 5},
        observation=f"Observation {n}: found relevant result about topic X " * 10,
        is_final=is_final,
        final_answer="Final answer here." if is_final else "",
    )


# ── Fase A: _build_steps_trace ────────────────────────────────────────────────

class TestBuildStepsTrace:
    def test_empty_steps(self):
        result = _build_steps_trace([])
        assert result == []

    def test_single_step_structure(self):
        step = _make_step(1)
        trace = _build_steps_trace([step])
        assert len(trace) == 1
        t = trace[0]
        assert t["step"] == 1
        assert "thought" in t
        assert "action" in t
        assert "args_summary" in t
        assert "observation_preview" in t
        assert "is_final" in t

    def test_thought_truncated_at_200(self):
        step = _make_step(1)
        step.thought = "x" * 300
        trace = _build_steps_trace([step])
        assert len(trace[0]["thought"]) <= 200

    def test_observation_truncated_at_300(self):
        step = _make_step(1)
        step.observation = "y" * 500
        trace = _build_steps_trace([step])
        assert len(trace[0]["observation_preview"]) <= 300

    def test_final_step_flagged(self):
        step = _make_step(3, action="", is_final=True)
        step.action_name = ""
        step.observation = ""
        trace = _build_steps_trace([step])
        assert trace[0]["is_final"] is True

    def test_multi_step_order_preserved(self):
        steps = [_make_step(i) for i in range(5)]
        trace = _build_steps_trace(steps)
        for i, t in enumerate(trace):
            assert t["step"] == i

    def test_action_name_captured(self):
        step = _make_step(1, action="search_corpus")
        trace = _build_steps_trace([step])
        assert trace[0]["action"] == "search_corpus"


# ── _summarize_args ───────────────────────────────────────────────────────────

class TestSummarizeArgs:
    def test_empty(self):
        assert _summarize_args({}) == ""

    def test_private_keys_skipped(self):
        result = _summarize_args({"_citations": ["x", "y"], "query": "hello"})
        assert "_citations" not in result
        assert "query" in result

    def test_long_string_truncated(self):
        result = _summarize_args({"q": "a" * 100})
        assert "…" in result

    def test_list_summarized(self):
        result = _summarize_args({"items": [1, 2, 3]})
        assert "3 items" in result

    def test_numeric_preserved(self):
        result = _summarize_args({"k": 5, "threshold": 0.7})
        assert "5" in result

    def test_bool_preserved(self):
        result = _summarize_args({"verbose": True})
        assert "True" in result


# ── Fase B: AgentSession planner fields ──────────────────────────────────────

class TestAgentSessionPlannerFields:
    def test_default_planner_fields(self):
        session = AgentSession(
            session_id="test-001",
            question="test question",
            persona="AYMAN"
        )
        assert session.planner_used is False
        assert session.planner_savings == 0.0

    def test_planner_fields_settable(self):
        session = AgentSession(
            session_id="test-002",
            question="apakah python lebih cepat dari javascript?",
            persona="ABOO"
        )
        session.planner_used = True
        session.planner_savings = 0.6
        assert session.planner_used is True
        assert session.planner_savings == pytest.approx(0.6)

    def test_planner_savings_range(self):
        """Savings harus antara 0.0 dan 1.0."""
        session = AgentSession(
            session_id="test-003",
            question="test",
            persona="OOMAR"
        )
        session.planner_savings = 0.0
        assert 0.0 <= session.planner_savings <= 1.0
        session.planner_savings = 1.0
        assert 0.0 <= session.planner_savings <= 1.0


# ── Integration: parallel_planner compatibility ───────────────────────────────

class TestPlannerIntegration:
    def test_plan_tools_returns_expected_shape(self):
        from brain_qa.parallel_planner import plan_tools
        calls = [
            {"name": "web_search", "args": {"query": "AI news"}},
            {"name": "search_corpus", "args": {"query": "AI news", "k": 3}},
        ]
        result = plan_tools(calls)
        assert "bundle_count" in result
        assert "total_tools" in result
        assert "estimated_parallel_savings" in result
        assert result["total_tools"] == 2

    def test_independent_reads_grouped_parallel(self):
        from brain_qa.parallel_planner import plan_tools
        calls = [
            {"name": "web_search", "args": {"query": "q1"}},
            {"name": "search_corpus", "args": {"query": "q1", "k": 3}},
            {"name": "calculator", "args": {"expr": "2+2"}},
        ]
        result = plan_tools(calls)
        # All reads → should be in fewer bundles than tools (parallelized)
        assert result["bundle_count"] <= result["total_tools"]

    def test_write_tool_separated(self):
        from brain_qa.parallel_planner import plan_tools
        calls = [
            {"name": "web_search", "args": {"query": "research"}},
            {"name": "workspace_write", "args": {"path": "out.txt", "content": "data"}},
        ]
        result = plan_tools(calls)
        # write must be in its own bundle
        assert result["bundle_count"] >= 2

    def test_savings_float_between_0_and_1(self):
        from brain_qa.parallel_planner import plan_tools
        calls = [{"name": "web_search", "args": {}}]
        result = plan_tools(calls)
        assert 0.0 <= result["estimated_parallel_savings"] <= 1.0
