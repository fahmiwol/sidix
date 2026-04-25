"""
parallel_executor.py — Parallel Tool Execution for SIDIX
Enables concurrent execution of independent tools using a thread pool.

Jiwa Sprint 4 — Fase B: Bundle-by-bundle execution wired from parallel_planner.
"""

from __future__ import annotations
import concurrent.futures
from typing import Any
from .agent_tools import call_tool, ToolResult

def execute_parallel(
    tool_calls: list[dict[str, Any]],
    *,
    session_id: str = "parallel",
    step: int = 0,
    allow_restricted: bool = False
) -> list[tuple[dict, ToolResult]]:
    """
    Execute multiple tool calls in parallel.
    Each tool_call should be a dict: {"name": str, "args": dict}.
    Returns a list of (tool_call, ToolResult) tuples.
    """
    results: list[tuple[dict, ToolResult]] = []
    
    if not tool_calls:
        return results
        
    # If only one tool, run it sync to avoid overhead
    if len(tool_calls) == 1:
        tc = tool_calls[0]
        res = call_tool(
            tool_name=tc["name"],
            args=tc["args"],
            session_id=session_id,
            step=step,
            allow_restricted=allow_restricted
        )
        return [(tc, res)]

    # Run in parallel using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tool_calls), 8)) as executor:
        # Create futures
        future_to_tc = {
            executor.submit(
                call_tool,
                tool_name=tc["name"],
                args=tc["args"],
                session_id=session_id,
                step=step,
                allow_restricted=allow_restricted
            ): tc
            for tc in tool_calls
        }
        
        # Collect results in original order
        # Wait for all to complete
        concurrent.futures.wait(future_to_tc.keys())
        
        # Build results list maintaining order
        for tc in tool_calls:
            # Find the future for this tool call
            # (Note: dict iteration preserves order since Python 3.7)
            for future, future_tc in future_to_tc.items():
                if future_tc is tc:
                    results.append((tc, future.result()))
                    break
                    
    return results


# ── Jiwa Sprint 4: Bundle-by-bundle execution ────────────────────────────────

def execute_plan(
    execution_plan,
    *,
    session_id: str = "parallel",
    step: int = 0,
    allow_restricted: bool = False,
    verbose: bool = False,
) -> dict:
    """
    Execute an ExecutionPlan bundle-by-bundle.

    Each bundle runs in parallel internally.
    Bundles execute sequentially (wait for bundle N before starting N+1).
    This respects WRITE-sequentiality and dependency chains.

    Args:
        execution_plan: ExecutionPlan dari ParallelPlanner (bundle list)
        session_id, step, allow_restricted: forwarded ke call_tool
        verbose: print progress

    Returns:
        dict dengan keys:
            - results: list[(tool_call_dict, ToolResult)]  (flat, in plan order)
            - bundle_results: list[list[(tool_call_dict, ToolResult)]] (per bundle)
            - total_tools: int
            - bundles_executed: int
            - failed_count: int
    """
    from .parallel_planner import ExecutionPlan, PlanBundle

    flat_results: list[tuple[dict, ToolResult]] = []
    bundle_results: list[list[tuple[dict, ToolResult]]] = []
    failed_count = 0

    if not execution_plan or not execution_plan.bundles:
        return {
            "results": flat_results,
            "bundle_results": bundle_results,
            "total_tools": 0,
            "bundles_executed": 0,
            "failed_count": 0,
        }

    for bundle in execution_plan.bundles:
        if not isinstance(bundle, PlanBundle):
            continue
        tool_calls = [{"name": n.tool_name, "args": n.args} for n in bundle.nodes]
        if not tool_calls:
            continue

        if verbose:
            names = [n.tool_name for n in bundle.nodes]
            print(f"  [Bundle {bundle.bundle_id}] Running: {names}")

        # Execute this bundle in parallel
        batch = execute_parallel(
            tool_calls,
            session_id=session_id,
            step=step,
            allow_restricted=allow_restricted,
        )
        bundle_results.append(batch)
        flat_results.extend(batch)

        for _tc, res in batch:
            if not res.success:
                failed_count += 1

        if verbose:
            ok = sum(1 for _, r in batch if r.success)
            print(f"  [Bundle {bundle.bundle_id}] Done: {ok}/{len(batch)} OK")

    return {
        "results": flat_results,
        "bundle_results": bundle_results,
        "total_tools": len(flat_results),
        "bundles_executed": len(bundle_results),
        "failed_count": failed_count,
    }

def merge_observations(parallel_results: list[tuple[dict, ToolResult]]) -> str:
    """
    Merge multiple tool results into a single observation string.
    """
    if not parallel_results:
        return "No results."
        
    if len(parallel_results) == 1:
        return parallel_results[0][1].output
        
    blocks = []
    for tc, res in parallel_results:
        status = "SUCCESS" if res.success else "FAILED"
        block = f"--- ACTION: {tc['name']} ({status}) ---\n"
        if res.success:
            block += res.output
        else:
            block += f"Error: {res.error}"
        blocks.append(block)
        
    return "\n\n".join(blocks)
