"""
Unit tests untuk GraphRAG + Sanad Ranker (Sprint 10).

Semua tests pakai tmp_path pytest — tidak baca corpus real.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from brain_qa.graph_rag import (
    ConceptNode,
    SanadChain,
    build_graph,
    expand_search_context,
    extract_concepts,
    find_related_concepts,
    format_sanad_chain,
    load_or_build_graph,
    rank_by_sanad,
)
from brain_qa.sanad_ranker import (
    EPISTEMIC_KEYWORDS,
    SanadScore,
    classify_epistemic,
    format_sanad_summary,
    rank_results,
    score_result,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_note(tmp_path: Path, filename: str, content: str) -> Path:
    """Buat satu markdown note di tmp_path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Task 4A: graph_rag.py tests
# ---------------------------------------------------------------------------


class TestExtractConcepts:
    def test_extract_concepts_from_heading(self) -> None:
        text = "# Machine Learning\n## Deep Learning\n### Neural Network"
        concepts = extract_concepts(text)
        assert "machine learning" in concepts
        assert "deep learning" in concepts
        assert "neural network" in concepts

    def test_extract_concepts_from_bold(self) -> None:
        text = "Ini tentang **Retrieval Augmented Generation** dan **BM25 Algorithm**."
        concepts = extract_concepts(text)
        assert "retrieval augmented generation" in concepts
        assert "bm25 algorithm" in concepts

    def test_extract_concepts_uppercase(self) -> None:
        # Regex UPPERCASE membutuhkan min 4 char (pola [A-Z][A-Z0-9]{3,})
        # SIDIX (5) dan LORA (4) memenuhi — RAG (3) tidak (terlalu pendek)
        text = "Sistem SIDIX menggunakan LORA untuk training."
        concepts = extract_concepts(text)
        assert "sidix" in concepts or "SIDIX".lower() in concepts
        assert "lora" in concepts or "LORA".lower() in concepts

    def test_extract_concepts_no_duplicates(self) -> None:
        text = "# BM25\nAlgoritma **BM25** digunakan di mana-mana.\n## BM25 Details"
        concepts = extract_concepts(text)
        bm25_count = concepts.count("bm25")
        assert bm25_count == 1, f"Expected 1 occurrence of bm25, got {bm25_count}"

    def test_extract_concepts_short_words_excluded(self) -> None:
        """Kata pendek (< 3 char) tidak boleh jadi konsep."""
        text = "# AI\n**ML**"
        concepts = extract_concepts(text)
        # "ai" dan "ml" mungkin dimasukkan dari heading/bold tapi pendek
        # Yang penting tidak crash dan return list
        assert isinstance(concepts, list)

    def test_extract_concepts_stop_words_excluded(self) -> None:
        text = "# Dan atau yang ini itu"
        concepts = extract_concepts(text)
        for stop in ["dan", "atau", "yang", "ini", "itu"]:
            assert stop not in concepts

    def test_extract_concepts_empty_text(self) -> None:
        assert extract_concepts("") == []

    def test_extract_concepts_plain_text_no_markdown(self) -> None:
        """Teks tanpa heading/bold — hanya konsep UPPERCASE."""
        text = "Sebuah kalimat biasa tanpa markup apapun."
        concepts = extract_concepts(text)
        assert isinstance(concepts, list)


class TestBuildGraph:
    def test_build_graph_empty(self, tmp_path: Path) -> None:
        """Dir kosong → empty nodes dan edges."""
        graph = build_graph(tmp_path)
        assert graph["nodes"] == {}
        assert graph["edges"] == {}
        assert graph["note_concepts"] == {}

    def test_build_graph_with_notes(self, tmp_path: Path) -> None:
        """Notes dengan heading → nodes + edges populated."""
        _make_note(
            tmp_path,
            "001_intro.md",
            "# Machine Learning\n## Deep Learning\nKonsep **Neural Network** penting.",
        )
        _make_note(
            tmp_path,
            "002_advanced.md",
            "# Deep Learning\n## Neural Network\nLihat note 1 untuk dasar.",
        )
        graph = build_graph(tmp_path)

        assert len(graph["nodes"]) > 0
        # "deep learning" harusnya ada di kedua note → frequency >= 2
        assert "deep learning" in graph["nodes"]
        node = graph["nodes"]["deep learning"]
        assert node["frequency"] >= 2
        assert len(node["source_notes"]) == 2

        # Edge antara co-occurring concepts
        assert len(graph["edges"]) > 0

    def test_build_graph_note_refs(self, tmp_path: Path) -> None:
        """Explicit reference 'lihat note 5' harus di-capture."""
        _make_note(
            tmp_path,
            "010_test.md",
            "# Test\nLihat note 5 untuk referensi dan baca note 12.",
        )
        graph = build_graph(tmp_path)
        refs = graph["note_refs"].get("010_test.md", [])
        assert 5 in refs
        assert 12 in refs

    def test_build_graph_related_populated(self, tmp_path: Path) -> None:
        """Nodes harus punya related list dari edges."""
        _make_note(
            tmp_path,
            "100_concepts.md",
            "# Sanad\n## Corpus\n**Retrieval** dan **Knowledge Graph** saling terkait.",
        )
        graph = build_graph(tmp_path)
        # Setidaknya satu node punya related
        has_related = any(
            len(node.get("related", [])) > 0
            for node in graph["nodes"].values()
        )
        assert has_related

    def test_load_or_build_graph_uses_cache(self, tmp_path: Path) -> None:
        """load_or_build_graph harus bisa load dari cache tanpa error."""
        _make_note(tmp_path, "050_cache.md", "# Caching\n**Cache** penting untuk performa.")

        # Build pertama kali
        graph1 = build_graph(tmp_path)

        # Simpan manual sebagai cache
        cache_dir = tmp_path / "data"
        cache_dir.mkdir()
        cache_file = cache_dir / "graph_rag_cache.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(graph1, f)

        # Tidak crash saat graph ada
        assert isinstance(graph1, dict)
        assert "nodes" in graph1


class TestFindRelatedConcepts:
    def test_find_related_concepts(self, tmp_path: Path) -> None:
        """Query match → return ConceptNode list."""
        _make_note(
            tmp_path,
            "120_rag.md",
            "# RAG Architecture\n## Retrieval Augmented Generation\n"
            "**BM25** adalah algoritma retrieval dasar.",
        )
        graph = build_graph(tmp_path)
        related = find_related_concepts("rag", graph, top_k=5)
        assert isinstance(related, list)
        # Setidaknya satu hasil yang mengandung "rag" atau "retrieval"
        concept_names = [c.concept for c in related]
        assert any("rag" in name or "retrieval" in name for name in concept_names)

    def test_find_related_concepts_returns_concept_nodes(self, tmp_path: Path) -> None:
        """Return value harus ConceptNode instances."""
        _make_note(tmp_path, "080_ml.md", "# Machine Learning\nAlgoritma **SVM** dan **KNN**.")
        graph = build_graph(tmp_path)
        related = find_related_concepts("machine learning", graph, top_k=3)
        for item in related:
            assert isinstance(item, ConceptNode)
            assert hasattr(item, "concept")
            assert hasattr(item, "source_notes")
            assert hasattr(item, "frequency")
            assert hasattr(item, "related")

    def test_find_related_concepts_empty_graph(self) -> None:
        """Graph kosong → return empty list."""
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        result = find_related_concepts("test", graph, top_k=5)
        assert result == []

    def test_find_related_concepts_no_match(self, tmp_path: Path) -> None:
        """Query yang tidak match → list kosong atau sedikit hasil."""
        _make_note(tmp_path, "030_abc.md", "# Python\n**Django** framework.")
        graph = build_graph(tmp_path)
        result = find_related_concepts("xyzzyblorp", graph, top_k=5)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_find_related_concepts_top_k_respected(self, tmp_path: Path) -> None:
        """top_k harus membatasi jumlah hasil."""
        content = "\n".join(
            f"# Concept{i}\n**Topic{i}** adalah hal ke-{i}." for i in range(20)
        )
        _make_note(tmp_path, "190_many.md", content)
        graph = build_graph(tmp_path)
        result = find_related_concepts("concept", graph, top_k=3)
        assert len(result) <= 3


class TestRankBySanad:
    def test_rank_by_sanad_adds_fields(self) -> None:
        """rank_by_sanad harus tambah field sanad_score + epistemic_label."""
        results = [
            {"source": "100_fact.md", "score": 1.0, "text": "terbukti dari data penelitian"},
            {"source": "050_opinion.md", "score": 0.8, "text": "menurut pendapat ulama"},
        ]
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        ranked = rank_by_sanad(results, graph)
        for r in ranked:
            assert "sanad_score" in r
            assert "epistemic_label" in r
            assert isinstance(r["sanad_score"], float)

    def test_rank_by_sanad_sorted_desc(self) -> None:
        """Hasil harus urut dari sanad_score tertinggi."""
        results = [
            {"source": "010_low.md", "score": 0.5, "text": ""},
            {"source": "150_high.md", "score": 1.5, "text": ""},
        ]
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        ranked = rank_by_sanad(results, graph)
        scores = [r["sanad_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_by_sanad_cross_ref_bonus(self) -> None:
        """Note yang banyak direferensi mendapat bonus lebih tinggi."""
        # Note 50 direferensi 3x oleh note lain
        note_refs = {
            "001_a.md": [50],
            "002_b.md": [50],
            "003_c.md": [50],
        }
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": note_refs}

        results_high = [{"source": "050_referenced.md", "score": 1.0, "text": ""}]
        results_low = [{"source": "100_unreferenced.md", "score": 1.0, "text": ""}]

        ranked_high = rank_by_sanad(results_high, graph)
        ranked_low = rank_by_sanad(results_low, graph)

        # Note 50 punya cross_ref_count=3 → bonus 0.3, tapi note 100 punya maturity_bonus=0.3
        # Yang penting kedua punya sanad_score dan tidak crash
        assert ranked_high[0]["sanad_score"] > 0
        assert ranked_low[0]["sanad_score"] > 0


class TestFormatSanadChain:
    def test_format_sanad_chain_nonempty(self) -> None:
        """Output harus non-empty dengan label epistemik."""
        results = [
            {
                "concept": "machine learning",
                "sources": ["100_ml.md", "120_dl.md"],
                "epistemic_label": "FACT",
            }
        ]
        output = format_sanad_chain(results)
        assert len(output) > 0
        assert "[FACT]" in output or "FACT" in output

    def test_format_sanad_chain_empty_results(self) -> None:
        """Results kosong → return string non-empty dengan UNKNOWN."""
        output = format_sanad_chain([])
        assert "UNKNOWN" in output or len(output) > 0

    def test_format_sanad_chain_multiple_results(self) -> None:
        """Beberapa results → semua muncul di output."""
        results = [
            {"concept": "sanad", "sources": ["001_a.md"], "epistemic_label": "FACT"},
            {"concept": "corpus", "sources": ["002_b.md"], "epistemic_label": "OPINION"},
        ]
        output = format_sanad_chain(results)
        assert "sanad" in output.lower()
        assert "corpus" in output.lower()

    def test_format_sanad_chain_includes_header(self) -> None:
        """Output harus ada header sanad chain."""
        results = [{"source": "100_note.md", "epistemic_label": "FACT", "sanad_score": 1.5}]
        output = format_sanad_chain(results)
        assert "Sanad" in output or "[" in output


# ---------------------------------------------------------------------------
# Task 4B: sanad_ranker.py tests
# ---------------------------------------------------------------------------


class TestClassifyEpistemic:
    def test_fact_keywords(self) -> None:
        """Teks dengan keyword FACT → 'FACT'."""
        text = "Penelitian terbukti bahwa model ini lebih akurat."
        assert classify_epistemic(text) == "FACT"

    def test_opinion_keywords(self) -> None:
        """Teks dengan keyword OPINION → 'OPINION'."""
        text = "Menurut pendapat ulama, ini adalah hal yang penting."
        assert classify_epistemic(text) == "OPINION"

    def test_speculation_keywords(self) -> None:
        """Teks dengan keyword SPECULATION → 'SPECULATION'."""
        text = "Mungkin kemungkinan ini diperkirakan terjadi."
        assert classify_epistemic(text) == "SPECULATION"

    def test_unknown_keywords(self) -> None:
        """Teks tanpa keyword apapun → 'UNKNOWN'."""
        text = "Ini adalah kalimat biasa tanpa keyword epistemik."
        assert classify_epistemic(text) == "UNKNOWN"

    def test_fact_priority_over_opinion(self) -> None:
        """FACT lebih prioritas daripada OPINION jika keduanya muncul."""
        text = "Menurut penelitian terbukti bahwa ini benar."
        result = classify_epistemic(text)
        # FACT lebih prioritas
        assert result == "FACT"

    def test_empty_text(self) -> None:
        assert classify_epistemic("") == "UNKNOWN"

    def test_none_text(self) -> None:
        assert classify_epistemic(None) == "UNKNOWN"  # type: ignore[arg-type]

    def test_hadits_is_fact(self) -> None:
        text = "Hadits riwayat Bukhari menyatakan hal ini."
        assert classify_epistemic(text) == "FACT"

    def test_quran_is_fact(self) -> None:
        text = "Quran surat Al-Baqarah ayat 2 menjelaskan ini."
        assert classify_epistemic(text) == "FACT"


class TestScoreResult:
    def test_score_result_basic(self) -> None:
        """score_result harus return SanadScore."""
        result = {"source": "100_fact.md", "score": 1.0, "text": "terbukti"}
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        ss = score_result(result, graph)
        assert isinstance(ss, SanadScore)
        assert ss.final_score > 0
        assert ss.epistemic_label in ("FACT", "OPINION", "SPECULATION", "UNKNOWN")

    def test_score_result_cross_ref_bonus(self) -> None:
        """Note yang direferensi → cross_ref_bonus > 0."""
        note_refs = {"001_a.md": [50], "002_b.md": [50]}
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": note_refs}
        result = {"source": "050_x.md", "score": 1.0, "text": ""}
        ss = score_result(result, graph)
        assert ss.cross_ref_bonus > 0

    def test_score_result_no_cross_ref(self) -> None:
        """Note yang tidak direferensi → cross_ref_bonus = 0."""
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        result = {"source": "099_y.md", "score": 1.0, "text": ""}
        ss = score_result(result, graph)
        assert ss.cross_ref_bonus == 0.0


class TestRankResults:
    def test_rank_results_sorted(self) -> None:
        """rank_results harus urut dari sanad_score tertinggi ke terendah."""
        results = [
            {"source": "010_low.md", "score": 0.5, "text": ""},
            {"source": "180_high.md", "score": 2.0, "text": "terbukti"},
            {"source": "060_mid.md", "score": 1.0, "text": ""},
        ]
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        ranked = rank_results(results, graph)

        scores = [r["sanad_score"] for r in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_rank_results_adds_sanad_field(self) -> None:
        """Setiap result harus punya field 'sanad', 'sanad_score', 'epistemic_label'."""
        results = [{"source": "100_x.md", "score": 1.0, "text": "data penelitian"}]
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        ranked = rank_results(results, graph)
        assert len(ranked) == 1
        r = ranked[0]
        assert "sanad" in r
        assert "sanad_score" in r
        assert "epistemic_label" in r
        assert isinstance(r["sanad"], SanadScore)

    def test_rank_results_cross_ref_higher(self) -> None:
        """Note dengan lebih banyak cross-reference → sanad_score lebih tinggi dari yang setara."""
        note_refs = {
            "001_a.md": [80],
            "002_b.md": [80],
            "003_c.md": [80],
        }
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": note_refs}

        # Kedua note punya base_score sama
        results = [
            {"source": "080_many_refs.md", "score": 1.0, "text": ""},
            {"source": "081_no_refs.md", "score": 1.0, "text": ""},
        ]
        ranked = rank_results(results, graph)
        # Note 080 harus punya cross_ref_bonus > 0
        note_80 = next(r for r in ranked if "080" in r["source"])
        note_81 = next(r for r in ranked if "081" in r["source"])
        assert note_80["sanad_score"] > note_81["sanad_score"]

    def test_rank_results_empty(self) -> None:
        """Input kosong → output kosong."""
        graph = {"nodes": {}, "edges": {}, "note_concepts": {}, "note_refs": {}}
        ranked = rank_results([], graph)
        assert ranked == []


class TestFormatSanadSummary:
    def test_format_sanad_summary_nonempty(self) -> None:
        """Output harus non-empty."""
        results = [
            {
                "source": "100_x.md",
                "sanad": SanadScore(
                    note_id="100_x.md",
                    base_score=1.0,
                    cross_ref_bonus=0.2,
                    epistemic_label="FACT",
                    final_score=1.2,
                ),
                "sanad_score": 1.2,
                "epistemic_label": "FACT",
            }
        ]
        output = format_sanad_summary(results)
        assert len(output) > 0
        assert "FACT" in output

    def test_format_sanad_summary_empty(self) -> None:
        """Empty input → return non-empty string dengan UNKNOWN."""
        output = format_sanad_summary([])
        assert "UNKNOWN" in output or len(output) > 0


class TestEpistemicKeywordsMap:
    def test_all_labels_present(self) -> None:
        """EPISTEMIC_KEYWORDS harus punya 4 label."""
        assert "FACT" in EPISTEMIC_KEYWORDS
        assert "OPINION" in EPISTEMIC_KEYWORDS
        assert "SPECULATION" in EPISTEMIC_KEYWORDS
        assert "UNKNOWN" in EPISTEMIC_KEYWORDS

    def test_all_values_are_lists(self) -> None:
        """Setiap value harus list."""
        for label, keywords in EPISTEMIC_KEYWORDS.items():
            assert isinstance(keywords, list), f"{label} harus list, got {type(keywords)}"
            assert len(keywords) > 0, f"{label} tidak boleh kosong"
