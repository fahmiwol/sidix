"""
conversation_memory.py
======================
Session-based conversation history store untuk SIDIX.

Menyimpan riwayat percakapan per session_id sehingga LLM bisa
mempertahankan konteks antar pesan.

Lokasi: apps/brain_qa/brain_qa/conversation_memory.py
"""

import time
import threading
from collections import OrderedDict
from typing import Optional


# ── Konfigurasi ────────────────────────────────────────────────────────────────

MAX_SESSIONS      = 1000   # maksimum session aktif di memori
MAX_TURNS_PER_SESSION = 20 # maksimum turn (user+assistant) per session
SESSION_TTL_SECONDS = 3600 # 1 jam — session dihapus jika idle
MAX_TOKENS_ESTIMATE = 6000 # estimasi max tokens history (ganti sesuai model)


# ── Internal store ─────────────────────────────────────────────────────────────

class ConversationMemory:
    """
    In-process conversation store dengan auto-eviction.

    Untuk production dengan multiple workers, ganti _store dengan
    Redis: `redis.get(session_id)` / `redis.setex(session_id, TTL, json.dumps(history))`
    """

    def __init__(
        self,
        max_sessions: int = MAX_SESSIONS,
        max_turns: int = MAX_TURNS_PER_SESSION,
        ttl: int = SESSION_TTL_SECONDS,
    ):
        self._store: OrderedDict[str, dict] = OrderedDict()
        self._lock = threading.Lock()
        self.max_sessions = max_sessions
        self.max_turns = max_turns
        self.ttl = ttl

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_history(self, session_id: str) -> list[dict]:
        """Ambil history untuk session_id. Return [] jika tidak ada / expired."""
        with self._lock:
            entry = self._store.get(session_id)
            if entry is None:
                return []
            if time.time() - entry["last_active"] > self.ttl:
                del self._store[session_id]
                return []
            # bump ke atas (LRU)
            self._store.move_to_end(session_id)
            entry["last_active"] = time.time()
            return list(entry["history"])

    def append_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
    ) -> None:
        """
        Tambahkan satu turn (user + assistant) ke history.
        Otomatis trim jika melebihi max_turns.
        """
        with self._lock:
            if session_id not in self._store:
                self._evict_if_needed()
                self._store[session_id] = {
                    "history": [],
                    "last_active": time.time(),
                }
            entry = self._store[session_id]
            entry["history"].append({"role": "user",      "content": user_message})
            entry["history"].append({"role": "assistant", "content": assistant_message})
            entry["last_active"] = time.time()

            # Trim: buang turn terlama jika melebihi batas
            # Selalu hapus 2 sekaligus (user+assistant) untuk menjaga pasangan
            while len(entry["history"]) > self.max_turns * 2:
                entry["history"].pop(0)
                entry["history"].pop(0)

            self._store.move_to_end(session_id)

    def clear_session(self, session_id: str) -> None:
        """Reset history untuk session tertentu (misal saat user klik 'New Chat')."""
        with self._lock:
            self._store.pop(session_id, None)

    def get_stats(self) -> dict:
        """Untuk monitoring / debug."""
        with self._lock:
            return {
                "active_sessions": len(self._store),
                "max_sessions": self.max_sessions,
                "ttl_seconds": self.ttl,
            }

    # ── Internal ───────────────────────────────────────────────────────────────

    def _evict_if_needed(self) -> None:
        """Hapus session terlama jika store sudah penuh (LRU eviction)."""
        while len(self._store) >= self.max_sessions:
            self._store.popitem(last=False)  # hapus yang paling lama


# ── Singleton global ───────────────────────────────────────────────────────────
# Import ini di agent_react.py dan router.

memory = ConversationMemory()


# ── Helper: build messages untuk LLM ──────────────────────────────────────────

def build_messages_with_history(
    system_prompt: str,
    history: list[dict],
    current_user_message: str,
    max_history_chars: int = 12000,
) -> list[dict]:
    """
    Gabungkan system prompt + history + pesan sekarang menjadi
    list messages yang siap dikirim ke LLM.

    max_history_chars: batas karakter total history untuk menghindari
    context overflow. History terlama dibuang lebih dulu.
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Trim history dari depan jika terlalu panjang
    trimmed = list(history)
    total_chars = sum(len(m["content"]) for m in trimmed)
    while trimmed and total_chars > max_history_chars:
        removed = trimmed.pop(0)
        total_chars -= len(removed["content"])
        # Buang pasangannya juga jika masih ada
        if trimmed:
            removed2 = trimmed.pop(0)
            total_chars -= len(removed2["content"])

    messages.extend(trimmed)
    messages.append({"role": "user", "content": current_user_message})
    return messages
