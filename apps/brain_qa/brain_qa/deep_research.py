"""
deep_research.py — SIDIX Deep Research Recursive Engine
=========================================================

Mode DEEP_RESEARCH implementation for ModeRouter.
Recursive multi-source research: corpus → web → follow-up → synthesis report.

Process:
  1. Initial search (corpus + web) for query
  2. Extract key findings and identify knowledge gaps
  3. Generate follow-up sub-queries for gaps
  4. Recursive search (up to max_iterations)
  5. Synthesize structured report with citations

Integration:
  - mode_router.py: DEEP_RESEARCH config references this module
  - mcp_server_wrap.py: exposed as sidix_deep_research tool
  - agent_serve.py: chat_holistic DEEP path can call this directly

Author: Kimi | Date: 2026-05-07
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class ResearchFinding:
    source: str          # "corpus:<filename>" | "web:<url>" | "pdf:<path>"
    snippet: str         # relevant text excerpt
    confidence: float    # 0.0-1.0
    topic: str           # sub-topic this finding addresses


@dataclass
class ResearchReport:
    query: str
    findings: list[ResearchFinding] = field(default_factory=list)
    sub_queries: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    synthesis: str = ""
    citations: list[dict] = field(default_factory=list)
    duration_ms: int = 0
    iterations: int = 0


# ── Recursive Research Engine ─────────────────────────────────────────────────

_MAX_CHARS_PER_SOURCE = 4000
_MAX_FINDINGS_PER_ITER = 8
_MAX_SUB_QUERIES = 3


def _search_corpus(query: str, k: int = 5) -> list[dict]:
    """BM25 search corpus. Returns list of {source, snippet, score}."""
    try:
        from .agent_tools import call_tool
        result = call_tool(
            tool_name="search_corpus",
            args={"query": query, "k": k},
            session_id=f"deep_research_{int(time.time())}",
            step=1,
        )
        if not result.success:
            return []
        # Parse output — search_corpus returns markdown-like text
        lines = result.output.split("\n")
        findings = []
        current = {}
        for line in lines:
            if line.startswith("Source: "):
                if current:
                    findings.append(current)
                current = {"source": f"corpus:{line[8:].strip()}", "snippet": "", "score": 0.5}
            elif line.startswith("Score: ") and current:
                try:
                    current["score"] = float(line[7:].strip())
                except ValueError:
                    pass
            elif current and line.strip() and not line.startswith("---"):
                current["snippet"] += line + "\n"
        if current:
            findings.append(current)
        return findings[:k]
    except Exception as e:
        log.warning("[deep_research] corpus search failed: %s", e)
        return []


def _search_web(query: str, max_results: int = 5) -> list[dict]:
    """Web search via DuckDuckGo. Returns list of {source, snippet, score}."""
    try:
        from .agent_tools import call_tool
        result = call_tool(
            tool_name="web_search",
            args={"query": query, "max_results": max_results},
            session_id=f"deep_research_{int(time.time())}",
            step=1,
        )
        if not result.success:
            return []
        # Parse web_search output — returns markdown list
        findings = []
        lines = result.output.split("\n")
        for line in lines:
            m = re.match(r"\d+\.\s+\[(.+?)\]\((.+?)\)\s*[-:]\s*(.+)", line)
            if m:
                title, url, snippet = m.groups()
                findings.append({
                    "source": f"web:{url}",
                    "snippet": f"{title}\n{snippet}",
                    "score": 0.6,
                })
        return findings[:max_results]
    except Exception as e:
        log.warning("[deep_research] web search failed: %s", e)
        return []


def _extract_key_findings(text: str, topic: str, source: str) -> list[ResearchFinding]:
    """Extract bullet-point findings from source text."""
    findings = []
    # Simple extraction: split by sentences, keep substantive ones
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sent in sentences[:_MAX_FINDINGS_PER_ITER]:
        sent = sent.strip()
        if len(sent) < 20:
            continue
        # Skip meta/social sentences
        if re.match(r"^(login|sign up|subscribe|follow|share|comment|advertisement)", sent, re.I):
            continue
        findings.append(ResearchFinding(
            source=source,
            snippet=sent[:500],
            confidence=0.6,
            topic=topic,
        ))
    return findings


def _generate_followup_queries(findings: list[ResearchFinding], original_query: str) -> list[str]:
    """Generate sub-queries based on knowledge gaps."""
    if not findings:
        return [f"{original_query} overview"]

    # Extract topics covered
    topics_covered = set(f.topic for f in findings)
    all_snippets = " ".join(f.snippet for f in findings)

    # Heuristic gap detection: look for question words in snippets that suggest missing info
    gaps = []
    if "belum jelas" in all_snippets.lower() or "belum diketahui" in all_snippets.lower():
        gaps.append("faktor yang belum diketahui")
    if len(findings) < 3:
        gaps.append("aspek tambahan")

    # Generate sub-queries
    sub_queries = []
    base = original_query.strip().rstrip("?!")

    if "timeline" not in all_snippets.lower() and "sejarah" not in all_snippets.lower():
        sub_queries.append(f"{base} timeline sejarah perkembangan")
    if "contoh" not in all_snippets.lower() and "case study" not in all_snippets.lower():
        sub_queries.append(f"{base} contoh kasus studi konkret")
    if "pro kontra" not in all_snippets.lower() and "kelebihan kekurangan" not in all_snippets.lower():
        sub_queries.append(f"{base} kelebihan kekurangan analisis kritik")

    # Fallback: just expand query
    if len(sub_queries) < 2:
        sub_queries.append(f"{base} penelitian terbaru 2025 2026")
        sub_queries.append(f"{base} pandangan berbeda perspektif alternatif")

    return sub_queries[:_MAX_SUB_QUERIES]


def _synthesize_report(query: str, findings: list[ResearchFinding], iterations: int, duration_ms: int) -> ResearchReport:
    """Synthesize final report from all findings."""
    # Group by source type
    corpus_findings = [f for f in findings if f.source.startswith("corpus:")]
    web_findings = [f for f in findings if f.source.startswith("web:")]

    # Build synthesis text
    lines = [
        f"# Laporan Riset: {query}",
        "",
        f"**Metode:** Recursive multi-source research ({iterations} iterasi, {len(findings)} temuan)",
        f"**Durasi:** {duration_ms/1000:.1f} detik",
        "",
        "## Ringkasan Eksekutif",
        "",
    ]

    # Executive summary: concatenate top findings
    top_findings = sorted(findings, key=lambda f: f.confidence, reverse=True)[:5]
    for i, f in enumerate(top_findings, 1):
        lines.append(f"{i}. {f.snippet}")
    lines.append("")

    # Corpus section
    if corpus_findings:
        lines.append("## Temuan dari Korpus SIDIX")
        lines.append("")
        for f in corpus_findings[:6]:
            lines.append(f"- **{f.source}**: {f.snippet}")
        lines.append("")

    # Web section
    if web_findings:
        lines.append("## Temuan dari Web")
        lines.append("")
        for f in web_findings[:6]:
            lines.append(f"- **{f.source}**: {f.snippet}")
        lines.append("")

    # Citations
    citations = []
    seen = set()
    for f in findings:
        key = (f.source, f.snippet[:80])
        if key not in seen:
            seen.add(key)
            citations.append({"source": f.source, "snippet": f.snippet[:200]})

    return ResearchReport(
        query=query,
        findings=findings,
        synthesis="\n".join(lines),
        citations=citations,
        duration_ms=duration_ms,
        iterations=iterations,
    )


# ── Public API ────────────────────────────────────────────────────────────────

def run_deep_research(
    query: str,
    max_iterations: int = 3,
    max_depth: int = 2,
    persona: str = "ALEY",
) -> ResearchReport:
    """
    Run recursive deep research on a query.

    Args:
        query: Research topic/question
        max_iterations: Max recursive search rounds (default 3)
        max_depth: Max depth per sub-query chain (default 2)
        persona: Persona hint for synthesis (default ALEY = researcher)

    Returns:
        ResearchReport with findings, synthesis, and citations
    """
    t0 = time.time()
    all_findings: list[ResearchFinding] = []
    all_sub_queries: list[str] = []
    iterations = 0

    # Iteration 0: initial broad search
    log.info("[deep_research] start: query=%s max_iter=%s", query[:60], max_iterations)

    corpus_results = _search_corpus(query, k=5)
    web_results = _search_web(query, max_results=5)

    for r in corpus_results + web_results:
        findings = _extract_key_findings(r.get("snippet", ""), query, r.get("source", "unknown"))
        all_findings.extend(findings)

    iterations = 1

    # Iterations 1..N: recursive follow-up
    current_queries = [query]
    for depth in range(1, max_depth + 1):
        if iterations >= max_iterations:
            break

        sub_queries = _generate_followup_queries(all_findings, query)
        all_sub_queries.extend(sub_queries)

        for sq in sub_queries:
            if iterations >= max_iterations:
                break
            log.info("[deep_research] depth=%d sub_query=%s", depth, sq[:60])

            # Search both corpus and web for sub-query
            sub_corpus = _search_corpus(sq, k=3)
            sub_web = _search_web(sq, max_results=3)

            for r in sub_corpus + sub_web:
                findings = _extract_key_findings(r.get("snippet", ""), sq, r.get("source", "unknown"))
                all_findings.extend(findings)

            iterations += 1

    duration_ms = int((time.time() - t0) * 1000)
    log.info("[deep_research] done: %d findings, %d iterations, %dms", len(all_findings), iterations, duration_ms)

    return _synthesize_report(query, all_findings, iterations, duration_ms)


# ── MCP-compatible wrapper ────────────────────────────────────────────────────

def deep_research_tool(args: dict) -> dict:
    """
    MCP-compatible wrapper for run_deep_research.
    Returns dict compatible with ToolResult expectations.
    """
    query = str(args.get("query", "")).strip()
    if not query:
        return {"success": False, "output": "", "error": "query tidak boleh kosong"}

    max_iterations = int(args.get("max_iterations", 3))
    max_depth = int(args.get("max_depth", 2))

    try:
        report = run_deep_research(query, max_iterations=max_iterations, max_depth=max_depth)
        return {
            "success": True,
            "output": report.synthesis,
            "citations": report.citations,
            "metadata": {
                "iterations": report.iterations,
                "duration_ms": report.duration_ms,
                "n_findings": len(report.findings),
            },
        }
    except Exception as e:
        log.exception("[deep_research] tool error")
        return {"success": False, "output": "", "error": f"Deep research failed: {e}"}


__all__ = [
    "ResearchFinding",
    "ResearchReport",
    "run_deep_research",
    "deep_research_tool",
]