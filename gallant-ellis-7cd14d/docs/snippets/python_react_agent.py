# -*- coding: utf-8 -*-
"""
Snippet: Panggil SIDIX ReAct agent endpoint POST /agent/chat.

ReAct (Reasoning + Acting) agent SIDIX mendukung penggunaan tools
seperti RAG query, ledger lookup, dan kalkulasi sederhana.

Dependensi:
    pip install httpx

Cara menggunakan:
    python python_react_agent.py

Pastikan agent_serve.py brain_qa berjalan di port 8000 (atau sesuaikan BASE_URL).
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

import httpx

# ── Konfigurasi ────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"   # URL SIDIX agent server (own-stack)
TIMEOUT = 60.0                       # Detik (ReAct bisa butuh beberapa langkah)


# ── Tipe data ──────────────────────────────────────────────────────────────────
AgentMessage = dict[str, str]  # {"role": "user"|"assistant", "content": "..."}


class AgentToolUse:
    """Representasi satu step tool usage dari ReAct agent."""

    def __init__(self, raw: dict):
        self.tool_name: str = raw.get("tool", "unknown")
        self.tool_input: Any = raw.get("input", {})
        self.tool_output: Any = raw.get("output", None)
        self.step: int = raw.get("step", 0)

    def __repr__(self) -> str:
        return f"ToolUse(step={self.step}, tool={self.tool_name})"


class AgentResponse:
    """Respons dari POST /agent/chat."""

    def __init__(self, raw: dict):
        self.answer: str = raw.get("answer", "")
        self.reasoning: str = raw.get("reasoning", "")
        self.tool_uses: list[AgentToolUse] = [
            AgentToolUse(t) for t in raw.get("tool_uses", [])
        ]
        self.citations: list[dict] = raw.get("citations", [])
        self.persona: str = raw.get("persona", "general")
        self.latency_ms: Optional[float] = raw.get("latency_ms")

    def print_summary(self) -> None:
        """Cetak ringkasan respons terformat."""
        print("─" * 60)
        print(f"Persona   : {self.persona}")
        if self.latency_ms:
            print(f"Latency   : {self.latency_ms:.0f}ms")

        if self.tool_uses:
            print(f"\nTool steps ({len(self.tool_uses)}):")
            for tu in self.tool_uses:
                print(f"  [{tu.step}] {tu.tool_name} → {str(tu.tool_output)[:80]}")

        if self.reasoning:
            print(f"\nReasoning:\n  {self.reasoning[:300]}{'...' if len(self.reasoning) > 300 else ''}")

        print(f"\nJawaban:\n  {self.answer}")

        if self.citations:
            print(f"\nSitasi ({len(self.citations)}):")
            for i, cite in enumerate(self.citations[:3], 1):
                print(f"  [{i}] {cite.get('source', '?')} (skor: {cite.get('score', 0):.3f})")

        print("─" * 60)


# ── Client ─────────────────────────────────────────────────────────────────────
class SIDIXAgentClient:
    """Client untuk SIDIX ReAct agent endpoint."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._history: list[AgentMessage] = []

    def chat(
        self,
        message: str,
        persona: str = "general",
        tools: Optional[list[str]] = None,
        reset_history: bool = False,
    ) -> AgentResponse:
        """
        Kirim pesan ke ReAct agent.

        Args:
            message:       Pesan dari pengguna
            persona:       Persona/domain (e.g. "fiqh", "ushul", "general")
            tools:         Daftar tool yang diizinkan (None = semua)
            reset_history: Reset riwayat percakapan sebelum mengirim

        Returns:
            AgentResponse dengan answer, reasoning, dan tool_uses
        """
        if reset_history:
            self._history.clear()

        # Tambah pesan user ke riwayat
        self._history.append({"role": "user", "content": message})

        payload: dict[str, Any] = {
            "messages": self._history,
            "persona": persona,
        }
        if tools is not None:
            payload["allowed_tools"] = tools

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/agent/chat",
                json=payload,
            )
            response.raise_for_status()
            raw = response.json()

        agent_resp = AgentResponse(raw)

        # Tambah respons asisten ke riwayat untuk percakapan multi-turn
        self._history.append({"role": "assistant", "content": agent_resp.answer})

        return agent_resp

    def clear_history(self) -> None:
        """Reset riwayat percakapan."""
        self._history.clear()

    def health(self) -> dict:
        """Cek status agent server."""
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()


# ── Contoh penggunaan ──────────────────────────────────────────────────────────
def main() -> None:
    client = SIDIXAgentClient()

    # Health check
    print("=== SIDIX ReAct Agent ===")
    try:
        health = client.health()
        print("Status:", health.get("status", "?"))
    except httpx.ConnectError:
        print("ERROR: Agent server tidak berjalan di", BASE_URL)
        print("Pastikan: python apps/brain_qa/agent_serve.py")
        sys.exit(1)

    # Contoh 1: Query tunggal dengan tool RAG
    print("\n=== Turn 1: Query dengan RAG tool ===")
    resp1 = client.chat(
        message="Jelaskan konsep ijtihad dan syarat-syaratnya menurut ulama ushul fiqh.",
        persona="ushul",
        tools=["rag_query", "ledger_lookup"],
    )
    resp1.print_summary()

    # Contoh 2: Follow-up multi-turn (riwayat otomatis dikirim)
    print("\n=== Turn 2: Follow-up (multi-turn) ===")
    resp2 = client.chat(
        message="Siapa ulama kontemporer yang dikenal ahli dalam bidang ini?",
        persona="ushul",
    )
    resp2.print_summary()

    # Contoh 3: Reset dan mulai percakapan baru
    print("\n=== Turn 3: Percakapan baru (reset history) ===")
    resp3 = client.chat(
        message="Apa pengertian maqasid al-syariah menurut Ibn Ashur?",
        persona="fiqh",
        reset_history=True,
    )
    resp3.print_summary()


if __name__ == "__main__":
    main()
