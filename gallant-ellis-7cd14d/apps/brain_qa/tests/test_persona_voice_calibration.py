"""Tests for persona_voice_calibration.py — Jiwa Sprint Phase 1."""

import pytest
import tempfile
import os

from brain_qa.persona_voice_calibration import (
    VoiceCalibrationStore,
    VoiceProfile,
    _parse_explicit_feedback,
    _clamp,
)


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield VoiceCalibrationStore(data_dir=tmpdir)


class TestExplicitFeedbackParser:
    """Test _parse_explicit_feedback heuristic."""

    def test_formal_positive(self):
        dim, delta = _parse_explicit_feedback("lebih formal dong")
        assert dim == "formality"
        assert delta > 0

    def test_formal_negative(self):
        dim, delta = _parse_explicit_feedback("terlalu formal")
        assert dim == "formality"
        assert delta < 0

    def test_casual_positive(self):
        dim, delta = _parse_explicit_feedback("lebih santai ya")
        assert dim == "formality"
        assert delta < 0

    def test_depth_positive(self):
        dim, delta = _parse_explicit_feedback("lebih detail dong")
        assert dim == "depth"
        assert delta > 0

    def test_depth_negative(self):
        dim, delta = _parse_explicit_feedback("terlalu panjang")
        assert dim == "depth"
        assert delta < 0

    def test_warmth_positive(self):
        dim, delta = _parse_explicit_feedback("lebih hangat")
        assert dim == "warmth"
        assert delta > 0

    def test_humor_positive(self):
        dim, delta = _parse_explicit_feedback("lebih lucu dong")
        assert dim == "humor"
        assert delta > 0

    def test_religiosity(self):
        dim, delta = _parse_explicit_feedback("lebih islami")
        assert dim == "religiosity"
        assert delta > 0

    def test_nusantara(self):
        dim, delta = _parse_explicit_feedback("lebih nusantara")
        assert dim == "nusantara_flavor"
        assert delta > 0

    def test_no_match(self):
        dim, delta = _parse_explicit_feedback("saya suka jawabannya")
        assert dim is None
        assert delta == 0.0


class TestClamp:
    def test_clamp_within(self):
        assert _clamp(0.5) == 0.5

    def test_clamp_max(self):
        assert _clamp(1.5) == 1.0

    def test_clamp_min(self):
        assert _clamp(-1.5) == -1.0


class TestVoiceProfile:
    def test_default_values(self):
        p = VoiceProfile(user_id="u1", persona="ABOO")
        assert p.warmth == 0.0
        assert p.formality == 0.0
        assert p.depth == 0.0
        assert p.humor == 0.0
        assert p.religiosity == 0.0
        assert p.nusantara_flavor == 0.0
        assert p.sample_count == 0


class TestVoiceCalibrationStore:
    def test_get_profile_creates_default(self, store):
        p = store.get_profile("user1", "UTZ")
        assert p.user_id == "user1"
        assert p.persona == "UTZ"
        assert p.warmth == 0.0

    def test_record_explicit_updates_dimension(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        p = store.get_profile("user1", "ABOO")
        assert p.formality == pytest.approx(0.15)
        assert p.sample_count == 1

    def test_record_explicit_clamps_at_max(self, store):
        # Apply many positive formality feedbacks
        for _ in range(12):
            store.record_explicit("user1", "ABOO", "lebih formal")
        p = store.get_profile("user1", "ABOO")
        assert p.formality == 1.0

    def test_record_thumbs_up(self, store):
        store.record_thumbs("user1", "ABOO", "up")
        p = store.get_profile("user1", "ABOO")
        assert p.sample_count == 1
        # Distributed across all dimensions
        assert p.warmth > 0
        assert p.formality > 0

    def test_record_thumbs_down(self, store):
        store.record_thumbs("user1", "ABOO", "down")
        p = store.get_profile("user1", "ABOO")
        assert p.sample_count == 1
        assert p.warmth < 0

    def test_record_jariyah_reinforces_direction(self, store):
        # Set warmth positive first
        store.record_explicit("user1", "ABOO", "lebih hangat")
        warmth_before = store.get_profile("user1", "ABOO").warmth
        store.record_jariyah("user1", "ABOO")
        warmth_after = store.get_profile("user1", "ABOO").warmth
        assert warmth_after > warmth_before

    def test_get_voice_hint_multiple(self, store):
        # Need 3x same dimension to cross 0.3 threshold (0.15 * 3 = 0.45)
        for _ in range(3):
            store.record_explicit("user1", "ABOO", "lebih formal")
            store.record_explicit("user1", "ABOO", "lebih hangat")
        hint = store.get_voice_hint("user1", "ABOO")
        assert "formal" in hint
        assert "hangat" in hint
        assert "Preferensi user" in hint

    def test_get_voice_hint_empty(self, store):
        hint = store.get_voice_hint("user1", "ABOO")
        assert hint == ""

    def test_get_modifiers(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        mods = store.get_modifiers("user1", "ABOO")
        assert mods["formality"] == pytest.approx(0.15)
        assert mods["sample_count"] == 1
        assert "warmth" in mods

    def test_reset_profile(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        store.reset_profile("user1", "ABOO")
        p = store.get_profile("user1", "ABOO")
        assert p.formality == 0.0
        assert p.sample_count == 0

    def test_persistence(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        # Create new store pointing to same dir
        store2 = VoiceCalibrationStore(data_dir=store.data_dir)
        p = store2.get_profile("user1", "ABOO")
        assert p.formality == pytest.approx(0.15)

    def test_feedback_log_written(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        assert os.path.exists(store.feedback_path)
        with open(store.feedback_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1
        data = __import__("json").loads(lines[0])
        assert data["feedback_type"] == "explicit"
        assert data["dimension"] == "formality"

    def test_multiple_personas_isolated(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        store.record_explicit("user1", "UTZ", "lebih santai")
        p_aboo = store.get_profile("user1", "ABOO")
        p_utz = store.get_profile("user1", "UTZ")
        assert p_aboo.formality > 0
        assert p_utz.formality < 0

    def test_multiple_users_isolated(self, store):
        store.record_explicit("user1", "ABOO", "lebih formal")
        store.record_explicit("user2", "ABOO", "lebih santai")
        p1 = store.get_profile("user1", "ABOO")
        p2 = store.get_profile("user2", "ABOO")
        assert p1.formality > 0
        assert p2.formality < 0
