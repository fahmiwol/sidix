"""
test_hybrid_retrieval.py — Sprint 25 Sprint B+C
==========================================================================

Smoke + integration tests untuk:
- dense_index.build_dense_index / load_dense_index / dense_search
- hybrid_search._rrf_fuse + hybrid_search.hybrid_search end-to-end
- reranker.rerank_indices graceful fallback
- query.answer_query_and_citations BM25 vs hybrid path

Tidak depend on sentence-transformers / numpy-via-HF — pakai mock embed_fn.
Numpy required (untuk dense_index core math).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass
class _FakeChunk:
    text: str


def _mock_embed(text: str):
    import numpy as np
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    v = rng.standard_normal(64).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def test_dense_env_gating():
    from brain_qa import dense_index
    os.environ.pop("SIDIX_HYBRID_RETRIEVAL", None)
    assert dense_index.is_enabled_via_env() is False
    os.environ["SIDIX_HYBRID_RETRIEVAL"] = "1"
    assert dense_index.is_enabled_via_env() is True
    os.environ.pop("SIDIX_HYBRID_RETRIEVAL", None)


def test_reranker_env_gating():
    from brain_qa import reranker
    os.environ.pop("SIDIX_RERANK", None)
    assert reranker.is_enabled_via_env() is False
    os.environ["SIDIX_RERANK"] = "1"
    assert reranker.is_enabled_via_env() is True
    os.environ.pop("SIDIX_RERANK", None)


def test_dense_index_roundtrip():
    pytest.importorskip("numpy")
    from brain_qa import dense_index
    chunks = [_FakeChunk(text=t) for t in [
        "hello world",
        "kucing lucu",
        "mesin AI generatif",
        "Tesla Edison kompetisi",
        "SIDIX self-evolving agent",
    ]]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        ok = dense_index.build_dense_index(
            chunks, out_dir=out, embed_fn=_mock_embed, model_name="mock-64d"
        )
        assert ok is True
        loaded = dense_index.load_dense_index(out)
        assert loaded is not None
        matrix, meta = loaded
        assert matrix.shape == (5, 64)
        assert meta["chunk_count"] == 5
        assert meta["dim"] == 64
        # Self-match
        res = dense_index.dense_search(
            "SIDIX self-evolving agent", matrix, embed_fn=_mock_embed, top_k=3,
        )
        assert len(res) == 3
        top_idx, top_score = res[0]
        assert top_idx == 4
        assert top_score > 0.99


def test_dense_index_missing_returns_none():
    from brain_qa import dense_index
    with tempfile.TemporaryDirectory() as td:
        assert dense_index.load_dense_index(Path(td)) is None


def test_rrf_fusion_math():
    from brain_qa import hybrid_search
    fused = hybrid_search._rrf_fuse([
        [(0, 5.0), (1, 4.0), (2, 3.0)],
        [(2, 0.9), (0, 0.8), (3, 0.7)],
    ])
    # idx 0: rank 1 in bm25, rank 2 in dense
    expected_0 = 1 / (60 + 1) + 1 / (60 + 2)
    # idx 2: rank 3 in bm25, rank 1 in dense
    expected_2 = 1 / (60 + 3) + 1 / (60 + 1)
    assert abs(fused[0] - expected_0) < 1e-9
    assert abs(fused[2] - expected_2) < 1e-9
    # idx 0 should win (rank-1 + rank-2 vs rank-3 + rank-1)
    assert fused[0] > fused[2]


def test_reranker_graceful_no_model():
    """Reranker tanpa CrossEncoder installed → return original order with score 0."""
    from brain_qa import reranker
    out = reranker.rerank_indices(
        query="q",
        candidate_indices=[0, 2, 1],
        chunks_text=["x", "y", "z"],
        rerank_fn=None,  # auto-load — likely fails on CI without sentence-transformers
    )
    assert len(out) == 3
    # Either real reranker scored, or fallback returned with score 0.0
    indices = [i for i, _ in out]
    assert sorted(indices) == [0, 1, 2]


def test_query_bm25_path_then_hybrid_path():
    """End-to-end: build mini index, run BM25 vs hybrid path, both work."""
    pytest.importorskip("numpy")
    pytest.importorskip("rank_bm25")

    td = tempfile.mkdtemp(prefix="sidix_test_hybrid_")
    try:
        corpus_root = Path(td) / "corpus"
        corpus_root.mkdir(parents=True)
        (corpus_root / "note_a.md").write_text(
            "# Tesla Edison\n" + "Kisah kompetisi DC vs AC dan listrik dunia. " * 10,
            encoding="utf-8",
        )
        (corpus_root / "note_b.md").write_text(
            "# Kucing\n" + "Kucing lucu suka tidur siang. " * 10,
            encoding="utf-8",
        )
        (corpus_root / "note_c.md").write_text(
            "# SIDIX\n" + "SIDIX self-evolving AI creative agent yang tumbuh dan belajar. " * 10,
            encoding="utf-8",
        )
        index_dir = Path(td) / "index"

        os.environ.pop("SIDIX_BUILD_DENSE", None)
        from brain_qa.indexer import build_index
        build_index(
            root_override=str(corpus_root),
            out_dir_override=str(index_dir),
            chunk_chars=400,
            chunk_overlap=40,
        )
        assert (index_dir / "READY").exists()

        # BM25 path (default)
        os.environ.pop("SIDIX_HYBRID_RETRIEVAL", None)
        from brain_qa.query import answer_query_and_citations, _load_chunks
        _, cit_bm25 = answer_query_and_citations(
            question="SIDIX agent",
            index_dir_override=str(index_dir),
            k=3,
            max_snippet_chars=200,
            persona="INAN",
            persona_reason="test",
        )
        assert any("note_c" in c["source_path"] for c in cit_bm25)

        # Build dense with mock embed
        from brain_qa.dense_index import build_dense_index
        chunks = _load_chunks(index_dir)
        ok = build_dense_index(
            chunks, out_dir=index_dir, embed_fn=_mock_embed, model_name="mock-64d",
        )
        assert ok is True
        assert (index_dir / "embeddings.npy").exists()

        # Hybrid path with mocked embed_fn
        import brain_qa.embedding_loader as el
        import brain_qa.dense_index as di
        _orig_embed_fn = el.load_embed_fn
        _orig_dense_search = di.dense_search
        try:
            el.load_embed_fn = lambda *a, **k: _mock_embed
            di.dense_search = lambda q, m, embed_fn=None, top_k=20: _orig_dense_search(
                q, m, embed_fn=_mock_embed, top_k=top_k
            )
            os.environ["SIDIX_HYBRID_RETRIEVAL"] = "1"
            _, cit_hybrid = answer_query_and_citations(
                question="SIDIX agent",
                index_dir_override=str(index_dir),
                k=3,
                max_snippet_chars=200,
                persona="INAN",
                persona_reason="test",
            )
            assert len(cit_hybrid) >= 1
            # Note_c should still appear (BM25 strongly matches)
            assert any("note_c" in c["source_path"] for c in cit_hybrid)
        finally:
            el.load_embed_fn = _orig_embed_fn
            di.dense_search = _orig_dense_search
            os.environ.pop("SIDIX_HYBRID_RETRIEVAL", None)
    finally:
        shutil.rmtree(td)
