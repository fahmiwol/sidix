# -*- coding: utf-8 -*-
"""
tests/test_persona.py — SIDIX v0.6.0+
Unit tests for brain_qa.persona — persona routing for SIDIX.

Nama persona diupdate 2026-04-23:
  MIGHAN → AYMAN | TOARD → ABOO | FACH → OOMAR | HAYFAR → ALEY | INAN → UTZ
Nama lama masih backward-compat via _PERSONA_ALIAS.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

import pytest

from brain_qa.persona import normalize_persona, route_persona, PersonaDecision, _PERSONA_SET


class TestNormalizePersona:
    """Tests for normalize_persona()."""

    def test_valid_uppercase(self):
        assert normalize_persona("ALEY") == "ALEY"

    def test_valid_lowercase_converted(self):
        assert normalize_persona("aley") == "ALEY"

    def test_valid_mixedcase(self):
        assert normalize_persona("Oomar") == "OOMAR"

    def test_all_valid_new_personas(self):
        """Nama baru semua valid."""
        for p in ["ABOO", "OOMAR", "AYMAN", "ALEY", "UTZ"]:
            assert normalize_persona(p) == p

    def test_backward_compat_old_names(self):
        """Nama lama diterjemahkan ke nama baru secara otomatis."""
        assert normalize_persona("MIGHAN") == "AYMAN"
        assert normalize_persona("TOARD")  == "ABOO"
        assert normalize_persona("FACH")   == "OOMAR"
        assert normalize_persona("HAYFAR") == "ALEY"
        assert normalize_persona("INAN")   == "UTZ"

    def test_none_returns_none(self):
        assert normalize_persona(None) is None

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Unknown persona"):
            normalize_persona("INVALID_PERSONA")

    def test_persona_set_completeness(self):
        """Ensure SIDIX has exactly 5 personas (nama baru)."""
        assert len(_PERSONA_SET) == 5
        expected = {"ABOO", "OOMAR", "AYMAN", "ALEY", "UTZ"}
        assert _PERSONA_SET == expected


class TestRoutePersona:
    """Tests for route_persona() keyword-based routing."""

    def test_returns_persona_decision(self):
        result = route_persona("apa itu python?")
        assert isinstance(result, PersonaDecision)
        assert result.persona in _PERSONA_SET

    def test_coding_question_routes_aboo(self):
        """Coding → ABOO (engineer/technical)."""
        result = route_persona("bagaimana cara debug bug ini di python?")
        assert result.persona == "ABOO"

    def test_creative_question_routes_utz(self):
        """Creative → UTZ (creative/design)."""
        result = route_persona("bantu desain poster untuk acara")
        assert result.persona == "UTZ"

    def test_research_question_routes_aley(self):
        """Research → ALEY (research/academic)."""
        result = route_persona("tolong bantu riset literatur untuk tesis ini")
        assert result.persona == "ALEY"

    def test_planning_question_routes_oomar(self):
        """Planning → OOMAR (strategic/planning)."""
        result = route_persona("buat roadmap dan strategi untuk proyek")
        assert result.persona == "OOMAR"

    def test_simple_question_routes_ayman(self):
        """Default/simple → AYMAN (general/warm)."""
        result = route_persona("apa kabar?")
        assert result.persona == "AYMAN"

    def test_explicit_prefix_new_name(self):
        """Explicit prefix dengan nama baru."""
        result = route_persona("ABOO: analisis pro kontra PostgreSQL vs MySQL")
        assert result.persona == "ABOO"

    def test_explicit_prefix_old_name_compat(self):
        """Explicit prefix dengan nama lama — backward compat."""
        result = route_persona("TOARD: buat roadmap Q3")
        assert result.persona == "ABOO"

    def test_confidence_is_float(self):
        result = route_persona("apa itu kecerdasan buatan?")
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_scores_dict_has_all_personas(self):
        result = route_persona("test question")
        assert set(result.scores.keys()) == _PERSONA_SET

    def test_reason_is_nonempty_string(self):
        result = route_persona("explain this code")
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0

    def test_persona_not_none(self):
        """route_persona() must always return a non-None persona."""
        result = route_persona("")
        assert result.persona is not None
        assert result.persona in _PERSONA_SET
