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
    "persona_fanout": 20.0,    # UX-fix 2026-04-30: 75→45 dengan model 1.5b lighter (Ollama CPU bottleneck)
    "tool_registry": 5.0,
}

# UX-fix 2026-04-30: VPS Ollama CPU bottleneck. Default fanout 3 persona (creative
# + engineer + community) BUKAN 5. User explicit pilih persona di dropdown =
# tambahan persona tunggal di synthesis.
PERSONAS_FULL = ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")
PERSONAS = ("UTZ", "ABOO", "AYMAN")  # Default fanout (3 = balance speed/diversity)
# Lighter model untuk persona ringkas (1.5B vs 7B = 5x faster di CPU)
PERSONA_FANOUT_MODEL = "qwen2.5:1.5b"


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
    """Multi-engine web search: SearxNG + Brave + Wikipedia — collect ALL, merge, dedup."""
    from .searxng_search import searxng_search_async
    from .brave_search import brave_search_async
    from .wiki_lookup import search_wikipedia

    tasks = {
        "searxng": asyncio.create_task(searxng_search_async(query, max_results=5)),
        "brave": asyncio.create_task(brave_search_async(query, max_results=5)),
        "wikipedia": asyncio.create_task(_wiki_async(query)),
    }
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    all_hits = []
    engines_used = []
    for (name, task), result in zip(tasks.items(), results):
        if isinstance(result, Exception):
            log.warning(f"[web_search] {name} failed: {result}")
            continue
        if result:
            engines_used.append(name)
            if isinstance(result, list):
                all_hits.extend(result)
            else:
                all_hits.append(result)

    # Deduplicate by URL
    seen_urls = set()
    deduped = []
    for h in all_hits:
        url = getattr(h, 'url', '')
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        deduped.append(h)

    # Fallback: Google AI Search if ALL engines failed/empty
    if not deduped:
        try:
            from .google_ai_search import google_ai_search_async
            g_hits = await google_ai_search_async(query, max_results=5)
            if g_hits:
                engines_used.append("google_ai")
                for h in g_hits:
                    url = getattr(h, 'url', '')
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        deduped.append(h)
        except Exception as exc:
            log.warning("[web_search] google_ai fallback failed: %s", exc)

    if not deduped:
        return {"output": "", "engines": []}

    lines = []
    for h in deduped[:8]:
        title = getattr(h, 'title', '')
        url = getattr(h, 'url', '')
        snippet = getattr(h, 'snippet', '')
        lines.append(f"- {title} ({url})\n  {snippet}")
    return {"output": "\n\n".join(lines), "engines": engines_used, "n_hits": len(deduped)}


async def _wiki_async(query: str):
    """Async wrapper for Wikipedia search."""
    from .wiki_lookup import search_wikipedia
    try:
        return await asyncio.to_thread(search_wikipedia, query, max_results=3)
    except Exception:
        return []




async def _src_google_ai_search(query: str) -> dict:
    """Gemini 2.0 Flash via google_ai_search module.
    
    Uses simplified prompt-based search (google_search_tool unsupported on this API key).
    Returns: structured hits compatible with web search output.
    """
    try:
        from .google_ai_search import google_ai_search_async
        hits = await google_ai_search_async(query, max_results=5)
        if not hits:
            return {"output": "", "note": "google_ai_no_results"}
        lines = []
        for h in hits[:5]:
            title = getattr(h, 'title', '')
            url = getattr(h, 'url', '')
            snippet = getattr(h, 'snippet', '')
            lines.append(f"- {title} ({url})\n  {snippet}")
        return {"output": "\n\n".join(lines), "engine": "google_ai_gemini", "n_hits": len(hits)}
    except Exception as e:
        log.warning("[google_ai_search] error: %s", e)
        return {"output": "", "note": f"error: {e}"}

async def _src_corpus_search(query: str) -> dict:
    """BM25 corpus search.

    Sprint Α bug fix: _tool_search_corpus returns ToolResult dataclass,
    bukan dict. Need attribute access not .get().
    Also returns raw_chunks for corpus passthrough (anti-hallucination).
    """
    try:
        from rank_bm25 import BM25Okapi
        from .query import _load_chunks, _load_tokens, default_index_dir
        from .text import tokenize

        index_dir = default_index_dir()
        chunks = _load_chunks(index_dir)
        tokens = _load_tokens(index_dir)
        if not chunks or len(tokens) != len(chunks):
            raise RuntimeError("Index corrupted")

        q_tokens = tokenize(query)
        bm25 = BM25Okapi(tokens)
        scores = bm25.get_scores(q_tokens)
        if not len(scores):
            raise RuntimeError("No scores")

        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:5]
        raw_chunks = []
        for idx in ranked:
            if scores[idx] <= 0.0:
                break
            c = chunks[idx]
            raw_chunks.append({
                "text": c.text,
                "source_path": c.source_path,
                "source_title": c.source_title,
                "sanad_tier": c.sanad_tier,
                "score": float(scores[idx]),
            })

        if raw_chunks:
            raw_text = "\n\n---\n\n".join(
                f"[source: {c['source_title']} | tier: {c['sanad_tier']}]\n{c['text']}"
                for c in raw_chunks
            )
            return {"results": raw_chunks, "raw_text": raw_text, "n_hits": len(raw_chunks)}
    except Exception as e:
        log.debug("[corpus_search] direct BM25 failed: %s", e)

    # Fallback: try search_corpus tool (returns ToolResult dataclass)
    try:
        from .agent_tools import _tool_search_corpus
        tool_result = await asyncio.to_thread(_tool_search_corpus, {"query": query, "k": 3})
        output_text = ""
        if hasattr(tool_result, "output"):
            output_text = str(tool_result.output or "")
        elif isinstance(tool_result, dict):
            output_text = str(tool_result.get("output", ""))
        else:
            output_text = str(tool_result)
        return {"output": output_text[:1500]}
    except Exception as e:
        return {"output": "", "note": f"corpus_error: {e}"}


async def _src_dense_index(query: str) -> dict:
    """Dense semantic search via embedding_loader."""
    try:
        from .dense_index import search_dense
        result = await asyncio.to_thread(search_dense, query, top_k=3)
        return {"results": result if result else []}
    except Exception as e:
        return {"results": [], "note": f"dense_unavailable: {type(e).__name__}"}


async def _src_persona_fanout(query: str, personas: tuple = PERSONAS) -> dict:
    """N-persona paralel ringkas via Ollama lokal (gratis CPU).

    UX-fix 2026-04-30: pakai qwen2.5:1.5b (1GB) bukan sidix-lora 7B (4.7GB).
    Default 3 persona (UTZ creative · ABOO engineer · AYMAN community) untuk
    balance speed/diversity. VPS CPU bottleneck handled.

    Setiap persona dapat 80-120 token ringkasan dari sudut pandangnya.
    """
    from .ollama_llm import ollama_available, ollama_generate
    from .cot_system_prompts import PERSONA_DESCRIPTIONS

    if not ollama_available():
        return {"results": {}, "note": "ollama_unavailable"}

    async def _one_persona(p: str) -> tuple[str, str]:
        desc = PERSONA_DESCRIPTIONS.get(p.upper(), "")
        system = (
            f"{desc}\n\n"
            f"Berikan SUDUT PANDANG SINGKAT (max 80 kata) dari perspektif {p} "
            f"untuk pertanyaan user. Fokus ke INSIGHT distinctive sesuai karakter persona, "
            f"bukan jawaban lengkap."
        )
        try:
            text, mode = await asyncio.to_thread(
                ollama_generate, query, system=system, max_tokens=80,
                temperature=0.7, model=PERSONA_FANOUT_MODEL,
            )
            return p, text or ""
        except Exception as e:
            return p, f"[ERROR: {type(e).__name__}]"

    # Paralel N persona via asyncio.gather
    results = await asyncio.gather(*[_one_persona(p) for p in personas])
    return {"results": dict(results), "n_persona": len(personas), "model": PERSONA_FANOUT_MODEL}


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
            tasks.append(("google_ai", _safe_call("google_ai",
                                            _src_google_ai_search(query),
                                            15.0)))
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
