"""
test_persona_research_fanout.py — Sprint 58B tests

Tests for persona_research_fanout.py Phase 2 (Jurus 1000 Bayangan parallel research).
All LLM calls mocked — CI stays fast regardless of Ollama availability.

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

from brain_qa.persona_research_fanout import (
    PERSONA_ANGLES,
    PERSONAS,
    FanoutBundle,
    PersonaContribution,
    _parse_findings,
    _research_one_persona,
    _synthesize_contributions,
    gather,
    synthesize,
)


# ── _parse_findings ───────────────────────────────────────────────────────────

class TestParseFindings:
    def test_dash_bullets(self):
        text = "- Bullet one\n- Bullet two\n- Bullet three"
        result = _parse_findings(text)
        assert result == ["Bullet one", "Bullet two", "Bullet three"]

    def test_star_bullets(self):
        text = "* Star one\n* Star two"
        result = _parse_findings(text)
        assert result == ["Star one", "Star two"]

    def test_mixed_markers(self):
        text = "- dash\n• dot\n* star"
        result = _parse_findings(text)
        assert len(result) == 3

    def test_prose_lines_included(self):
        text = "Some prose\nAnother line"
        result = _parse_findings(text)
        assert "Some prose" in result

    def test_headers_excluded(self):
        text = "# Header\n## Sub\n- item"
        result = _parse_findings(text)
        assert not any(r.startswith("#") for r in result)
        assert "item" in result

    def test_empty_returns_empty(self):
        assert _parse_findings("") == []
        assert _parse_findings("   ") == []

    def test_deduplication(self):
        text = "- same item\n- same item\n- different"
        result = _parse_findings(text)
        assert result.count("same item") == 1
        assert "different" in result

    def test_capped_at_8(self):
        text = "\n".join(f"- item {i}" for i in range(20))
        result = _parse_findings(text)
        assert len(result) <= 8


# ── _research_one_persona ─────────────────────────────────────────────────────

class TestResearchOnePersona:
    def test_success_with_ollama_mock(self):
        """Persona research returns valid PersonaContribution when LLM works."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   return_value=("- Use FastAPI\n- Handle edge cases\n- Write tests", "ollama")):
            contrib = _research_one_persona("ABOO", "t1", "apps/foo.py", "make it production")

        assert contrib.persona == "ABOO"
        assert contrib.angle == PERSONA_ANGLES["ABOO"]
        assert len(contrib.findings) == 3
        assert contrib.confidence == 0.7
        assert contrib.error == ""

    def test_stub_mode_low_confidence(self):
        """When LLM is stub (unavailable), confidence should be 0.1."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   return_value=("", "stub")):
            contrib = _research_one_persona("UTZ", "t2", "apps/bar.py", "make beautiful")

        assert contrib.persona == "UTZ"
        assert contrib.confidence == 0.1

    def test_exception_returns_error_contribution(self):
        """Exception during research returns contribution with error field."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=RuntimeError("connection refused")):
            contrib = _research_one_persona("OOMAR", "t3", "apps/baz.py", "strategize")

        assert contrib.persona == "OOMAR"
        assert contrib.error != ""
        assert contrib.confidence == 0.0

    def test_all_5_personas_valid_angles(self):
        """Each persona has a valid angle defined."""
        for p in PERSONAS:
            assert p in PERSONA_ANGLES
            assert PERSONA_ANGLES[p]


# ── _synthesize_contributions ─────────────────────────────────────────────────

class TestSynthesizeContributions:
    def _contribs(self) -> dict[str, PersonaContribution]:
        return {
            "UTZ": PersonaContribution("UTZ", "creative", ["Use bold colors", "Minimalist layout"], confidence=0.8),
            "ABOO": PersonaContribution("ABOO", "technical", ["Async handler", "Connection pooling"], confidence=0.8),
            "OOMAR": PersonaContribution("OOMAR", "strategy", ["Start with MVP", "Validate with users"], confidence=0.8),
        }

    def test_synthesis_calls_llm(self):
        """Synthesis calls LLM with combined findings."""
        captured = {}
        def fake_llm(system, user, **kwargs):
            captured["user"] = user
            return ("Synthesis: async MVP with bold minimal design.", "ollama")

        with patch("brain_qa.persona_research_fanout._call_research_llm", side_effect=fake_llm):
            result = _synthesize_contributions(self._contribs(), "build feature X", "apps/x.py")

        assert "Synthesis" in result
        # User prompt should contain findings from each persona
        assert "UTZ" in captured["user"]
        assert "ABOO" in captured["user"]

    def test_empty_contributions_graceful(self):
        result = _synthesize_contributions({}, "goal", "path")
        assert "[fanout]" in result.lower() or result == "[fanout] No contributions to synthesize."

    def test_llm_empty_falls_back_to_concat(self):
        """If LLM returns empty, concat findings as fallback."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   return_value=("", "stub")):
            result = _synthesize_contributions(self._contribs(), "goal", "path")

        # Should still have some content from concat fallback
        assert result  # not empty


# ── gather (integration, mocked LLM) ─────────────────────────────────────────

class TestGather:
    def _mock_llm(self, persona_idx: dict | None = None):
        """Returns a side_effect function that returns different findings per call."""
        responses = [
            "- Creative direction: bold\n- Minimize visual noise",
            "- Use async handlers\n- Add connection pooling",
            "- Start small, validate fast\n- Framework: Jobs-to-be-done",
            "- Literature supports modular approach\n- Paper: separation of concerns",
            "- Community prefers simple onboarding\n- Empathy-first design",
            "Synthesis: unified context combining all perspectives.",  # synthesis call
        ]
        call_count = [0]

        def fake_call(system, user, **kwargs):
            i = call_count[0] % len(responses)
            call_count[0] += 1
            return responses[i], "ollama"

        return fake_call

    def test_gather_5_persona_returns_bundle(self):
        """gather() returns FanoutBundle with 5 contributions."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=self._mock_llm()):
            bundle = gather("task-fanout", "apps/foo.py", "make production-ready")

        assert isinstance(bundle, FanoutBundle)
        assert bundle.task_id == "task-fanout"
        assert bundle.total_personas == 5
        assert len(bundle.contributions) == 5
        for p in PERSONAS:
            assert p in bundle.contributions

    def test_gather_sets_synthesis(self):
        """gather() populates synthesis field."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=self._mock_llm()):
            bundle = gather("task-s", "apps/foo.py", "goal")

        assert bundle.synthesis
        assert len(bundle.synthesis) > 5

    def test_gather_sets_sanad_chain(self):
        """gather() populates sanad_chain with per-persona entries."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=self._mock_llm()):
            bundle = gather("task-sanad", "apps/foo.py", "goal")

        assert len(bundle.sanad_chain) == 5
        for entry in bundle.sanad_chain:
            assert "persona" in entry
            assert "confidence" in entry
            assert "findings_count" in entry

    def test_gather_confidence_aggregated(self):
        """gather() confidence = average of successful persona confidences."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=self._mock_llm()):
            bundle = gather("task-conf", "apps/foo.py", "goal")

        assert 0.0 <= bundle.confidence <= 1.0

    def test_gather_subset_personas(self):
        """gather() with subset of personas only invokes those personas."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=self._mock_llm()):
            bundle = gather("task-sub", "apps/foo.py", "goal", personas=("UTZ", "ABOO"))

        assert bundle.total_personas == 2
        assert "UTZ" in bundle.contributions
        assert "ABOO" in bundle.contributions
        assert "OOMAR" not in bundle.contributions

    def test_gather_handles_no_llm_gracefully(self):
        """gather() with stub LLM returns bundle without exception."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   return_value=("", "stub")):
            bundle = gather("task-stub", "apps/foo.py", "goal")

        assert isinstance(bundle, FanoutBundle)
        # confidence may be 0 but not exception
        assert bundle.total_personas == 5

    def test_gather_empty_personas_returns_empty_bundle(self):
        """gather() with empty/invalid personas = empty FanoutBundle."""
        bundle = gather("task-empty", "apps/foo.py", "goal", personas=("UNKNOWN",))
        assert bundle.total_personas == 0
        assert bundle.contributions == {}

    def test_gather_tracks_duration(self):
        """gather() records duration_ms in bundle."""
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   side_effect=self._mock_llm()):
            bundle = gather("task-dur", "apps/foo.py", "goal")

        assert bundle.duration_ms >= 0


# ── synthesize (re-synthesis) ─────────────────────────────────────────────────

class TestSynthesize:
    def test_re_synthesize_existing_bundle(self):
        """synthesize() on existing FanoutBundle produces non-empty string."""
        bundle = FanoutBundle(
            task_id="x",
            contributions={
                "UTZ": PersonaContribution("UTZ", "creative", ["Use gradients"]),
                "ABOO": PersonaContribution("ABOO", "technical", ["Cache results"]),
            }
        )
        with patch("brain_qa.persona_research_fanout._call_research_llm",
                   return_value=("Re-synthesized: cache + gradients.", "ollama")):
            result = synthesize(bundle)
        assert result

    def test_re_synthesize_empty_bundle(self):
        bundle = FanoutBundle(task_id="empty")
        result = synthesize(bundle)
        assert result == ""
