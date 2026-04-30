"""Ringkasan ringan percakapan / sesi agen (tanpa LLM tambahan)."""

from __future__ import annotations

from typing import Any

from .agent_react import AgentSession


def build_session_summary(session: AgentSession) -> dict[str, Any]:
    q = (session.question or "").strip()
    a = (session.final_answer or "").strip()
    tools: list[str] = []
    for s in session.steps:
        if s.action_name and not s.is_final and s.action_name not in tools:
            tools.append(s.action_name)
    q_short = q[:280] + ("…" if len(q) > 280 else "")
    a_short = a[:400] + ("…" if len(a) > 400 else "")
    lines = [f"Pertanyaan: {q_short}"]
    if tools:
        lines.append("Alat: " + " → ".join(tools))
    lines.append(f"Jawaban (cuplikan): {a_short}")
    bullets = [
        f"Persona: {session.persona}",
        f"Keyakinan: {session.confidence or '—'}",
        f"Langkah: {len(session.steps)}",
    ]
    return {"summary": "\n".join(lines), "bullets": bullets}
