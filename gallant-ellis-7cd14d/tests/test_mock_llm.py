# -*- coding: utf-8 -*-
"""
tests/test_mock_llm.py — Projek Badar Task 57 (G4)
Unit tests for brain_qa.mock_llm — MockLLM stub for CI without GPU.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure the brain_qa package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

import pytest

from brain_qa.mock_llm import MockLLM, get_llm_generate_fn, is_mock_mode, mock_llm_instance


class TestMockLLM:
    """Tests for the MockLLM class."""

    def test_instantiate(self):
        llm = MockLLM()
        assert llm is not None

    def test_is_mock_always_true(self):
        llm = MockLLM()
        assert llm.is_mock() is True

    def test_generate_returns_string(self):
        llm = MockLLM()
        result = llm.generate("test query")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_prefix(self):
        """All mock responses must start with [SIDIX-MOCK] for unambiguous detection."""
        llm = MockLLM()
        result = llm.generate("hello world")
        assert result.startswith("[SIDIX-MOCK]"), f"Expected [SIDIX-MOCK] prefix, got: {result[:50]}"

    def test_keyword_test(self):
        llm = MockLLM()
        result = llm.generate("run a test please")
        assert "[SIDIX-MOCK]" in result
        # Should match "test" keyword
        assert "mock" in result.lower() or "ci" in result.lower() or "test" in result.lower()

    def test_keyword_health(self):
        llm = MockLLM()
        result = llm.generate("health check status")
        assert "[SIDIX-MOCK]" in result
        assert "health" in result.lower()

    def test_keyword_rag(self):
        llm = MockLLM()
        result = llm.generate("explain rag retrieval")
        assert "[SIDIX-MOCK]" in result
        assert "rag" in result.lower() or "bm25" in result.lower() or "retrieval" in result.lower()

    def test_keyword_persona(self):
        llm = MockLLM()
        result = llm.generate("what is persona routing")
        assert "[SIDIX-MOCK]" in result
        assert "persona" in result.lower()

    def test_default_response_for_unknown(self):
        llm = MockLLM()
        result = llm.generate("something completely unrelated xyz123")
        assert "[SIDIX-MOCK]" in result

    def test_persona_echo_in_response(self):
        """Response should echo back the persona name."""
        llm = MockLLM()
        result = llm.generate("test", persona="HAYFAR")
        assert "HAYFAR" in result

    def test_max_tokens_echo(self):
        llm = MockLLM()
        result = llm.generate("test", max_tokens=128)
        assert "128" in result

    def test_callable_alias(self):
        """MockLLM() should be callable directly, same as .generate()."""
        llm = MockLLM()
        result1 = llm.generate("health query")
        result2 = llm("health query")
        assert result1 == result2

    def test_deterministic_output(self):
        """Same prompt → same response every time."""
        llm = MockLLM()
        r1 = llm.generate("test prompt", persona="FACH")
        r2 = llm.generate("test prompt", persona="FACH")
        assert r1 == r2

    def test_repr(self):
        llm = MockLLM()
        assert "MockLLM" in repr(llm)


class TestGetLlmGenerateFn:
    """Tests for the get_llm_generate_fn factory."""

    def test_force_mock_true(self):
        result = get_llm_generate_fn(force_mock=True)
        assert result is not None
        assert isinstance(result, MockLLM)

    def test_force_mock_false(self):
        result = get_llm_generate_fn(force_mock=False)
        assert result is None

    def test_env_var_1_activates_mock(self, monkeypatch):
        monkeypatch.setenv("SIDIX_USE_MOCK_LLM", "1")
        result = get_llm_generate_fn()
        assert result is not None
        assert isinstance(result, MockLLM)

    def test_env_var_0_returns_none(self, monkeypatch):
        monkeypatch.setenv("SIDIX_USE_MOCK_LLM", "0")
        result = get_llm_generate_fn()
        assert result is None


class TestIsMockMode:
    """Tests for the is_mock_mode() convenience function."""

    def test_env_0(self, monkeypatch):
        monkeypatch.setenv("SIDIX_USE_MOCK_LLM", "0")
        assert is_mock_mode() is False

    def test_env_1(self, monkeypatch):
        monkeypatch.setenv("SIDIX_USE_MOCK_LLM", "1")
        assert is_mock_mode() is True

    def test_env_unset(self, monkeypatch):
        monkeypatch.delenv("SIDIX_USE_MOCK_LLM", raising=False)
        assert is_mock_mode() is False
