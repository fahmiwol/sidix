# -*- coding: utf-8 -*-
"""
Unit tests: Jiwa Sprint 4 Fase B — Parallel Planner wired to Executor.
Verifikasi bundle-by-bundle execution respects deps / WRITE-sequentiality.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.parallel_planner import (
    ParallelPlanner,
    PlanNode,
    ToolMode,
    ExecutionPlan,
)
from brain_qa.parallel_executor import execute_plan, execute_parallel
from brain_qa.agent_tools import call_tool, ToolResult


# ── Planner unit tests ───────────────────────────────────────────────────────

def test_planner_groups_independent_reads_into_one_bundle():
    planner = ParallelPlanner()
    nodes = [
        PlanNode("search_corpus", {"query": "x"}),
        PlanNode("calculator", {"expression": "1+1"}),
        PlanNode("list_sources", {}),
    ]
    plan = planner.plan(nodes)
    assert len(plan.bundles) == 1
    assert len(plan.bundles[0].nodes) == 3
    assert plan.estimated_parallel_savings > 0.6


def test_planner_separates_write_from_read():
    planner = ParallelPlanner()
    nodes = [
        PlanNode("search_corpus", {"query": "x"}),
        PlanNode("workspace_write", {"path": "x", "content": "y"}, mode=ToolMode.WRITE),
    ]
    plan = planner.plan(nodes)
    assert len(plan.bundles) == 2
    names_0 = [n.tool_name for n in plan.bundles[0].nodes]
    names_1 = [n.tool_name for n in plan.bundles[1].nodes]
    assert "search_corpus" in names_0
    assert "workspace_write" in names_1


def test_planner_respects_duckduckgo_resource_limit():
    planner = ParallelPlanner()
    nodes = [PlanNode("web_search", {"query": f"q{i}"}) for i in range(5)]
    plan = planner.plan(nodes)
    # Max 3 per resource group → should split into at least 2 bundles
    assert len(plan.bundles) >= 2
    for b in plan.bundles:
        assert len(b.nodes) <= 3


def test_planner_dependency_chain_creates_multiple_bundles():
    planner = ParallelPlanner()
    nodes = [
        PlanNode("search_corpus", {"query": "x"}),
        PlanNode("read_chunk", {"chunk_id": "1"}, depends_on=["search_corpus"]),
        PlanNode("calculator", {"expression": "2+2"}),
    ]
    plan = planner.plan(nodes)
    # read_chunk depends on search_corpus → cannot be in same bundle as search_corpus
    assert len(plan.bundles) >= 2


def test_planner_single_node_one_bundle():
    planner = ParallelPlanner()
    plan = planner.plan([PlanNode("calculator", {"expression": "5*5"})])
    assert len(plan.bundles) == 1
    assert plan.bundles[0].nodes[0].tool_name == "calculator"


def test_planner_from_tool_names_convenience():
    planner = ParallelPlanner()
    plan = planner.plan_from_tool_names([
        {"name": "search_corpus", "args": {"query": "x"}},
        {"name": "web_search", "args": {"query": "y"}},
        {"name": "workspace_write", "args": {"path": "z", "content": "c"}},
    ])
    assert len(plan.bundles) == 2  # reads first, write second
    read_bundle = plan.bundles[0]
    write_bundle = plan.bundles[1]
    assert {n.tool_name for n in read_bundle.nodes} == {"search_corpus", "web_search"}
    assert write_bundle.nodes[0].tool_name == "workspace_write"


# ── Executor unit tests ──────────────────────────────────────────────────────

def test_execute_plan_empty_returns_empty():
    empty_plan = ExecutionPlan(bundles=[])
    result = execute_plan(empty_plan, session_id="t", step=0)
    assert result["total_tools"] == 0
    assert result["bundles_executed"] == 0
    assert result["results"] == []


def test_execute_plan_single_bundle_with_real_tools():
    """Use calculator — safe, no network, deterministic."""
    planner = ParallelPlanner()
    plan = planner.plan([
        PlanNode("calculator", {"expression": "1+2"}),
        PlanNode("calculator", {"expression": "3*4"}),
    ])
    result = execute_plan(plan, session_id="t", step=0)
    assert result["bundles_executed"] == 1
    assert result["total_tools"] == 2
    assert result["failed_count"] == 0
    outputs = [res.output for _, res in result["results"]]
    assert any("3" in o for o in outputs)  # 1+2
    assert any("12" in o for o in outputs)  # 3*4


def test_execute_plan_two_bundles_sequential():
    """
    Bundle 0: calculator (READ)
    Bundle 1: workspace_write (WRITE) — but workspace_write needs actual FS.
    Instead, monkeypatch to verify sequential execution semantics.
    """
    import concurrent.futures

    call_order = []

    def _mock_call_tool(*, tool_name, args, session_id, step, allow_restricted=False):
        call_order.append(tool_name)
        return ToolResult(success=True, output=f"ok-{tool_name}")

    from brain_qa import parallel_executor as pe_mod
    original_call_tool = pe_mod.call_tool
    pe_mod.call_tool = _mock_call_tool
    try:
        planner = ParallelPlanner()
        plan = planner.plan([
            PlanNode("calculator", {"expression": "1"}),
            PlanNode("workspace_write", {"path": "x", "content": "y"}, mode=ToolMode.WRITE),
        ])
        result = execute_plan(plan, session_id="t", step=0)
        assert result["bundles_executed"] == 2
        assert result["total_tools"] == 2
        # Because bundles execute sequentially, we can verify order
        assert call_order[0] == "calculator"
        assert call_order[1] == "workspace_write"
    finally:
        pe_mod.call_tool = original_call_tool


def test_execute_plan_resource_limit_splits_bundles():
    """5 DDG searches → >=2 bundles due to _MAX_PER_RESOURCE=3."""
    planner = ParallelPlanner()
    plan = planner.plan([PlanNode("web_search", {"query": f"q{i}"}) for i in range(5)])
    assert len(plan.bundles) >= 2
    # We do NOT actually execute web_search to avoid network calls in unit tests.
    # The planner grouping is the critical behavior under test.


def test_execute_parallel_fallback_single_tool():
    """execute_parallel with 1 tool should not use thread pool overhead."""
    results = execute_parallel(
        [{"name": "calculator", "args": {"expression": "10-3"}}],
        session_id="t",
        step=0,
    )
    assert len(results) == 1
    assert results[0][1].success
    assert "7" in results[0][1].output


def test_execute_parallel_multiple_tools():
    results = execute_parallel(
        [
            {"name": "calculator", "args": {"expression": "2+3"}},
            {"name": "calculator", "args": {"expression": "4*5"}},
        ],
        session_id="t",
        step=0,
    )
    assert len(results) == 2
    outputs = [r.output for _, r in results]
    assert any("5" in o for o in outputs)
    assert any("20" in o for o in outputs)
