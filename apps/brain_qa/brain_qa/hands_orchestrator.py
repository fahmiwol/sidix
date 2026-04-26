"""
hands_orchestrator.py — 1000 Hands Parallel Multi-Task (Q1 2027 Foundation)
==============================================================================

Per SIDIX_DEFINITION_20260426 Daily Capability #10:
> "Multitasking AI agent... Bergerak seperti memiliki 1000 tangan, membuat
>  design sambil mengerjakan script coding, sambil membaca riset, sambil
>  memposting dan lainnya."

Plus DIRECTION_LOCK Q1 2027 P2 moonshot:
> "1000 hands parallel orchestrator"

Vol 17 = **FOUNDATION STUB** untuk Q1 2027 full implementation. Hari ini
implement minimal:
- Plan splitter (1 user goal → N sub-task per persona)
- Sub-task spec + dispatcher (queue, no actual parallel exec yet)
- Synthesizer placeholder (combine outputs)

Q1 2027 full implementation:
- Real parallel ReAct loops via Celery + Redis worker pool
- Per-persona dedicated LoRA (multiagent finetuning, note 221)
- Live progress streaming SSE
- Cross-task dependency resolver

Filosofi: AI Agency in a Box (note 229 Q4 2027 vision). User chat:
"launch brand kopi" → SIDIX spawn 4 sub-agent paralel → 30 menit kemudian
deliver landing + social calendar + TVC + KOL outreach.

Modul ini = blueprint + stub. Real concurrency Q1 2027.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class SubTask:
    """1 sub-task untuk dispatch ke 1 persona."""
    id: str
    parent_goal_id: str
    persona: str             # UTZ | ABOO | OOMAR | ALEY | AYMAN
    sub_goal: str
    deliverable: str         # apa yang diharapkan keluar
    estimated_minutes: int = 5
    priority: int = 1        # 1-5, 5=highest
    depends_on: list[str] = field(default_factory=list)  # task IDs yang harus selesai dulu
    status: str = "pending"  # pending | running | completed | failed | skipped
    output: str = ""
    error: str = ""
    duration_ms: int = 0


@dataclass
class CompoundGoal:
    """User goal yang di-split jadi sub-tasks."""
    id: str
    ts: str
    user_goal: str
    sub_tasks: list[SubTask] = field(default_factory=list)
    final_synthesis: str = ""
    overall_status: str = "planning"  # planning | dispatching | running | synthesizing | completed | failed
    total_duration_ms: int = 0
    user_id: str = ""


# ── Persona-task affinity (which persona fits which task type) ───────────────

_PERSONA_AFFINITY = {
    "UTZ": ["design", "visual", "creative", "story", "metaphor", "brand", "ui", "ux",
            "color", "logo", "illustration", "moodboard", "naming", "tagline"],
    "ABOO": ["code", "implement", "deploy", "debug", "api", "architecture", "test",
             "build", "infrastructure", "devops", "database", "performance"],
    "OOMAR": ["business", "strategy", "market", "competitor", "pricing", "revenue",
              "roi", "launch", "growth", "decision", "monetize", "funding"],
    "ALEY": ["research", "paper", "study", "analyze", "compare", "evidence",
             "literature", "citation", "theory", "validate"],
    "AYMAN": ["summarize", "explain", "communicate", "outreach", "draft", "post",
              "schedule", "social", "general", "casual"],
}


# ── Path ───────────────────────────────────────────────────────────────────────

def _goals_log() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "compound_goals.jsonl"


# ── Plan splitter (user goal → N sub-tasks) ──────────────────────────────────

def _call_llm(prompt: str, *, max_tokens: int = 800, temperature: float = 0.5) -> str:
    """Unified LLM call — sama pattern dengan modul cognitive lain."""
    try:
        from .ollama_llm import ollama_generate
        text, mode = ollama_generate(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text and not mode.startswith("mock_error"):
            return text
    except Exception as e:
        log.debug("[hands] ollama fail: %s", e)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text:
            return text
    except Exception as e:
        log.debug("[hands] generate_sidix fail: %s", e)
    return ""


def _heuristic_split(user_goal: str) -> list[SubTask]:
    """
    Fallback splitter: keyword-based. Kalau goal mention keyword X, assign
    sub-task ke persona dengan affinity X.
    """
    goal_lower = user_goal.lower()
    parent_id = f"goal_{uuid.uuid4().hex[:8]}"
    sub_tasks = []

    persona_assigned = set()
    for persona, keywords in _PERSONA_AFFINITY.items():
        match_count = sum(1 for kw in keywords if kw in goal_lower)
        if match_count > 0:
            persona_assigned.add(persona)
            sub_tasks.append(SubTask(
                id=f"sub_{uuid.uuid4().hex[:8]}",
                parent_goal_id=parent_id,
                persona=persona,
                sub_goal=f"({persona} angle) {user_goal}",
                deliverable=f"Output dari sudut {persona}",
                estimated_minutes=5 + match_count * 2,
                priority=2 + min(match_count, 3),
            ))

    # Default fallback: at minimum AYMAN summarize
    if not sub_tasks:
        sub_tasks.append(SubTask(
            id=f"sub_{uuid.uuid4().hex[:8]}",
            parent_goal_id=parent_id,
            persona="AYMAN",
            sub_goal=user_goal,
            deliverable="Jawaban umum",
            estimated_minutes=3,
            priority=2,
        ))

    return sub_tasks


def split_goal_into_subtasks(
    user_goal: str,
    *,
    use_llm: bool = True,
) -> CompoundGoal:
    """
    Split user goal jadi sub-tasks per persona. LLM-based (canonical) atau
    heuristic fallback.
    """
    goal = CompoundGoal(
        id=f"goal_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
        user_goal=user_goal[:500],
    )

    if not use_llm:
        goal.sub_tasks = _heuristic_split(user_goal)
        goal.overall_status = "planning"
        return goal

    # LLM-based split
    prompt = f"""User goal:
"{user_goal}"

Split goal ini jadi 2-4 sub-tasks paralel, masing-masing assigned ke 1 persona.
Persona available:
- UTZ (creative/visual): brainstorm, naming, design, metafora
- ABOO (engineer): code, debug, api, architecture
- OOMAR (strategist): business, market, ROI, decision
- ALEY (academic): research, paper, theory, evidence
- AYMAN (general): summarize, draft, schedule, casual

Output ONLY JSON:
{{
  "sub_tasks": [
    {{
      "persona": "UTZ|ABOO|OOMAR|ALEY|AYMAN",
      "sub_goal": "spesifik sub-goal untuk persona ini",
      "deliverable": "apa output yang dihasilkan",
      "estimated_minutes": 5,
      "priority": 3
    }}
  ]
}}

Jangan generic. Tiap sub-task spesifik untuk persona-nya. Output JSON:"""

    response = _call_llm(prompt, max_tokens=800, temperature=0.4)
    if not response:
        # Fallback heuristic
        goal.sub_tasks = _heuristic_split(user_goal)
        return goal

    try:
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)
        data = json.loads(response)

        sub_tasks_data = data.get("sub_tasks", [])
        for st_data in sub_tasks_data[:5]:  # cap 5 sub-tasks
            persona = st_data.get("persona", "AYMAN").upper()
            if persona not in _PERSONA_AFFINITY:
                persona = "AYMAN"
            goal.sub_tasks.append(SubTask(
                id=f"sub_{uuid.uuid4().hex[:8]}",
                parent_goal_id=goal.id,
                persona=persona,
                sub_goal=(st_data.get("sub_goal") or "")[:300],
                deliverable=(st_data.get("deliverable") or "")[:200],
                estimated_minutes=int(st_data.get("estimated_minutes", 5)),
                priority=int(st_data.get("priority", 2)),
            ))
    except Exception as e:
        log.debug("[hands] LLM JSON parse fail: %s, fallback heuristic", e)
        goal.sub_tasks = _heuristic_split(user_goal)

    if not goal.sub_tasks:
        goal.sub_tasks = _heuristic_split(user_goal)

    return goal


# ── Dispatcher (Q1 2027 = real parallel; vol 17 = sequential stub) ───────────

def dispatch_subtasks(goal: CompoundGoal, *, sequential: bool = True) -> CompoundGoal:
    """
    Dispatch sub-tasks. Vol 17 stub = sequential execution (no actual parallel).
    Q1 2027 = Celery + Redis parallel worker pool.

    Each sub-task spawn ReAct loop via run_react() dengan persona-specific prompt.
    """
    if not goal.sub_tasks:
        goal.overall_status = "failed"
        return goal

    goal.overall_status = "dispatching"
    t_start = time.time()

    if sequential:
        # Sequential stub (vol 17)
        for st in goal.sub_tasks:
            t0 = time.time()
            st.status = "running"
            try:
                from .agent_react import run_react
                session = run_react(
                    question=f"{st.sub_goal}\n\nDeliverable: {st.deliverable}",
                    persona=st.persona,
                    client_id=f"hands_orch_{goal.id}",
                    simple_mode=True,  # fast path untuk sub-task
                    agent_mode=True,
                )
                st.output = (session.final_answer or "")[:1500]
                st.status = "completed"
            except Exception as e:
                st.error = str(e)[:300]
                st.status = "failed"
            st.duration_ms = int((time.time() - t0) * 1000)
    else:
        # TODO Q1 2027: real parallel via Celery + Redis
        # for st in goal.sub_tasks:
        #     celery_task.delay(run_react_async, st)
        # results = celery.gather(...)
        log.warning("[hands] parallel mode tidak available di vol 17, fallback sequential")
        return dispatch_subtasks(goal, sequential=True)

    goal.total_duration_ms = int((time.time() - t_start) * 1000)
    goal.overall_status = "synthesizing"
    return goal


# ── Synthesizer (combine outputs jadi 1 deliverable) ─────────────────────────

def synthesize_compound(goal: CompoundGoal) -> CompoundGoal:
    """
    AYMAN synthesize semua sub-task output jadi 1 final deliverable.
    """
    completed = [st for st in goal.sub_tasks if st.status == "completed"]
    if not completed:
        goal.final_synthesis = (
            "[1000_hands stub] Tidak ada sub-task completed. Sub-tasks failed atau pending. "
            "Real parallel orchestration target Q1 2027."
        )
        goal.overall_status = "failed"
        return goal

    # Build summary prompt
    summaries_text = "\n\n".join(
        f"=== {st.persona} (priority {st.priority}, {st.duration_ms}ms) ===\n"
        f"Sub-goal: {st.sub_goal}\n"
        f"Output: {st.output[:800]}"
        for st in completed
    )

    prompt = f"""User goal asli:
"{goal.user_goal}"

{len(completed)} persona sudah selesai menjawab dari sudut masing-masing:

{summaries_text}

Tugas (sebagai AYMAN synthesizer): combine semua output jadi 1 deliverable
final yang:
- Address user goal asli
- Highlight kontribusi tiap persona (ringkas)
- Identify konflik/tradeoff kalau ada
- Rekomendasi langkah next

Output langsung dalam bahasa hangat, max 400 kata. Tanpa preamble."""

    synthesis = _call_llm(prompt, max_tokens=900, temperature=0.5)
    if synthesis and synthesis.strip():
        goal.final_synthesis = synthesis.strip()[:2000]
        goal.overall_status = "completed"
    else:
        # Fallback: concatenate
        goal.final_synthesis = "## Compound Output\n\n" + "\n\n".join(
            f"### {st.persona}\n{st.output[:500]}" for st in completed
        )
        goal.overall_status = "completed"

    return goal


# ── End-to-end orchestrator ───────────────────────────────────────────────────

def orchestrate(user_goal: str, *, use_llm_split: bool = True) -> CompoundGoal:
    """
    Full pipeline: split → dispatch → synthesize.

    Vol 17 = sequential stub (1-3 menit total untuk 3-4 sub-tasks).
    Q1 2027 = real parallel (~30 second untuk same workload).
    """
    goal = split_goal_into_subtasks(user_goal, use_llm=use_llm_split)
    if goal.sub_tasks:
        goal = dispatch_subtasks(goal, sequential=True)
        goal = synthesize_compound(goal)

    # Persist
    try:
        with _goals_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(goal), ensure_ascii=False) + "\n")
    except Exception:
        pass

    return goal


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Untuk admin dashboard."""
    path = _goals_log()
    if not path.exists():
        return {"total_goals": 0}

    total = 0
    completed = 0
    failed = 0
    avg_subtasks = []
    durations = []
    persona_count: dict[str, int] = {}

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    total += 1
                    status = e.get("overall_status", "")
                    if status == "completed":
                        completed += 1
                    elif status == "failed":
                        failed += 1
                    sts = e.get("sub_tasks", [])
                    avg_subtasks.append(len(sts))
                    if e.get("total_duration_ms"):
                        durations.append(int(e["total_duration_ms"]))
                    for st in sts:
                        p = st.get("persona", "?")
                        persona_count[p] = persona_count.get(p, 0) + 1
                except Exception:
                    continue
    except Exception:
        return {"total_goals": 0}

    return {
        "total_goals": total,
        "completed": completed,
        "failed": failed,
        "avg_subtasks_per_goal": round(sum(avg_subtasks) / len(avg_subtasks), 2) if avg_subtasks else 0,
        "avg_duration_ms": int(sum(durations) / len(durations)) if durations else 0,
        "persona_distribution": persona_count,
    }


__all__ = [
    "SubTask", "CompoundGoal",
    "split_goal_into_subtasks",
    "dispatch_subtasks",
    "synthesize_compound",
    "orchestrate",
    "stats",
]
