"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

dev_task_queue.py — Sprint 40 Phase 1 (Autonomous Developer task queue)

SQLite-backed queue untuk task autonomous development. Founder add task
via CLI/Telegram/dashboard → dipick by `autonomous_developer.tick()` cron
setiap 30 menit.

State machine:
  pending → in_progress → review → approved → merged
                       └→ rejected
                       └→ escalated (max iter exhausted)
                       └→ expired (7d no owner verdict)

Relationship:
- Consumed oleh: autonomous_developer.py (orchestrator)
- Owner via: __main__.py CLI + agent_serve.py endpoints
- Audit ke: hafidz_ledger via tiap state transition

Reference: docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md
"""
from __future__ import annotations

import logging
import os
import sqlite3
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Configurable via env for testing + different deployments (Sprint 40 E2E)
_DATA_DIR = Path(os.getenv("SIDIX_DATA_DIR", "/opt/sidix/.data"))
_QUEUE_DB = _DATA_DIR / "autonomous_dev" / "task_queue.sqlite3"

VALID_STATES = (
    "pending", "in_progress", "review", "approved",
    "merged", "rejected", "escalated", "expired",
)
DEFAULT_OWNER_TIMEOUT_DAYS = 7
DEFAULT_MAX_ITER = 5


@dataclass
class DevTask:
    """One unit of autonomous development work."""
    task_id: str = ""
    target_path: str = ""           # e.g. "Mighan-tasks/cursor-001-mighan-canvas"
    goal: str = ""                  # human description "production-ready: auth+save+deploy"
    priority: int = 50              # 0-100, higher first
    state: str = "pending"
    iter_count: int = 0
    max_iter: int = DEFAULT_MAX_ITER
    owner_verdict: str = "pending"  # pending | approved | rejected
    owner_feedback: str = ""        # used pada request_changes flow
    branch_name: str = ""           # autonomous-dev/<task_id>
    pr_url: str = ""
    error_log: str = ""
    persona_fanout: bool = False    # leverage multi-persona research mode
    created_at: str = ""
    updated_at: str = ""
    cycle_id: str = ""              # untuk hafidz ledger


def _conn() -> sqlite3.Connection:
    _QUEUE_DB.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(_QUEUE_DB))


def init_db() -> None:
    """Idempotent schema init."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS dev_tasks (
                task_id TEXT PRIMARY KEY,
                target_path TEXT NOT NULL,
                goal TEXT NOT NULL,
                priority INTEGER DEFAULT 50,
                state TEXT DEFAULT 'pending',
                iter_count INTEGER DEFAULT 0,
                max_iter INTEGER DEFAULT 5,
                owner_verdict TEXT DEFAULT 'pending',
                owner_feedback TEXT DEFAULT '',
                branch_name TEXT DEFAULT '',
                pr_url TEXT DEFAULT '',
                error_log TEXT DEFAULT '',
                persona_fanout INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                cycle_id TEXT DEFAULT ''
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_state_priority ON dev_tasks(state, priority DESC)")


def add_task(target_path: str, goal: str, priority: int = 50,
             persona_fanout: bool = False) -> DevTask:
    """Create new pending task."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    task_id = f"autodev-{int(time.time())}-{abs(hash(target_path)) % 10000:04d}"
    branch = f"autonomous-dev/{task_id}"
    cycle = f"autodev-cycle-{int(time.time())}"

    task = DevTask(
        task_id=task_id, target_path=target_path, goal=goal,
        priority=priority, persona_fanout=persona_fanout,
        branch_name=branch, created_at=now, updated_at=now,
        cycle_id=cycle,
    )

    with _conn() as c:
        c.execute("""
            INSERT INTO dev_tasks
            (task_id, target_path, goal, priority, state, max_iter,
             persona_fanout, branch_name, created_at, updated_at, cycle_id)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?)
        """, (task.task_id, task.target_path, task.goal, task.priority,
              task.max_iter, int(task.persona_fanout), task.branch_name,
              task.created_at, task.updated_at, task.cycle_id))

    log.info("[autodev_queue] added task=%s target=%s", task_id, target_path)
    return task


def pick_next() -> Optional[DevTask]:
    """Return highest-priority pending task, or None."""
    init_db()
    with _conn() as c:
        c.row_factory = sqlite3.Row
        row = c.execute("""
            SELECT * FROM dev_tasks
            WHERE state = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """).fetchone()
    if not row:
        return None
    return _row_to_task(row)


def list_tasks(state: Optional[str] = None, limit: int = 50) -> list[DevTask]:
    """List tasks, optionally filtered by state."""
    init_db()
    query = "SELECT * FROM dev_tasks"
    params: tuple = ()
    if state:
        if state not in VALID_STATES:
            raise ValueError(f"invalid state: {state}")
        query += " WHERE state = ?"
        params = (state,)
    query += " ORDER BY created_at DESC LIMIT ?"
    params = (*params, limit)

    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(query, params).fetchall()
    return [_row_to_task(r) for r in rows]


def get_task(task_id: str) -> Optional[DevTask]:
    init_db()
    with _conn() as c:
        c.row_factory = sqlite3.Row
        row = c.execute("SELECT * FROM dev_tasks WHERE task_id = ?",
                        (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def update_state(task_id: str, new_state: str, **fields) -> bool:
    """Transition task state + optional field updates."""
    if new_state not in VALID_STATES:
        raise ValueError(f"invalid state: {new_state}")
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    set_clauses = ["state = ?", "updated_at = ?"]
    values: list = [new_state, now]
    for k, v in fields.items():
        set_clauses.append(f"{k} = ?")
        values.append(v)
    values.append(task_id)

    with _conn() as c:
        cur = c.execute(
            f"UPDATE dev_tasks SET {', '.join(set_clauses)} WHERE task_id = ?",
            tuple(values),
        )
        ok = cur.rowcount > 0
    if ok:
        log.info("[autodev_queue] task=%s state=%s", task_id, new_state)
    return ok


def _row_to_task(row: sqlite3.Row) -> DevTask:
    d = dict(row)
    d["persona_fanout"] = bool(d.get("persona_fanout", 0))
    return DevTask(**{k: v for k, v in d.items() if k in DevTask.__dataclass_fields__})


__all__ = [
    "DevTask", "VALID_STATES", "init_db",
    "add_task", "pick_next", "list_tasks", "get_task", "update_state",
]
