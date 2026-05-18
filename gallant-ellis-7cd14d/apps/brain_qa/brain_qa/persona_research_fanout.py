"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

persona_research_fanout.py — Sprint 40 Phase 1 (Multi-Agent Persona Research)

Implements jurus 1000 bayangan + per-persona research pattern (LOCK 2026-04-29
founder reminder). For complex autonomous_developer tasks, spawn 5 persona
researchers in parallel — each persona has specialized angle:

  UTZ   → creative direction, visual trends, aesthetic patterns
  ABOO  → technical research, engineering benchmarks, library updates
  OOMAR → strategy/business research, market analysis, competitor intel
  ALEY  → academic/methodical, paper search, theoretical foundation
  AYMAN → community/social, sentiment analysis, user feedback

Output dari masing-masing persona researcher → curated → merged via cognitive
synthesis → unified context for code_diff_planner.

Phase 1 scope: scaffold dengan dataclass + dispatcher signatures.
Phase 2: wire to autonomous_researcher.py per persona.

Reference:
- project_sidix_multi_agent_pattern.md
- research note 279 (Cara SIDIX action — multi-perspective)
- research note 281 (Sintesis multi-dimensi)
- autonomous_researcher.py (existing pattern to extend)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

PERSONAS = ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")

PERSONA_ANGLES = {
    "UTZ":   "creative direction, visual trends, aesthetic patterns, brand inspiration",
    "ABOO":  "technical research, engineering benchmarks, library updates, performance",
    "OOMAR": "strategy/business, market analysis, competitor intel, framework tradeoffs",
    "ALEY":  "academic/methodical, paper search, theoretical foundation, citation chain",
    "AYMAN": "community/social, sentiment analysis, user feedback, narrative patterns",
}


@dataclass
class PersonaContribution:
    """One persona's research output for a task."""
    persona: str = ""
    angle: str = ""
    findings: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class FanoutBundle:
    """Aggregated multi-persona research → input untuk diff_planner."""
    task_id: str = ""
    contributions: dict[str, PersonaContribution] = field(default_factory=dict)
    synthesis: str = ""              # cognitive synthesis text
    sanad_chain: list[dict] = field(default_factory=list)
    confidence: float = 0.5


def gather(task_id: str, target_path: str, goal: str,
           personas: tuple = PERSONAS) -> FanoutBundle:
    """Spawn N persona researchers in parallel → aggregate findings.

    Phase 1: scaffold returns empty contributions.
    Phase 2: wires to autonomous_researcher per persona, parallel via
             threading.ThreadPoolExecutor or asyncio.gather.

    Args:
        task_id: dev task identifier
        target_path: scaffold path being worked on
        goal: production-ready criteria
        personas: subset of PERSONAS to spawn (default all 5)
    """
    log.info("[persona_fanout] task=%s personas=%s", task_id, personas)

    bundle = FanoutBundle(task_id=task_id, confidence=0.0)

    for p in personas:
        if p not in PERSONA_ANGLES:
            log.warning("[persona_fanout] unknown persona %s", p)
            continue
        bundle.contributions[p] = PersonaContribution(
            persona=p,
            angle=PERSONA_ANGLES[p],
            findings=[f"[STUB Phase 1] {p} research for {target_path}"],
            confidence=0.0,
        )

    bundle.synthesis = (
        f"[STUB Phase 1] Cognitive synthesis pending. "
        f"Phase 2 will merge {len(bundle.contributions)} persona perspectives."
    )

    return bundle


def synthesize(bundle: FanoutBundle) -> str:
    """Cross-perspective synthesis layer.

    Phase 1 stub. Phase 2 implements:
    - Find consensus across personas (sanad multi-source convergence)
    - Surface tensions/disagreements (don't average, hold productively)
    - Output structured synthesis dengan citation per persona contribution
    """
    if not bundle.contributions:
        return ""
    angles = [c.angle for c in bundle.contributions.values()]
    return f"[STUB] Synthesis across {len(angles)} angles."


__all__ = ["PERSONAS", "PERSONA_ANGLES", "PersonaContribution",
           "FanoutBundle", "gather", "synthesize"]
