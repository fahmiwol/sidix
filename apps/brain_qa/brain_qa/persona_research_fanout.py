"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

persona_research_fanout.py — Sprint 40 Phase 2 / Sprint 58B
(Multi-Agent Persona Research — Jurus 1000 Bayangan)

Implements jurus 1000 bayangan + per-persona research pattern (LOCK 2026-04-29
founder reminder). For complex autonomous_developer tasks, spawn 5 persona
researchers in parallel — each persona has specialized angle:

  UTZ   → creative direction, visual trends, aesthetic patterns
  ABOO  → technical research, engineering benchmarks, library updates
  OOMAR → strategy/business research, market analysis, competitor intel
  ALEY  → academic/methodical, paper search, theoretical foundation
  AYMAN → community/social, sentiment analysis, user feedback

Sprint 58B (2026-04-29):
  - Each persona gets a targeted research prompt (its own angle)
  - Parallel execution via ThreadPoolExecutor (non-blocking)
  - Timeout per-persona: 90s (Ollama VPS estimate)
  - Cognitive synthesis: LLM synthesizes all 5 findings into unified context
  - Sanad chain: per-persona confidence tracked
  - Graceful degradation: persona timeout = empty contribution (not crash)

Output: FanoutBundle → fed into code_diff_planner for richer planning context.

Reference:
- project_sidix_multi_agent_pattern.md
- research note 279 (Cara SIDIX action — multi-perspective)
- research note 281 (Sintesis multi-dimensi)
- autonomous_researcher.py (existing pattern to extend)
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

PERSONAS = ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")

PERSONA_ANGLES = {
    "UTZ":   "creative direction, visual trends, aesthetic patterns, brand inspiration",
    "ABOO":  "technical research, engineering benchmarks, library updates, performance",
    "OOMAR": "strategy/business, market analysis, competitor intel, framework tradeoffs",
    "ALEY":  "academic/methodical, paper search, theoretical foundation, citation chain",
    "AYMAN": "community/social, sentiment analysis, user feedback, narrative patterns",
}

# System prompts tuned per persona (Sprint 15 voice LOCK: see cot_system_prompts.py)
_PERSONA_SYSTEMS = {
    "UTZ": (
        "Kamu UTZ — persona kreatif-visual dari SIDIX. "
        "Lihat setiap problem dari angle kreativitas, estetika, brand, dan inspirasi visual. "
        "Output kamu: bullet list temuan konkret dari sudut pandang kreatif. "
        "Singkat, tajam, inspiring. Pakai bahasa kasual tapi insightful."
    ),
    "ABOO": (
        "Kamu ABOO — persona engineer-praktis dari SIDIX. "
        "Analisis dari sudut teknis: libraries, performance, best practices, trade-off implementasi. "
        "Output kamu: bullet list temuan konkret dari sudut engineering. "
        "Langsung ke point, technical depth, cite library/pattern spesifik bila tahu."
    ),
    "OOMAR": (
        "Kamu OOMAR — persona strategist-framework dari SIDIX. "
        "Analisis dari sudut bisnis: market context, framework keputusan, trade-off strategis. "
        "Output kamu: bullet list temuan konkret dari sudut strategi. "
        "Systemik, framework-first, long-term thinking."
    ),
    "ALEY": (
        "Kamu ALEY — persona researcher-metodikal dari SIDIX. "
        "Analisis dari sudut akademis: teori, metodologi, literatur yang relevan. "
        "Output kamu: bullet list temuan konkret dari sudut riset. "
        "Cite konsep atau metodologi spesifik. Jujur kalau tidak tahu."
    ),
    "AYMAN": (
        "Kamu AYMAN — persona hangat-empatik dari SIDIX. "
        "Analisis dari sudut manusia: UX, sentimen komunitas, adoption, narrative. "
        "Output kamu: bullet list temuan konkret dari sudut pengguna. "
        "Hangat, human-centric, consider diverse stakeholders."
    ),
}

# Per-persona research prompt template
_RESEARCH_PROMPT_TEMPLATE = """## Research Task
Task ID: {task_id}
Target: {target_path}
Goal: {goal}

## Your Angle: {angle}

Berikan 3-5 temuan konkret yang relevan dari perspektif kamu ({persona}).
Format: bullet list, setiap poin actionable atau insightful.
Focus pada apa yang bisa membantu implementasi goal di atas.
Jangan panjang — cukup bullet list tajam dan concrete."""

# Synthesis prompt — merges all persona findings into unified context
_SYNTHESIS_SYSTEM = (
    "Kamu SIDIX Cognitive Synthesis Engine. "
    "Tugasmu: merge insight dari 5 persona peneliti (UTZ/ABOO/OOMAR/ALEY/AYMAN) "
    "menjadi unified context untuk code planning. "
    "Jangan average — surface consensus DAN tensions. "
    "Output: paragraph ringkas (3-5 kalimat) yang capture cross-perspective wisdom. "
    "Bahasa Indonesia."
)

_SYNTHESIS_PROMPT_TEMPLATE = """## Goal
{goal}

## Target
{target_path}

## Findings per Persona:
{findings_block}

## Instruction
Synthesize semua perspektif di atas menjadi 1 paragraf unified context
untuk dipakai oleh code diff planner. Highlight consensus dan key tensions."""

# Timeouts
_PERSONA_TIMEOUT_S = 90   # per-persona LLM call timeout
_SYNTHESIS_TIMEOUT_S = 60  # synthesis call timeout


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class PersonaContribution:
    """One persona's research output for a task."""
    persona: str = ""
    angle: str = ""
    findings: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.5
    duration_ms: int = 0
    error: str = ""


@dataclass
class FanoutBundle:
    """Aggregated multi-persona research → input untuk diff_planner."""
    task_id: str = ""
    contributions: dict[str, PersonaContribution] = field(default_factory=dict)
    synthesis: str = ""              # cognitive synthesis text
    sanad_chain: list[dict] = field(default_factory=list)
    confidence: float = 0.5
    total_personas: int = 0
    successful_personas: int = 0
    duration_ms: int = 0


# ── LLM call helper ──────────────────────────────────────────────────────────

def _call_research_llm(system: str, user: str,
                       max_tokens: int = 300,
                       temperature: float = 0.5) -> tuple[str, str]:
    """Call LLM for research. Returns (text, mode). Ollama fallback chain."""
    # Try 1: LoRA PEFT
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(
            prompt=user, system=system,
            max_tokens=max_tokens, temperature=temperature,
        )
        if mode == "local_lora":
            return text, "local_lora"
    except Exception as e:
        log.debug("[fanout] generate_sidix error: %s", e)

    # Try 2: Ollama
    try:
        from .ollama_llm import ollama_generate, ollama_available
        if ollama_available():
            text, mode = ollama_generate(
                prompt=user, system=system,
                max_tokens=max_tokens, temperature=temperature,
            )
            if mode == "ollama":
                return text, "ollama"
    except Exception as e:
        log.warning("[fanout] ollama error: %s", e)

    return "", "stub"


def _parse_findings(text: str) -> list[str]:
    """Extract bullet-list items from LLM response."""
    if not text.strip():
        return []
    lines = text.strip().splitlines()
    findings: list[str] = []
    for line in lines:
        stripped = line.strip()
        # Accept lines starting with bullet markers or non-empty content
        if stripped.startswith(("-", "•", "*", "·")):
            cleaned = stripped.lstrip("-•*· ").strip()
            if cleaned:
                findings.append(cleaned)
        elif stripped and not stripped.startswith(("#", "=", "##")):
            # Non-header, non-empty line
            findings.append(stripped)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for f in findings:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique[:8]  # cap at 8 findings per persona


def _research_one_persona(
    persona: str,
    task_id: str,
    target_path: str,
    goal: str,
) -> PersonaContribution:
    """Research for one persona. Called in parallel thread."""
    t0 = time.time()
    angle = PERSONA_ANGLES.get(persona, "")
    system = _PERSONA_SYSTEMS.get(persona, "Kamu researcher SIDIX.")
    user = _RESEARCH_PROMPT_TEMPLATE.format(
        task_id=task_id,
        target_path=target_path,
        goal=goal,
        angle=angle,
        persona=persona,
    )

    try:
        text, mode = _call_research_llm(system, user)
        findings = _parse_findings(text)
        confidence = 0.7 if mode not in ("stub", "") else 0.1
        dur = int((time.time() - t0) * 1000)
        log.info("[fanout] %s done mode=%s findings=%d dur=%dms",
                 persona, mode, len(findings), dur)
        return PersonaContribution(
            persona=persona,
            angle=angle,
            findings=findings if findings else [f"[{mode}] No findings returned"],
            confidence=confidence,
            duration_ms=dur,
        )
    except Exception as e:
        dur = int((time.time() - t0) * 1000)
        log.warning("[fanout] %s error: %s", persona, e)
        return PersonaContribution(
            persona=persona,
            angle=angle,
            findings=[],
            confidence=0.0,
            duration_ms=dur,
            error=str(e),
        )


def _synthesize_contributions(
    contributions: dict[str, PersonaContribution],
    goal: str,
    target_path: str,
) -> str:
    """Cognitive synthesis: merge 5 persona findings → unified context string."""
    if not contributions:
        return "[fanout] No contributions to synthesize."

    # Build findings block
    blocks: list[str] = []
    for persona, contrib in contributions.items():
        if contrib.findings:
            bullets = "\n".join(f"  - {f}" for f in contrib.findings)
            blocks.append(f"### {persona} ({contrib.angle})\n{bullets}")
        else:
            err = f" (error: {contrib.error})" if contrib.error else " (no findings)"
            blocks.append(f"### {persona}{err}")

    findings_block = "\n\n".join(blocks)
    user = _SYNTHESIS_PROMPT_TEMPLATE.format(
        goal=goal,
        target_path=target_path,
        findings_block=findings_block,
    )

    text, mode = _call_research_llm(
        _SYNTHESIS_SYSTEM, user,
        max_tokens=400,
        temperature=0.3,
    )
    if text.strip():
        log.info("[fanout] synthesis done mode=%s len=%d", mode, len(text))
        return text.strip()

    # Fallback: naive concat
    log.warning("[fanout] synthesis LLM empty — fallback to concat")
    summary_parts = []
    for persona, contrib in contributions.items():
        if contrib.findings:
            summary_parts.append(
                f"{persona}: " + "; ".join(contrib.findings[:2])
            )
    return " | ".join(summary_parts) if summary_parts else "[no synthesis available]"


# ── Public API ───────────────────────────────────────────────────────────────

def gather(
    task_id: str,
    target_path: str,
    goal: str,
    personas: tuple = PERSONAS,
    max_workers: Optional[int] = None,
) -> FanoutBundle:
    """Spawn N persona researchers in parallel → aggregate findings.

    Sprint 58B: full implementation. Parallel ThreadPoolExecutor, each
    persona calls Ollama (or generate_sidix if LoRA available), then
    cognitive synthesis merges all findings.

    Args:
        task_id: dev task identifier
        target_path: scaffold path being worked on
        goal: production-ready criteria
        personas: subset of PERSONAS to spawn (default all 5)
        max_workers: ThreadPool workers (default = len(personas))

    Returns:
        FanoutBundle with per-persona contributions + synthesis + confidence.
    """
    t0 = time.time()
    valid_personas = [p for p in personas if p in PERSONA_ANGLES]
    if not valid_personas:
        log.warning("[fanout] no valid personas — returning empty bundle")
        return FanoutBundle(task_id=task_id)

    workers = max_workers or len(valid_personas)
    log.info("[fanout] task=%s personas=%s workers=%d", task_id, valid_personas, workers)

    contributions: dict[str, PersonaContribution] = {}

    with ThreadPoolExecutor(max_workers=workers) as exe:
        future_map = {
            exe.submit(_research_one_persona, p, task_id, target_path, goal): p
            for p in valid_personas
        }
        for fut in as_completed(future_map, timeout=_PERSONA_TIMEOUT_S + 5):
            persona = future_map[fut]
            try:
                contributions[persona] = fut.result(timeout=1)
            except FutureTimeout:
                log.warning("[fanout] %s timed out", persona)
                contributions[persona] = PersonaContribution(
                    persona=persona,
                    angle=PERSONA_ANGLES.get(persona, ""),
                    findings=[],
                    confidence=0.0,
                    error="timeout",
                )
            except Exception as e:
                log.error("[fanout] %s exception: %s", persona, e)
                contributions[persona] = PersonaContribution(
                    persona=persona,
                    angle=PERSONA_ANGLES.get(persona, ""),
                    findings=[],
                    confidence=0.0,
                    error=str(e),
                )

    # Cognitive synthesis
    synthesis = _synthesize_contributions(contributions, goal, target_path)

    # Sanad chain: track source per persona
    sanad_chain = [
        {
            "persona": p,
            "angle": c.angle,
            "confidence": c.confidence,
            "findings_count": len(c.findings),
            "duration_ms": c.duration_ms,
            "error": c.error,
        }
        for p, c in contributions.items()
    ]

    # Bundle confidence = average of successful personas
    successful = [c for c in contributions.values() if not c.error and c.findings]
    avg_confidence = (
        sum(c.confidence for c in successful) / len(successful)
        if successful else 0.0
    )

    bundle = FanoutBundle(
        task_id=task_id,
        contributions=contributions,
        synthesis=synthesis,
        sanad_chain=sanad_chain,
        confidence=round(avg_confidence, 3),
        total_personas=len(valid_personas),
        successful_personas=len(successful),
        duration_ms=int((time.time() - t0) * 1000),
    )

    log.info("[fanout] done task=%s success=%d/%d confidence=%.2f dur=%dms",
             task_id, bundle.successful_personas, bundle.total_personas,
             bundle.confidence, bundle.duration_ms)
    return bundle


def synthesize(bundle: FanoutBundle) -> str:
    """Re-synthesize an existing FanoutBundle (for re-scoring or refresh).

    Wraps _synthesize_contributions for external callers.
    """
    if not bundle.contributions:
        return ""
    return _synthesize_contributions(
        bundle.contributions,
        goal="[re-synthesis]",
        target_path="[re-synthesis]",
    )


__all__ = [
    "PERSONAS", "PERSONA_ANGLES",
    "PersonaContribution", "FanoutBundle",
    "gather", "synthesize",
]
