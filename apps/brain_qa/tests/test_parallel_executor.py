"""
test_parallel_executor.py — Tests for Parallel Tool Execution
"""

import time
import pytest
from brain_qa.parallel_executor import execute_parallel, merge_observations
from brain_qa.agent_tools import TOOL_REGISTRY, ToolSpec, ToolResult

# Mock tool that sleeps to verify parallelism
def _mock_sleep_tool(args: dict) -> ToolResult:
    duration = float(args.get("duration", 0.1))
    time.sleep(duration)
    return ToolResult(success=True, output=f"Slept for {duration}s")

def test_execute_parallel():
    # Setup mock tools in registry
    TOOL_REGISTRY["mock_sleep"] = ToolSpec(
        name="mock_sleep",
        description="Sleeps",
        params=["duration"],
        permission="open",
        fn=_mock_sleep_tool
    )
    
    tool_calls = [
        {"name": "mock_sleep", "args": {"duration": 0.5}},
        {"name": "mock_sleep", "args": {"duration": 0.5}},
        {"name": "mock_sleep", "args": {"duration": 0.5}},
    ]
    
    start_time = time.time()
    results = execute_parallel(tool_calls)
    duration = time.time() - start_time
    
    assert len(results) == 3
    assert all(res.success for tc, res in results)
    # If parallel, total duration should be ~0.5s, not 1.5s
    assert duration < 1.0, f"Execution too slow: {duration}s (expected parallel)"
    
    obs = merge_observations(results)
    assert "ACTION: mock_sleep (SUCCESS)" in obs
    assert "Slept for 0.5s" in obs

def test_merge_observations_empty():
    assert merge_observations([]) == "No results."
