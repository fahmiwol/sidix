"""
problem_decomposer.py — Polya-style Problem Solving Engine
============================================================

User question 2026-04-26:
> "Terakhir gimana caranya sidix bantu mecahin masalah?"

SIDIX problem-solving framework, inspired by George Polya's "How to Solve It"
(1945) — masih jadi pedoman matematikawan + engineer 80 tahun setelah ditulis.

4 Tahap Polya:
  1. **UNDERSTAND** — apa masalahnya? data apa yang ada? apa yang dicari?
  2. **PLAN** — strategi apa yang relevan? ada kasus serupa? bisa decompose?
  3. **EXECUTE** — jalankan plan, monitor, adjust
  4. **REVIEW** — apakah solusi benar? bisa di-generalize? lessons learned?

SIDIX implementation:
- Phase 1 → search_corpus + pattern_extractor (cari prinsip umum yang related)
- Phase 2 → orchestration_plan (existing) + Burst mode untuk creative angle
- Phase 3 → ReAct loop dengan tools (existing)
- Phase 4 → confidence eval + maybe pattern_extractor save (kalau ada
  generalization baru) + skill distill (kalau success novel)

Output: structured ProblemSolution dengan 4 tahap visible — bukan jawaban
opaque, tapi reasoning chain yang user bisa audit.

Filosofi: "AI yang menjawab cepat" vs "AI yang menyelesaikan masalah".
SIDIX target #2 — slower per-step tapi structurally sound.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class ProblemSolution:
    """4-phase Polya-style decomposition."""
    id: str
    ts: str
    problem_statement: str            # original user input

    # Phase 1: Understand
    given_data: list[str] = field(default_factory=list)
    unknown_target: str = ""
    constraints: list[str] = field(default_factory=list)
    related_patterns: list[dict] = field(default_factory=list)  # from pattern_extractor

    # Phase 2: Plan
    strategy: str = ""                # high-level approach
    sub_goals: list[str] = field(default_factory=list)
    tools_needed: list[str] = field(default_factory=list)
    similar_solved_cases: list[str] = field(default_factory=list)

    # Phase 3: Execute (filled by ReAct loop external)
    execution_steps: list[dict] = field(default_factory=list)
    final_answer: str = ""

    # Phase 4: Review
    correctness_check: str = ""
    confidence_estimate: float = 0.5
    generalizable_insight: str = ""    # bisa jadi pattern baru?
    lessons_learned: list[str] = field(default_factory=list)


# ── Phase 1: UNDERSTAND ────────────────────────────────────────────────────────

def understand_problem(problem: str) -> dict:
    """
    Decompose problem statement → given/unknown/constraints.
    LLM-based, prompted dengan Polya framework.
    """
    try:
        try:
            from .ollama_llm import generate as llm_gen
        except Exception:
            from .local_llm import generate_sidix as llm_gen
    except Exception:
        return {"given_data": [], "unknown_target": "", "constraints": []}

    prompt = f"""Problem: "{problem}"

Decompose dengan framework Polya. Output ONLY JSON:
{{
  "given_data": ["data atau fakta yang sudah ada di problem"],
  "unknown_target": "apa yang dicari / dipecahkan",
  "constraints": ["batasan / requirement"]
}}

Jangan filler. Pendek tapi spesifik. Output JSON:"""

    try:
        out = llm_gen(prompt, max_tokens=300, temperature=0.3)
        if isinstance(out, dict):
            response = out.get("text") or out.get("response") or ""
        else:
            response = out or ""
        response = re.sub(r"^```(?:json)?\s*", "", response.strip())
        response = re.sub(r"\s*```$", "", response)
        return json.loads(response)
    except Exception as e:
        log.debug("[decompose] understand fail: %s", e)
        return {"given_data": [], "unknown_target": problem[:200], "constraints": []}


def retrieve_related_patterns(problem: str, top_k: int = 3) -> list[dict]:
    """Pull patterns from pattern_extractor library yang relevan."""
    try:
        from .pattern_extractor import search_patterns
        return search_patterns(problem, top_k=top_k, min_confidence=0.3)
    except Exception:
        return []


# ── Phase 2: PLAN ──────────────────────────────────────────────────────────────

def plan_strategy(
    problem: str,
    understanding: dict,
    patterns: list[dict],
) -> dict:
    """
    Generate strategi + sub-goals + tools needed.
    Pakai existing orchestration_plan kalau available.
    """
    # Try existing orchestration_plan first (lebih sophisticated)
    try:
        from .orchestration import build_plan  # type: ignore
        plan = build_plan(problem)
        if plan:
            return {
                "strategy": plan.get("strategy", ""),
                "sub_goals": plan.get("sub_goals", []),
                "tools_needed": plan.get("tools", []),
                "similar_solved_cases": [],
            }
    except Exception:
        pass

    # Fallback: LLM gen
    try:
        try:
            from .ollama_llm import generate as llm_gen
        except Exception:
            from .local_llm import generate_sidix as llm_gen
    except Exception:
        return {"strategy": "", "sub_goals": [], "tools_needed": []}

    pat_summary = ""
    if patterns:
        pat_summary = "\n\nRelated patterns (induktif yang mungkin applicable):\n" + \
            "\n".join(f"- {p.get('extracted_principle', '')}" for p in patterns[:3])

    prompt = f"""Problem: "{problem}"
Diketahui: {understanding.get('given_data', [])}
Dicari: {understanding.get('unknown_target', '')}
Constraints: {understanding.get('constraints', [])}{pat_summary}

Strategi pemecahan masalah. Output ONLY JSON:
{{
  "strategy": "1-2 kalimat high-level approach",
  "sub_goals": ["langkah konkret 1", "langkah 2", "langkah 3"],
  "tools_needed": ["search_corpus", "web_search", "code_sandbox", ...],
  "similar_solved_cases": ["referensi kasus serupa kalau ada"]
}}

Output JSON:"""

    try:
        out = llm_gen(prompt, max_tokens=500, temperature=0.4)
        if isinstance(out, dict):
            response = out.get("text") or out.get("response") or ""
        else:
            response = out or ""
        response = re.sub(r"^```(?:json)?\s*", "", response.strip())
        response = re.sub(r"\s*```$", "", response)
        return json.loads(response)
    except Exception as e:
        log.debug("[decompose] plan fail: %s", e)
        return {"strategy": "", "sub_goals": [], "tools_needed": []}


# ── Phase 4: REVIEW ────────────────────────────────────────────────────────────

def review_solution(
    problem: str,
    solution: ProblemSolution,
) -> dict:
    """
    Critical review: apakah solusi benar? bisa generalize? lessons?
    """
    try:
        try:
            from .ollama_llm import generate as llm_gen
        except Exception:
            from .local_llm import generate_sidix as llm_gen
    except Exception:
        return {"correctness_check": "", "confidence": 0.5,
                "generalizable_insight": "", "lessons": []}

    prompt = f"""Problem original: "{problem}"
Solusi: "{solution.final_answer[:600]}"

Review kritis. Output ONLY JSON:
{{
  "correctness_check": "1-2 kalimat: solusi benar? ada blunder?",
  "confidence": 0.0-1.0,
  "generalizable_insight": "kalau ada prinsip umum yang bisa dipakai lagi, sebutkan. Kalau tidak ada, kosongkan.",
  "lessons": ["lesson learned 1", "lesson 2"]
}}

Output JSON:"""

    try:
        out = llm_gen(prompt, max_tokens=400, temperature=0.4)
        if isinstance(out, dict):
            response = out.get("text") or out.get("response") or ""
        else:
            response = out or ""
        response = re.sub(r"^```(?:json)?\s*", "", response.strip())
        response = re.sub(r"\s*```$", "", response)
        data = json.loads(response)
        return {
            "correctness_check": (data.get("correctness_check") or "")[:300],
            "confidence": float(data.get("confidence", 0.5)),
            "generalizable_insight": (data.get("generalizable_insight") or "")[:300],
            "lessons": data.get("lessons") or [],
        }
    except Exception as e:
        log.debug("[decompose] review fail: %s", e)
        return {"correctness_check": "", "confidence": 0.5,
                "generalizable_insight": "", "lessons": []}


# ── End-to-end orchestration ───────────────────────────────────────────────────

def decompose_problem(problem: str) -> ProblemSolution:
    """
    Full Polya 4-phase tanpa eksekusi (Phase 3) — Phase 3 dilakukan oleh
    ReAct loop external (caller).

    Output ProblemSolution yang Phase 1+2+4 sudah filled.
    Caller fill Phase 3 (execution_steps + final_answer) sebelum panggil
    review_solution(...) untuk Phase 4.
    """
    sol = ProblemSolution(
        id=f"prob_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
        problem_statement=problem[:600],
    )

    # Phase 1
    understanding = understand_problem(problem)
    sol.given_data = [s for s in understanding.get("given_data", []) if s][:8]
    sol.unknown_target = (understanding.get("unknown_target") or "")[:200]
    sol.constraints = [s for s in understanding.get("constraints", []) if s][:6]
    sol.related_patterns = retrieve_related_patterns(problem)

    # Phase 2
    plan = plan_strategy(problem, understanding, sol.related_patterns)
    sol.strategy = (plan.get("strategy") or "")[:300]
    sol.sub_goals = [s for s in plan.get("sub_goals", []) if s][:8]
    sol.tools_needed = [s for s in plan.get("tools_needed", []) if s][:8]
    sol.similar_solved_cases = [s for s in plan.get("similar_solved_cases", []) if s][:5]

    return sol


def review_and_extract_pattern(
    sol: ProblemSolution,
    *,
    auto_save_pattern: bool = True,
) -> ProblemSolution:
    """
    Phase 4: review + maybe extract pattern (kalau generalizable).
    Disebut setelah caller fill final_answer.
    """
    review = review_solution(sol.problem_statement, sol)
    sol.correctness_check = review.get("correctness_check", "")
    sol.confidence_estimate = review.get("confidence", 0.5)
    sol.generalizable_insight = review.get("generalizable_insight", "")
    sol.lessons_learned = review.get("lessons", [])

    # Auto-save pattern kalau ada generalizable insight
    if auto_save_pattern and sol.generalizable_insight and len(sol.generalizable_insight) > 20:
        try:
            from .pattern_extractor import extract_pattern_from_text, save_pattern
            pat = extract_pattern_from_text(
                sol.generalizable_insight,
                source_example=sol.problem_statement,
                derived_from=f"problem:{sol.id}",
            )
            if pat:
                save_pattern(pat)
                log.info("[decompose] saved derived pattern %s from problem %s",
                         pat.id, sol.id)
        except Exception:
            pass

    return sol


__all__ = [
    "ProblemSolution",
    "understand_problem", "plan_strategy", "review_solution",
    "decompose_problem", "review_and_extract_pattern",
]
