"""
knowledge_graph_query.py — Query SIDIX Knowledge Graph
=======================================================
Query by concept name → return:
  - related concepts (top N by co-occurrence weight)
  - source files (research notes + docs)
  - implementation files + status
  - mention count
  - suggested next steps (bila status "missing" → list docs yang menjelaskan)

Tidak pakai vendor API. Pure dict lookup ke graph dari brain_synthesizer.
"""

from __future__ import annotations

import difflib
from typing import Optional

from .brain_synthesizer import build_knowledge_graph, CONCEPT_LEXICON


def _normalize(concept: str) -> Optional[str]:
    """Map user input ke canonical concept. Fuzzy match bila tak exact."""
    if not concept:
        return None
    # Exact
    for c in CONCEPT_LEXICON:
        if c.lower() == concept.lower().replace(" ", "_"):
            return c
    # Alias
    lower = concept.lower().strip()
    for canonical, aliases in CONCEPT_LEXICON.items():
        for a in aliases:
            if a.lower() == lower:
                return canonical
    # Fuzzy: best match di canonical names
    candidates = list(CONCEPT_LEXICON.keys())
    close = difflib.get_close_matches(
        concept.replace(" ", "_"), candidates, n=1, cutoff=0.6
    )
    if close:
        return close[0]
    return None


def query(concept: str, top_k: int = 10) -> dict:
    """
    Return struktur:
    {
      ok: bool,
      concept: canonical name or null,
      matched_from: input asli,
      related: [{concept, weight}, ...],
      source_files: [path, ...],
      impl_files: [path, ...],
      impl_status: "missing" | "partial" | "implemented",
      mention_count: int,
      suggestions: [str, ...]
    }
    """
    canonical = _normalize(concept)
    if not canonical:
        # Fuzzy suggestions
        candidates = list(CONCEPT_LEXICON.keys())
        close = difflib.get_close_matches(
            concept.replace(" ", "_"), candidates, n=5, cutoff=0.3
        )
        return {
            "ok": False,
            "matched_from": concept,
            "reason": f"Concept '{concept}' tidak ditemukan di lexicon.",
            "did_you_mean": close,
        }

    graph = build_knowledge_graph()
    node = graph["nodes"].get(canonical)
    if not node:
        return {
            "ok": False,
            "matched_from": concept,
            "concept": canonical,
            "reason": "Concept ada di lexicon tapi tidak ada di graph (belum pernah disebut di manapun).",
        }

    # Related dengan weight (ambil dari edges)
    edges_for_node: list[dict] = []
    for e in graph["edges"]:
        if e["source"] == canonical or e["target"] == canonical:
            other = e["target"] if e["source"] == canonical else e["source"]
            edges_for_node.append({"concept": other, "weight": e["weight"]})
    edges_for_node.sort(key=lambda x: -x["weight"])

    suggestions: list[str] = []
    if node["impl_status"] == "missing":
        suggestions.append(
            f"Konsep ini disebut {node['mention_count']}x di dokumen tapi belum ada modul Python."
        )
        if node["source_notes"]:
            suggestions.append(
                f"Baca dokumen-dokumen ini untuk scope implementasi: {node['source_notes'][:3]}"
            )
        suggestions.append(
            "Pertimbangkan masukkan sebagai task via POST /synthesize/run → lihat gaps."
        )
    elif node["impl_status"] == "partial":
        suggestions.append("Implementasi ada tapi tidak lengkap. Cek impl_files untuk detail.")

    return {
        "ok": True,
        "matched_from": concept,
        "concept": canonical,
        "related": edges_for_node[:top_k],
        "source_files": node["source_notes"],
        "impl_files": node["impl_files"],
        "impl_status": node["impl_status"],
        "mention_count": node["mention_count"],
        "suggestions": suggestions,
    }


def list_concepts() -> list[str]:
    """Semua canonical concept yang dikenal."""
    return sorted(CONCEPT_LEXICON.keys())
