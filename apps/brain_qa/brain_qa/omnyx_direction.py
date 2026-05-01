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
    # Sprint Speed Demon: complexity tracking
    complexity: str = "analytical"
    synth_model: str = "qwen2.5:7b"
    # Sprint A+B: Sanad + Hafidz
    sanad_score: float = 0.0
    sanad_verdict: str = ""
    hafidz_injected: bool = False
    hafidz_stored: bool = False


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

    # Sprint Speed Demon (2026-05-01): complexity-based routing
    # Maps intent → (complexity, n_persona, synthesis_model)
    COMPLEXITY_MAP = {
        "factual_who":        ("simple", 0, "qwen2.5:1.5b"),
        "factual_when":       ("simple", 0, "qwen2.5:1.5b"),
        "factual_where":      ("simple", 0, "qwen2.5:1.5b"),
        "factual_what":       ("simple", 0, "qwen2.5:1.5b"),
        "factual_how_many":   ("simple", 0, "qwen2.5:1.5b"),
        "calculation":        ("simple", 0, "qwen2.5:1.5b"),
        "coding":             ("creative", 1, "qwen2.5:7b"),
        "creative":           ("creative", 1, "qwen2.5:7b"),
        "comparison":         ("analytical", 3, "qwen2.5:7b"),
        "opinion":            ("analytical", 3, "qwen2.5:7b"),
        "general":            ("analytical", 3, "qwen2.5:7b"),
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

    @classmethod
    def classify_complexity(cls, query: str) -> tuple[str, list[str], str, int, str]:
        """Return (intent_type, tools, complexity, n_persona, synthesis_model).

        Sprint Speed Demon: detect complexity to skip persona_fanout
        for simple factual queries, reducing latency from 87s to ~5s.
        """
        intent, tools = cls.classify(query)
        complexity, n_persona, model = cls.COMPLEXITY_MAP.get(
            intent, ("analytical", 3, "qwen2.5:7b")
        )
        log.info("[omnyx] Complexity: %s | persona=%d | model=%s", complexity, n_persona, model)
        return intent, tools, complexity, n_persona, model


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
        from .multi_source_orchestrator import _src_web_search
        query = args.get("query", "")
        result = await _src_web_search(query, deep_fetch=True)
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
        """Process user query through OMNYX tool-calling loop.

        Sprint Speed Demon (2026-05-01): complexity-aware routing.
        Simple factual queries skip persona_fanout → latency 87s → ~5s.
        
        Sprint A+B (2026-05-01): Sanad validation + Hafidz memory injection.
        """
        import uuid
        t0 = time.monotonic()

        session = OmnyxSession(
            session_id=f"omnyx_{uuid.uuid4().hex[:8]}",
            query=query,
            persona=persona,
        )

        # Sprint Speed Demon: detect complexity early
        intent, recommended_tools, complexity, n_persona, synth_model = \
            IntentClassifier.classify_complexity(query)
        session.complexity = complexity  # attach for downstream use
        session.synth_model = synth_model

        log.info(
            "[omnyx] Session %s started: %r | complexity=%s persona=%d model=%s",
            session.session_id, query[:60], complexity, n_persona, synth_model,
        )

        # Sprint B: Pre-query Hafidz memory retrieval
        hafidz_context = None
        try:
            from .hafidz_injector import HafidzInjector, build_hafidz_prompt
            hafidz = HafidzInjector()
            hafidz_context = await hafidz.retrieve_context(query, persona, max_examples=2)
            if hafidz_context.golden_examples or hafidz_context.lesson_warnings:
                session.hafidz_injected = True
                log.info("[omnyx] Hafidz context injected: %d examples, %d warnings",
                         len(hafidz_context.golden_examples), len(hafidz_context.lesson_warnings))
        except Exception as e:
            log.warning("[omnyx] Hafidz retrieval failed: %s", e)

        # Turn 1: Intent classification + initial tool calls
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

        # Turn 2: Determine if more tools needed (complexity-aware)
        # Sprint Speed Demon: skip extra turns for simple queries
        if complexity != "simple" and len(session.turns) < self.max_turns:
            turn2 = await self._plan_next_turn(session, query, persona, complexity, n_persona)
            if turn2.tool_calls:
                results = await asyncio.gather(*[
                    self.executor.execute(call) for call in turn2.tool_calls
                ])
                turn2.tool_results = list(results)
                session.turns.append(turn2)

        # Synthesis: merge all tool results into final answer
        # Sprint B: inject Hafidz context into synthesis
        session.final_answer, session.confidence, session.sources_used = \
            await self._synthesize(session, query, persona, complexity, synth_model, hafidz_context)

        # Sprint A: Sanad validation post-synthesis
        try:
            from .sanad_orchestra import SanadOrchestra, get_threshold
            sanad = SanadOrchestra()
            
            # Build sources dict from session turns
            sources = {}
            tool_outputs = []
            tools_used = []
            for turn in session.turns:
                for r in turn.tool_results:
                    if r.success and r.output:
                        sources[r.tool_name] = r.output
                        tool_outputs.append(r.output)
                        tools_used.append(r.tool_name)
            
            sanad_result = await sanad.validate(
                answer=session.final_answer,
                query=query,
                sources=sources,
                persona=persona,
                tools_used=tools_used,
                tool_outputs=tool_outputs,
                complexity=complexity,
            )
            
            session.sanad_score = sanad_result.consensus_score
            session.sanad_verdict = sanad_result.verdict
            
            log.info("[omnyx] Sanad validation: score=%.2f verdict=%s",
                     sanad_result.consensus_score, sanad_result.verdict)
            
            # Sprint B: Store to Hafidz based on Sanad score
            try:
                from .hafidz_injector import HafidzInjector
                hafidz_store = HafidzInjector()
                threshold = get_threshold(complexity, tools_used)
                store_result = await hafidz_store.store_result(
                    query=query,
                    answer=session.final_answer,
                    persona=persona,
                    sanad_score=sanad_result.consensus_score,
                    threshold=threshold,
                    sources_used=session.sources_used,
                    tools_used=tools_used,
                    failure_context=sanad_result.failure_context or "",
                )
                session.hafidz_stored = store_result.get("stored", False)
                log.info("[omnyx] Hafidz stored: %s → %s", 
                         store_result.get("store", "unknown"), store_result.get("note_id", ""))
            except Exception as e:
                log.warning("[omnyx] Hafidz store failed: %s", e)
            
            # Sprint C: Pattern extraction from conversation
            try:
                from .pattern_extractor import maybe_extract_from_conversation
                maybe_extract_from_conversation(
                    user_message=query,
                    assistant_response=session.final_answer,
                    session_id=session.session_id,
                )
            except Exception as e:
                log.debug("[omnyx] Pattern extraction failed: %s", e)
            
            # If retry verdict, attempt one more synthesis with failure context
            if sanad_result.verdict == "retry" and sanad_result.failure_context:
                log.info("[omnyx] Sanad retry triggered with failure context")
                session.final_answer = await self._retry_synthesis(
                    session, query, persona, complexity, synth_model, 
                    sanad_result.failure_context, hafidz_context
                )
                # Re-validate after retry
                sanad_result2 = await sanad.validate(
                    answer=session.final_answer,
                    query=query,
                    sources=sources,
                    persona=persona,
                    tools_used=tools_used,
                    tool_outputs=tool_outputs,
                    complexity=complexity,
                )
                session.sanad_score = sanad_result2.consensus_score
                session.sanad_verdict = sanad_result2.verdict
                
        except Exception as e:
            log.warning("[omnyx] Sanad validation failed: %s", e)

        session.total_latency_ms = int((time.monotonic() - t0) * 1000)

        # Auto-store verified knowledge (legacy path)
        await self._auto_store(session)

        log.info(
            "[omnyx] Session %s complete: turns=%d, confidence=%s, sanad=%.2f/%s, latency=%dms",
            session.session_id, len(session.turns), session.confidence,
            session.sanad_score, session.sanad_verdict,
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
        """Format corpus primer answer."""
        from .cognitive_synthesizer import _strip_yaml_frontmatter
        raw_text = corpus_data.get("raw_text", corpus_data.get("output", ""))
        clean = _strip_yaml_frontmatter(raw_text)
        return clean.strip() + "\n\n(Sumber: corpus SIDIX, sanad tier: primer)"

    async def _plan_next_turn(
        self, session: OmnyxSession, query: str, persona: str,
        complexity: str = "analytical", n_persona: int = 3,
    ) -> TurnContext:
        """Plan additional tool calls based on previous results.

        Sprint Speed Demon: skip persona_brain for simple factual queries.
        """
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
            turn.tool_calls.append(ToolCall(
                tool_name="calculator",
                args={"expression": self._extract_expression(query)},
                call_id=f"t{turn.turn}_calc",
                turn=turn.turn,
            ))

        # Sprint Speed Demon: skip persona for simple queries
        if complexity != "simple" and n_persona > 0:
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
        self, session: OmnyxSession, query: str, persona: str,
        complexity: str = "analytical", synth_model: str = "qwen2.5:7b",
        hafidz_context=None,
    ) -> tuple[str, str, list[str]]:
        """Synthesize final answer from all tool results.

        Sprint Speed Demon: for simple factual queries, use lighter model
        or skip synthesis entirely if corpus passthrough already happened.
        
        Sprint B: inject Hafidz context (golden examples + lesson warnings)
        into synthesis prompt for improved quality.
        """
        from .cognitive_synthesizer import CognitiveSynthesizer
        from .multi_source_orchestrator import SourceBundle, SourceResult

        # Build SourceBundle from tool results
        bundle = SourceBundle(query=query)
        sources_used = []

        for turn in session.turns:
            for r in turn.tool_results:
                if not r.success or not r.output:
                    continue
                src = SourceResult(source=r.tool_name, success=True, data=r.output, latency_ms=r.latency_ms)
                if r.tool_name == "corpus_search":
                    bundle.corpus = src; sources_used.append("corpus")
                elif r.tool_name == "dense_search":
                    bundle.dense = src; sources_used.append("dense_index")
                elif r.tool_name in ("web_search", "google_ai_search"):
                    bundle.web = src; sources_used.append("web_search")
                elif r.tool_name == "persona_brain":
                    bundle.persona_fanout = src; sources_used.append("persona_fanout")

        # Sprint Speed Demon: simple factual → lighter synthesis or direct format
        if complexity == "simple":
            # Try corpus passthrough first
            from .cognitive_synthesizer import _try_corpus_passthrough
            direct = _try_corpus_passthrough(bundle)
            if direct:
                return direct, "tinggi", list(set(sources_used))
            # Try web direct answer
            if bundle.web and bundle.web.success and bundle.web.data:
                web_text = bundle.web.data.get("output", "")
                if web_text:
                    return web_text[:1200], "sedang", list(set(sources_used))

        # Sprint B: Build Hafidz injection if available
        hafidz_prompt = ""
        if hafidz_context:
            try:
                from .hafidz_injector import build_hafidz_prompt
                hafidz_prompt = build_hafidz_prompt(hafidz_context)
            except Exception as e:
                log.debug("[omnyx] Hafidz prompt build failed: %s", e)

        # Use cognitive synthesizer (with model hint if supported)
        synth = CognitiveSynthesizer()
        try:
            # If hafidz_prompt exists, we need to inject it into the synthesis
            if hafidz_prompt:
                result = await self._synthesize_with_hafidz(
                    synth, bundle, query, hafidz_prompt, synth_model
                )
            else:
                result = await synth.synthesize(bundle, model=synth_model)
        except TypeError:
            # Fallback: older synthesizer without model param
            result = await synth.synthesize(bundle)
        return result.answer, result.confidence, list(set(sources_used))
    
    async def _synthesize_with_hafidz(
        self, synth, bundle, query: str, hafidz_prompt: str, synth_model: str
    ):
        """Synthesize with Hafidz context injected into prompt."""
        import asyncio
        from .cognitive_synthesizer import _build_synthesis_prompt
        from .ollama_llm import ollama_generate
        
        system, user, sources_used = _build_synthesis_prompt(query, bundle)
        
        # Inject Hafidz context before the question
        injected_user = f"{hafidz_prompt}\n\n{user}"
        
        try:
            response, _mode = await asyncio.to_thread(
                ollama_generate,
                f"{system}\n\n{injected_user}",
                system="",
                model=synth_model,
                max_tokens=600,
                temperature=0.6,
            )
            from .cognitive_synthesizer import SynthesisResult
            return SynthesisResult(
                answer=response,
                confidence="sedang",
                sources_used=sources_used,
                n_sources=len(sources_used),
                latency_ms=0,
                method="llm_synthesis_hafidz",
            )
        except Exception as e:
            log.warning("[omnyx] Hafidz synthesis failed, fallback to standard: %s", e)
            return await synth.synthesize(bundle, model=synth_model)
    
    async def _retry_synthesis(
        self, session: OmnyxSession, query: str, persona: str,
        complexity: str, synth_model: str, failure_context: str,
        hafidz_context=None,
    ) -> str:
        """Retry synthesis with failure context from Sanad."""
        import asyncio
        from .ollama_llm import ollama_generate
        
        retry_prompt = f"""Jawaban sebelumnya gagal validasi Sanad.

Masalah yang ditemukan:
{failure_context}

Pertanyaan user: {query}

Silakan jawab ulang dengan memperbaiki masalah di atas. Pastikan setiap klaim faktual:
1. Didukung oleh sumber yang valid
2. Tidak mengandung halusinasi
3. Akurat dan dapat diverifikasi

Jawaban baru:"""
        
        try:
            response, _mode = await asyncio.to_thread(
                ollama_generate,
                retry_prompt,
                system="",
                model=synth_model,
                max_tokens=600,
                temperature=0.5,
            )
            return response
        except Exception as e:
            log.warning("[omnyx] Retry synthesis failed: %s", e)
            return session.final_answer  # return original if retry fails

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
        # Sprint Speed Demon: expose complexity for observability
        "complexity": session.complexity,
        "synth_model": session.synth_model,
        # Sprint A+B: expose Sanad + Hafidz metrics
        "sanad_score": session.sanad_score,
        "sanad_verdict": session.sanad_verdict,
        "hafidz_injected": session.hafidz_injected,
        "hafidz_stored": session.hafidz_stored,
    }


# ── Backward-compatible wrapper (used by agent_serve.py /agent/chat_holistic) ──

class OMNYXDirector:
    """Wrapper class with .run() method for compat with VPS endpoint."""

    async def run(self, query: str, persona: str = "UTZ") -> dict:
        return await omnyx_process(query, persona)
