"""
sanad_orchestrator.py — Unified Sanad Orkestra (v2)
====================================================

Founder Architecture Diagram LOCK (2026-04-30):
    INPUT → OTAK (Intent + Persona + Mode)
          ↔ Other Persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) — lensa berpikir
          ↔ Jurs 1000 Bayangan (5 branch paralel)
          → SANAD ORKESTRA (Sintesis → Validate → Relevan Score 9.5++)
          → OUTPUT

5 Branches (fan-out paralel):
    1. LLM direct (RunPod hybrid_generate)
    2. Wiki lookup (wiki_lookup_fast)
    3. Corpus search (BM25 + Sanad rerank)
    4. Dense index (BGE-M3 semantic embedding) — NEW v2
    5. Tool registry (heuristic match) — NEW v2
    6. Persona fanout (3-5 persona angle) — NEW v2

Key additions v2:
    - Persona-weighted query refinement (persona = lensa sejak awal)
    - Relevan Score 0-10 dengan threshold 9.5++
    - Loop balik kalau score < 9.5 (max 2 iterasi)
    - SanadResult expanded: relevan_score, iteration_count, sanad_tier, persona_used

Anti-pattern dihindari:
- ❌ Sequential branch execution
- ❌ Block on slowest branch
- ❌ Trust 1 branch blindly
- ❌ Persona hanya filter suara di akhir
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List

log = logging.getLogger(__name__)

# Per-branch timeouts (seconds, hard caps)
_TIMEOUT_LLM = 12.0
_TIMEOUT_WIKI = 8.0
_TIMEOUT_CORPUS = 4.0
_TIMEOUT_DENSE = 5.0
_TIMEOUT_TOOLS = 3.0
_TIMEOUT_FANOUT = 45.0
_TIMEOUT_TOTAL = 35.0  # raised for 5 branches + iter loop

# Vol 22: per-branch iteration config
_MAX_ITER = 2  # MVP: 1 retry on failure (total 2 attempts)
_MIN_RELEVANCE_FOR_ACCEPT = 0.3  # below this, retry with refined query

# ── Persona-weighted query lens (founder vision: persona = thinking lens) ─────
_PERSONA_QUERY_MODIFIER = {
    "UTZ":   "creative visual aesthetic trend inspiration",
    "ABOO":  "technical engineering implementation benchmark performance",
    "OOMAR": "strategy business ROI market competitor framework",
    "ALEY":  "academic paper citation methodology theoretical",
    "AYMAN": "community social sentiment user narrative general",
}

# ── Relevan Score 9.5++ weights (founder diagram LOCK) ────────────────────────
_RELEVAN_WEIGHT_AGREEMENT = 0.30
_RELEVAN_WEIGHT_SANAD_TIER = 0.25
_RELEVAN_WEIGHT_MAQASHID = 0.20
_RELEVAN_WEIGHT_CONFIDENCE = 0.15
_RELEVAN_WEIGHT_PERSONA_ALIGN = 0.10
_RELEVAN_THRESHOLD_LOLOS = 9.5
_RELEVAN_THRESHOLD_DISCLAIMER = 7.0
_MAX_SANAD_ITERATIONS = 2  # loop back max times


# ── Vol 22: Query refinement strategies (per branch type) ─────────────────────

_STOPWORDS_ID_EN = {
    "siapa", "apa", "kapan", "dimana", "bagaimana", "kenapa", "mengapa",
    "yang", "ini", "itu", "saja", "juga", "kah",
    "sekarang", "saat", "ini", "hari",
    "tolong", "mohon", "ya", "dong",
    "berapa", "manakah", "adakah",
    "who", "what", "when", "where", "why", "how", "which",
    "is", "are", "was", "were", "the", "a", "an",
    "now", "today", "currently", "current",
    "please", "tell", "me", "us",
    "explain", "jelaskan", "describe",
}


def _refine_query_simplify(query: str) -> str:
    """Strip stopwords + punctuation. Used for retry on web/wiki branches."""
    import re
    q = query.lower().strip().rstrip("?!.,;:")
    tokens = re.findall(r"\w+", q)
    keep = [t for t in tokens if t not in _STOPWORDS_ID_EN and len(t) >= 3]
    return " ".join(keep) if keep else q


def _refine_query_expand(query: str) -> str:
    """Add common synonyms for corpus retry."""
    additions = []
    ql = query.lower()
    if "ai" in ql or "kecerdasan" in ql:
        additions.append("artificial intelligence machine learning")
    if "fiqh" in ql or "hukum" in ql:
        additions.append("syariah mazhab")
    if "code" in ql or "coding" in ql or "python" in ql:
        additions.append("programming algorithm implementation")
    return query + " " + " ".join(additions) if additions else query


@dataclass
class BranchResult:
    """Output dari satu branch agent."""
    branch: str                    # "llm" / "wiki" / "corpus"
    claim: str                     # primary claim text (1-3 sentences)
    relevance: float               # [0, 1] — branch's self-confidence
    sources: list[dict]            # citations (url, title, snippet)
    raw_text: str = ""             # full branch output (for render fallback)
    duration_ms: int = 0
    error: Optional[str] = None    # set if branch failed
    fingerprint: str = ""          # for clustering (MVP: lowercase claim)
    iterations: int = 1            # Vol 22: how many tries this branch made
    refined_queries: list[str] = field(default_factory=list)  # query history per iter


@dataclass
class SanadResult:
    """Output dari sanad consensus orchestrator (expanded v2)."""
    validated_claim: Optional[str]
    agreement_pct: float
    contributing_branches: list[str]
    all_branches: list[BranchResult]
    citations: list[dict]
    total_duration_ms: int
    render_context: str = ""       # context untuk LLM persona render
    relevan_score: float = 0.0     # 0-10, founder threshold 9.5++
    iteration_count: int = 1       # berapa kali loop balik
    sanad_tier: str = ""           # primer | ulama | peer_review | aggregator
    persona_used: str = ""         # persona yang aktif sebagai lensa


# ── Branch implementations ──────────────────────────────────────────────────

async def _branch_llm(question: str, persona: str) -> BranchResult:
    """LLM direct branch: generate dari knowledge bobot LoRA + base."""
    t0 = time.time()
    try:
        from .runpod_serverless import hybrid_generate
        # Run sync hybrid_generate in thread (it's blocking httpx)
        loop = asyncio.get_event_loop()
        sys_prompt = (
            f"Kamu SIDIX persona {persona}. Jawab faktual berdasarkan pengetahuanmu. "
            "Singkat (max 2-3 kalimat). Kalau tidak yakin, sebutkan kemungkinan, "
            "bukan tebakan. Jangan tambah label epistemik."
        )
        text, mode = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: hybrid_generate(
                    prompt=question, system=sys_prompt,
                    max_tokens=200, temperature=0.4,
                ),
            ),
            timeout=_TIMEOUT_LLM,
        )
        # MVP relevance: high if text non-empty and not error string
        relevance = 0.7 if (text and "error" not in mode.lower()) else 0.0
        return BranchResult(
            branch="llm", claim=text or "", raw_text=text or "",
            relevance=relevance, sources=[],
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=(text or "").lower()[:200],
        )
    except asyncio.TimeoutError:
        return BranchResult(branch="llm", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error="timeout")
    except Exception as e:
        log.warning("[sanad] llm branch error: %s", e)
        return BranchResult(branch="llm", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error=str(e)[:200])


async def _branch_wiki(question: str) -> BranchResult:
    """Wikipedia lookup branch — Vol 22: with iteration on empty result."""
    t0 = time.time()
    queries_tried = []
    try:
        from .wiki_lookup import wiki_lookup_fast, format_for_llm_context, to_citations
        loop = asyncio.get_event_loop()
        results = []
        current_q = question
        for iter_num in range(1, _MAX_ITER + 1):
            queries_tried.append(current_q)
            try:
                results = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda q=current_q: wiki_lookup_fast(q, max_articles=3)),
                    timeout=_TIMEOUT_WIKI,
                )
                if results:
                    break  # got hits, exit iter loop
                # Empty: refine for next iter
                if iter_num < _MAX_ITER:
                    current_q = _refine_query_simplify(current_q)
                    if current_q == queries_tried[-1]:
                        break  # refinement no-op, give up
                    log.debug("[wiki] iter %d: refined '%s'", iter_num + 1, current_q[:60])
            except asyncio.TimeoutError:
                break

        if not results:
            return BranchResult(branch="wiki", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="empty results after iter",
                                iterations=len(queries_tried),
                                refined_queries=queries_tried)
        context = format_for_llm_context(results, max_chars=3000)
        primary = results[0].extract[:500]
        relevance = min(1.0, 0.6 + 0.1 * len(results))
        return BranchResult(
            branch="wiki", claim=primary, raw_text=context,
            relevance=relevance, sources=to_citations(results),
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=primary.lower()[:200],
            iterations=len(queries_tried),
            refined_queries=queries_tried,
        )
    except asyncio.TimeoutError:
        return BranchResult(branch="wiki", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error="timeout")
    except Exception as e:
        log.warning("[sanad] wiki branch error: %s", e)
        return BranchResult(branch="wiki", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error=str(e)[:200])


async def _branch_corpus(question: str, persona: str = "AYMAN") -> BranchResult:
    """Corpus BM25 search branch — Vol 22: with iteration on empty/low-rel."""
    t0 = time.time()
    queries_tried = []
    try:
        from .agent_tools import _tool_search_corpus
        loop = asyncio.get_event_loop()
        result = None
        current_q = question
        for iter_num in range(1, _MAX_ITER + 1):
            queries_tried.append(current_q)
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda q=current_q: _tool_search_corpus({"query": q, "k": 3, "persona": persona}),
                    ),
                    timeout=_TIMEOUT_CORPUS,
                )
                if result and result.success and result.output.strip():
                    break  # got result
                # Refine: expand query (synonym injection)
                if iter_num < _MAX_ITER:
                    current_q = _refine_query_expand(current_q)
                    if current_q == queries_tried[-1]:
                        break
                    log.debug("[corpus] iter %d: expanded '%s'", iter_num + 1, current_q[:60])
            except asyncio.TimeoutError:
                break

        if not result or not result.success or not result.output.strip():
            return BranchResult(branch="corpus", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error=(result.error if result else "no result") or "empty",
                                iterations=len(queries_tried),
                                refined_queries=queries_tried)
        # MVP: take output as claim (already formatted with snippets)
        primary = result.output[:1500]
        sources = [
            {"type": "corpus", "title": c.get("source_title", "?"),
             "url": c.get("source_path", ""),
             "snippet": c.get("snippet", "")[:200]}
            for c in (result.citations or [])[:3]
        ]
        # Relevance: presence of citations + content length proxy
        relevance = min(1.0, 0.5 + 0.1 * len(sources))
        return BranchResult(
            branch="corpus", claim=primary, raw_text=primary,
            relevance=relevance, sources=sources,
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=primary.lower()[:200],
            iterations=len(queries_tried),
            refined_queries=queries_tried,
        )
    except asyncio.TimeoutError:
        return BranchResult(branch="corpus", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error="timeout")
    except Exception as e:
        log.warning("[sanad] corpus branch error: %s", e)
        return BranchResult(branch="corpus", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error=str(e)[:200])


# ── NEW BRANCHES (Vol 23+ expansion per founder architecture diagram) ───────

async def _branch_dense(question: str, persona: str = "AYMAN") -> BranchResult:
    """Dense semantic search branch — BGE-M3 embedding similarity."""
    t0 = time.time()
    try:
        from .dense_index import load_dense_index, dense_search
        from .indexer import INDEX_DIR
        from .embedding_loader import load_embed_fn
        index_dir = Path(INDEX_DIR) if INDEX_DIR else Path(".data/index")
        loaded = load_dense_index(index_dir)
        if loaded is None:
            return BranchResult(branch="dense", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="dense index not built")
        matrix, meta = loaded
        embed_fn = load_embed_fn()
        if embed_fn is None:
            return BranchResult(branch="dense", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="embed_fn unavailable")
        results = dense_search(question, matrix, embed_fn=embed_fn, top_k=5)
        if not results:
            return BranchResult(branch="dense", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="no dense matches")
        # Build claim from top-3 matches
        top_idxs = [idx for idx, _ in results[:3]]
        # Load chunk texts via indexer metadata
        chunk_meta_path = index_dir / "chunk_meta.json"
        snippets = []
        sources = []
        if chunk_meta_path.exists():
            import json
            chunk_meta = json.loads(chunk_meta_path.read_text(encoding="utf-8"))
            for idx in top_idxs:
                if 0 <= idx < len(chunk_meta):
                    cm = chunk_meta[idx]
                    snippets.append(cm.get("text", "")[:300])
                    sources.append({
                        "type": "dense",
                        "title": cm.get("source_title", "dense-corpus"),
                        "url": cm.get("source_path", ""),
                        "snippet": cm.get("text", "")[:200],
                    })
        claim = " ".join(snippets)[:800] if snippets else ""
        avg_score = sum(s for _, s in results[:3]) / 3 if results else 0
        relevance = min(1.0, avg_score + 0.2)  # boost slightly for dense
        return BranchResult(
            branch="dense", claim=claim, raw_text=claim,
            relevance=relevance, sources=sources,
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=claim.lower()[:200],
        )
    except Exception as e:
        log.warning("[sanad] dense branch error: %s", e)
        return BranchResult(branch="dense", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error=str(e)[:200])


async def _branch_tools(question: str) -> BranchResult:
    """Tool registry heuristic branch — match query ke available tools."""
    t0 = time.time()
    try:
        from .agent_tools import list_available_tools
        tools = list_available_tools()
        if not tools:
            return BranchResult(branch="tools", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="no tools registered")
        # Simple keyword overlap heuristic
        q_lower = question.lower()
        matches = []
        for t in tools:
            name = t.get("name", "").lower()
            desc = t.get("description", "").lower()
            score = 0
            if any(tok in name for tok in q_lower.split()):
                score += 0.5
            if any(tok in desc for tok in q_lower.split()):
                score += 0.3
            if score > 0:
                matches.append({"name": t.get("name"), "score": score, "desc": t.get("description", "")})
        matches.sort(key=lambda x: x["score"], reverse=True)
        top = matches[:3]
        if not top:
            return BranchResult(branch="tools", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="no tool match")
        claim_lines = [f"Tool '{m['name']}' tersedia: {m['desc'][:100]}" for m in top]
        claim = "; ".join(claim_lines)
        sources = [{"type": "tool", "title": m["name"], "url": "", "snippet": m["desc"]} for m in top]
        return BranchResult(
            branch="tools", claim=claim, raw_text=claim,
            relevance=min(1.0, top[0]["score"] + 0.2), sources=sources,
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=claim.lower()[:200],
        )
    except Exception as e:
        log.warning("[sanad] tools branch error: %s", e)
        return BranchResult(branch="tools", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error=str(e)[:200])


async def _branch_persona_fanout(question: str, persona: str = "AYMAN") -> BranchResult:
    """Persona fanout branch — 3-5 persona mikir paralel untuk multi-perspective.
    Phase 1: stub returns perspective hint only.
    Phase 2: wire ke persona_research_fanout.gather()."""
    t0 = time.time()
    try:
        # Phase 1: lightweight — persona lensa sebagai tambahan sudut pandang
        from .persona_router import normalize_persona
        all_personas = ["UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"]
        target = normalize_persona(persona)
        # Exclude target persona (sudah di-cover oleh branch LLM utama)
        others = [p for p in all_personas if p != target]
        perspectives = []
        for p in others[:3]:  # max 3 additional angles
            angle = _PERSONA_QUERY_MODIFIER.get(p, "")
            perspectives.append(f"[{p}] Lihat dari sudut: {angle}")
        claim = "; ".join(perspectives)
        return BranchResult(
            branch="persona_fanout", claim=claim, raw_text=claim,
            relevance=0.6, sources=[],
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=claim.lower()[:200],
        )
    except Exception as e:
        log.warning("[sanad] persona_fanout branch error: %s", e)
        return BranchResult(branch="persona_fanout", claim="", relevance=0, sources=[],
                            duration_ms=int((time.time() - t0) * 1000),
                            error=str(e)[:200])


# ── Persona-weighted query refinement (founder: persona = lensa berpikir) ────

def _persona_weighted_query(question: str, persona: str) -> str:
    """Tambah persona lensa ke query sebelum fan-out.
    UTZ cari visual/aesthetic, ALEY cari paper/citation, dll."""
    modifier = _PERSONA_QUERY_MODIFIER.get(persona, "")
    if not modifier:
        return question
    # Hanya inject kalau query belum mengandung kata kunci persona
    q_lower = question.lower()
    mod_tokens = set(modifier.split())
    if any(tok in q_lower for tok in mod_tokens):
        return question
    return f"{question} ({modifier})"


# ── Relevan Score 9.5++ (founder architecture diagram LOCK) ───────────────────

def _calculate_relevan_score(
    agreement_pct: float,
    sanad_tier: str,
    maqashid_score: float,
    confidence_idx: float,
    persona_align: float,
) -> float:
    """Hitung relevan score 0-10 berdasarkan formula founder.
    Threshold: >= 9.5 lolos, 7.0-9.4 disclaimer, < 7.0 loop balik."""
    tier_map = {"primer": 1.0, "ulama": 0.8, "peer_review": 0.6, "aggregator": 0.4, "unknown": 0.3, "": 0.3}
    tier_score = tier_map.get(sanad_tier, 0.3)
    raw = (
        agreement_pct * _RELEVAN_WEIGHT_AGREEMENT +
        tier_score * _RELEVAN_WEIGHT_SANAD_TIER +
        maqashid_score * _RELEVAN_WEIGHT_MAQASHID +
        confidence_idx * _RELEVAN_WEIGHT_CONFIDENCE +
        persona_align * _RELEVAN_WEIGHT_PERSONA_ALIGN
    )
    return round(raw * 10, 2)


# ── Sanad consensus ──────────────────────────────────────────────────────────

def _jaccard(a: str, b: str) -> float:
    """Char n-gram Jaccard similarity (cheap, no embedding needed)."""
    if not a or not b:
        return 0.0
    set_a = set(a[i:i+4] for i in range(len(a) - 3))
    set_b = set(b[i:i+4] for i in range(len(b) - 3))
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _consensus(branches: list[BranchResult]) -> tuple[Optional[BranchResult], float, list[str]]:
    """
    MVP consensus: cluster branches by similarity, return cluster with most votes.
    Returns (canonical_result, agreement_pct, list_of_contributing_branch_names).
    """
    valid = [b for b in branches if b.error is None and b.claim]
    if not valid:
        return None, 0.0, []

    # Greedy clustering (MVP, O(N²) but N=3-8 so cheap)
    clusters: list[list[BranchResult]] = []
    for b in valid:
        placed = False
        for cluster in clusters:
            if _jaccard(b.fingerprint, cluster[0].fingerprint) >= 0.3:
                cluster.append(b)
                placed = True
                break
        if not placed:
            clusters.append([b])

    # Largest cluster wins
    clusters.sort(key=lambda c: (len(c), max(b.relevance for b in c)), reverse=True)
    winner = clusters[0]
    canonical = max(winner, key=lambda b: b.relevance)
    agreement = len(winner) / len(valid)
    contributing = [b.branch for b in winner]
    return canonical, agreement, contributing


def _build_render_context(branches: list[BranchResult], canonical: Optional[BranchResult]) -> str:
    """Build LLM render context dengan multi-source evidence."""
    chunks = []
    if canonical and canonical.raw_text:
        chunks.append(f"[Konsensus utama dari {canonical.branch}]\n{canonical.raw_text[:2000]}")
    for b in branches:
        if b.branch == (canonical.branch if canonical else None):
            continue
        if b.error or not b.claim:
            continue
        chunks.append(f"[Cross-check dari {b.branch}]\n{b.claim[:1500]}")
    return "\n\n".join(chunks)


# ── Main orchestrator ────────────────────────────────────────────────────────

async def run_sanad(question: str, persona: str = "AYMAN") -> SanadResult:
    """
    Run 5-branch parallel sanad consensus dengan persona-weighted query
    dan relevan score 9.5++ (founder architecture diagram LOCK).

    Flow:
      1. Persona-weighted query refinement
      2. Fan-out 5 branches paralel
      3. Sanad consensus (Jaccard + vote)
      4. Relevan Score 9.5++
      5. Kalau < 9.5 → loop balik refine query (max 2 iterasi)
      6. Return SanadResult dengan score + iteration_count
    """
    t_start = time.time()
    iteration = 1
    current_q = _persona_weighted_query(question, persona)

    while iteration <= _MAX_SANAD_ITERATIONS:
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    _branch_llm(current_q, persona),
                    _branch_wiki(current_q),
                    _branch_corpus(current_q, persona),
                    _branch_dense(current_q, persona),
                    _branch_tools(current_q),
                    _branch_persona_fanout(current_q, persona),
                    return_exceptions=False,
                ),
                timeout=_TIMEOUT_TOTAL,
            )
        except asyncio.TimeoutError:
            log.warning("[sanad] total timeout iter=%d — returning partial", iteration)
            results = []

        if not results:
            return SanadResult(
                validated_claim=None,
                agreement_pct=0.0,
                contributing_branches=[],
                all_branches=[],
                citations=[],
                total_duration_ms=int((time.time() - t_start) * 1000),
                relevan_score=0.0,
                iteration_count=iteration,
                persona_used=persona,
            )

        canonical, agreement, contributing = _consensus(results)
        citations = []
        for b in results:
            if b.error is None:
                citations.extend(b.sources)
        render_ctx = _build_render_context(results, canonical)

        # Determine sanad tier from contributing branches
        tier_priority = ["primer", "ulama", "peer_review", "aggregator", "unknown"]
        detected_tier = "unknown"
        for t in tier_priority:
            if any(t in (s.get("type", "") or s.get("title", "")).lower() for s in citations):
                detected_tier = t
                break

        # Calculate relevan score
        confidence_idx = max((b.relevance for b in results if b.error is None), default=0.0)
        persona_align = 0.8 if persona in contributing else 0.5  # simplistic
        # Maqashid placeholder (integrate real maqashid_evaluator when wired)
        maqashid_score = 0.9  # default safe until real eval wired
        relevan = _calculate_relevan_score(
            agreement_pct=agreement,
            sanad_tier=detected_tier,
            maqashid_score=maqashid_score,
            confidence_idx=confidence_idx,
            persona_align=persona_align,
        )

        log.info(
            "[sanad] iter=%d question='%s' branches=%d ok=%d agreement=%.2f relevan=%.2f winner=%s duration=%dms",
            iteration, question[:60], len(results),
            sum(1 for b in results if b.error is None),
            agreement, relevan,
            canonical.branch if canonical else "none",
            int((time.time() - t_start) * 1000),
        )

        # Founder threshold: >= 9.5 lolos, < 7.0 loop balik, 7.0-9.4 disclaimer
        if relevan >= _RELEVAN_THRESHOLD_LOLOS or iteration >= _MAX_SANAD_ITERATIONS:
            return SanadResult(
                validated_claim=canonical.claim if canonical else None,
                agreement_pct=agreement,
                contributing_branches=contributing,
                all_branches=results,
                citations=citations,
                total_duration_ms=int((time.time() - t_start) * 1000),
                render_context=render_ctx,
                relevan_score=relevan,
                iteration_count=iteration,
                sanad_tier=detected_tier,
                persona_used=persona,
            )

        # Loop balik: refine query dengan persona lensa + synonym expand
        iteration += 1
        current_q = _refine_query_expand(_persona_weighted_query(question, persona))
        log.info("[sanad] relevan %.2f < %.1f — loop balik iter=%d, refined_q='%s'",
                 relevan, _RELEVAN_THRESHOLD_LOLOS, iteration, current_q[:60])

    # Fallback (should not reach here due to loop condition, but defensive)
    return SanadResult(
        validated_claim=canonical.claim if canonical else None,
        agreement_pct=agreement,
        contributing_branches=contributing,
        all_branches=results,
        citations=citations,
        total_duration_ms=int((time.time() - t_start) * 1000),
        render_context=render_ctx,
        relevan_score=relevan,
        iteration_count=iteration,
        sanad_tier=detected_tier,
        persona_used=persona,
    )


__all__ = ["BranchResult", "SanadResult", "run_sanad"]
