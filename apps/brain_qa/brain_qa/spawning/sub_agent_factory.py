"""
sub_agent_factory.py — Sprint K: Sub-Agent Factory untuk Multi-Agent Spawning

Konsep:
  Factory pattern untuk menciptakan sub-agents dengan persona, tools, dan
  konfigurasi spesifik. Tiap sub-agent adalah instance ReAct loop dengan
  persona dan toolset yang terbatas.

  Mengadaptasi CrewAI's role-based agent design dan OpenAI SDK's
  agent-as-tool pattern.

  5 Sub-Agent Types (LOCKED):
    - research    → ALEY  → gather & synthesize
    - generation  → UTZ   → produce content
    - validation  → ALEY  → verify & critique
    - memory      → AYMAN → store & retrieve
    - orchestration → OOMAR → coordinate

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

log = logging.getLogger("sidix.spawning.factory")


# ── Agent Registry ───────────────────────────────────────────────────────

@dataclass
class AgentSpec:
    """Specification untuk sub-agent."""
    agent_type: str
    persona: str
    system_prompt: str
    tools: list[str]
    layer: int  # execution layer (-1 = any layer)
    max_tokens: int = 600
    temperature: float = 0.7
    description: str = ""


_AGENT_REGISTRY: dict[str, AgentSpec] = {
    "research": AgentSpec(
        agent_type="research",
        persona="ALEY",
        system_prompt=(
            "Kamu adalah Research Agent — researcher yang berbasis bukti. "
            "Tugasmu mengumpulkan dan mensintesis informasi dari berbagai sumber. "
            "Gunakan tools: corpus_search, web_search, dense_search. "
            "Output: ringkasan temuan dengan sumber yang jelas."
        ),
        tools=["search_corpus", "search_web", "dense_search", "calculator"],
        layer=0,
        temperature=0.5,
        description="Evidence gatherer and synthesizer",
    ),
    "generation": AgentSpec(
        agent_type="generation",
        persona="UTZ",
        system_prompt=(
            "Kamu adalah Generation Agent — kreator yang visioner. "
            "Tugasmu memproduksi konten berkualitas tinggi dari input research. "
            "Gunakan tools: generate_content_plan, generate_copy, text_to_image. "
            "Output: konten kreatif yang original dan coherent."
        ),
        tools=["generate_content_plan", "generate_copy", "workspace_write"],
        layer=1,
        temperature=0.85,
        description="Creative content producer",
    ),
    "validation": AgentSpec(
        agent_type="validation",
        persona="ALEY",
        system_prompt=(
            "Kamu adalah Validation Agent — kritikus yang skeptis. "
            "Tugasmu memverifikasi output dari Generation Agent. "
            "Evaluasi: keakuratan, kelengkapan, konsistensi, dan kualitas sumber. "
            "Gunakan tools: sanad_validate, critique. "
            "Output: JSON {score, reasoning, suggestions, confidence}."
        ),
        tools=["sanad_validate", "critique", "search_corpus"],
        layer=2,
        temperature=0.4,
        description="Quality verifier and critic",
    ),
    "memory": AgentSpec(
        agent_type="memory",
        persona="AYMAN",
        system_prompt=(
            "Kamu adalah Memory Agent — librarian yang terorganisir. "
            "Tugasmu menyimpan dan mengindeks hasil intermediate ke Hafidz. "
            "Gunakan tools: hafidz_store, pattern_extract. "
            "Output: konfirmasi penyimpanan dengan metadata."
        ),
        tools=["hafidz_store", "pattern_extract", "workspace_list"],
        layer=-1,
        temperature=0.6,
        description="Storage and indexing manager",
    ),
    "orchestration": AgentSpec(
        agent_type="orchestration",
        persona="OOMAR",
        system_prompt=(
            "Kamu adalah Orchestration Agent — strategist yang melihat gambaran besar. "
            "Tugasmu mengkoordinasikan sub-agents dan menyelesaikan konflik. "
            "Gunakan tools: orchestration_plan, roadmap_next_items. "
            "Output: rencana koordinasi dengan prioritas dan trade-off."
        ),
        tools=["orchestration_plan", "roadmap_next_items", "workspace_read"],
        layer=-1,
        temperature=0.6,
        description="Coordination and conflict resolution",
    ),
}


# ── SubAgent Handle ──────────────────────────────────────────────────────

@dataclass
class SubAgentHandle:
    """Handle untuk spawned sub-agent."""
    agent_id: str
    agent_type: str
    persona: str
    task: str
    status: str = "idle"  # idle | running | completed | failed | timeout
    result: Optional[dict[str, Any]] = None
    started_at: str = ""
    completed_at: str = ""
    error: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()


# ── SubAgentFactory ──────────────────────────────────────────────────────

class SubAgentFactory:
    """Factory untuk menciptakan dan menjalankan sub-agents.

    Usage:
        factory = SubAgentFactory()
        handle = factory.spawn("research", "Cari data tentang X", shared_ctx)
        result = factory.run(handle)  # blocking execution
    """

    def __init__(self, max_tokens_default: int = 600):
        self.max_tokens_default = max_tokens_default

    # ── Factory Methods ──────────────────────────────────────────────────

    def get_spec(self, agent_type: str) -> AgentSpec:
        """Get agent specification."""
        agent_type = agent_type.lower()
        if agent_type not in _AGENT_REGISTRY:
            raise ValueError(f"Unknown agent type: {agent_type}. "
                           f"Available: {list(_AGENT_REGISTRY.keys())}")
        return _AGENT_REGISTRY[agent_type]

    def list_types(self) -> list[str]:
        """List available agent types."""
        return list(_AGENT_REGISTRY.keys())

    def spawn(
        self,
        agent_type: str,
        task: str,
        shared_ctx: Any,  # SharedContext
        parent_task_id: str = "",
    ) -> SubAgentHandle:
        """Spawn a sub-agent (create handle, don't run yet)."""
        spec = self.get_spec(agent_type)
        agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"

        handle = SubAgentHandle(
            agent_id=agent_id,
            agent_type=agent_type,
            persona=spec.persona,
            task=task,
        )

        # Write spawn event ke shared context
        if shared_ctx is not None:
            shared_ctx.write(
                key=f"spawn_event_{agent_id}",
                value={
                    "event": "spawned",
                    "agent_type": agent_type,
                    "persona": spec.persona,
                    "task": task,
                    "parent_task_id": parent_task_id,
                    "layer": spec.layer,
                },
                agent_id=agent_id,
                agent_type=agent_type,
                layer=spec.layer,
            )

        log.info("[spawning] Spawned %s (type=%s, persona=%s)",
                 agent_id, agent_type, spec.persona)
        return handle

    # ── Execution ────────────────────────────────────────────────────────

    def run(self, handle: SubAgentHandle, shared_ctx: Any) -> SubAgentHandle:
        """Execute sub-agent task (blocking, sync).

        Runs the agent via OMNYX Director with restricted toolset.
        """
        spec = self.get_spec(handle.agent_type)
        handle.status = "running"

        try:
            # Build prompt dengan context dari shared workspace
            prompt = self._build_prompt(handle, spec, shared_ctx)

            # Run via OMNYX Director (simplified — tanpa full ReAct loop)
            result = self._execute_agent(prompt, spec)

            handle.result = {
                "output": result,
                "agent_type": handle.agent_type,
                "persona": handle.persona,
            }
            handle.status = "completed"
            handle.completed_at = datetime.now(timezone.utc).isoformat()

            # Write result ke shared context
            if shared_ctx is not None:
                shared_ctx.write(
                    key=f"result_{handle.agent_id}",
                    value=handle.result,
                    agent_id=handle.agent_id,
                    agent_type=handle.agent_type,
                    layer=spec.layer,
                )

            log.info("[spawning] %s completed (type=%s)",
                     handle.agent_id, handle.agent_type)

        except Exception as e:
            handle.status = "failed"
            handle.error = str(e)
            log.warning("[spawning] %s failed: %s", handle.agent_id, e)

        return handle

    def _build_prompt(
        self,
        handle: SubAgentHandle,
        spec: AgentSpec,
        shared_ctx: Any,
    ) -> str:
        """Build execution prompt dengan context injection."""
        # Inject relevant context dari layers sebelumnya
        context_snippets = []
        if shared_ctx is not None and spec.layer > 0:
            # Ambil output dari layer sebelumnya
            prev_layer = spec.layer - 1
            prev_outputs = shared_ctx.layer_output(prev_layer)
            for i, out in enumerate(prev_outputs[:3]):  # max 3 prev outputs
                snippet = json.dumps(out, ensure_ascii=False)[:500]
                context_snippets.append(f"[Prev Output {i+1}]: {snippet}")

        context_block = "\n".join(context_snippets) if context_snippets else ""

        prompt = (
            f"{spec.system_prompt}\n\n"
            f"Task: {handle.task}\n\n"
        )
        if context_block:
            prompt += f"Context from previous agents:\n{context_block}\n\n"
        prompt += "Provide your output now."

        return prompt

    def _execute_agent(self, prompt: str, spec: AgentSpec) -> str:
        """Execute agent via LLM call (simplified, sync)."""
        # Gunakan persona_adapter untuk persona-specific generation
        from ..persona_adapter import generate_with_persona
        return generate_with_persona(
            prompt,
            persona=spec.persona,
            max_tokens=spec.max_tokens,
            temperature=spec.temperature,
        )

    # ── Batch Execution ──────────────────────────────────────────────────

    def spawn_batch(
        self,
        agent_type: str,
        tasks: list[str],
        shared_ctx: Any,
        parent_task_id: str = "",
    ) -> list[SubAgentHandle]:
        """Spawn multiple agents of same type for parallel execution."""
        return [
            self.spawn(agent_type, task, shared_ctx, parent_task_id)
            for task in tasks
        ]

    # ── Stats ────────────────────────────────────────────────────────────

    @staticmethod
    def get_registry_stats() -> dict[str, dict]:
        """Get stats for all registered agent types."""
        return {
            name: {
                "persona": spec.persona,
                "layer": spec.layer,
                "tools": spec.tools,
                "temperature": spec.temperature,
                "description": spec.description,
            }
            for name, spec in _AGENT_REGISTRY.items()
        }
