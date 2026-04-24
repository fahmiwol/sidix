"""
parallel_executor.py — Parallel Tool Execution for SIDIX
Enables concurrent execution of independent tools using a thread pool.
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
