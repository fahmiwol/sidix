"""
a2a_mock_agent.py — Mock External A2A Agent for Testing

Simple FastAPI app (or standalone functions) that mimics an external A2A-compatible agent.
Used for integration testing of A2AClient without needing a real external agent.

Run standalone:
    python -m brain_qa.a2a_mock_agent
    # → serves on http://localhost:9999

Or import functions for testing:
    from brain_qa.a2a_mock_agent import mock_agent_card, mock_tasks_send
"""

from __future__ import annotations

import time
import uuid
from typing import Any


# ── Mock data ────────────────────────────────────────────────────────────────


def mock_agent_card() -> dict:
    """Return a mock AgentCard JSON-compatible dict."""
    return {
        "name": "Mock Calculator Agent",
        "description": "A mock external agent for testing A2A delegation. Echoes and calculates simple expressions.",
        "url": "http://localhost:9999",
        "version": "0.1.0",
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "statePersistence": False,
        },
        "authentication": {
            "schemes": ["none"],
        },
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "calculator",
                "name": "Calculator",
                "description": "Evaluate simple math expressions.",
                "tags": ["math", "calculator", "compute"],
                "examples": ["What is 2 + 2?", "Calculate 100 * 0.15"],
            },
            {
                "id": "echo",
                "name": "Echo",
                "description": "Echo back the input message with formatting.",
                "tags": ["echo", "test", "debug"],
                "examples": ["Hello world"],
            },
        ],
        "mcpEndpoint": "",
    }


_MOCK_TASKS: dict[str, dict] = {}


def _extract_text(body: dict) -> str:
    message = body.get("message", {})
    parts = message.get("parts", [])
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            return part.get("text", "")
    return ""


def mock_tasks_send(body: dict) -> dict:
    """Handle POST /a2a/tasks/send — sync task creation + completion."""
    user_text = _extract_text(body)
    task_id = f"mock-task-{uuid.uuid4().hex[:8]}"
    created_at = time.time()

    # Simple heuristic: if message looks like math, evaluate it
    answer = _mock_process(user_text)

    task = {
        "id": task_id,
        "status": "completed",
        "artifacts": [
            {
                "parts": [{"type": "text", "text": answer}],
                "index": 0,
                "append": False,
            }
        ],
        "history": [
            {"role": "user", "parts": [{"type": "text", "text": user_text}]},
            {"role": "agent", "parts": [{"type": "text", "text": answer}]},
        ],
        "metadata": {"agent_name": "Mock Calculator Agent"},
        "created_at": created_at,
        "updated_at": time.time(),
    }
    _MOCK_TASKS[task_id] = task
    return task


def mock_tasks_get(task_id: str) -> dict:
    """Handle GET /a2a/tasks/{taskId}."""
    task = _MOCK_TASKS.get(task_id)
    if task is None:
        return {"error": "task not found"}
    return task


def mock_tasks_cancel(task_id: str) -> dict:
    """Handle POST /a2a/tasks/cancel."""
    task = _MOCK_TASKS.get(task_id)
    if task is None:
        return {"error": "task not found"}
    if task["status"] in ("completed", "failed", "canceled"):
        return task
    task["status"] = "canceled"
    task["updated_at"] = time.time()
    return task


def mock_tasks_send_subscribe(body: dict) -> Iterator[str]:
    """Handle POST /a2a/tasks/sendSubscribe — SSE generator."""
    import json as _json

    user_text = _extract_text(body)
    task_id = f"mock-task-{uuid.uuid4().hex[:8]}"
    created_at = time.time()

    # Initial submitted state
    task = {
        "id": task_id,
        "status": "submitted",
        "artifacts": [],
        "history": [
            {"role": "user", "parts": [{"type": "text", "text": user_text}]},
        ],
        "metadata": {"agent_name": "Mock Calculator Agent"},
        "created_at": created_at,
        "updated_at": created_at,
    }
    _MOCK_TASKS[task_id] = task
    yield f"data: {_json.dumps({'event': 'task_status_update', 'task': task})}\n\n"

    # Simulate brief work
    time.sleep(0.1)
    task["status"] = "working"
    task["updated_at"] = time.time()
    yield f"data: {_json.dumps({'event': 'task_status_update', 'task': task})}\n\n"

    # Complete
    time.sleep(0.1)
    answer = _mock_process(user_text)
    task["status"] = "completed"
    task["artifacts"] = [
        {
            "parts": [{"type": "text", "text": answer}],
            "index": 0,
            "append": False,
        }
    ]
    task["history"].append(
        {"role": "agent", "parts": [{"type": "text", "text": answer}]}
    )
    task["updated_at"] = time.time()
    yield f"data: {_json.dumps({'event': 'task_status_update', 'task': task})}\n\n"
    yield f"data: {_json.dumps({'event': 'task_artifact_update', 'artifact': task['artifacts'][0], 'task_id': task_id})}\n\n"
    yield f"data: {_json.dumps({'event': 'close'})}\n\n"


def _mock_process(user_text: str) -> str:
    """Mock processing logic: calculator or echo."""
    import re

    text = user_text.strip()
    if not text:
        return "[Mock Agent] Received empty message."

    # Try simple math: digits, operators, spaces, dots, commas, percent
    math_expr = re.sub(r"[^\d\s\+\-\*\/\(\)\.\,\%]", "", text)
    # Heuristic: if after stripping we have a reasonable expression
    clean = "".join(text.split())
    simple_match = re.match(r"^[\d\+\-\*\/\(\)\.\,\%]+$", clean)
    if simple_match and len(clean) >= 3:
        try:
            # Safe eval with limited scope
            result = eval(clean, {"__builtins__": {}})  # noqa: S307
            return f"[Mock Agent] Calculated: {clean} = {result}"
        except Exception:
            pass

    # Echo with prefix
    return f"[Mock Agent] Echo: {text}"


# ── FastAPI app (optional, for standalone testing) ───────────────────────────


def create_mock_app() -> Any:
    """Create a FastAPI app for the mock agent."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import StreamingResponse
    except ImportError as exc:
        raise RuntimeError("FastAPI tidak terinstall. Jalankan: pip install fastapi uvicorn") from exc

    app = FastAPI(title="Mock A2A Agent", version="0.1.0")

    @app.get("/.well-known/agent-card.json")
    def agent_card():
        return mock_agent_card()

    @app.post("/a2a/tasks/send")
    def tasks_send(body: dict):
        return mock_tasks_send(body)

    @app.get("/a2a/tasks/{task_id}")
    def tasks_get(task_id: str):
        return mock_tasks_get(task_id)

    @app.post("/a2a/tasks/sendSubscribe")
    def tasks_send_subscribe(body: dict):
        return StreamingResponse(mock_tasks_send_subscribe(body), media_type="text/event-stream")

    @app.post("/a2a/tasks/cancel")
    def tasks_cancel(body: dict):
        task_id = body.get("taskId", body.get("id", ""))
        if not task_id:
            return {"error": "taskId or id required"}
        return mock_tasks_cancel(task_id)

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_mock_app()
    uvicorn.run(app, host="0.0.0.0", port=9999)
