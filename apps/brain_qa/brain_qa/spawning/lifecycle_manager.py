"""
lifecycle_manager.py — Sprint K: Lifecycle Manager untuk Multi-Agent Spawning

Konsep:
  Mengelola siklus hidup sub-agents: spawn → monitor → aggregate → graceful kill.
  Mengadaptasi shadow_pool.py's ChakraBudget untuk resource tracking dan
  council.py's ThreadPool pattern untuk parallel execution.

  Safety:
    - Max concurrent agents: 10
    - Timeout per layer: 120s default
    - No recursive spawn (depth = 1)
    - Audit log: semua events ke JSONL

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger("sidix.spawning.lifecycle")


# ── Storage ──────────────────────────────────────────────────────────────

SPAWN_LOG = Path("brain/public/spawning/log.jsonl")
SPAWN_LOG.parent.mkdir(parents=True, exist_ok=True)


# ── Config ───────────────────────────────────────────────────────────────

MAX_CONCURRENT_AGENTS = 10
DEFAULT_LAYER_TIMEOUT = 120.0
MAX_RETRY_ATTEMPTS = 2


# ── Data Structures ──────────────────────────────────────────────────────

@dataclass
class AgentStatus:
    """Status snapshot untuk sub-agent."""
    agent_id: str
    agent_type: str
    status: str  # idle | running | completed | failed | timeout
    result_preview: str = ""
    error: str = ""
    duration_ms: int = 0


@dataclass
class LayerResult:
    """Result dari satu execution layer."""
    layer: int
    agents: list[AgentStatus]
    all_passed: bool = False
    avg_score: float = 0.0
    duration_ms: int = 0


@dataclass
class SpawnResult:
    """Final result dari spawn session."""
    task_id: str
    status: str  # completed | failed | timeout | partial
    layers: list[LayerResult]
    synthesized_answer: str = ""
    citations: list[str] = None
    total_duration_ms: int = 0
    error: str = ""

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


# ── Audit Logging ────────────────────────────────────────────────────────

def _audit_log(event: str, task_id: str, details: dict[str, Any]) -> None:
    """Append structured log entry."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "task_id": task_id,
        "details": details,
    }
    try:
        with SPAWN_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.debug("[spawning] Audit log failed: %s", e)


# ── ChakraBudget (reuse dari shadow_pool.py) ─────────────────────────────

@dataclass
class ChakraBudget:
    """Resource budget untuk spawn session."""
    max_tokens: int = 100_000
    max_latency_ms: int = 300_000  # 5 minutes
    max_agents: int = MAX_CONCURRENT_AGENTS

    tokens_used: int = 0
    latency_ms: int = 0
    agents_spawned: int = 0

    def can_spawn(self) -> bool:
        return self.agents_spawned < self.max_agents

    def record_spawn(self, estimated_tokens: int = 1000) -> bool:
        if not self.can_spawn():
            return False
        self.agents_spawned += 1
        self.tokens_used += estimated_tokens
        return True

    def record_latency(self, delta_ms: int) -> None:
        self.latency_ms += delta_ms

    def is_exhausted(self) -> bool:
        return (
            self.tokens_used >= self.max_tokens
            or self.latency_ms >= self.max_latency_ms
            or self.agents_spawned >= self.max_agents
        )

    def to_dict(self) -> dict:
        return {
            "max_tokens": self.max_tokens,
            "max_latency_ms": self.max_latency_ms,
            "max_agents": self.max_agents,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "agents_spawned": self.agents_spawned,
            "exhausted": self.is_exhausted(),
        }


# ── LifecycleManager ─────────────────────────────────────────────────────

class LifecycleManager:
    """Manages spawn → execution → aggregation lifecycle.

    Usage:
        lm = LifecycleManager(task_id="task_001")
        handles = lm.spawn_layer(layer=0, agent_type="research", tasks=[...], ctx=ctx)
        layer_result = lm.execute_layer(handles, ctx=ctx)
        final = lm.aggregate_final(synthesize=True)
    """

    def __init__(
        self,
        task_id: str,
        budget: Optional[ChakraBudget] = None,
        layer_timeout: float = DEFAULT_LAYER_TIMEOUT,
    ):
        self.task_id = task_id
        self.budget = budget or ChakraBudget()
        self.layer_timeout = layer_timeout
        self._handles: dict[str, Any] = {}  # agent_id → SubAgentHandle
        self._layer_results: list[LayerResult] = []
        self._start_time = time.time()

        _audit_log("session_init", task_id, self.budget.to_dict())

    # ── Spawn ────────────────────────────────────────────────────────────

    def spawn_layer(
        self,
        layer: int,
        agent_type: str,
        tasks: list[str],
        factory: Any,  # SubAgentFactory
        shared_ctx: Any,  # SharedContext
    ) -> list[Any]:
        """Spawn a layer of agents. Returns handles."""
        available = self.budget.max_agents - self.budget.agents_spawned
        if len(tasks) > available:
            raise RuntimeError(
                f"Budget exhausted: need {len(tasks)} agents but only "
                f"{available} slots available (max={self.budget.max_agents})"
            )

        handles = []
        for task in tasks:
            if not self.budget.record_spawn():
                break
            handle = factory.spawn(agent_type, task, shared_ctx, self.task_id)
            self._handles[handle.agent_id] = handle
            handles.append(handle)

        _audit_log(
            "layer_spawned",
            self.task_id,
            {"layer": layer, "agent_type": agent_type, "count": len(handles)},
        )
        log.info("[spawning] task=%s layer=%d spawned %d %s agents",
                 self.task_id, layer, len(handles), agent_type)
        return handles

    # ── Execute ──────────────────────────────────────────────────────────

    def execute_layer(
        self,
        handles: list[Any],
        factory: Any,
        shared_ctx: Any,
        layer: int = 0,
    ) -> LayerResult:
        """Execute a layer of agents in parallel."""
        layer_start = time.time()
        statuses = []

        # Parallel execution via ThreadPool (reuse council.py pattern)
        max_workers = min(len(handles), 8)
        completed = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_handle = {
                executor.submit(factory.run, h, shared_ctx): h
                for h in handles
            }

            for future in as_completed(future_to_handle, timeout=self.layer_timeout):
                handle = future_to_handle[future]
                try:
                    result_handle = future.result()
                    completed += 1
                    duration = int((time.time() - layer_start) * 1000)
                    preview = ""
                    if result_handle.result and "output" in result_handle.result:
                        preview = str(result_handle.result["output"])[:200]

                    statuses.append(AgentStatus(
                        agent_id=result_handle.agent_id,
                        agent_type=result_handle.agent_type,
                        status=result_handle.status,
                        result_preview=preview,
                        error=result_handle.error,
                        duration_ms=duration,
                    ))

                except Exception as e:
                    failed += 1
                    handle.status = "timeout" if "timeout" in str(e).lower() else "failed"
                    statuses.append(AgentStatus(
                        agent_id=handle.agent_id,
                        agent_type=handle.agent_type,
                        status=handle.status,
                        error=str(e),
                    ))
                    log.warning("[spawning] task=%s agent=%s failed: %s",
                                self.task_id, handle.agent_id, e)

        layer_duration = int((time.time() - layer_start) * 1000)
        self.budget.record_latency(layer_duration)

        # Determine if layer passed (all agents completed)
        all_passed = all(s.status == "completed" for s in statuses)

        layer_result = LayerResult(
            layer=layer,
            agents=statuses,
            all_passed=all_passed,
            duration_ms=layer_duration,
        )
        self._layer_results.append(layer_result)

        _audit_log(
            "layer_completed",
            self.task_id,
            {
                "layer": layer,
                "completed": completed,
                "failed": failed,
                "duration_ms": layer_duration,
                "all_passed": all_passed,
            },
        )
        log.info("[spawning] task=%s layer=%d completed (%d/%d success, %dms)",
                 self.task_id, layer, completed, len(handles), layer_duration)
        return layer_result

    # ── Aggregate ────────────────────────────────────────────────────────

    def aggregate_final(
        self,
        shared_ctx: Any,
        synthesizer_persona: str = "AYMAN",
    ) -> SpawnResult:
        """Aggregate all layer results into final synthesized answer."""
        total_duration = int((time.time() - self._start_time) * 1000)

        # Build synthesis prompt dari semua layer outputs
        context_dump = shared_ctx.snapshot() if shared_ctx else {}
        layer_outputs = []
        for lr in self._layer_results:
            for agent in lr.agents:
                if agent.result_preview:
                    layer_outputs.append(
                        f"[{agent.agent_type}] {agent.result_preview}"
                    )

        synthesis_input = "\n".join(layer_outputs)
        prompt = (
            "Kamu adalah Lead Synthesizer (AYMAN). Tugasmu menggabungkan "
            "hasil dari multiple sub-agents menjadi jawaban final yang "
            "koheren, komprehensif, dan well-structured.\n\n"
            f"Goal: {context_dump.get('goal', 'Unknown')}\n\n"
            f"Sub-agent outputs:\n{synthesis_input}\n\n"
            "Synthesize a final answer. Include citations where applicable."
        )

        # Synthesize via LLM
        synthesized = ""
        try:
            from ..persona_adapter import generate_with_persona
            synthesized = generate_with_persona(
                prompt,
                persona=synthesizer_persona,
                max_tokens=800,
                temperature=0.65,
            )
        except Exception as e:
            log.warning("[spawning] Synthesis failed: %s", e)
            synthesized = f"[Synthesis error: {e}]\n\nRaw outputs:\n{synthesis_input}"

        status = "completed"
        if any(not lr.all_passed for lr in self._layer_results):
            status = "partial"
        if self.budget.is_exhausted():
            status = "budget_exhausted"

        result = SpawnResult(
            task_id=self.task_id,
            status=status,
            layers=self._layer_results,
            synthesized_answer=synthesized,
            total_duration_ms=total_duration,
        )

        # Write final ke shared context
        if shared_ctx is not None:
            shared_ctx.write(
                key="final_synthesis",
                value={
                    "answer": synthesized,
                    "status": status,
                    "duration_ms": total_duration,
                },
                agent_id="synthesizer",
                agent_type="synthesis",
                layer=999,
            )
            shared_ctx.set_status(status)

        _audit_log(
            "session_completed",
            self.task_id,
            {
                "status": status,
                "total_duration_ms": total_duration,
                "layers": len(self._layer_results),
                "budget": self.budget.to_dict(),
            },
        )
        log.info("[spawning] task=%s final status=%s (%dms)",
                 self.task_id, status, total_duration)
        return result

    # ── Stats ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        """Current session stats."""
        return {
            "task_id": self.task_id,
            "budget": self.budget.to_dict(),
            "layers_completed": len(self._layer_results),
            "agents_tracked": len(self._handles),
            "elapsed_ms": int((time.time() - self._start_time) * 1000),
        }

    # ── Cleanup ──────────────────────────────────────────────────────────

    def kill_all(self) -> None:
        """Force kill all tracked agents (graceful shutdown)."""
        for handle in self._handles.values():
            if handle.status in ("running", "idle"):
                handle.status = "killed"
        _audit_log("session_killed", self.task_id, {"agents": len(self._handles)})
