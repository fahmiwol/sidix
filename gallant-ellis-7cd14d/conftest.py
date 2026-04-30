"""
conftest.py — Projek Badar Task 71 (G4)
Root-level pytest configuration for SIDIX/Mighan test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ── sys.path setup ─────────────────────────────────────────────────────────────
# Ensure brain_qa package is importable from repo root
_REPO_ROOT = Path(__file__).parent
_BRAIN_QA_APP = _REPO_ROOT / "apps" / "brain_qa"

if str(_BRAIN_QA_APP) not in sys.path:
    sys.path.insert(0, str(_BRAIN_QA_APP))


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_llm():
    """
    Returns a MockLLM instance for CI testing without GPU.

    Usage:
        def test_something(mock_llm):
            response = mock_llm.generate("apa itu BM25?")
            assert response  # deterministic, non-empty
    """
    from brain_qa.mock_llm import MockLLM  # type: ignore[import]

    return MockLLM()


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """
    Creates a temporary .data directory structure for testing brain_qa components.

    Returns the path to the temp data directory with:
        .data/
            settings.json  (minimal valid settings)
            storage_manifest.json  (minimal valid manifest)

    Usage:
        def test_indexer(tmp_data_dir):
            assert (tmp_data_dir / "settings.json").exists()
    """
    import json

    data_dir = tmp_path / ".data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Minimal settings.json
    settings = {
        "version": "1.0",
        "index_type": "bm25",
        "corpus_dir": "brain/public",
        "top_k": 5,
    }
    (data_dir / "settings.json").write_text(
        json.dumps(settings, indent=2), encoding="utf-8"
    )

    # Minimal storage_manifest.json
    manifest = {
        "version": "1.0",
        "schema_version": 1,
        "index_built": False,
        "total_documents": 0,
        "index_files": [],
    }
    (data_dir / "storage_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return data_dir


@pytest.fixture
def sample_question() -> str:
    """
    Returns a standard demo question for use in RAG/query tests.

    Usage:
        def test_rag_pipeline(sample_question):
            assert "SIDIX" in sample_question
    """
    return "Apa itu SIDIX?"
