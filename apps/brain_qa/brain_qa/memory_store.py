"""
memory_store.py — SIDIX Conversational Memory Layer
====================================================

Menyimpan session history dan user preferences secara persistent
(SQLite) supaya SIDIX bisa:
  1. Melanjutkan percakapan (conversation threading)
  2. Ingat preferensi user (bahasa, persona, literacy)
  3. Retrieve context dari percakapan sebelumnya untuk RAG-style injection

Env:
    SIDIX_MEMORY_DB — path SQLite (default: data/sidix_memory.db)
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .paths import default_data_dir

log = logging.getLogger("sidix.memory")

MEMORY_DB_PATH = os.getenv(
    "SIDIX_MEMORY_DB",
    str(default_data_dir() / "sidix_memory.db"),
)
_MAX_CONTEXT_TURNS = int(os.getenv("SIDIX_MEMORY_CONTEXT_TURNS", "12"))
_MAX_CONVERSATION_AGE_DAYS = int(os.getenv("SIDIX_MEMORY_CONV_AGE_DAYS", "30"))

_local = threading.local()


def _conn() -> sqlite3.Connection:
    if not hasattr(_local, "db"):
        _local.db = sqlite3.connect(MEMORY_DB_PATH, check_same_thread=False)
        _local.db.row_factory = sqlite3.Row
    return _local.db


@contextmanager
def _transaction():
    conn = _conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


_INIT_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL DEFAULT 'anon',
    title           TEXT,
    persona         TEXT DEFAULT 'mighan',
    language        TEXT,
    literacy        TEXT,
    cultural_frame  TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    metadata_json   TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS messages (
    message_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),
    content         TEXT NOT NULL,
    persona         TEXT,
    citations_json  TEXT DEFAULT '[]',
    confidence_score REAL,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id         TEXT PRIMARY KEY,
    display_name    TEXT,
    preferred_language TEXT DEFAULT 'id',
    preferred_persona  TEXT DEFAULT 'mighan',
    literacy        TEXT DEFAULT 'awam',
    cultural_frame  TEXT DEFAULT 'nusantara',
    interests_json  TEXT DEFAULT '[]',
    total_messages  INTEGER DEFAULT 0,
    total_conversations INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    Path(MEMORY_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with _transaction() as conn:
        conn.executescript(_INIT_SQL)
    log.info("Memory DB initialized: %s", MEMORY_DB_PATH)


def create_conversation(
    user_id: str = "anon",
    title: str = "",
    persona: str = "mighan",
    language: str = "",
    literacy: str = "",
    cultural_frame: str = "",
    metadata: Optional[dict] = None,
) -> str:
    conv_id = str(uuid.uuid4())[:12]
    now = _now()
    with _transaction() as conn:
        conn.execute(
            """
            INSERT INTO conversations
            (conversation_id, user_id, title, persona, language, literacy,
             cultural_frame, created_at, updated_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv_id, user_id, title or "New Chat", persona, language,
                literacy, cultural_frame, now, now, json.dumps(metadata or {}),
            ),
        )
        conn.execute(
            """
            INSERT INTO user_profiles (user_id, created_at, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                total_conversations = total_conversations + 1,
                updated_at = excluded.updated_at
            """,
            (user_id, now, now),
        )
    return conv_id


def get_conversation(conv_id: str) -> Optional[dict]:
    with _transaction() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?", (conv_id,)
        ).fetchone()
    return dict(row) if row else None


def list_conversations(user_id: str = "anon", limit: int = 50, offset: int = 0) -> list[dict]:
    cutoff = f"-{ _MAX_CONVERSATION_AGE_DAYS } days"
    with _transaction() as conn:
        rows = conn.execute(
            """
            SELECT * FROM conversations
            WHERE user_id = ?
              AND updated_at > datetime('now', ?)
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, cutoff, limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def rename_conversation(conv_id: str, title: str) -> bool:
    with _transaction() as conn:
        cur = conn.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE conversation_id = ?",
            (title, _now(), conv_id),
        )
    return cur.rowcount > 0


def delete_conversation(conv_id: str) -> bool:
    with _transaction() as conn:
        cur = conn.execute(
            "DELETE FROM conversations WHERE conversation_id = ?", (conv_id,)
        )
    return cur.rowcount > 0


def add_message(
    conv_id: str,
    role: str,
    content: str,
    persona: str = "",
    citations: Optional[list[dict]] = None,
    confidence_score: Optional[float] = None,
) -> int:
    now = _now()
    with _transaction() as conn:
        cur = conn.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content, persona, citations_json,
             confidence_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv_id, role, content, persona,
                json.dumps(citations or []),
                confidence_score, now,
            ),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
            (now, conv_id),
        )
    return cur.lastrowid or 0


def get_messages(conv_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    with _transaction() as conn:
        rows = conn.execute(
            """
            SELECT * FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            (conv_id, limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_context(conv_id: str, turns: int = _MAX_CONTEXT_TURNS) -> list[dict]:
    limit = turns * 2
    with _transaction() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM messages
            WHERE conversation_id = ? AND role IN ('user', 'assistant')
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (conv_id, limit),
        ).fetchall()
    result = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    return result


def get_or_create_user(user_id: str = "anon") -> dict:
    with _transaction() as conn:
        row = conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        if row:
            return dict(row)
        now = _now()
        conn.execute(
            """
            INSERT INTO user_profiles
            (user_id, created_at, updated_at)
            VALUES (?, ?, ?)
            """,
            (user_id, now, now),
        )
        return {
            "user_id": user_id,
            "preferred_language": "id",
            "preferred_persona": "mighan",
            "literacy": "awam",
            "cultural_frame": "nusantara",
            "interests_json": "[]",
            "total_messages": 0,
            "total_conversations": 0,
        }


def update_user_preferences(user_id: str, **kwargs: Any) -> bool:
    allowed = {
        "display_name", "preferred_language", "preferred_persona",
        "literacy", "cultural_frame", "interests_json",
    }
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return False
    fields["updated_at"] = _now()
    cols = ", ".join(f"{k} = ?" for k in fields)
    vals = list(fields.values()) + [user_id]
    with _transaction() as conn:
        cur = conn.execute(
            f"UPDATE user_profiles SET {cols} WHERE user_id = ?",
            vals,
        )
    return cur.rowcount > 0


def save_session(
    session: Any,
    conv_id: Optional[str] = None,
    user_id: str = "anon",
) -> None:
    """
    Save an AgentSession (or similar dataclass) into memory store.
    Best-effort: never raises.
    """
    try:
        conv = conv_id or getattr(session, "conversation_id", None)
        if not conv:
            conv = create_conversation(
                user_id=user_id,
                title=getattr(session, "question", "")[:60],
                persona=getattr(session, "persona", "mighan"),
                language=getattr(session, "user_language", ""),
                literacy=getattr(session, "user_literacy", ""),
                cultural_frame=getattr(session, "user_cultural_frame", ""),
            )
        # Save user question
        add_message(
            conv, "user",
            getattr(session, "question", ""),
            persona=getattr(session, "persona", ""),
        )
        # Save assistant answer
        add_message(
            conv, "assistant",
            getattr(session, "final_answer", ""),
            persona=getattr(session, "persona", ""),
            citations=getattr(session, "citations", None),
            confidence_score=getattr(session, "confidence_score", None),
        )
        # Update user message count
        with _transaction() as conn:
            conn.execute(
                """
                UPDATE user_profiles
                SET total_messages = total_messages + 2,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (_now(), user_id),
            )
    except Exception as e:
        log.warning("save_session best-effort failed: %s", e)
