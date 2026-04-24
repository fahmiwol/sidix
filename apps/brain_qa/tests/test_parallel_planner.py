"""
test_parallel_planner.py — Test Parallel Tool Planner

Jiwa Sprint 3 Fase F (Kimi)
"""

import pytest
from brain_qa.parallel_planner import (
    ParallelPlanner,
    PlanNode,
    ToolMode,
    plan_tools,
    _TOOL_MODES,
    _TOOL_DEPS,
    _RESOURCE_GROUPS,
    _MAX_PER_RESOURCE,
)


class TestParallelPlanner:

    def test_independent_reads_single_bundle(self):
        planner = ParallelPlanner()
        nodes = [
            PlanNode("search_corpus", {"query": "x"}),
            PlanNode("calculator", {"expr": "1+1"}),
            PlanNode("list_sources", {}),
        ]
        plan = planner.plan(nodes)
        assert len(plan.bundles) == 1
        assert plan.estimated_parallel_savings == pytest.approx(0.67, 0.01)

    def test_write_separates_bundle(self):
        planner = ParallelPlanner()
        nodes = [
            PlanNode("search_corpus", {"query": "x"}),
            PlanNode("workspace_write", {"path": "x", "content": "y"}, mode=ToolMode.WRITE),
        ]
        plan = planner.plan(nodes)
        assert len(plan.bundles) == 2
        assert plan.bundles[0].nodes[0].mode == ToolMode.READ
        assert plan.bundles[1].nodes[0].mode == ToolMode.WRITE

    def test_dependency_creates_sequential_bundles(self):
        planner = ParallelPlanner()
        nodes = [
            PlanNode("search_corpus", {"query": "x"}),
            PlanNode("read_chunk", {"chunk_id": "1"}, depends_on=["search_corpus"]),
        ]
        plan = planner.plan(nodes)
        assert len(plan.bundles) == 2
        assert plan.bundles[0].nodes[0].tool_name == "search_corpus"
        assert plan.bundles[1].nodes[0].tool_name == "read_chunk"

    def test_resource_limit_splits_bundles(self):
        planner = ParallelPlanner()
        nodes = [PlanNode("web_search", {"query": f"q{i}"}) for i in range(5)]
        plan = planner.plan(nodes)
        assert len(plan.bundles) >= 2
        for bundle in plan.bundles:
            web_search_count = sum(1 for n in bundle.nodes if n.tool_name == "web_search")
            assert web_search_count <= _MAX_PER_RESOURCE

    def test_mixed_read_write_sequence(self):
        planner = ParallelPlanner()
        nodes = [
            PlanNode("search_corpus", {"query": "x"}),
            PlanNode("web_search", {"query": "y"}),
            PlanNode("workspace_write", {"path": "a"}, mode=ToolMode.WRITE),
            PlanNode("workspace_patch", {"path": "a"}, mode=ToolMode.WRITE),
        ]
        plan = planner.plan(nodes)
        # First bundle: reads
        assert plan.bundles[0].nodes[0].mode == ToolMode.READ
        # Remaining: writes (each gets own bundle)
        write_bundles = [b for b in plan.bundles if any(n.mode == ToolMode.WRITE for n in b.nodes)]
        assert len(write_bundles) >= 2

    def test_convenience_api(self):
        result = plan_tools([
            {"name": "search_corpus", "args": {"query": "x"}},
            {"name": "calculator", "args": {"expr": "1+1"}},
        ])
        assert result["bundle_count"] == 1
        assert result["total_tools"] == 2
        assert result["bundles"][0]["parallel"] is True
        assert "search_corpus" in result["bundles"][0]["tools"]

    def test_empty_plan(self):
        planner = ParallelPlanner()
        plan = planner.plan([])
        assert len(plan.bundles) == 0
        assert plan.estimated_parallel_savings == 0.0

    def test_single_node(self):
        planner = ParallelPlanner()
        plan = planner.plan([PlanNode("search_corpus", {"query": "x"})])
        assert len(plan.bundles) == 1
        assert len(plan.bundles[0].nodes) == 1

    def test_tool_mode_registry(self):
        assert _TOOL_MODES["search_corpus"] == ToolMode.READ
        assert _TOOL_MODES["workspace_write"] == ToolMode.WRITE
        assert _TOOL_MODES["code_sandbox"] == ToolMode.HYBRID

    def test_dependency_registry(self):
        assert "search_corpus" in _TOOL_DEPS["read_chunk"]
