"""
mcp_server_wrap.py — Wrap SIDIX Tools sebagai MCP Server (Model Context Protocol)
=====================================================================================

Per DIRECTION_LOCK Q3 2026 P2:
> "MCP server wrap 17 tool existing"

Plus user vision (note 229):
> "MCP mampu membuka, mengakses segalanya"

MCP (Anthropic, Nov 2024) = JSON-RPC standar untuk LLM ↔ tool. Tool yang
ditulis sekali bisa dipakai di:
- Claude Desktop
- Cursor
- smolagents
- continue.dev
- 100+ MCP-compatible client

Modul ini = **registry + JSON-RPC handler** untuk expose SIDIX tools sebagai
MCP server. Bidirectional:

**Phase A — SIDIX as MCP Server** (export ✅ vol 17):
- Wrap 17 internal tools jadi MCP method
- Handler stdio atau HTTP (JSON-RPC 2.0)
- Result: Claude Desktop bisa pakai tool SIDIX (search_corpus, web_search,
  pattern_extractor, dll)

**Phase B — SIDIX as MCP Client** (import, Q4 2026):
- Konsumsi MCP server publik (filesystem, blender, figma, postgres)
- Add ke ReAct tool registry runtime
- Result: SIDIX akses external tools via standard protocol

Vol 17 implement Phase A foundation: registry + JSON-RPC handler stub.
Production deploy via FastMCP Q3 2026.

Reference:
- MCP spec: https://modelcontextprotocol.io
- FastMCP Python SDK: https://github.com/jlowin/fastmcp
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class MCPToolSpec:
    """1 tool spec untuk MCP registry."""
    name: str                      # snake_case name
    description: str               # 1-2 line, dipakai LLM untuk pick tool
    input_schema: dict             # JSON Schema untuk arguments
    sidix_module: str              # path ke implementation
    category: str = "general"      # "search" | "web" | "code" | "cognitive" | "memory"
    is_admin: bool = False         # require admin token
    rate_limit_per_min: int = 60


# ── Registry seed (mapping ke 17+ existing SIDIX tools) ───────────────────────

_TOOL_REGISTRY: list[MCPToolSpec] = [
    # === Cognitive tools (vol 5-6) ===
    MCPToolSpec(
        name="sidix_pattern_extract",
        description="Ekstrak prinsip umum (induktif generalisasi) dari teks observation. "
                    "Input: text dengan klaim faktual (contoh: 'kalau X dibakar jadi arang, "
                    "kayu juga jadi arang'). Output: pattern principle + domain + keywords + confidence.",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Observation atau klaim faktual"},
            },
            "required": ["text"],
        },
        sidix_module="apps/brain_qa/brain_qa/pattern_extractor.py",
        category="cognitive",
    ),
    MCPToolSpec(
        name="sidix_aspiration_analyze",
        description="Detect capability gap dari user message ('GPT bisa, saya juga bisa'). "
                    "Output: spec implementasi (target, competitors, decomposition, resources, "
                    "novel_angle, effort).",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "User message yang ekspresikan keinginan"},
            },
            "required": ["text"],
        },
        sidix_module="apps/brain_qa/brain_qa/aspiration_detector.py",
        category="cognitive",
    ),
    MCPToolSpec(
        name="sidix_skill_synthesize",
        description="Synthesize Python skill baru dari task description. Generate code, "
                    "validate AST, test sandbox. Save permanent kalau sukses.",
        input_schema={
            "type": "object",
            "properties": {
                "task_description": {"type": "string"},
                "auto_test": {"type": "boolean", "default": True},
            },
            "required": ["task_description"],
        },
        sidix_module="apps/brain_qa/brain_qa/tool_synthesizer.py",
        category="cognitive",
        is_admin=True,
    ),
    MCPToolSpec(
        name="sidix_problem_decompose",
        description="Polya 4-phase decomposition: Understand (given/unknown/constraints) "
                    "+ Plan (strategy/sub_goals/tools_needed). Phase 3 ReAct, Phase 4 review.",
        input_schema={
            "type": "object",
            "properties": {
                "problem": {"type": "string"},
            },
            "required": ["problem"],
        },
        sidix_module="apps/brain_qa/brain_qa/problem_decomposer.py",
        category="cognitive",
    ),
    MCPToolSpec(
        name="sidix_socratic_probe",
        description="Apakah pertanyaan butuh clarifying question dulu sebelum jawab? "
                    "Return: probe decision + suggested clarifying questions.",
        input_schema={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "persona": {"type": "string", "default": "AYMAN"},
            },
            "required": ["question"],
        },
        sidix_module="apps/brain_qa/brain_qa/socratic_probe.py",
        category="cognitive",
    ),
    MCPToolSpec(
        name="sidix_persona_route",
        description="Auto-detect optimal persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) dari user "
                    "message style. Tier 1 keyword + history-aware override.",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "user_id": {"type": "string", "default": ""},
            },
            "required": ["message"],
        },
        sidix_module="apps/brain_qa/brain_qa/persona_router.py",
        category="cognitive",
    ),

    # === Multi-agent (vol 10) ===
    MCPToolSpec(
        name="sidix_critique",
        description="Critique LLM output. Mode: devil_advocate | quality_check | destruction_test. "
                    "Return: severity + score + issues + suggested_improvements.",
        input_schema={
            "type": "object",
            "properties": {
                "output": {"type": "string"},
                "mode": {"type": "string", "default": "quality_check"},
                "context": {"type": "string", "default": ""},
            },
            "required": ["output"],
        },
        sidix_module="apps/brain_qa/brain_qa/agent_critic.py",
        category="cognitive",
    ),
    MCPToolSpec(
        name="sidix_tadabbur",
        description="3-persona iterate same query → konvergensi pattern. Untuk deep question "
                    "yang butuh holistic view. 7 LLM call (mahal, tidak untuk casual).",
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "personas": {"type": "array", "items": {"type": "string"}, "default": ["UTZ", "ABOO", "OOMAR"]},
            },
            "required": ["prompt"],
        },
        sidix_module="apps/brain_qa/brain_qa/tadabbur_mode.py",
        category="cognitive",
    ),

    # === RAG + Memory (vol 7) ===
    MCPToolSpec(
        name="sidix_search_corpus",
        description="BM25 search SIDIX corpus (230+ research notes + brain knowledge). "
                    "Return chunks dengan sanad chain.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        sidix_module="apps/brain_qa/brain_qa/agent_react.py",  # search_corpus tool
        category="search",
    ),
    MCPToolSpec(
        name="sidix_memory_snapshot",
        description="Snapshot 5-layer immutable memory: patterns + skills + research_notes + "
                    "activity_log + aspirations + lora_snapshots + compound_score.",
        input_schema={"type": "object", "properties": {}},
        sidix_module="apps/brain_qa/brain_qa/continual_memory.py",
        category="memory",
        is_admin=True,
    ),

    # === Proactive (vol 9, 15) ===
    MCPToolSpec(
        name="sidix_proactive_scan",
        description="Hourly anomaly scan: pattern clusters + aspiration themes + activity. "
                    "Return list anomaly + suggested self-prompts.",
        input_schema={"type": "object", "properties": {}},
        sidix_module="apps/brain_qa/brain_qa/proactive_trigger.py",
        category="cognitive",
        is_admin=True,
    ),
    MCPToolSpec(
        name="sidix_trend_feeds",
        description="Fetch external AI/tech trend feeds (HN + arxiv + GitHub + HF papers). "
                    "Return aggregated items + cross-source anomaly.",
        input_schema={
            "type": "object",
            "properties": {
                "limit_per_source": {"type": "integer", "default": 5},
            },
        },
        sidix_module="apps/brain_qa/brain_qa/proactive_feeds.py",
        category="search",
        is_admin=True,
    ),

    # === Sensorial (vol 15) ===
    MCPToolSpec(
        name="sidix_voice_synth",
        description="Text → speech via tts_engine (Piper, 4 bahasa: id/en/ar/ms). "
                    "Future Q3 2026: Step-Audio expressive voice clone.",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "language": {"type": "string", "default": "id"},
            },
            "required": ["text"],
        },
        sidix_module="apps/brain_qa/brain_qa/sensorial_input.py",
        category="audio",
    ),

    # === CodeAct (vol 17) ===
    MCPToolSpec(
        name="sidix_code_action",
        description="Execute Python code action. Auto-detect ```python``` block, validate AST, "
                    "run di sandbox, return output. CodeAct pattern (Wang 2024).",
        input_schema={
            "type": "object",
            "properties": {
                "code_or_llm_output": {"type": "string"},
                "auto_execute": {"type": "boolean", "default": True},
                "timeout_seconds": {"type": "integer", "default": 10},
            },
            "required": ["code_or_llm_output"],
        },
        sidix_module="apps/brain_qa/brain_qa/codeact_adapter.py",
        category="code",
    ),

    # === Context (vol 11) ===
    MCPToolSpec(
        name="sidix_context_triple",
        description="Derive zaman/makan/haal context vector untuk current request. "
                    "Privacy-conscious bucket (no precise location stored).",
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "default": ""},
                "verbose": {"type": "boolean", "default": False},
            },
        },
        sidix_module="apps/brain_qa/brain_qa/context_triple.py",
        category="cognitive",
    ),

    # === Creative (vol 16) ===
    MCPToolSpec(
        name="sidix_creative_registry",
        description="Registry 33 creative tools (visual/video/audio/3d/agent/marketing). "
                    "Track adoption status: planned/evaluating/wired/shipped.",
        input_schema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "default": ""},
                "status": {"type": "string", "default": ""},
            },
        },
        sidix_module="apps/brain_qa/brain_qa/creative_tools_registry.py",
        category="cognitive",
        is_admin=True,
    ),

    # === Wisdom Gate (vol 5b Kimi) ===
    MCPToolSpec(
        name="sidix_wisdom_gate",
        description="Pre-action safety check: Pareto + Method Mirror + sensitive topic guard. "
                    "Block destructive keyword (delete/format/kill).",
        input_schema={
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "proposed_action": {"type": "string"},
            },
            "required": ["question", "proposed_action"],
        },
        sidix_module="apps/brain_qa/brain_qa/wisdom_gate.py",
        category="cognitive",
    ),
]


# ── MCP JSON-RPC handler (Phase A foundation) ─────────────────────────────────

def list_tools(category: str = "", admin_ok: bool = False) -> list[dict]:
    """
    MCP standard `tools/list` method response.
    Filter by category + admin context.
    """
    out = []
    for spec in _TOOL_REGISTRY:
        if category and spec.category != category:
            continue
        if spec.is_admin and not admin_ok:
            continue
        out.append({
            "name": spec.name,
            "description": spec.description,
            "inputSchema": spec.input_schema,
        })
    return out


def get_tool_spec(name: str) -> Optional[MCPToolSpec]:
    """Lookup single tool spec by name."""
    for spec in _TOOL_REGISTRY:
        if spec.name == name:
            return spec
    return None


def stats() -> dict:
    """MCP server stats untuk admin dashboard."""
    by_category: dict[str, int] = {}
    admin_only = 0
    for spec in _TOOL_REGISTRY:
        by_category[spec.category] = by_category.get(spec.category, 0) + 1
        if spec.is_admin:
            admin_only += 1
    return {
        "total_tools": len(_TOOL_REGISTRY),
        "by_category": by_category,
        "admin_only": admin_only,
        "public": len(_TOOL_REGISTRY) - admin_only,
    }


# ── Manifest export (untuk MCP server config) ─────────────────────────────────

def export_manifest() -> dict:
    """
    Export full MCP server manifest. Format compatible dengan FastMCP /
    MCP standard. Dipakai saat deploy MCP server (Q3 2026).
    """
    return {
        "name": "sidix-cognitive",
        "version": "2.0.0",
        "description": (
            "SIDIX Cognitive MCP Server — pattern extraction, aspiration "
            "detection, tool synthesis, problem decomposition, persona routing, "
            "memory consolidation, proactive trigger, creative registry. "
            "17 tools dari SIDIX cognitive infrastructure."
        ),
        "license": "MIT",
        "homepage": "https://github.com/fahmiwol/sidix",
        "tools": [
            {
                "name": spec.name,
                "description": spec.description,
                "inputSchema": spec.input_schema,
                "metadata": {
                    "category": spec.category,
                    "is_admin": spec.is_admin,
                    "rate_limit_per_min": spec.rate_limit_per_min,
                },
            }
            for spec in _TOOL_REGISTRY
        ],
    }


__all__ = [
    "MCPToolSpec",
    "list_tools",
    "get_tool_spec",
    "stats",
    "export_manifest",
]
