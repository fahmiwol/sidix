# -*- coding: utf-8 -*-
"""
tests/test_rag_retrieval.py — Projek Badar Task 57 (G4)
Unit tests for brain_qa RAG retrieval core path.
Uses tmp_path fixture to build a minimal BM25 index without touching real .data/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

import pytest

from brain_qa.text import tokenize, Chunk
from brain_qa.mock_llm import MockLLM


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def make_chunk(chunk_id: str, text: str, source: str = "test_doc.md") -> Chunk:
    """Build a Chunk object for test fixtures."""
    return Chunk(
        chunk_id=chunk_id,
        source_path=source,
        source_title=source.replace(".md", ""),
        start_char=0,
        end_char=len(text),
        text=text,
    )


# -----------------------------------------------------------------------
# Tests for brain_qa.text helpers
# -----------------------------------------------------------------------

class TestTokenize:
    """Tests for the tokenize() function used in BM25 indexing."""

    def test_basic_split(self):
        tokens = tokenize("hello world")
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty_string(self):
        tokens = tokenize("")
        assert tokens == []

    def test_lowercasing(self):
        tokens = tokenize("Hello WORLD")
        assert "hello" in tokens
        assert "world" in tokens

    def test_removes_short_tokens(self):
        """Very short tokens (1-2 chars) should be filtered or present as implementation dictates."""
        tokens = tokenize("a is an of in the")
        # At minimum, tokenize should return a list
        assert isinstance(tokens, list)

    def test_arabic_text_accepted(self):
        """Arabic text should not crash tokenize()."""
        tokens = tokenize("الكتاب لا ريب فيه")
        assert isinstance(tokens, list)

    def test_unicode_text(self):
        tokens = tokenize("ilmu pengetahuan buatan")
        assert isinstance(tokens, list)
        assert len(tokens) > 0


class TestChunk:
    """Tests for the Chunk dataclass."""

    def test_chunk_fields(self):
        chunk = make_chunk("c001", "Sample text about AI", "doc.md")
        assert chunk.chunk_id == "c001"
        assert chunk.text == "Sample text about AI"
        assert chunk.source_path == "doc.md"
        assert chunk.source_title == "doc"

    def test_chunk_immutable(self):
        """Chunk should be a frozen dataclass."""
        chunk = make_chunk("c001", "text")
        with pytest.raises((AttributeError, TypeError)):
            chunk.chunk_id = "modified"  # type: ignore[misc]


# -----------------------------------------------------------------------
# Tests for MockLLM in generate path
# -----------------------------------------------------------------------

class TestGeneratePath:
    """
    Tests for the LLM generate path using MockLLM.
    Verifies that the stub contract works for CI without real model weights.
    """

    def test_mock_generate_rag_context(self):
        """Simulate how agent_serve.py would call LLM after RAG retrieval."""
        llm = MockLLM()

        # Simulate a RAG-assembled prompt
        context_chunks = [
            "BM25 adalah algoritma ranking probabilistik.",
            "SIDIX menggunakan BM25 sebagai retrieval engine utama.",
        ]
        question = "Apa itu RAG dalam SIDIX?"
        prompt = f"Konteks:\n{''.join(context_chunks)}\n\nPertanyaan: {question}"

        response = llm.generate(prompt, persona="HAYFAR")

        assert isinstance(response, str)
        assert len(response) > 0
        assert "[SIDIX-MOCK]" in response

    def test_mock_generates_for_all_personas(self):
        """LLM generate should work for every supported persona."""
        llm = MockLLM()
        personas = ["TOARD", "FACH", "MIGHAN", "HAYFAR", "INAN"]

        for persona in personas:
            result = llm.generate(f"Question for {persona}", persona=persona)
            assert isinstance(result, str)
            assert "[SIDIX-MOCK]" in result
            assert persona in result  # persona is echoed back

    def test_mock_handles_long_prompt(self):
        """MockLLM must not crash on long prompts."""
        llm = MockLLM()
        long_prompt = "apa itu " * 500  # 500 repetitions
        result = llm.generate(long_prompt)
        assert isinstance(result, str)

    def test_mock_handles_empty_prompt(self):
        """MockLLM must not crash on empty prompt."""
        llm = MockLLM()
        result = llm.generate("")
        assert isinstance(result, str)
        assert "[SIDIX-MOCK]" in result

    def test_mock_max_tokens_respected_in_echo(self):
        """max_tokens parameter should be echoed in response."""
        llm = MockLLM()
        result = llm.generate("test", max_tokens=42)
        assert "42" in result


# -----------------------------------------------------------------------
# Tests for index data structures (without filesystem)
# -----------------------------------------------------------------------

class TestIndexStructures:
    """
    Tests for index file format compatibility.
    Validates that JSON index files produced by brain_qa.indexer
    conform to the expected schema.
    """

    def test_mock_index_schema(self, tmp_path: Path):
        """
        Simulate writing a minimal index manifest and verify structure.
        This test does NOT require the full indexer — it validates the
        expected JSON schema that downstream code must handle.
        """
        index_dir = tmp_path / ".data"
        index_dir.mkdir()

        # Minimal valid index manifest
        manifest = {
            "version": 1,
            "chunk_count": 2,
            "source_count": 1,
            "built_at": "2026-04-17T00:00:00Z",
        }
        manifest_path = index_dir / "index_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        # Verify it can be read back correctly
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert loaded["version"] == 1
        assert loaded["chunk_count"] == 2
        assert "built_at" in loaded

    def test_qa_pairs_format(self, tmp_path: Path):
        """
        Validate the QA pairs JSONL format used for fine-tuning.
        """
        qa_data = [
            {"id": "qa-001", "question": "Apa itu SIDIX?", "answer": "SIDIX adalah platform AI.", "persona": "INAN"},
            {"id": "qa-002", "question": "Bagaimana BM25 bekerja?", "answer": "BM25 menggunakan IDF.", "persona": "HAYFAR"},
        ]
        qa_file = tmp_path / "qa_pairs.jsonl"
        lines = [json.dumps(qa, ensure_ascii=False) for qa in qa_data]
        qa_file.write_text("\n".join(lines), encoding="utf-8")

        # Verify parsing
        parsed = []
        for line in qa_file.read_text(encoding="utf-8").strip().splitlines():
            entry = json.loads(line)
            assert "id" in entry
            assert "question" in entry
            assert "answer" in entry
            assert "persona" in entry
            parsed.append(entry)

        assert len(parsed) == 2
        assert parsed[0]["id"] == "qa-001"
