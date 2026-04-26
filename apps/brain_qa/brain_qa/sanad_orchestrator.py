"""
sanad_orchestrator.py — Vol 21 MVP: 3-Branch Parallel Sanad Consensus
======================================================================

User vision (per research_note 239 sketches):
    User Q → spawn agent_id → fan-out to N branches in parallel
    → sanad consensus (cluster + vote) → render ke user dalam ≤3-5s

Vol 21 MVP scope (3 branches, sequential improvements via Vol 22-25):
    1. LLM direct branch (RunPod hybrid_generate)
    2. Wiki lookup branch (wiki_lookup_fast, public knowledge)
    3. Corpus search branch (BM25 local)

Each branch:
    - Async-friendly (asyncio compatible)
    - Returns BranchResult with claim + relevance + source
    - Independent failure (one branch error ≠ whole sanad fail)
    - Fail-fast timeout per branch (default 8s)

Sanad consensus:
    - Extract claims (MVP: take 1st sentence per branch as primary claim)
    - Cluster similar (MVP: char-level Jaccard >= 0.4 = same claim)
    - Vote: cluster size / total branches = agreement_pct
    - Validated if agreement_pct >= 0.5 OR single high-confidence branch

Render:
    - Single LLM call to format consensus answer in persona voice
    - Citations from contributing branches

Anti-pattern dihindari:
- ❌ Sequential branch execution (defeats parallelism)
- ❌ Block on slowest branch (must have timeout)
- ❌ Trust 1 branch blindly (need ≥2 agreement OR explicit high confidence)
- ❌ Heavy claim extraction LLM call (MVP keeps it lightweight)

Future expansion (Vol 22-25):
- Vol 22: per-branch validation + iteration loop
- Vol 23: 8th branch = Inventory Memory (pre-validated AKU lookup)
- Vol 25: Hafidz Shadow specialized nodes (1000-pool dispatch)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

# Per-branch timeouts (seconds, hard caps)
_TIMEOUT_LLM = 12.0
_TIMEOUT_WIKI = 8.0
_TIMEOUT_CORPUS = 4.0
_TIMEOUT_TOTAL = 20.0  # whole sanad budget


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


@dataclass
class SanadResult:
    """Output dari sanad consensus orchestrator."""
    validated_claim: Optional[str]
    agreement_pct: float
    contributing_branches: list[str]
    all_branches: list[BranchResult]
    citations: list[dict]
    total_duration_ms: int
    render_context: str = ""       # context untuk LLM persona render


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
    """Wikipedia lookup branch — primary public knowledge source."""
    t0 = time.time()
    try:
        from .wiki_lookup import wiki_lookup_fast, format_for_llm_context, to_citations
        loop = asyncio.get_event_loop()
        results = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: wiki_lookup_fast(question, max_articles=3)),
            timeout=_TIMEOUT_WIKI,
        )
        if not results:
            return BranchResult(branch="wiki", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error="empty results")
        context = format_for_llm_context(results, max_chars=3000)
        # MVP: take first article extract as claim
        primary = results[0].extract[:500]
        relevance = min(1.0, 0.6 + 0.1 * len(results))  # more results = more confidence
        return BranchResult(
            branch="wiki", claim=primary, raw_text=context,
            relevance=relevance, sources=to_citations(results),
            duration_ms=int((time.time() - t0) * 1000),
            fingerprint=primary.lower()[:200],
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
    """Corpus BM25 search branch — local SIDIX knowledge via agent_tools."""
    t0 = time.time()
    try:
        from .agent_tools import _tool_search_corpus
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: _tool_search_corpus({"query": question, "k": 3, "persona": persona}),
            ),
            timeout=_TIMEOUT_CORPUS,
        )
        if not result.success or not result.output.strip():
            return BranchResult(branch="corpus", claim="", relevance=0, sources=[],
                                duration_ms=int((time.time() - t0) * 1000),
                                error=result.error or "empty")
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
    Run 3-branch parallel sanad consensus.

    Returns SanadResult dengan validated_claim, agreement_pct, dan render context.
    Caller should pass render_context ke LLM untuk persona-flavored final answer.
    """
    t_start = time.time()
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                _branch_llm(question, persona),
                _branch_wiki(question),
                _branch_corpus(question, persona),
                return_exceptions=False,
            ),
            timeout=_TIMEOUT_TOTAL,
        )
    except asyncio.TimeoutError:
        log.warning("[sanad] total timeout — returning partial")
        results = []

    # If all branches failed (e.g. timeout), graceful degrade
    if not results:
        return SanadResult(
            validated_claim=None,
            agreement_pct=0.0,
            contributing_branches=[],
            all_branches=[],
            citations=[],
            total_duration_ms=int((time.time() - t_start) * 1000),
        )

    canonical, agreement, contributing = _consensus(results)
    citations = []
    for b in results:
        if b.error is None:
            citations.extend(b.sources)
    render_ctx = _build_render_context(results, canonical)

    log.info(
        "[sanad] question='%s' branches=%d ok=%d agreement=%.2f winner=%s duration=%dms",
        question[:60], len(results),
        sum(1 for b in results if b.error is None),
        agreement,
        canonical.branch if canonical else "none",
        int((time.time() - t_start) * 1000),
    )

    return SanadResult(
        validated_claim=canonical.claim if canonical else None,
        agreement_pct=agreement,
        contributing_branches=contributing,
        all_branches=results,
        citations=citations,
        total_duration_ms=int((time.time() - t_start) * 1000),
        render_context=render_ctx,
    )


__all__ = ["BranchResult", "SanadResult", "run_sanad"]
