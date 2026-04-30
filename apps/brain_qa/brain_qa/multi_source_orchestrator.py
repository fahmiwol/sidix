"""
multi_source_orchestrator.py — Sprint Α (Jurus Seribu Bayangan)

Orchestrator yang mengerahkan SEMUA resource SIDIX paralel (per visi bos
2026-04-30 evening). REPLACE pattern lama "routing otomatis pilih 1 sumber"
dengan multi-source paralel default.

Sources yang di-fan-out simultan:
  1. web_search    — DuckDuckGo + Wikipedia (~5-15s)
  2. corpus_search — BM25 lokal corpus (<1s)
  3. dense_index   — semantic embedding search (<1s)
  4. persona_fanout — 5 persona ringkas via Ollama lokal (parallel ~30s)
  5. tool_registry  — relevant tools auto-detect (<1s)
  6. (future) external_apis — HF, public APIs

Pattern: asyncio.gather dengan return_exceptions=True. Kalau 1 source fail,
lainnya tetap proceed → stability built-in (Sprint 0 embedded).

Output: SourceBundle dataclass dengan semua hasil + errors per source.
Kemudian di-pass ke cognitive_synthesizer untuk merge jadi 1 jawaban utuh.

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT (see repo LICENSE)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger("sidix.multi_source")

# Per-source timeout (detik) — kalau exceed, source skipped, lainnya proceed
DEFAULT_TIMEOUTS = {
    "web_search": 25.0,        # Sprint Α bug fix: 15→25 (DDG sometimes slow)
    "corpus_search": 5.0,
    "dense_index": 5.0,
    "persona_fanout": 75.0,    # Sprint Α bug fix: 45→75 (5 persona Ollama paralel exceed 45s)
    "tool_registry": 5.0,
}

PERSONAS = ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")


@dataclass
class SourceResult:
    """Hasil dari 1 source dengan metadata + error tracking."""
    source: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    latency_ms: int = 0


@dataclass
class SourceBundle:
    """Bundle dari semua source — input ke cognitive_synthesizer."""
    query: str
    web: Optional[SourceResult] = None
    corpus: Optional[SourceResult] = None
    dense: Optional[SourceResult] = None
    persona_fanout: Optional[SourceResult] = None  # data = dict[persona -> ringkasan]
    tools: Optional[SourceResult] = None  # data = list of tool_id yang relevan
    total_latency_ms: int = 0
    errors: list[str] = field(default_factory=list)

    def successful_sources(self) -> list[SourceResult]:
        """Return source yang berhasil (untuk synthesis)."""
        return [s for s in (self.web, self.corpus, self.dense,
                            self.persona_fanout, self.tools)
                if s is not None and s.success]

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "web": _result_to_dict(self.web),
            "corpus": _result_to_dict(self.corpus),
            "dense": _result_to_dict(self.dense),
            "persona_fanout": _result_to_dict(self.persona_fanout),
            "tools": _result_to_dict(self.tools),
            "total_latency_ms": self.total_latency_ms,
            "errors": self.errors,
            "n_successful": len(self.successful_sources()),
        }


def _result_to_dict(r: Optional[SourceResult]) -> Optional[dict]:
    if r is None:
        return None
    return {
        "source": r.source,
        "success": r.success,
        "latency_ms": r.latency_ms,
        "error": r.error,
        # data not always serializable — caller handle truncation
        "data_preview": str(r.data)[:200] if r.data else None,
    }


async def _safe_call(source_name: str, coro, timeout: float) -> SourceResult:
    """Wrap call dengan timeout + error capture. Tidak crash kalau fail."""
    t0 = time.monotonic()
    try:
        data = await asyncio.wait_for(coro, timeout=timeout)
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return SourceResult(source=source_name, success=True, data=data, latency_ms=elapsed_ms)
    except asyncio.TimeoutError:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        log.warning(f"[orchestrator] {source_name} timeout after {timeout}s")
        return SourceResult(source=source_name, success=False,
                            error=f"timeout_{int(timeout)}s", latency_ms=elapsed_ms)
    except Exception as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        log.warning(f"[orchestrator] {source_name} fail: {type(e).__name__}: {e}")
        return SourceResult(source=source_name, success=False,
                            error=f"{type(e).__name__}: {str(e)[:100]}",
                            latency_ms=elapsed_ms)


# ── Source adapter wrappers ─────────────────────────────────────────────
# Wrap existing sync code jadi async via asyncio.to_thread.

async def _src_web_search(query: str) -> dict:
    """Wrap web_search tool (DuckDuckGo + Wikipedia fallback)."""
    from .agent_tools import _tool_web_search
    result = await asyncio.to_thread(_tool_web_search, {"query": query, "max_results": 5})
    return {"output": result.get("output", "")[:2000], "raw": result}


async def _src_corpus_search(query: str) -> dict:
    """BM25 corpus search.

    Sprint Α bug fix: _tool_search_corpus returns ToolResult dataclass,
    bukan dict. Need attribute access not .get().
    """
    try:
        from .corpus_search import search as corpus_search
        result = await asyncio.to_thread(corpus_search, query, top_k=3)
        return {"results": result[:3] if result else []}
    except Exception:
        # Fallback: try search_corpus tool (returns ToolResult dataclass)
        from .agent_tools import _tool_search_corpus
        tool_result = await asyncio.to_thread(_tool_search_corpus, {"query": query, "k": 3})
        # ToolResult might be dataclass with .output attr, or dict from older code
        output_text = ""
        if hasattr(tool_result, "output"):
            output_text = str(tool_result.output or "")
        elif isinstance(tool_result, dict):
            output_text = str(tool_result.get("output", ""))
        else:
            output_text = str(tool_result)
        return {"output": output_text[:1500]}


async def _src_dense_index(query: str) -> dict:
    """Dense semantic search via embedding_loader."""
    try:
        from .dense_index import search_dense
        result = await asyncio.to_thread(search_dense, query, top_k=3)
        return {"results": result if result else []}
    except Exception as e:
        return {"results": [], "note": f"dense_unavailable: {type(e).__name__}"}


async def _src_persona_fanout(query: str, personas: tuple = PERSONAS) -> dict:
    """5-persona paralel ringkas via Ollama lokal (gratis CPU).

    Setiap persona dapat 80-150 token ringkasan dari sudut pandangnya.
    Synthesis bertanggung jawab merge jadi full answer.
    """
    from .ollama_llm import ollama_available, ollama_generate
    from .cot_system_prompts import PERSONA_DESCRIPTIONS

    if not ollama_available():
        return {"results": {}, "note": "ollama_unavailable"}

    async def _one_persona(p: str) -> tuple[str, str]:
        desc = PERSONA_DESCRIPTIONS.get(p.upper(), "")
        system = (
            f"{desc}\n\n"
            f"Berikan SUDUT PANDANG SINGKAT (max 100 kata) dari perspektif {p} "
            f"untuk pertanyaan user. Fokus ke INSIGHT distinctive sesuai karakter persona, "
            f"bukan jawaban lengkap."
        )
        try:
            text, mode = await asyncio.to_thread(
                ollama_generate, query, system=system, max_tokens=150, temperature=0.7
            )
            return p, text or ""
        except Exception as e:
            return p, f"[ERROR: {type(e).__name__}]"

    # Paralel 5 persona via asyncio.gather
    results = await asyncio.gather(*[_one_persona(p) for p in personas])
    return {"results": dict(results), "n_persona": len(personas)}


async def _src_tool_registry(query: str) -> dict:
    """Heuristic match query ke tool descriptions yang relevan.

    Phase 1 (sekarang): keyword match sederhana.
    Phase 2 (future): cosine similarity dense embedding tool descriptions.
    """
    # Keyword heuristics (low-cost, no LLM)
    q_lower = query.lower()
    relevant: list[str] = []

    if any(t in q_lower for t in ("gambar", "image", "buat foto", "design visual")):
        relevant.append("image_gen")
    if any(t in q_lower for t in ("hitung", "calculate", "berapa")):
        relevant.append("calculator")
    if any(t in q_lower for t in ("kode", "code", "fungsi", "function", "script")):
        relevant.append("code_sandbox")
    if any(t in q_lower for t in ("pdf", "ekstrak dari pdf")):
        relevant.append("pdf_extract")

    return {"relevant_tools": relevant, "n": len(relevant)}


# ── Main orchestrator ───────────────────────────────────────────────────

class MultiSourceOrchestrator:
    """Mengerahkan semua resource SIDIX paralel — jurus seribu bayangan."""

    def __init__(self, timeouts: Optional[dict] = None):
        self.timeouts = {**DEFAULT_TIMEOUTS, **(timeouts or {})}

    async def gather_all(
        self,
        query: str,
        *,
        enable_web: bool = True,
        enable_corpus: bool = True,
        enable_dense: bool = True,
        enable_persona_fanout: bool = True,
        enable_tools: bool = True,
        personas: tuple = PERSONAS,
    ) -> SourceBundle:
        """Fan-out paralel ke semua source. Return SourceBundle."""
        t0 = time.monotonic()
        bundle = SourceBundle(query=query)

        tasks = []
        if enable_web:
            tasks.append(("web", _safe_call("web_search",
                                            _src_web_search(query),
                                            self.timeouts["web_search"])))
        if enable_corpus:
            tasks.append(("corpus", _safe_call("corpus_search",
                                               _src_corpus_search(query),
                                               self.timeouts["corpus_search"])))
        if enable_dense:
            tasks.append(("dense", _safe_call("dense_index",
                                              _src_dense_index(query),
                                              self.timeouts["dense_index"])))
        if enable_persona_fanout:
            tasks.append(("persona_fanout", _safe_call("persona_fanout",
                                                       _src_persona_fanout(query, personas),
                                                       self.timeouts["persona_fanout"])))
        if enable_tools:
            tasks.append(("tools", _safe_call("tool_registry",
                                              _src_tool_registry(query),
                                              self.timeouts["tool_registry"])))

        # Paralel execute — return_exceptions=False because _safe_call already wraps
        labels, coros = zip(*tasks) if tasks else ((), ())
        results = await asyncio.gather(*coros)

        for label, result in zip(labels, results):
            setattr(bundle, label, result)
            if not result.success:
                bundle.errors.append(f"{label}: {result.error}")

        bundle.total_latency_ms = int((time.monotonic() - t0) * 1000)

        log.info(
            f"[orchestrator] query='{query[:60]!r}' total={bundle.total_latency_ms}ms "
            f"successful={len(bundle.successful_sources())}/{len(tasks)} "
            f"errors={len(bundle.errors)}"
        )
        return bundle


__all__ = [
    "MultiSourceOrchestrator",
    "SourceBundle",
    "SourceResult",
    "PERSONAS",
]
