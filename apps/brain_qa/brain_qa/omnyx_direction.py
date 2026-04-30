"""
omnyx_direction.py — SIDIX Orchestrator Multi-source Nusantara Yield eXecutor

Arsitektur:
  OMNYX = director layer autentik SIDIX yang mengatur alur tool-calling
  tanpa bergantung pada vendor API (Google/Gemini/OpenAI) untuk decision logic.

  Pattern adopted: tool context circulation (inspired by Gemini API docs)
  Implementation: pure Python + self-hosted Qwen/Ollama for intent detection

Flow:
  1. User query → IntentClassifier (rule-based + light LLM)
  2. Intent → ToolPlanner (decide which tools to call, in what order)
  3. ToolExecutor → parallel/sequential execution
  4. ContextAccumulator → collect all tool results
  5. SynthesisRouter → route to persona brain or neutral synthesizer
  6. KnowledgeAccumulator → save verified answer to corpus

Tools (built-in + custom):
  - corpus_search     → BM25 local corpus
  - dense_search      → semantic embedding search
  - web_search        → multi-engine (SearxNG + Brave + Wikipedia + Google AI)
  - calculator        → numerical computation
  - persona_brain     → persona-specific reasoning (5 persona)
  - knowledge_store   → persist answer to corpus index

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger("sidix.omnyx")


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class ToolCall:
    """Represents a tool call decision by OMNYX."""
    tool_name: str
    args: dict[str, Any]
    call_id: str  # unique ID for tracking
    turn: int = 1


@dataclass
class ToolResult:
    """Result from executing a tool call."""
    call_id: str
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    latency_ms: int = 0


@dataclass
class TurnContext:
    """Context accumulated across turns (tool context circulation)."""
    turn: int
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    reasoning: str = ""  # OMNYX reasoning for this turn


@dataclass
class OmnyxSession:
    """Full OMNYX session state."""
    session_id: str
    query: str
    persona: str = "UTZ"
    turns: list[TurnContext] = field(default_factory=list)
    final_answer: str = ""
    confidence: str = "rendah"
    sources_used: list[str] = field(default_factory=list)
    total_latency_ms: int = 0
    knowledge_stored: bool = False


# ── Tool Registry ────────────────────────────────────────────────────────

class ToolRegistry:
    """Registry of available tools for OMNYX."""

    TOOL_SCHEMAS = {
        "corpus_search": {
            "description": "Search local BM25 corpus for factual knowledge",
            "parameters": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "default": 3},
            },
        },
        "dense_search": {
            "description": "Semantic embedding search for conceptual matches",
            "parameters": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "default": 3},
            },
        },
        "web_search": {
            "description": "Multi-engine web search for current events",
            "parameters": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 5},
            },
        },
        "calculator": {
            "description": "Numerical computation",
            "parameters": {
                "expression": {"type": "string", "description": "Math expression to evaluate"},
            },
        },
        "persona_brain": {
            "description": "Get perspective from specific persona brain",
            "parameters": {
                "query": {"type": "string", "description": "Query for persona"},
                "persona": {"type": "string", "description": "Persona name (UTZ/ABOO/ALEY/AYMAN/OOMAR)"},
            },
        },
        "knowledge_store": {
            "description": "Store verified answer to corpus for future retrieval",
            "parameters": {
                "question": {"type": "string", "description": "Original question"},
                "answer": {"type": "string", "description": "Verified answer"},
                "sources": {"type": "array", "description": "List of source IDs"},
                "persona": {"type": "string", "description": "Persona who generated this"},
            },
        },
    }

    @classmethod
    def get_schema(cls, tool_name: str) -> Optional[dict]:
        return cls.TOOL_SCHEMAS.get(tool_name)

    @classmethod
    def list_tools(cls) -> list[str]:
        return list(cls.TOOL_SCHEMAS.keys())


# ── Intent Classifier ────────────────────────────────────────────────────

class IntentClassifier:
    """Lightweight intent detection for OMNYX.

    Hybrid approach:
    - Rule-based heuristics (fast, 0ms)
    - Light LLM fallback (Qwen 1.5B via Ollama, ~500ms)
    """

    # Heuristic patterns for quick classification
    PATTERNS = {
        "factual_who": ["siapa", "who is", "siapakah"],
        "factual_when": ["kapan", "when", "tanggal berapa"],
        "factual_where": ["dimana", "di mana", "where is"],
        "factual_what": ["apa", "what is", "apakah"],
        "factual_how_many": ["berapa", "how many", "how much"],
        "coding": ["buat kode", "coding", "function", "script", "code"],
        "creative": ["buat gambar", "image", "design", "video", "tts"],
        "calculation": ["hitung", "calculate", "kali", "bagi", "tambah", "kurang"],
        "comparison": ["bandingkan", "compare", "vs", "versus", "lebih baik"],
        "opinion": ["menurutmu", "bagaimana pendapat", "what do you think"],
    }

    TOOL_MAP = {
        "factual_who": ["corpus_search", "web_search"],
        "factual_when": ["corpus_search", "web_search"],
        "factual_where": ["corpus_search", "web_search", "dense_search"],
        "factual_what": ["corpus_search", "dense_search", "web_search"],
        "factual_how_many": ["corpus_search", "calculator", "web_search"],
        "coding": ["corpus_search", "web_search", "persona_brain"],
        "creative": ["corpus_search", "persona_brain"],
        "calculation": ["calculator", "corpus_search"],
        "comparison": ["corpus_search", "dense_search", "web_search"],
        "opinion": ["persona_brain", "dense_search"],
    }

    @classmethod
    def classify(cls, query: str) -> tuple[str, list[str]]:
        """Return (intent_type, recommended_tools)."""
        q_lower = query.lower()

        # Rule-based matching
        for intent, keywords in cls.PATTERNS.items():
            if any(kw in q_lower for kw in keywords):
                tools = cls.TOOL_MAP.get(intent, ["corpus_search", "web_search"])
                log.info("[omnyx] Intent detected (rule): %s → %s", intent, tools)
                return intent, tools

        # Default: general factual → corpus + web
        log.info("[omnyx] Intent detected (default): general → corpus + web")
        return "general", ["corpus_search", "dense_search", "web_search"]


# ── Tool Executor ────────────────────────────────────────────────────────

class ToolExecutor:
    """Execute tool calls and return results."""

    def __init__(self):
        self._handlers = {
            "corpus_search": self._exec_corpus_search,
            "dense_search": self._exec_dense_search,
            "web_search": self._exec_web_search,
            "calculator": self._exec_calculator,
            "persona_brain": self._exec_persona_brain,
            "knowledge_store": self._exec_knowledge_store,
        }

    async def execute(self, call: ToolCall) -> ToolResult:
        t0 = time.monotonic()
        handler = self._handlers.get(call.tool_name)
        if not handler:
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=f"Unknown tool: {call.tool_name}",
            )

        try:
            output = await handler(call.args)
            latency = int((time.monotonic() - t0) * 1000)
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=True,
                output=output,
                latency_ms=latency,
            )
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            log.warning("[omnyx] Tool %s failed: %s", call.tool_name, e)
            return ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                success=False,
                output=None,
                error=f"{type(e).__name__}: {e}",
                latency_ms=latency,
            )

    # ── Individual tool handlers ─────────────────────────────────────────

    async def _exec_corpus_search(self, args: dict) -> dict:
        from .multi_source_orchestrator import _src_corpus_search
        return await _src_corpus_search(args.get("query", ""))

    async def _exec_dense_search(self, args: dict) -> dict:
        from .multi_source_orchestrator import _src_dense_index
        return await _src_dense_index(args.get("query", ""))

    async def _exec_web_search(self, args: dict) -> dict:
        from .multi_source_orchestrator import _src_web_search, _src_google_ai_search
        query = args.get("query", "")
        # Try web search first, fallback to Google AI
        result = await _src_web_search(query)
        if not result.get("output"):
            result = await _src_google_ai_search(query)
        return result

    async def _exec_calculator(self, args: dict) -> dict:
        import math
        expr = args.get("expression", "")
        # Safe eval with limited namespace
        safe_ns = {
            "abs": abs, "round": round, "max": max, "min": min,
            "pow": pow, "sum": sum, "len": len,
            "math": math,
        }
        try:
            result = eval(expr, {"__builtins__": {}}, safe_ns)
            return {"result": result, "expression": expr}
        except Exception as e:
            return {"error": str(e), "expression": expr}

    async def _exec_persona_brain(self, args: dict) -> dict:
        from .multi_source_orchestrator import _src_persona_fanout
        query = args.get("query", "")
        persona = args.get("persona", "UTZ")
        result = await _src_persona_fanout(query, personas=(persona,))
        return result

    async def _exec_knowledge_store(self, args: dict) -> dict:
        """Store verified answer to corpus as new knowledge."""
        from .knowledge_accumulator import store_knowledge
        return await store_knowledge(
            question=args.get("question", ""),
            answer=args.get("answer", ""),
            sources=args.get("sources", []),
            persona=args.get("persona", "OMNYX"),
        )


# ── OMNYX Director ───────────────────────────────────────────────────────

class OmnyxDirector:
    """Main director class for OMNYX tool-calling flow."""

    def __init__(self, max_turns: int = 3):
        self.max_turns = max_turns
        self.executor = ToolExecutor()

    async def process(
        self,
        query: str,
        persona: str = "UTZ",
        *,
        debug: bool = False,
    ) -> OmnyxSession:
        """Process user query through OMNYX tool-calling loop."""
        import uuid
        t0 = time.monotonic()

        session = OmnyxSession(
            session_id=f"omnyx_{uuid.uuid4().hex[:8]}",
            query=query,
            persona=persona,
        )

        log.info("[omnyx] Session %s started: %r", session.session_id, query[:60])

        # Turn 1: Intent classification + initial tool calls
        intent, recommended_tools = IntentClassifier.classify(query)
        turn1 = TurnContext(turn=1)

        for i, tool_name in enumerate(recommended_tools):
            call = ToolCall(
                tool_name=tool_name,
                args={"query": query},
                call_id=f"t1_{i}_{tool_name}",
                turn=1,
            )
            turn1.tool_calls.append(call)

        # Execute initial tools in parallel
        results = await asyncio.gather(*[
            self.executor.execute(call) for call in turn1.tool_calls
        ])
        turn1.tool_results = list(results)
        session.turns.append(turn1)

        # Check if corpus passthrough applies (fast path)
        corpus_result = self._find_corpus_primer(turn1.tool_results)
        if corpus_result:
            log.info("[omnyx] Corpus passthrough triggered")
            session.final_answer = self._format_corpus_answer(corpus_result)
            session.confidence = "tinggi"
            session.sources_used = ["corpus"]
            session.total_latency_ms = int((time.monotonic() - t0) * 1000)

            # Auto-store to knowledge base
            await self._auto_store(session)
            return session

        # Turn 2: Determine if more tools needed
        if len(session.turns) < self.max_turns:
            turn2 = await self._plan_next_turn(session, query, persona)
            if turn2.tool_calls:
                results = await asyncio.gather(*[
                    self.executor.execute(call) for call in turn2.tool_calls
                ])
                turn2.tool_results = list(results)
                session.turns.append(turn2)

        # Synthesis: merge all tool results into final answer
        session.final_answer, session.confidence, session.sources_used = \
            await self._synthesize(session, query, persona)

        session.total_latency_ms = int((time.monotonic() - t0) * 1000)

        # Auto-store verified knowledge
        await self._auto_store(session)

        log.info(
            "[omnyx] Session %s complete: turns=%d, confidence=%s, latency=%dms",
            session.session_id, len(session.turns), session.confidence,
            session.total_latency_ms,
        )
        return session

    # ── Internal helpers ─────────────────────────────────────────────────

    def _find_corpus_primer(self, results: list[ToolResult]) -> Optional[dict]:
        """Check if corpus result has primer-tier data."""
        for r in results:
            if r.tool_name == "corpus_search" and r.success and r.output:
                data = r.output
                raw_text = ""
                if isinstance(data, dict):
                    raw_text = data.get("raw_text", data.get("output", ""))
                else:
                    raw_text = str(data)
                if "sanad_tier: primer" in raw_text.lower():
                    return data
        return None

    def _format_corpus_answer(self, corpus_data: dict) -> str:
        """Format corpus primer answer into clean readable text."""
        from .cognitive_synthesizer import _strip_yaml_frontmatter
        import re

        raw_text = corpus_data.get("raw_text", corpus_data.get("output", ""))
        clean = _strip_yaml_frontmatter(raw_text)

        # Remove markdown headings, keep content clean
        clean = re.sub(r'^#+\s*', '', clean, flags=re.MULTILINE)
        # Remove bullet marker artifacts
        clean = re.sub(r'^\s*[-*]\s*', '• ', clean, flags=re.MULTILINE)
        # Remove excessive blank lines
        clean = re.sub(r'\n{3,}', '\n\n', clean)

        # Extract key facts for a concise answer
        lines = clean.strip().split("\n")
        # Find lines that look like factual statements
        factual_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip metadata-like lines
            if line.startswith('[') and '|' in line:
                continue
            if 'source:' in line.lower() and 'tier:' in line.lower():
                continue
            factual_lines.append(line)

        # Build concise answer
        answer = "\n".join(factual_lines[:15])  # Limit to ~15 lines
        if not answer:
            answer = clean.strip()[:800]

        return answer + "\n\n(Sumber: corpus SIDIX, sanad tier: primer)"

    async def _plan_next_turn(
        self, session: OmnyxSession, query: str, persona: str
    ) -> TurnContext:
        """Plan additional tool calls based on previous results."""
        turn = TurnContext(turn=len(session.turns) + 1)

        # Check if web search is needed (no corpus results or weak results)
        has_corpus = any(
            r.tool_name == "corpus_search" and r.success and r.output
            for r in session.turns[-1].tool_results
        )
        has_web = any(
            r.tool_name == "web_search" for r in session.turns[-1].tool_results
        )

        if not has_corpus and not has_web:
            # No local knowledge → try web
            turn.tool_calls.append(ToolCall(
                tool_name="web_search",
                args={"query": query, "max_results": 5},
                call_id=f"t{turn.turn}_web",
                turn=turn.turn,
            ))

        # Check if calculation is needed (numbers in query)
        import re
        if re.search(r'\d+\s*[\+\-\*\/\^]\s*\d+', query) or "berapa" in query.lower():
            # Try to extract expression
            turn.tool_calls.append(ToolCall(
                tool_name="calculator",
                args={"expression": self._extract_expression(query)},
                call_id=f"t{turn.turn}_calc",
                turn=turn.turn,
            ))

        # Get persona perspective
        turn.tool_calls.append(ToolCall(
            tool_name="persona_brain",
            args={"query": query, "persona": persona},
            call_id=f"t{turn.turn}_persona",
            turn=turn.turn,
        ))

        return turn

    def _extract_expression(self, query: str) -> str:
        """Extract mathematical expression from query."""
        import re
        # Simple extraction: find numbers and operators
        patterns = [
            r'(\d+\.?\d*)\s*([\+\-\*\/\^])\s*(\d+\.?\d*)',
            r'akar\s+dari\s+(\d+\.?\d*)',
            r'pangkat\s+(\d+)\s+dari\s+(\d+\.?\d*)',
        ]
        for p in patterns:
            m = re.search(p, query, re.I)
            if m:
                if "akar" in query.lower():
                    return f"math.sqrt({m.group(1)})"
                if "pangkat" in query.lower():
                    return f"pow({m.group(2)}, {m.group(1)})"
                return f"{m.group(1)} {m.group(2)} {m.group(3)}"
        return "0"

    async def _synthesize(
        self, session: OmnyxSession, query: str, persona: str
    ) -> tuple[str, str, list[str]]:
        """Synthesize final answer from all tool results."""
        from .cognitive_synthesizer import CognitiveSynthesizer
        from .multi_source_orchestrator import SourceBundle, SourceResult

        # Build SourceBundle from tool results
        bundle = SourceBundle(query=query)
        sources_used = []

        for turn in session.turns:
            for r in turn.tool_results:
                if not r.success or not r.output:
                    continue
                src = SourceResult(success=True, data=r.output, latency_ms=r.latency_ms)
                if r.tool_name == "corpus_search":
                    bundle.corpus = src; sources_used.append("corpus")
                elif r.tool_name == "dense_search":
                    bundle.dense = src; sources_used.append("dense_index")
                elif r.tool_name in ("web_search", "google_ai_search"):
                    bundle.web = src; sources_used.append("web_search")
                elif r.tool_name == "persona_brain":
                    bundle.persona_fanout = src; sources_used.append("persona_fanout")

        # Use cognitive synthesizer
        synth = CognitiveSynthesizer()
        result = await synth.synthesize(bundle)
        return result.answer, result.confidence, list(set(sources_used))

    async def _auto_store(self, session: OmnyxSession) -> None:
        """Auto-store verified knowledge to corpus."""
        if session.confidence in ("tinggi", "sedang") and len(session.final_answer) > 50:
            try:
                store_result = await self.executor.execute(ToolCall(
                    tool_name="knowledge_store",
                    args={
                        "question": session.query,
                        "answer": session.final_answer,
                        "sources": session.sources_used,
                        "persona": session.persona,
                    },
                    call_id="store_auto",
                ))
                session.knowledge_stored = store_result.success
                log.info("[omnyx] Knowledge stored: %s", store_result.success)
            except Exception as e:
                log.warning("[omnyx] Knowledge store failed: %s", e)


# ── Public API ───────────────────────────────────────────────────────────

async def omnyx_process(
    query: str,
    persona: str = "UTZ",
    *,
    debug: bool = False,
) -> dict:
    """Public entry point for OMNYX Direction.

    Returns dict compatible with /agent/chat_holistic response format.
    """
    director = OmnyxDirector()
    session = await director.process(query, persona, debug=debug)

    return {
        "answer": session.final_answer,
        "confidence": session.confidence,
        "sources_used": session.sources_used,
        "method": "omnyx_direction",
        "duration_ms": session.total_latency_ms,
        "n_turns": len(session.turns),
        "knowledge_stored": session.knowledge_stored,
        "persona": session.persona,
    }
