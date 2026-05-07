"""
a2a_server.py — A2A (Agent-to-Agent) Protocol Server for SIDIX
Phase 2: Accept tasks from external agents via Google's A2A protocol.

Core subset:
  POST /a2a/tasks/send          — sync task creation + completion
  GET  /a2a/tasks/{taskId}      — get task state
  POST /a2a/tasks/sendSubscribe — SSE streaming
  POST /a2a/tasks/cancel        — cancel task
"""

from __future__ import annotations

import enum
import logging
import threading
import time
import uuid
from typing import Any

from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class TaskStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class TextPart(BaseModel):
    type: str = "text"
    text: str


class FilePart(BaseModel):
    type: str = "file"
    file: dict = Field(default_factory=dict)


class Part(BaseModel):
    type: str
    text: str = ""
    file: dict = Field(default_factory=dict)


class Message(BaseModel):
    role: str
    parts: list[dict]


class Artifact(BaseModel):
    parts: list[dict]
    index: int = 0
    append: bool = False


class Task(BaseModel):
    id: str
    status: TaskStatus
    artifacts: list[Artifact] = Field(default_factory=list)
    history: list[Message] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)


_TASKS: dict[str, Task] = {}
_TASK_LOCK = threading.Lock()


def _now() -> float:
    return time.time()


def create_task(message: Message) -> Task:
    task = Task(
        id=f"task-{uuid.uuid4().hex}",
        status=TaskStatus.SUBMITTED,
        history=[message],
    )
    with _TASK_LOCK:
        _TASKS[task.id] = task
    return task


def get_task(task_id: str) -> Task | None:
    with _TASK_LOCK:
        return _TASKS.get(task_id)


def _update_task(task_id: str, **kwargs: Any) -> Task | None:
    with _TASK_LOCK:
        task = _TASKS.get(task_id)
        if task is None:
            return None
        for k, v in kwargs.items():
            setattr(task, k, v)
        task.updated_at = _now()
        return task


def process_task_async(task_id: str) -> None:
    """Run in background thread. Calls existing SIDIX brain."""
    task = get_task(task_id)
    if task is None:
        return

    _update_task(task_id, status=TaskStatus.WORKING)

    try:
        user_text = ""
        for msg in task.history:
            if msg.role == "user":
                for part in msg.parts:
                    if part.get("type") == "text":
                        user_text = part.get("text", "")
                        break
                if user_text:
                    break

        if not user_text:
            _update_task(task_id, status=TaskStatus.FAILED)
            return

        # Heuristic: simple short query → direct generate, else ReAct
        _complex_keywords = [
            "research", "riset", "analisis", "analysis", "code", "kode",
            "program", "execute", "run", "cari", "search", "find", "buat",
            "generate", "create", "build", "develop", "write", "tulis",
        ]
        is_simple = (
            len(user_text.split()) < 15
            and not any(kw in user_text.lower() for kw in _complex_keywords)
        )

        if is_simple:
            from .local_llm import generate_sidix

            system = (
                "Kamu adalah SIDIX, AI multipurpose yang dibangun di atas prinsip "
                "kejujuran (sidq), sitasi (sanad), dan verifikasi (tabayyun). "
                "Jawab berdasarkan fakta, bedakan fakta vs hipotesis, "
                "sebutkan sumber jika ada, dan akui keterbatasan jika tidak tahu."
            )
            answer, _mode = generate_sidix(
                prompt=user_text,
                system=system,
                max_tokens=512,
                temperature=0.7,
            )
        else:
            from .agent_react import run_react

            session = run_react(
                question=user_text,
                persona="UTZ",
                client_id="",
                agency_id="",
                conversation_id="",
            )
            answer = session.final_answer or "(kosong)"

        agent_message = Message(
            role="agent",
            parts=[{"type": "text", "text": answer}],
        )
        artifact = Artifact(
            parts=[{"type": "text", "text": answer}],
            index=0,
            append=False,
        )

        current_history = list(task.history)
        current_history.append(agent_message)

        _update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            artifacts=[artifact],
            history=current_history,
        )
    except Exception as exc:
        log.warning("[a2a] process_task_async failed: %s", exc)
        _update_task(task_id, status=TaskStatus.FAILED)


def tasks_send(body: dict) -> dict:
    """Handle POST /a2a/tasks/send — sync, waits for completion."""
    message = Message(**body.get("message", {"role": "user", "parts": []}))
    task = create_task(message)

    thread = threading.Thread(target=process_task_async, args=(task.id,), daemon=True)
    thread.start()

    max_wait = 300  # 5 minutes
    poll_interval = 0.5
    elapsed = 0.0

    while elapsed < max_wait:
        current = get_task(task_id=task.id)
        if current is None:
            break
        if current.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED):
            break
        time.sleep(poll_interval)
        elapsed += poll_interval

    final = get_task(task_id=task.id)
    if final is None:
        return {"error": "task lost"}
    return final.model_dump()


def tasks_get(task_id: str) -> dict:
    """Handle GET /a2a/tasks/{taskId} — get current task state."""
    task = get_task(task_id)
    if task is None:
        return {"error": "task not found"}
    return task.model_dump()


def tasks_cancel(task_id: str) -> dict:
    """Handle POST /a2a/tasks/cancel — cancel a task."""
    task = get_task(task_id)
    if task is None:
        return {"error": "task not found"}
    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED):
        return task.model_dump()
    _update_task(task_id, status=TaskStatus.CANCELED)
    updated = get_task(task_id)
    return updated.model_dump() if updated else {"error": "task not found"}


def tasks_send_subscribe(body: dict):
    """Generator for SSE /a2a/tasks/sendSubscribe — stream task updates."""
    import json as _json

    message = Message(**body.get("message", {"role": "user", "parts": []}))
    task = create_task(message)

    yield f"data: {_json.dumps({'event': 'task_status_update', 'task': task.model_dump()})}\n\n"

    thread = threading.Thread(target=process_task_async, args=(task.id,), daemon=True)
    thread.start()

    max_wait = 300
    poll_interval = 0.5
    elapsed = 0.0
    last_status = task.status

    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        current = get_task(task_id=task.id)
        if current is None:
            yield f"data: {_json.dumps({'event': 'task_status_update', 'task': {'id': task.id, 'status': 'failed', 'error': 'task lost'}})}\n\n"
            break

        if current.status != last_status:
            yield f"data: {_json.dumps({'event': 'task_status_update', 'task': current.model_dump()})}\n\n"
            last_status = current.status

        if current.status == TaskStatus.COMPLETED and current.artifacts:
            for artifact in current.artifacts:
                yield f"data: {_json.dumps({'event': 'task_artifact_update', 'artifact': artifact.model_dump(), 'task_id': task.id})}\n\n"
            break

        if current.status in (TaskStatus.FAILED, TaskStatus.CANCELED):
            yield f"data: {_json.dumps({'event': 'task_status_update', 'task': current.model_dump()})}\n\n"
            break

    yield f"data: {_json.dumps({'event': 'close'})}\n\n"
