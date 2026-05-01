"""
supervisor.py — Sprint K: Spawn Supervisor untuk Multi-Agent Orchestration

Konsep:
  Supervisor Agent menerima goal → decompose into sub-tasks → schedule ke layers
  → execute via LifecycleManager.

  Mengadaptasi:
  - Mixture of Agents pattern: layered execution (layer N → layer N+1)
  - parallel_planner.py: dependency-aware scheduling
  - hands_orchestrator.py: goal split → sub-task → dispatch

  Execution strategy:
    - "auto" → Supervisor decides layers based on complexity
    - "research_first" → Layer 0 only, then synthesis
    - "parallel" → Flat parallel (council style)
    - "debate" → Layer 0 generates, Layer 1 validates iteratively

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from .shared_context import SharedContext
from .sub_agent_factory import SubAgentFactory
from .lifecycle_manager import LifecycleManager, ChakraBudget, SpawnResult

log = logging.getLogger("sidix.spawning.supervisor")


# ── Data Structures ──────────────────────────────────────────────────────

@dataclass
class SubTask:
    """Single sub-task dalam spawn plan."""
    task_id: str
    description: str
    agent_type: str
    layer: int
    depends_on: list[str] = None

    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


@dataclass
class SpawnPlan:
    """Complete execution plan."""
    goal: str
    strategy: str
    layers: dict[int, list[SubTask]]
    estimated_agents: int = 0
    complexity: str = "medium"


# ── SpawnSupervisor ──────────────────────────────────────────────────────

class SpawnSupervisor:
    """Supervisor Agent: task decomposition → spawn plan → execution.

    Usage:
        supervisor = SpawnSupervisor()
        result = supervisor.run(goal="...", strategy="auto", max_agents=5)
    """

    def __init__(self, default_timeout: float = 120.0):
        self.default_timeout = default_timeout
        self._factory = SubAgentFactory()

    # ── Task Decomposition ───────────────────────────────────────────────

    def decompose_task(self, goal: str, strategy: str = "auto") -> SpawnPlan:
        """Decompose goal into sub-tasks based on strategy."""
        complexity = self._assess_complexity(goal)

        if strategy == "auto":
            strategy = self._select_strategy(complexity)

        if strategy == "parallel":
            return self._plan_parallel(goal, complexity)
        elif strategy == "research_first":
            return self._plan_research_first(goal, complexity)
        elif strategy == "debate":
            return self._plan_debate(goal, complexity)
        else:  # default: layered
            return self._plan_layered(goal, complexity)

    def _assess_complexity(self, goal: str) -> str:
        """Heuristic complexity assessment."""
        goal_lower = goal.lower()
        score = 0

        # Length-based
        if len(goal) > 200:
            score += 2
        elif len(goal) > 100:
            score += 1

        # Keyword-based (cumulative, not break)
        complex_keywords = [
            "analisis", "analysis", "bandingkan", "compare",
            "evaluasi", "evaluate", "research", "riset",
            "buatlah", "create", "generate", "tulis",
            "kode", "code", "program", "aplikasi",
            "strategi", "strategy", "rencana", "plan",
        ]
        for kw in complex_keywords:
            if kw in goal_lower:
                score += 1

        # Multi-part indicators
        if any(c in goal for c in ["dan", "serta", "plus", "&", ",", ";"]):
            score += 1

        if score >= 4:
            return "complex"
        elif score >= 2:
            return "medium"
        return "simple"

    def _select_strategy(self, complexity: str) -> str:
        """Select execution strategy based on complexity."""
        return {
            "simple": "research_first",
            "medium": "layered",
            "complex": "layered",
        }.get(complexity, "layered")

    def _plan_layered(self, goal: str, complexity: str) -> SpawnPlan:
        """Full layered plan: Research → Generation → Validation → Synthesis."""
        layers = {}
        task_counter = 0

        # Layer 0: Research (1–2 agents)
        research_tasks = [
            SubTask(
                task_id=f"t{task_counter}",
                description=f"Gather evidence and sources for: {goal}",
                agent_type="research",
                layer=0,
            )
        ]
        if complexity == "complex":
            task_counter += 1
            research_tasks.append(SubTask(
                task_id=f"t{task_counter}",
                description=f"Deep-dive analysis and counter-arguments for: {goal}",
                agent_type="research",
                layer=0,
                depends_on=["t0"],
            ))
        layers[0] = research_tasks

        # Layer 1: Generation (1 agent)
        task_counter += 1
        layers[1] = [SubTask(
            task_id=f"t{task_counter}",
            description=f"Produce content/answer based on research for: {goal}",
            agent_type="generation",
            layer=1,
            depends_on=[t.task_id for t in research_tasks],
        )]

        # Layer 2: Validation (1 agent)
        task_counter += 1
        layers[2] = [SubTask(
            task_id=f"t{task_counter}",
            description=f"Verify accuracy, completeness, and quality of output for: {goal}",
            agent_type="validation",
            layer=2,
            depends_on=[layers[1][0].task_id],
        )]

        return SpawnPlan(
            goal=goal,
            strategy="layered",
            layers=layers,
            estimated_agents=sum(len(tasks) for tasks in layers.values()),
            complexity=complexity,
        )

    def _plan_research_first(self, goal: str, complexity: str) -> SpawnPlan:
        """Research-only then synthesis."""
        layers = {
            0: [SubTask(
                task_id="t0",
                description=f"Research and synthesize findings for: {goal}",
                agent_type="research",
                layer=0,
            )],
        }
        return SpawnPlan(
            goal=goal,
            strategy="research_first",
            layers=layers,
            estimated_agents=1,
            complexity=complexity,
        )

    def _plan_parallel(self, goal: str, complexity: str) -> SpawnPlan:
        """Flat parallel: all agents answer same goal, then synthesize."""
        # Council-style: 3 agents dengan angle berbeda
        layers = {
            0: [
                SubTask(
                    task_id="t0",
                    description=f"Technical/engineering perspective: {goal}",
                    agent_type="research",
                    layer=0,
                ),
                SubTask(
                    task_id="t1",
                    description=f"Strategic/business perspective: {goal}",
                    agent_type="orchestration",
                    layer=0,
                ),
                SubTask(
                    task_id="t2",
                    description=f"Creative/innovative perspective: {goal}",
                    agent_type="generation",
                    layer=0,
                ),
            ],
        }
        return SpawnPlan(
            goal=goal,
            strategy="parallel",
            layers=layers,
            estimated_agents=3,
            complexity=complexity,
        )

    def _plan_debate(self, goal: str, complexity: str) -> SpawnPlan:
        """Generate → Validate → Iterate (max 2 rounds)."""
        layers = {
            0: [SubTask(
                task_id="t0",
                description=f"Initial draft/proposal for: {goal}",
                agent_type="generation",
                layer=0,
            )],
            1: [SubTask(
                task_id="t1",
                description=f"Critique and identify weaknesses in draft for: {goal}",
                agent_type="validation",
                layer=1,
                depends_on=["t0"],
            )],
            2: [SubTask(
                task_id="t2",
                description=f"Revise draft based on critique for: {goal}",
                agent_type="generation",
                layer=2,
                depends_on=["t1"],
            )],
        }
        return SpawnPlan(
            goal=goal,
            strategy="debate",
            layers=layers,
            estimated_agents=3,
            complexity=complexity,
        )

    # ── Execution ────────────────────────────────────────────────────────

    def run(
        self,
        goal: str,
        strategy: str = "auto",
        max_agents: int = 5,
        timeout: Optional[float] = None,
        allow_restricted: bool = False,
    ) -> SpawnResult:
        """Full execution: decompose → spawn → execute → aggregate."""
        task_id = f"spawn_{uuid.uuid4().hex[:12]}"
        timeout = timeout or self.default_timeout

        # Decompose
        plan = self.decompose_task(goal, strategy)
        log.info("[spawning] task=%s strategy=%s agents=%d",
                 task_id, plan.strategy, plan.estimated_agents)

        # Enforce max agents
        if plan.estimated_agents > max_agents:
            # Trim layers
            self._trim_plan(plan, max_agents)

        # Require allow_restricted untuk >5 agents
        if plan.estimated_agents > 5 and not allow_restricted:
            raise PermissionError(
                f"Spawn requires {plan.estimated_agents} agents. "
                f"Set allow_restricted=true for >5 agents."
            )

        # Initialize context and lifecycle
        shared_ctx = SharedContext(task_id=task_id, goal=goal)
        budget = ChakraBudget(max_agents=max_agents, max_latency_ms=int(timeout * 1000))
        lifecycle = LifecycleManager(task_id=task_id, budget=budget, layer_timeout=timeout)

        # Execute per layer
        for layer_num in sorted(plan.layers.keys()):
            tasks = plan.layers[layer_num]
            if not tasks:
                continue

            # Spawn layer
            task_descriptions = [t.description for t in tasks]
            agent_type = tasks[0].agent_type  # all same type per layer

            handles = lifecycle.spawn_layer(
                layer=layer_num,
                agent_type=agent_type,
                tasks=task_descriptions,
                factory=self._factory,
                shared_ctx=shared_ctx,
            )

            # Execute layer
            layer_result = lifecycle.execute_layer(
                handles=handles,
                factory=self._factory,
                shared_ctx=shared_ctx,
                layer=layer_num,
            )

            # If layer failed, stop (unless it's research layer)
            if not layer_result.all_passed and layer_num > 0:
                log.warning("[spawning] task=%s layer=%d failed, stopping",
                            task_id, layer_num)
                break

            # Optional: Memory agent stores intermediate results
            if layer_num < max(plan.layers.keys()):
                self._maybe_persist_memory(shared_ctx, task_id, layer_num)

        # Final aggregation
        result = lifecycle.aggregate_final(shared_ctx)
        shared_ctx.persist()

        return result

    def _trim_plan(self, plan: SpawnPlan, max_agents: int) -> None:
        """Trim plan to fit within max_agents budget."""
        total = 0
        for layer_num in sorted(plan.layers.keys()):
            tasks = plan.layers[layer_num]
            if total + len(tasks) > max_agents:
                # Trim this layer
                allowed = max_agents - total
                plan.layers[layer_num] = tasks[:allowed]
            total += len(plan.layers[layer_num])
        plan.estimated_agents = total

    def _maybe_persist_memory(self, shared_ctx: Any, task_id: str, layer: int) -> None:
        """Optionally spawn memory agent to persist intermediate results."""
        # Simplified: just persist shared context ke disk
        # Full memory agent spawn bisa dilakukan di future iteration
        shared_ctx.persist()

    # ── Stats ────────────────────────────────────────────────────────────

    @staticmethod
    def get_available_strategies() -> list[dict[str, str]]:
        """List available execution strategies."""
        return [
            {"name": "auto", "description": "Supervisor selects strategy based on complexity"},
            {"name": "layered", "description": "Research → Generation → Validation → Synthesis"},
            {"name": "research_first", "description": "Research only, then synthesize"},
            {"name": "parallel", "description": "Council-style flat parallel with synthesis"},
            {"name": "debate", "description": "Generate → Critique → Revise (iterative)"},
        ]
