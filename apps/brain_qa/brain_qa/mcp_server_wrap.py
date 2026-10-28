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

    # === Web & Search (tools yang sudah ada di agent_tools.py, belum di-MCP-wrap) ===
    MCPToolSpec(
        name="sidix_web_search",
        description="Cari web umum via DuckDuckGo HTML (own parser, no API vendor). "
                    "Gunakan untuk pencarian luas, baru, atau yang tidak tercakup corpus/Wikipedia. "
                    "Params: query (str, wajib), max_results (int, default 8, max 15). "
                    "Return: daftar judul + URL + snippet.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Query pencarian"},
                "max_results": {"type": "integer", "default": 8, "minimum": 1, "maximum": 15},
            },
            "required": ["query"],
        },
        sidix_module="apps/brain_qa/brain_qa/agent_tools.py",
        category="web",
    ),

    # === Image Generation ===
    MCPToolSpec(
        name="sidix_generate_image",
        description="Generate gambar dari prompt teks via FLUX.1-schnell (local, no GPU needed for mock). "
                    "Graceful degradation: FLUX.1 → mock SVG placeholder. "
                    "Params: prompt (str wajib), steps (int 1-50 default 4), width/height (int 512-1536 default 1024), seed (int opsional).",
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt teks untuk gambar"},
                "steps": {"type": "integer", "default": 4, "minimum": 1, "maximum": 50},
                "width": {"type": "integer", "default": 1024, "minimum": 512, "maximum": 1536},
                "height": {"type": "integer", "default": 1024, "minimum": 512, "maximum": 1536},
                "seed": {"type": "integer"},
            },
            "required": ["prompt"],
        },
        sidix_module="apps/brain_qa/brain_qa/agent_tools.py",
        category="creative",
    ),

    # === Code Execution ===
    MCPToolSpec(
        name="sidix_execute_python",
        description="Jalankan snippet Python (komputasi murni, no IO sistem) di subprocess terisolasi. "
                    "Cocok untuk: hitung, transformasi data, simulasi, parse teks. Timeout 30 detik. "
                    "Params: code (str, Python source). Return: stdout + stderr.",
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python source code"},
                "timeout": {"type": "integer", "default": 30, "minimum": 5, "maximum": 60},
            },
            "required": ["code"],
        },
        sidix_module="apps/brain_qa/brain_qa/agent_tools.py",
        category="code",
    ),

    # === Deep Research ===
    MCPToolSpec(
        name="sidix_deep_research",
        description="Recursive multi-source deep research: corpus → web → follow-up → synthesis report. "
                    "Mode DEEP_RESEARCH implementation. Generate laporan komprehensif dengan citations. "
                    "Params: query (str wajib), max_iterations (int default 3), max_depth (int default 2). "
                    "Return: markdown report + findings + citations.",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topik/pertanyaan riset"},
                "max_iterations": {"type": "integer", "default": 3, "minimum": 1, "maximum": 10},
                "max_depth": {"type": "integer", "default": 2, "minimum": 1, "maximum": 5},
            },
            "required": ["query"],
        },
        sidix_module="apps/brain_qa/brain_qa/deep_research.py",
        category="research",
    ),
]


# ── Tool Execution Wiring (Phase B — 2026-05-07) ──────────────────────────────

# Mapping: nama MCP tool → nama tool di agent_tools.TOOL_REGISTRY
# Format: mcp_name: (agent_name, needs_allow_restricted)
_MCP_TO_AGENT_TOOL: dict[str, tuple[str, bool]] = {
    "sidix_search_corpus": ("search_corpus", False),
    "sidix_web_search": ("web_search", False),
    "sidix_generate_image": ("text_to_image", False),
    "sidix_execute_python": ("code_sandbox", False),
    "sidix_deep_research": ("deep_research", False),
    "sidix_web_fetch": ("web_fetch", False),
    "sidix_browser_fetch": ("browser_fetch", False),
    "sidix_calculator": ("calculator", False),
    "sidix_pdf_extract": ("pdf_extract", False),
    "sidix_workspace_list": ("workspace_list", False),
    "sidix_workspace_read": ("workspace_read", False),
    "sidix_workspace_write": ("workspace_write", True),
    "sidix_workspace_patch": ("workspace_patch", True),
}


def execute_tool(name: str, args: dict, *, session_id: str = "", step: int = 1, admin_ok: bool = False, allow_restricted: bool = False) -> dict:
    """
    Execute an MCP tool by dispatching to agent_tools.call_tool().

    Args:
        name: MCP tool name (e.g. 'sidix_web_search')
        args: Tool arguments dict
        session_id: Session ID for audit logging
        step: Step number for audit logging
        admin_ok: Whether admin-only tools are permitted
        allow_restricted: Whether restricted tools are permitted

    Returns:
        dict with keys: success (bool), output (str), error (str), citations (list)
    """
    from .agent_tools import call_tool as _agent_call_tool

    # Lookup mapping
    mapping = _MCP_TO_AGENT_TOOL.get(name)
    if not mapping:
        # Try direct name (some tools use same name)
        agent_name = name.replace("sidix_", "")
        needs_restricted = False
    else:
        agent_name, needs_restricted = mapping

    if needs_restricted and not allow_restricted:
        return {
            "success": False,
            "output": "",
            "error": f"Tool '{name}' requires allow_restricted=true. Set flag untuk mengaktifkan.",
            "citations": [],
        }

    # Check admin gate for tools that have is_admin in registry
    spec = get_tool_spec(name)
    if spec and spec.is_admin and not admin_ok:
        return {
            "success": False,
            "output": "",
            "error": f"Tool '{name}' is admin-only.",
            "citations": [],
        }

    try:
        result = _agent_call_tool(
            tool_name=agent_name,
            args=args,
            session_id=session_id or f"mcp_{uuid.uuid4().hex[:8]}",
            step=step,
        )
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "citations": [asdict(c) if hasattr(c, "__dataclass_fields__") else c for c in (result.citations or [])],
        }
    except Exception as e:
        log.exception("[mcp] execute_tool failed: %s", name)
        return {
            "success": False,
            "output": "",
            "error": f"Execution error: {e}",
            "citations": [],
        }


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
