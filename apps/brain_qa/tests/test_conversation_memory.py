"""
Test untuk conversation_memory.py
Jalankan: pytest tests/test_conversation_memory.py -v
"""

import pytest
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from brain_qa.conversation_memory import ConversationMemory, build_messages_with_history


# ── ConversationMemory Tests ───────────────────────────────────────────────────

class TestConversationMemory:

    def setup_method(self):
        self.mem = ConversationMemory(max_sessions=10, max_turns=5, ttl=60)

    def test_empty_history_returns_empty_list(self):
        assert self.mem.get_history("unknown-session") == []

    def test_append_and_retrieve(self):
        self.mem.append_turn("s1", "siapa presiden?", "Prabowo Subianto")
        history = self.mem.get_history("s1")
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "siapa presiden?"}
        assert history[1] == {"role": "assistant", "content": "Prabowo Subianto"}

    def test_multi_turn_context(self):
        """Ini yang memperbaiki bug utama: turn kedua punya konteks turn pertama."""
        self.mem.append_turn("s2", "siapa presiden indonesia?", "Prabowo Subianto")
        self.mem.append_turn("s2", "kalo wakilnya?", "Gibran Rakabuming Raka")

        history = self.mem.get_history("s2")
        assert len(history) == 4  # 2 turn × 2 (user+assistant)

        # Simulasi: messages yang dikirim ke LLM untuk pertanyaan ketiga
        messages = build_messages_with_history(
            system_prompt="Kamu SIDIX.",
            history=history,
            current_user_message="periode berapa mereka menjabat?",
        )

        # Pastikan history ada di messages → model punya konteks
        roles = [m["role"] for m in messages]
        assert roles == ["system", "user", "assistant", "user", "assistant", "user"]

    def test_trim_old_turns_when_exceed_max(self):
        """History harus di-trim otomatis saat melebihi max_turns."""
        for i in range(8):  # masukkan 8 turn, max hanya 5
            self.mem.append_turn("s3", f"pertanyaan {i}", f"jawaban {i}")

        history = self.mem.get_history("s3")
        # max_turns=5 → max 10 messages (5 turn × 2)
        assert len(history) <= 10
        # Pastikan yang tersisa adalah yang terbaru
        assert history[-1]["content"] == "jawaban 7"

    def test_clear_session(self):
        self.mem.append_turn("s4", "hello", "hi")
        self.mem.clear_session("s4")
        assert self.mem.get_history("s4") == []

    def test_session_isolation(self):
        """Session berbeda harus punya history berbeda."""
        self.mem.append_turn("user_A", "saya di Jakarta", "ok")
        self.mem.append_turn("user_B", "saya di Surabaya", "ok")

        hist_A = self.mem.get_history("user_A")
        hist_B = self.mem.get_history("user_B")

        assert "Jakarta" in hist_A[0]["content"]
        assert "Surabaya" in hist_B[0]["content"]
        assert len(hist_A) == 2
        assert len(hist_B) == 2

    def test_ttl_expiry(self):
        """Session harus expired setelah TTL."""
        mem = ConversationMemory(ttl=1)  # 1 detik TTL
        mem.append_turn("exp-session", "pertanyaan", "jawaban")
        assert len(mem.get_history("exp-session")) == 2

        time.sleep(1.1)
        assert mem.get_history("exp-session") == []  # expired

    def test_lru_eviction(self):
        """Session terlama harus dibuang saat max_sessions tercapai."""
        mem = ConversationMemory(max_sessions=3)
        mem.append_turn("s1", "q", "a")
        mem.append_turn("s2", "q", "a")
        mem.append_turn("s3", "q", "a")
        mem.append_turn("s4", "q", "a")  # s1 harus terevict

        # s1 sudah tidak ada
        assert mem.get_history("s1") == []
        # s2, s3, s4 masih ada
        assert len(mem.get_history("s2")) == 2
        assert len(mem.get_history("s4")) == 2


# ── build_messages_with_history Tests ─────────────────────────────────────────

class TestBuildMessages:

    def test_basic_structure(self):
        messages = build_messages_with_history(
            system_prompt="Kamu SIDIX.",
            history=[],
            current_user_message="halo",
        )
        assert messages[0]["role"] == "system"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "halo"

    def test_history_injected_correctly(self):
        history = [
            {"role": "user",      "content": "siapa presiden?"},
            {"role": "assistant", "content": "Prabowo"},
        ]
        messages = build_messages_with_history(
            system_prompt="Kamu SIDIX.",
            history=history,
            current_user_message="kalo wakilnya?",
        )
        assert len(messages) == 4  # system + 2 history + current
        assert messages[1]["content"] == "siapa presiden?"
        assert messages[2]["content"] == "Prabowo"
        assert messages[3]["content"] == "kalo wakilnya?"

    def test_trim_long_history(self):
        """History yang terlalu panjang harus di-trim dari depan."""
        long_history = []
        for i in range(20):
            long_history.append({"role": "user",      "content": "A" * 1000})
            long_history.append({"role": "assistant", "content": "B" * 1000})

        messages = build_messages_with_history(
            system_prompt="sys",
            history=long_history,
            current_user_message="pertanyaan baru",
            max_history_chars=5000,
        )
        history_in_messages = messages[1:-1]  # exclude system + current
        total = sum(len(m["content"]) for m in history_in_messages)
        assert total <= 5000

    def test_always_ends_with_current_message(self):
        messages = build_messages_with_history(
            system_prompt="sys",
            history=[{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}],
            current_user_message="pertanyaan terbaru",
        )
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "pertanyaan terbaru"


# ── Skenario Nyata ─────────────────────────────────────────────────────────────

class TestRealWorldScenario:

    def test_presiden_wakil_scenario(self):
        """
        Reproduksi bug yang dilaporkan:
        User: siapa presiden indonesia?
        AI: Prabowo Subianto
        User: kalo wakilnya?
        AI: [seharusnya jawab Gibran, bukan jawaban generik]
        """
        mem = ConversationMemory()
        system_prompt = "Kamu SIDIX, AI agent yang menjawab berdasarkan fakta."

        # Turn 1
        turn1_answer = "Presiden Indonesia adalah Prabowo Subianto untuk periode 2024-2029."
        mem.append_turn("session-test", "siapa presiden indonesia?", turn1_answer)

        # Turn 2 — ini yang dulu tidak nyambung
        history = mem.get_history("session-test")
        turn2_messages = build_messages_with_history(
            system_prompt=system_prompt,
            history=history,
            current_user_message="kalo wakilnya?",
        )

        roles = [m["role"] for m in turn2_messages]
        contents = [m["content"] for m in turn2_messages]

        assert "Prabowo" in contents[2]  # jawaban turn 1 ada di messages
        assert roles == ["system", "user", "assistant", "user"]
