"""
mock_llm.py — Stub Mock LLM for SIDIX CI (no GPU required).

Usage:
    Set environment variable SIDIX_USE_MOCK_LLM=1 to activate the mock.
    The MockLLM class provides the same interface as the real _llm_generate()
    in agent_serve.py but returns deterministic, keyword-driven fake responses.

    from brain_qa.mock_llm import get_llm_generate_fn
    generate = get_llm_generate_fn()
    response = generate(prompt="What is BM25?", persona="default", max_tokens=256)
"""

from __future__ import annotations

import os
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Pre-defined response corpus (deterministic — safe for assertions in tests)
# ---------------------------------------------------------------------------

_MOCK_RESPONSES: dict[str, str] = {
    "test": (
        "[SIDIX-MOCK] Test response acknowledged. "
        "The system is operating in mock LLM mode (SIDIX_USE_MOCK_LLM=1). "
        "No GPU or model weights are required in this mode."
    ),
    "health": (
        "[SIDIX-MOCK] Health check: OK. "
        "RAG pipeline: ready. BM25 index: ready. Agent loop: ready. "
        "Inference engine: mock (CI mode). All subsystems nominal."
    ),
    "rag": (
        "[SIDIX-MOCK] BM25 Retrieval-Augmented Generation (RAG) explanation: "
        "BM25 is a probabilistic ranking function used to retrieve the most relevant "
        "documents from a corpus given a query. SIDIX uses BM25 as its default "
        "retrieval engine before passing retrieved context to the language model. "
        "This is a mock response; real inference requires a loaded model checkpoint."
    ),
    "persona": (
        "[SIDIX-MOCK] Persona system: SIDIX supports multiple response personas "
        "(e.g., 'default', 'mighan', 'academic'). Each persona adjusts tone, "
        "citation style, and response length. Persona selection is passed per-request. "
        "This is a mock response; real persona conditioning requires the full model."
    ),
    "default": (
        "[SIDIX-MOCK] This is a deterministic mock response from the SIDIX stub LLM. "
        "Set SIDIX_USE_MOCK_LLM=0 and load a real model checkpoint to get actual "
        "language-model output. Prompt received and acknowledged."
    ),
}


def _match_keyword(prompt: str) -> str:
    """Return the best matching mock response key for *prompt*."""
    lowered = prompt.lower()
    for keyword in ("test", "health", "rag", "persona"):
        # Use word-boundary-aware check so "protest" doesn't match "test"
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            return keyword
    return "default"


# ---------------------------------------------------------------------------
# MockLLM class
# ---------------------------------------------------------------------------

class MockLLM:
    """
    Stub language model for CI pipelines that lack GPU / model weights.

    Interface mirrors the real _llm_generate() contract in agent_serve.py:
        generate(prompt, persona, max_tokens) -> str

    Activation:
        Instantiate directly, or let get_llm_generate_fn() choose based on
        the SIDIX_USE_MOCK_LLM environment variable.

    Keyword matching (deterministic):
        "test"    -> CI test acknowledgement
        "health"  -> Health-check status response
        "rag"     -> BM25/RAG explanation
        "persona" -> Persona system explanation
        (other)   -> Generic mock acknowledgement

    The response always starts with "[SIDIX-MOCK]" so tests can assert
    mock vs real responses unambiguously.
    """

    def __init__(self) -> None:
        self._active = True

    # ------------------------------------------------------------------
    # Primary interface (matches _llm_generate signature)
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        persona: str = "default",
        max_tokens: int = 512,
    ) -> str:
        """
        Return a deterministic mock response.

        Args:
            prompt:     The user query / assembled RAG prompt.
            persona:    Named persona (ignored in mock — always "mock" persona).
            max_tokens: Maximum tokens to generate (ignored in mock).

        Returns:
            A string starting with "[SIDIX-MOCK]" that corresponds to the
            first matching keyword in *prompt*, or the default stub response.
        """
        key = _match_keyword(prompt)
        base = _MOCK_RESPONSES[key]

        # Append persona echo so tests can verify persona plumbing
        suffix = f" [persona={persona!r}, max_tokens={max_tokens}]"
        return base + suffix

    # ------------------------------------------------------------------
    # Convenience: callable alias so MockLLM() can be used as a function
    # ------------------------------------------------------------------

    def __call__(
        self,
        prompt: str,
        persona: str = "default",
        max_tokens: int = 512,
    ) -> str:
        return self.generate(prompt=prompt, persona=persona, max_tokens=max_tokens)

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def is_mock(self) -> bool:
        """Always True for MockLLM — used to guard real-model-only code."""
        return True

    def __repr__(self) -> str:
        return "MockLLM(active=True, keywords=['test','health','rag','persona'])"


# ---------------------------------------------------------------------------
# Factory — respects SIDIX_USE_MOCK_LLM env variable
# ---------------------------------------------------------------------------

def get_llm_generate_fn(
    *,
    force_mock: Optional[bool] = None,
) -> "MockLLM | None":
    """
    Return a MockLLM instance when SIDIX_USE_MOCK_LLM=1, else None.

    Callers (e.g. agent_serve.py) should do:

        from brain_qa.mock_llm import get_llm_generate_fn
        _mock = get_llm_generate_fn()
        if _mock:
            _llm_generate = _mock.generate
        else:
            _llm_generate = load_real_model_generate_fn(...)

    Args:
        force_mock: Override env variable. True → always mock, False → never mock,
                    None (default) → read SIDIX_USE_MOCK_LLM.

    Returns:
        MockLLM instance if mock mode is active, else None.
    """
    if force_mock is True:
        return MockLLM()
    if force_mock is False:
        return None

    env_val = os.environ.get("SIDIX_USE_MOCK_LLM", "0").strip()
    if env_val == "1":
        return MockLLM()
    return None


def is_mock_mode() -> bool:
    """
    Quick boolean check — True when SIDIX_USE_MOCK_LLM=1 is set.

    Safe to call from any module that needs to gate GPU-requiring code.
    """
    return os.environ.get("SIDIX_USE_MOCK_LLM", "0").strip() == "1"


# ---------------------------------------------------------------------------
# Module-level singleton (convenience for import-and-use pattern)
# ---------------------------------------------------------------------------

#: Ready-to-use instance when SIDIX_USE_MOCK_LLM=1; None otherwise.
#: Import as: `from brain_qa.mock_llm import mock_llm_instance`
mock_llm_instance: Optional[MockLLM] = get_llm_generate_fn()
