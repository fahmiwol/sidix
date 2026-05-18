"""
GraphRAG — relasi konsep antar research notes SIDIX.

Node: konsep/topik (extracted dari heading + bold text di *.md)
Edge: co-occurrence dalam note yang sama, atau explicit reference (lihat note X)
Weight: frekuensi co-occurrence

Fungsi utama:
- build_graph(corpus_dir) -> dict
- find_related_concepts(query, graph, top_k=5) -> list[ConceptNode]
- expand_search_context(query, graph, base_results) -> expanded_results

Tidak butuh GPU. Pure Python + no networkx (dict biasa).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConceptNode:
    concept: str
    source_notes: list[str]   # nomor note yang menyebut konsep ini
    frequency: int
    related: list[str] = field(default_factory=list)


@dataclass
class SanadChain:
    answer_fragment: str
    source_note: str          # "183_topic.md"
    note_number: int
    confidence: float         # 0.0-1.0
    epistemic_label: str      # FACT/OPINION/SPECULATION/UNKNOWN


# ---------------------------------------------------------------------------
# Concept extraction
# ---------------------------------------------------------------------------

_RE_HEADING = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
_RE_BOLD = re.compile(r"\*\*(.+?)\*\*")
_RE_EXPLICIT_REF = re.compile(r"(?:lihat|baca|note|notes?)\s+(?:note\s+)?(\d+)", re.IGNORECASE)

# Kata yang terlalu umum untuk jadi konsep bermakna
_STOP_WORDS: frozenset[str] = frozenset({
    "dan", "atau", "yang", "ini", "itu", "dari", "untuk", "dengan", "dalam",
    "pada", "ke", "di", "oleh", "akan", "sudah", "bisa", "juga", "lebih",
    "adalah", "ada", "tidak", "jika", "saat", "the", "and", "or", "is",
    "in", "to", "of", "a", "an", "for", "with", "that", "this", "are",
    "can", "not", "if", "as", "be", "by", "has", "have", "it", "its",
    "---", "###", "##", "#",
})

_MIN_CONCEPT_LEN = 3
_MAX_CONCEPT_LEN = 60


def _clean_concept(raw: str) -> str:
    """Bersihkan teks konsep dari karakter markdown dan whitespace."""
    cleaned = re.sub(r"[`*_\[\]()>]", "", raw).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_concepts(text: str) -> list[str]:
    """
    Extract konsep dari teks markdown.

    Sumber:
    1. Heading (#, ##, ###)
    2. **Bold text**
    3. Kata kapital berulang (UPPERCASE words) yang bukan stop words

    Returns list[str] unik, sudah di-lowercase untuk normalisasi.
    """
    concepts: list[str] = []

    # 1. Headings
    for match in _RE_HEADING.finditer(text):
        raw = _clean_concept(match.group(1))
        if _MIN_CONCEPT_LEN <= len(raw) <= _MAX_CONCEPT_LEN:
            concepts.append(raw.lower())

    # 2. Bold text
    for match in _RE_BOLD.finditer(text):
        raw = _clean_concept(match.group(1))
        if _MIN_CONCEPT_LEN <= len(raw) <= _MAX_CONCEPT_LEN:
            concepts.append(raw.lower())

    # 3. UPPERCASE kata (min 4 char, tidak semua angka, tidak stopword)
    for word in re.findall(r"\b[A-Z][A-Z0-9]{3,}\b", text):
        if word.lower() not in _STOP_WORDS:
            concepts.append(word.lower())

    # Dedupe sambil preserve order
    seen: set[str] = set()
    unique: list[str] = []
    for c in concepts:
        if c not in seen and c.lower() not in _STOP_WORDS:
            seen.add(c)
            unique.append(c)
    return unique


def _extract_note_number(filename: str) -> int:
    """Ambil nomor dari nama file '183_topic.md' → 183. Return -1 jika tidak ditemukan."""
    m = re.match(r"^(\d+)_", filename)
    return int(m.group(1)) if m else -1


# ---------------------------------------------------------------------------
# Graph build & cache
# ---------------------------------------------------------------------------

def _graph_cache_path() -> Path:
    """Path cache graph di data/ relatif dari package brain_qa."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "graph_rag_cache.json"


def build_graph(corpus_dir: Path) -> dict:
    """
    Build graph dari corpus_dir/*.md files.

    Returns:
        {
          "nodes": { concept_str: {"concept": str, "source_notes": [str], "frequency": int, "related": [str]} },
          "edges": { "concept_a|||concept_b": int },  # weight = co-occurrence count
          "note_concepts": { "filename.md": [concept_str] },
          "note_refs": { "filename.md": [note_number_int] },
        }
    """
    nodes: dict[str, dict] = {}      # concept -> node dict
    edges: dict[str, int] = {}       # "c1|||c2" -> weight
    note_concepts: dict[str, list[str]] = {}
    note_refs: dict[str, list[int]] = {}

    md_files = sorted(corpus_dir.glob("*.md"))

    for md_file in md_files:
        fname = md_file.name
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        concepts = extract_concepts(text)
        note_concepts[fname] = concepts

        # Extract explicit references ("lihat note 183", "baca note 5")
        refs = [int(m.group(1)) for m in _RE_EXPLICIT_REF.finditer(text)]
        note_refs[fname] = refs

        # Update node frequency + source_notes
        for concept in concepts:
            if concept not in nodes:
                nodes[concept] = {
                    "concept": concept,
                    "source_notes": [],
                    "frequency": 0,
                    "related": [],
                }
            node = nodes[concept]
            if fname not in node["source_notes"]:
                node["source_notes"].append(fname)
            node["frequency"] += 1

        # Build co-occurrence edges: setiap pasang konsep dalam note yang sama
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                c1, c2 = concepts[i], concepts[j]
                edge_key = f"{c1}|||{c2}" if c1 < c2 else f"{c2}|||{c1}"
                edges[edge_key] = edges.get(edge_key, 0) + 1

    # Build related lists dari edges (top 10 per konsep by weight)
    concept_edges: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for edge_key, weight in edges.items():
        parts = edge_key.split("|||")
        if len(parts) == 2:
            c1, c2 = parts
            concept_edges[c1].append((c2, weight))
            concept_edges[c2].append((c1, weight))

    for concept, neighbors in concept_edges.items():
        if concept in nodes:
            sorted_neighbors = sorted(neighbors, key=lambda x: -x[1])
            nodes[concept]["related"] = [n for n, _ in sorted_neighbors[:10]]

    return {
        "nodes": nodes,
        "edges": edges,
        "note_concepts": note_concepts,
        "note_refs": note_refs,
    }


def load_or_build_graph(
    corpus_dir: Path,
    force_rebuild: bool = False,
) -> dict:
    """
    Load graph dari cache JSON jika ada dan corpus belum berubah.
    Rebuild jika cache tidak ada, force_rebuild=True, atau corpus lebih baru dari cache.
    """
    cache_path = _graph_cache_path()

    if not force_rebuild and cache_path.exists():
        try:
            cache_mtime = cache_path.stat().st_mtime
            # Cek apakah ada note yang lebih baru dari cache
            corpus_needs_rebuild = any(
                md.stat().st_mtime > cache_mtime
                for md in corpus_dir.glob("*.md")
            )
            if not corpus_needs_rebuild:
                with open(cache_path, encoding="utf-8") as f:
                    cached = json.load(f)
                # Konversi edge keys yang mungkin berubah saat JSON dump
                return cached
        except Exception:
            pass  # Rebuild jika cache corrupt

    graph = build_graph(corpus_dir)

    # Simpan ke cache (serialize list as-is, JSON-safe)
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        pass  # Gagal cache tidak fatal

    return graph


# ---------------------------------------------------------------------------
# Query functions
# ---------------------------------------------------------------------------

def find_related_concepts(
    query: str,
    graph: dict,
    top_k: int = 5,
) -> list[ConceptNode]:
    """
    Cari konsep yang relevan dengan query.

    Strategi:
    1. Direct match: query (atau kata dalam query) ada sebagai node
    2. Substring match: konsep yang mengandung kata dari query
    3. Rank by frequency + related count

    Returns list[ConceptNode] urut dari paling relevan.
    """
    nodes: dict[str, dict] = graph.get("nodes", {})
    if not nodes:
        return []

    query_lower = query.lower().strip()
    query_words = set(query_lower.split())

    scores: dict[str, float] = {}

    for concept, node in nodes.items():
        score = 0.0

        # Direct / exact match
        if concept == query_lower:
            score += 10.0
        elif query_lower in concept:
            score += 5.0
        elif concept in query_lower:
            score += 4.0
        else:
            # Partial word match
            concept_words = set(concept.split())
            overlap = query_words & concept_words
            if overlap:
                score += 2.0 * len(overlap) / max(len(query_words), 1)

        if score > 0:
            # Boost berdasarkan frekuensi dan jumlah sumber
            freq_boost = min(node.get("frequency", 1) / 50.0, 1.0)
            source_boost = min(len(node.get("source_notes", [])) / 20.0, 0.5)
            scores[concept] = score + freq_boost + source_boost

    # Sort by score desc
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]

    result: list[ConceptNode] = []
    for concept, _ in ranked:
        node = nodes[concept]
        result.append(ConceptNode(
            concept=node["concept"],
            source_notes=node["source_notes"],
            frequency=node["frequency"],
            related=node.get("related", []),
        ))
    return result


def expand_search_context(
    query: str,
    graph: dict,
    base_results: list[dict],
) -> list[dict]:
    """
    Perluas konteks pencarian berdasarkan konsep terkait dari graph.

    Mengambil konsep yang paling relevan dengan query, lalu menambahkan
    source notes dari konsep terkait yang belum ada di base_results.

    Returns list[dict] yang diperluas dengan field tambahan 'expanded_from'.
    """
    related = find_related_concepts(query, graph, top_k=3)

    existing_sources: set[str] = set()
    for r in base_results:
        src = r.get("source", r.get("filename", ""))
        if src:
            existing_sources.add(src)

    expanded = list(base_results)
    for concept_node in related:
        for src_note in concept_node.source_notes:
            if src_note not in existing_sources:
                expanded.append({
                    "source": src_note,
                    "concept": concept_node.concept,
                    "expanded_from": "graph_rag",
                    "frequency": concept_node.frequency,
                })
                existing_sources.add(src_note)

    return expanded


# ---------------------------------------------------------------------------
# Sanad ranking
# ---------------------------------------------------------------------------

_SPECULATIVE_KEYWORDS = frozenset({
    "mungkin", "kemungkinan", "diperkirakan", "belum pasti", "hipotesis",
    "spekulasi", "dugaan", "kata orang", "katanya", "konon",
    "specul", "maybe", "possibly", "uncertain", "hypothesis",
})

_OPINION_KEYWORDS = frozenset({
    "menurut", "pendapat", "pandangan", "ulama", "saya kira", "menurut saya",
    "berpendapat", "perspektif", "sudut pandang",
    "opinion", "view", "perspective",
})

_FACT_KEYWORDS = frozenset({
    "terbukti", "data menunjukkan", "penelitian", "hadits", "quran", "dalil",
    "sahih", "shahih", "authentic", "verified", "terhitung",
    "riset", "studi", "bukti", "evidence", "documented",
})


def _infer_epistemic_from_note_number(note_number: int) -> str:
    """
    Heuristic: note nomor lebih tinggi cenderung lebih matang/terverifikasi.
    Note 100+ = lebih likely FACT (corpus yang sudah mature).
    Note di bawah 50 = lebih likely masih exploratory.
    """
    if note_number >= 100:
        return "FACT"
    elif note_number >= 50:
        return "OPINION"
    elif note_number >= 1:
        return "SPECULATION"
    return "UNKNOWN"


def _infer_epistemic_from_text(snippet: str) -> str:
    """Cek keyword epistemik di snippet teks."""
    lower = snippet.lower()
    if any(kw in lower for kw in _SPECULATIVE_KEYWORDS):
        return "SPECULATION"
    if any(kw in lower for kw in _OPINION_KEYWORDS):
        return "OPINION"
    if any(kw in lower for kw in _FACT_KEYWORDS):
        return "FACT"
    return "UNKNOWN"


def rank_by_sanad(
    results: list[dict],
    graph: dict,
) -> list[dict]:
    """
    Rank hasil RAG berdasarkan sanad chain.

    Setiap result mendapat field tambahan:
    - sanad_score (float): skor gabungan
    - epistemic_label (str): FACT/OPINION/SPECULATION/UNKNOWN
    - cross_ref_count (int): berapa kali note ini direferensi note lain

    Urutan: sanad_score desc.
    """
    note_refs: dict[str, list[int]] = graph.get("note_refs", {})

    # Hitung cross-reference count: berapa banyak note mereferensi note tertentu
    target_ref_count: dict[int, int] = defaultdict(int)
    for refs in note_refs.values():
        for ref_num in refs:
            target_ref_count[ref_num] += 1

    ranked = []
    for result in results:
        source = result.get("source", result.get("filename", ""))
        note_number = _extract_note_number(source)
        snippet = result.get("text", result.get("content", result.get("snippet", "")))

        # Base score dari BM25/relevance (default 1.0 jika tidak ada)
        base_score = float(result.get("score", result.get("bm25_score", 1.0)))

        # Cross-reference bonus
        cross_ref_count = target_ref_count.get(note_number, 0)
        cross_ref_bonus = min(cross_ref_count * 0.1, 0.5)  # cap 0.5

        # Note-number maturity bonus (note lebih tinggi = lebih mature)
        if note_number >= 100:
            maturity_bonus = 0.3
        elif note_number >= 50:
            maturity_bonus = 0.15
        elif note_number >= 1:
            maturity_bonus = 0.05
        else:
            maturity_bonus = 0.0

        sanad_score = base_score + cross_ref_bonus + maturity_bonus

        # Epistemic label: kombinasi dari note_number + keyword dalam teks
        if snippet:
            ep_text = _infer_epistemic_from_text(str(snippet))
            ep_num = _infer_epistemic_from_note_number(note_number)
            # Text-based lebih spesifik; fallback ke note-number
            if ep_text != "UNKNOWN":
                epistemic_label = ep_text
            else:
                epistemic_label = ep_num
        else:
            epistemic_label = _infer_epistemic_from_note_number(note_number)

        result_copy = dict(result)
        result_copy["sanad_score"] = round(sanad_score, 4)
        result_copy["epistemic_label"] = epistemic_label
        result_copy["cross_ref_count"] = cross_ref_count
        result_copy["note_number"] = note_number
        ranked.append(result_copy)

    return sorted(ranked, key=lambda r: -r["sanad_score"])


def format_sanad_chain(results: list[dict]) -> str:
    """
    Format hasil sebagai sanad chain yang bisa diverifikasi.

    Output format:
    [FACT] Sumber: note 183 — konsep: rag, llm
    [OPINION] Sumber: note 45 — konsep: fine-tuning

    Jika result dari find_related_concepts (list[dict] dengan 'concept' + 'sources'),
    juga bisa handle format tersebut.
    """
    if not results:
        return "[UNKNOWN] Tidak ada hasil ditemukan."

    lines: list[str] = ["# Sanad Chain — Hasil Terverifikasi\n"]
    for i, result in enumerate(results, 1):
        source = result.get("source", result.get("filename", ""))
        note_number = result.get("note_number", _extract_note_number(source))
        epistemic_label = result.get("epistemic_label", "UNKNOWN")
        sanad_score = result.get("sanad_score", "")
        concept = result.get("concept", "")
        sources = result.get("sources", [])

        # Format berbeda untuk direct concept search vs ranked results
        if concept and sources:
            src_str = ", ".join(str(s) for s in sources[:3])
            score_str = f" (score: {sanad_score})" if sanad_score else ""
            lines.append(f"{i}. [{epistemic_label}] Konsep: **{concept}** — Sumber: {src_str}{score_str}")
        elif source:
            snippet = result.get("text", result.get("content", result.get("snippet", "")))
            snippet_str = str(snippet)[:120].replace("\n", " ").strip() if snippet else ""
            score_str = f" (sanad: {sanad_score})" if sanad_score else ""
            note_str = f"note {note_number}" if note_number > 0 else source
            lines.append(f"{i}. [{epistemic_label}] Sumber: {note_str}{score_str}")
            if snippet_str:
                lines.append(f"   > {snippet_str}…")
        else:
            lines.append(f"{i}. [{epistemic_label}] {result}")

    return "\n".join(lines)
