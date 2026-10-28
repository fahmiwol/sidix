"""
ado_state.py — SIDIX ADO State Schema (LangGraph-compatible TypedDict)

Adopted from MiganCore architecture 2026-05-07.
This module defines the canonical state that flows through SIDIX agentic loops.
Compatible with LangGraph StateGraph when migrated; usable as plain TypedDict today.

Design principles:
- Immutable-friendly: updates return new state (or use copy())
- Serializable: all fields must json.dumps-able
- Extensible: new fields can be added without breaking existing nodes
- Tenant-aware: every state carries tenant_id + agent_id for isolation
"""

from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    RESEARCHING = "researching"
    REASONING = "reasoning"
    TOOL_EXECUTING = "tool_executing"
    SYNTHESIZING = "synthesizing"
    REFLECTING = "reflecting"
    ESCALATED = "escalated"
    DONE = "done"


class OutputType(str, Enum):
    TEXT = "text"
    CODE = "code"
    IMAGE_PROMPT = "image_prompt"
    VIDEO_STORYBOARD = "video_storyboard"
    AUDIO_TTS = "audio_tts"
    THREE_D_PROMPT = "3d_prompt"
    STRUCTURED = "structured"


class MemoryTier(str, Enum):
    WORKING = "working"      # GPU HBM / current context (Letta core blocks)
    EPISODIC = "episodic"    # DRAM/SSD conversation log (PostgreSQL)
    SEMANTIC = "semantic"    # Vector DB facts (Qdrant/pgvector)
    PROCEDURAL = "procedural"  # LoRA adapters / skill library


# Backward-compatible: plain dict untuk message entries
MessageDict = Dict[str, Any]
ToolCallDict = Dict[str, Any]


class ADOState(TypedDict, total=False):
    """
    Canonical SIDIX ADO state.

    Fields marked REQUIRED must be present at graph start.
    Fields marked OPTIONAL are populated during execution.
    """
    # --- Identity & Routing (REQUIRED) ---
    tenant_id: str                    # Multi-tenant isolation key
    agent_id: str                     # Unique agent instance ID
    user_id: Optional[str]            # End-user identifier (if known)
    session_id: str                   # Conversation/session UUID
    language: str                     # "id" | "en" | "zh" — default "id"

    # --- Input (REQUIRED) ---
    messages: List[MessageDict]       # Chat history: [{role, content, ts}, ...]
    current_task: Optional[str]       # Normalized task description
    query_raw: str                    # Raw user input

    # --- Planning (OPTIONAL) ---
    plan: Optional[str]               # Step-by-step plan (LLM-generated)
    plan_steps: List[str]             # Parsed plan steps
    current_step_index: int           # Pointer to active step

    # --- Memory (OPTIONAL) ---
    memory_context: str               # Injected memory summary string
    memory_tiers_loaded: List[str]    # Which tiers were queried
    working_memory: Dict[str, Any]    # Core blocks: persona, human, task, world_state
    episodic_hits: List[Dict]         # Recent conversation summaries
    semantic_hits: List[Dict]         # Vector search results
    procedural_skills: List[str]      # Matched skill IDs from skill library

    # --- Multi-Source Orchestration (OPTIONAL) ---
    sources: Dict[str, Any]           # {web: [...], corpus: [...], dense: [...], persona: {...}}
    source_status: Dict[str, str]     # {web: "ok|timeout|error", ...}
    sanad_score: float                # 0.0–10.0 cross-verification score
    sanad_verdict: str                # "verified|partial|unverified|conflict"

    # --- Persona Fan-out (OPTIONAL) ---
    persona_outputs: Dict[str, str]   # {"UTZ": "...", "ABOO": "...", ...}
    persona_selected: Optional[str]   # If single-mode selected
    mode: str                         # "instant|thinking|agent|deep_research"
    persona_mode: str                 # "basic|single|pro|holistic"

    # --- Tool Execution (OPTIONAL) ---
    tool_calls: List[ToolCallDict]    # Pending/completed tool calls
    tool_results: List[Dict]          # Tool outputs
    tools_used: List[str]             # Names of tools invoked this turn

    # --- Reasoning & Synthesis (OPTIONAL) ---
    reasoning_trace: str              # Chain-of-thought / ReAct trace
    synthesis: str                    # Final merged response (pre-render)
    output_type: OutputType           # Detected output modality
    output_confidence: float          # 0.0–1.0 detector confidence
    output_reason: str                # Why this output_type was chosen
    attachments: List[Dict]           # [{type, url, mime, metadata}, ...]

    # --- Metadata & Control (OPTIONAL) ---
    iteration_count: int              # Circuit-breaker counter
    max_iterations: int               # Default 10
    status: AgentStatus               # Current node status
    reflections: List[str]            # Self-critique / muhasabah notes
    latency_ms: int                   # End-to-end latency tracking
    tokens_in: int                    # Input token count
    tokens_out: int                   # Output token count
    model_used: str                   # Which LLM served this turn

    # --- Error & Escalation (OPTIONAL) ---
    error: Optional[str]              # Error message if failed
    error_type: Optional[str]         # LOW_CONFIDENCE | OMNYX_EXCEPTION | ...
    escalated_to: Optional[str]       # Human/agent ID if escalated

    # --- Training & Feedback (OPTIONAL) ---
    feedback_score: Optional[float]   # User thumbs up/down / rating
    preference_pair: Optional[Dict]   # {chosen: str, rejected: str} for SimPO
    praxis_frame_ids: List[str]       # Matched case frame IDs from praxis_runtime


# --- Helper functions for state manipulation ---

def make_initial_state(
    tenant_id: str,
    agent_id: str,
    session_id: str,
    query: str,
    language: str = "id",
    max_iterations: int = 10,
) -> ADOState:
    """Factory untuk state awal yang valid."""
    return {
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "user_id": None,
        "session_id": session_id,
        "language": language,
        "messages": [],
        "current_task": None,
        "query_raw": query,
        "plan": None,
        "plan_steps": [],
        "current_step_index": 0,
        "memory_context": "",
        "memory_tiers_loaded": [],
        "working_memory": {},
        "episodic_hits": [],
        "semantic_hits": [],
        "procedural_skills": [],
        "sources": {},
        "source_status": {},
        "sanad_score": 0.0,
        "sanad_verdict": "unverified",
        "persona_outputs": {},
        "persona_selected": None,
        "persona_mode": "basic",
        "tool_calls": [],
        "tool_results": [],
        "tools_used": [],
        "reasoning_trace": "",
        "synthesis": "",
        "output_type": OutputType.TEXT,
        "output_confidence": 0.0,
        "output_reason": "",
        "attachments": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "status": AgentStatus.IDLE,
        "reflections": [],
        "latency_ms": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "model_used": "",
        "error": None,
        "error_type": None,
        "escalated_to": None,
        "feedback_score": None,
        "preference_pair": None,
        "praxis_frame_ids": [],
    }


def state_to_serializable(state: ADOState) -> Dict[str, Any]:
    """Convert state ke plain dict yang aman untuk JSON/logging."""
    d = dict(state)
    # Enum → string
    if isinstance(d.get("output_type"), Enum):
        d["output_type"] = d["output_type"].value
    if isinstance(d.get("status"), Enum):
        d["status"] = d["status"].value
    return d


def state_summary(state: ADOState) -> str:
    """Ringkasan 1-baris untuk logging/debug."""
    return (
        f"[ADOState agent={state.get('agent_id','?')} "
        f"status={state.get('status','?')} "
        f"iter={state.get('iteration_count',0)}/{state.get('max_iterations',10)} "
        f"sources={list(state.get('sources',{}).keys())} "
        f"sanad={state.get('sanad_score',0):.1f}]"
    )


# --- Backward compatibility dengan existing SIDIX code ---

def from_chat_request(
    request_dict: Dict[str, Any],
    tenant_id: str = "default",
    agent_id: str = "sidix-core",
) -> ADOState:
    """
    Migrate dari format request lama SIDIX ke ADOState canonical.
    Usage: wrap existing /agent/chat_holistic request body.
    """
    msgs = request_dict.get("messages", [])
    if not msgs and "message" in request_dict:
        msgs = [{"role": "user", "content": request_dict["message"]}]
    return make_initial_state(
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=request_dict.get("conversation_id", "sidix-session-0"),
        query=msgs[-1]["content"] if msgs else "",
        language=request_dict.get("language", "id"),
        max_iterations=request_dict.get("max_iterations", 10),
    )
