"""
Unit tests untuk memory_store — isolated, menggunakan tmp_path DB.
"""

from __future__ import annotations

import pytest

from brain_qa import memory_store


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    """Override DB path ke temporary directory untuk setiap test."""
    db_path = tmp_path / "test_memory.db"
    monkeypatch.setattr(memory_store, "MEMORY_DB_PATH", str(db_path))
    # Re-init connection pool
    if hasattr(memory_store._local, "db"):
        delattr(memory_store._local, "db")
    memory_store.init_db()
    yield
    if hasattr(memory_store._local, "db"):
        memory_store._local.db.close()
        delattr(memory_store._local, "db")


def test_create_and_get_conversation():
    conv_id = memory_store.create_conversation(user_id="u1", title="Hello")
    conv = memory_store.get_conversation(conv_id)
    assert conv is not None
    assert conv["user_id"] == "u1"
    assert conv["title"] == "Hello"


def test_list_conversations():
    memory_store.create_conversation(user_id="u2", title="A")
    memory_store.create_conversation(user_id="u2", title="B")
    rows = memory_store.list_conversations(user_id="u2", limit=10)
    assert len(rows) == 2
    assert rows[0]["title"] == "B"  # newest first


def test_add_and_get_messages():
    conv_id = memory_store.create_conversation()
    mid = memory_store.add_message(conv_id, "user", "Halo")
    assert mid > 0
    msgs = memory_store.get_messages(conv_id)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Halo"


def test_get_recent_context():
    conv_id = memory_store.create_conversation()
    memory_store.add_message(conv_id, "user", "Q1")
    memory_store.add_message(conv_id, "assistant", "A1")
    memory_store.add_message(conv_id, "user", "Q2")
    memory_store.add_message(conv_id, "assistant", "A2")
    ctx = memory_store.get_recent_context(conv_id, turns=2)
    assert len(ctx) == 4
    assert ctx[0]["role"] == "user"
    assert ctx[-1]["content"] == "A2"


def test_rename_conversation():
    conv_id = memory_store.create_conversation(title="Old")
    assert memory_store.rename_conversation(conv_id, "New") is True
    conv = memory_store.get_conversation(conv_id)
    assert conv["title"] == "New"


def test_delete_conversation():
    conv_id = memory_store.create_conversation()
    assert memory_store.delete_conversation(conv_id) is True
    assert memory_store.get_conversation(conv_id) is None


def test_user_profile_get_or_create():
    profile = memory_store.get_or_create_user("user_xyz")
    assert profile["user_id"] == "user_xyz"
    assert profile["preferred_language"] == "id"


def test_save_session_best_effort():
    """save_session harus tidak raise meski object aneh."""
    class FakeSession:
        conversation_id = ""
        question = "Test Q"
        final_answer = "Test A"
        persona = "UTZ"
        user_language = "id"
        citations = []
        confidence_score = 0.9

    memory_store.save_session(FakeSession(), user_id="u_test")
    # Tidak raise = pass
