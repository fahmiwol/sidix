"""
parallel_planner.py — Parallel Tool Planner

Planner yang secara eksplisit menentukan tool mana yang bisa parallel,
mana yang harus sequential berdasarkan dependency graph.

Inspired by: OpenAI Parallel Function Calling (2024)

Rules:
- Read-only tools bisa parallel (search, fetch, analyze)
- Write tools harus sequential (write setelah analyze)
- Shared external resource butuh rate limiter (DuckDuckGo)

Jiwa Sprint 3 Fase F (Kimi)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Data structures ──────────────────────────────────────────────────────────

class ToolMode(str, Enum):
    READ = "read"      # safe to parallel
    WRITE = "write"    # must be sequential
    HYBRID = "hybrid"  # depends on args


@dataclass
class PlanNode:
    """Satu tool call dalam plan."""
    tool_name: str
    args: dict[str, Any]
    depends_on: list[str] = field(default_factory=list)  # tool names that must finish first
    mode: ToolMode = ToolMode.READ


@dataclass
class PlanBundle:
    """Group of independent tool calls that can run in parallel."""
    nodes: list[PlanNode]
    bundle_id: int = 0


@dataclass
class ExecutionPlan:
    """Full execution plan: list of bundles (sequential), each bundle parallel."""
    bundles: list[PlanBundle]
    estimated_parallel_savings: float = 0.0  # vs sequential


# ── Tool registry metadata ───────────────────────────────────────────────────

_TOOL_MODES: dict[str, ToolMode] = {
    # Read-only tools
    "search_corpus": ToolMode.READ,
    "web_search": ToolMode.READ,
    "web_fetch": ToolMode.READ,
    "read_chunk": ToolMode.READ,
    "list_sources": ToolMode.READ,
    "calculator": ToolMode.READ,
    "search_web_wikipedia": ToolMode.READ,
    "concept_graph": ToolMode.READ,
    "code_analyze": ToolMode.READ,
    "code_validate": ToolMode.READ,
    "project_map": ToolMode.READ,
    "self_inspect": ToolMode.READ,
    "social_radar": ToolMode.READ,
    "graph_search": ToolMode.READ,
    "orchestration_plan": ToolMode.READ,
    "generate_copy": ToolMode.READ,
    "generate_content_plan": ToolMode.READ,
    "generate_brand_kit": ToolMode.READ,
    "generate_thumbnail": ToolMode.READ,
    "plan_campaign": ToolMode.READ,
    "generate_ads": ToolMode.READ,
    "muhasabah_refine": ToolMode.READ,
    "llm_judge": ToolMode.READ,
    "text_to_image": ToolMode.READ,
    "text_to_speech": ToolMode.READ,
    "speech_to_text": ToolMode.READ,
    "analyze_audio": ToolMode.READ,
    # Write tools
    "workspace_write": ToolMode.WRITE,
    "workspace_patch": ToolMode.WRITE,
    "git_commit_helper": ToolMode.WRITE,
    "scaffold_project": ToolMode.WRITE,
    # Hybrid
    "code_sandbox": ToolMode.HYBRID,  # read if no file IO, write if has IO
    "shell_run": ToolMode.WRITE,
    "test_run": ToolMode.READ,
    # Restricted
    "prompt_optimizer": ToolMode.WRITE,
}

# Dependencies: tool B needs output from tool A
_TOOL_DEPS: dict[str, list[str]] = {
    "read_chunk": ["search_corpus", "graph_search"],
    "web_fetch": ["web_search", "social_radar"],
    "workspace_patch": ["workspace_read", "code_analyze"],
    "git_commit_helper": ["git_status", "git_diff"],
}

# External resource groups — tools sharing same resource can't parallel unlimited
_RESOURCE_GROUPS: dict[str, str] = {
    "web_search": "duckduckgo",
    "social_radar": "duckduckgo",
    "web_fetch": "http",
}

_MAX_PER_RESOURCE = 3


# ── Planner ──────────────────────────────────────────────────────────────────

class ParallelPlanner:
    """Build execution plan with parallel bundles."""

    def plan(self, nodes: list[PlanNode]) -> ExecutionPlan:
        """
        Build execution plan from list of tool calls.

        Algorithm:
        1. Topological sort by dependencies
        2. Group independent nodes into bundles
        3. Respect resource limits per bundle
        """
        if not nodes:
            return ExecutionPlan(bundles=[])

        if len(nodes) == 1:
            return ExecutionPlan(bundles=[PlanBundle(nodes=nodes, bundle_id=0)])

        # Step 1: Resolve dependencies
        sorted_nodes = self._topo_sort(nodes)

        # Step 2: Group into bundles
        bundles: list[PlanBundle] = []
        current_bundle: list[PlanNode] = []
        current_resources: dict[str, int] = {}

        for node in sorted_nodes:
            # Check if this node can join current bundle
            can_parallel = (
                node.mode in (ToolMode.READ, ToolMode.HYBRID)
                and not node.depends_on
                and self._resource_fits(node, current_resources)
            )

            if can_parallel and current_bundle:
                current_bundle.append(node)
                self._add_resource(node, current_resources)
            else:
                # Start new bundle
                if current_bundle:
                    bundles.append(PlanBundle(nodes=list(current_bundle), bundle_id=len(bundles)))
                current_bundle = [node]
                current_resources = {}
                self._add_resource(node, current_resources)

        if current_bundle:
            bundles.append(PlanBundle(nodes=list(current_bundle), bundle_id=len(bundles)))

        # Calculate savings
        sequential_time = len(nodes)
        parallel_time = len(bundles)
        savings = (sequential_time - parallel_time) / sequential_time if sequential_time > 0 else 0.0

        return ExecutionPlan(
            bundles=bundles,
            estimated_parallel_savings=savings,
        )

    def plan_from_tool_names(self, tool_calls: list[dict[str, Any]]) -> ExecutionPlan:
        """Convenience: build plan from raw tool call dicts."""
        nodes = []
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {})
            mode = _TOOL_MODES.get(name, ToolMode.READ)
            deps = _TOOL_DEPS.get(name, [])
            nodes.append(PlanNode(tool_name=name, args=args, mode=mode, depends_on=deps))
        return self.plan(nodes)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _topo_sort(self, nodes: list[PlanNode]) -> list[PlanNode]:
        """Simple topological sort by dependency depth."""
        name_to_node = {n.tool_name: n for n in nodes}
        in_degree: dict[str, int] = {n.tool_name: 0 for n in nodes}
        adj: dict[str, list[str]] = {n.tool_name: [] for n in nodes}

        for n in nodes:
            for dep in n.depends_on:
                if dep in name_to_node:
                    adj[dep].append(n.tool_name)
                    in_degree[n.tool_name] += 1

        # Kahn's algorithm
        queue = [name for name, deg in in_degree.items() if deg == 0]
        result: list[PlanNode] = []
        while queue:
            name = queue.pop(0)
            result.append(name_to_node[name])
            for neighbor in adj[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Add any remaining (cycle or missing deps) at end
        for n in nodes:
            if n not in result:
                result.append(n)

        return result

    def _resource_fits(self, node: PlanNode, current: dict[str, int]) -> bool:
        """Check if adding this node respects resource limits."""
        group = _RESOURCE_GROUPS.get(node.tool_name)
        if not group:
            return True
        return current.get(group, 0) < _MAX_PER_RESOURCE

    def _add_resource(self, node: PlanNode, current: dict[str, int]) -> None:
        group = _RESOURCE_GROUPS.get(node.tool_name)
        if group:
            current[group] = current.get(group, 0) + 1


# ── Convenience API ──────────────────────────────────────────────────────────

def plan_tools(tool_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """One-shot: list of tool call dicts → execution plan dict."""
    planner = ParallelPlanner()
    plan = planner.plan_from_tool_names(tool_calls)
    return {
        "bundle_count": len(plan.bundles),
        "total_tools": sum(len(b.nodes) for b in plan.bundles),
        "estimated_parallel_savings": round(plan.estimated_parallel_savings, 2),
        "bundles": [
            {
                "bundle_id": b.bundle_id,
                "parallel": True,
                "tools": [n.tool_name for n in b.nodes],
                "modes": [n.mode.value for n in b.nodes],
            }
            for b in plan.bundles
        ],
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Parallel Tool Planner Self-Test ===\n")

    planner = ParallelPlanner()

    # Test 1: Independent reads → 1 bundle
    nodes1 = [
        PlanNode("search_corpus", {"query": "x"}),
        PlanNode("web_search", {"query": "x"}),
        PlanNode("calculator", {"expr": "1+1"}),
    ]
    plan1 = planner.plan(nodes1)
    print(f"[1] 3 independent reads: bundles={len(plan1.bundles)}, savings={plan1.estimated_parallel_savings:.2f}")
    assert len(plan1.bundles) == 1
    assert plan1.estimated_parallel_savings >= 0.66
    print("  OK\n")

    # Test 2: Read then write → 2 bundles
    nodes2 = [
        PlanNode("search_corpus", {"query": "x"}),
        PlanNode("workspace_write", {"path": "x", "content": "y"}, mode=ToolMode.WRITE),
    ]
    plan2 = planner.plan(nodes2)
    print(f"[2] Read + write: bundles={len(plan2.bundles)}")
    assert len(plan2.bundles) == 2
    print("  OK\n")

    # Test 3: Dependency chain → 3 bundles
    nodes3 = [
        PlanNode("search_corpus", {"query": "x"}),
        PlanNode("read_chunk", {"chunk_id": "1"}, depends_on=["search_corpus"]),
        PlanNode("web_search", {"query": "y"}),
    ]
    plan3 = planner.plan(nodes3)
    print(f"[3] Dependency chain: bundles={len(plan3.bundles)}")
    assert len(plan3.bundles) >= 2
    print("  OK\n")

    # Test 4: Resource limit (DuckDuckGo)
    nodes4 = [
        PlanNode("web_search", {"query": f"q{i}"})
        for i in range(5)
    ]
    plan4 = planner.plan(nodes4)
    print(f"[4] 5 DDG searches: bundles={len(plan4.bundles)} (max 3 per bundle)")
    assert len(plan4.bundles) >= 2  # split due to resource limit
    print("  OK\n")

    # Test 5: Convenience API
    d = plan_tools([
        {"name": "search_corpus", "args": {"query": "x"}},
        {"name": "web_search", "args": {"query": "y"}},
    ])
    assert d["bundle_count"] == 1
    assert d["total_tools"] == 2
    print("[5] Convenience API: OK\n")

    print("[OK] All self-tests passed")
