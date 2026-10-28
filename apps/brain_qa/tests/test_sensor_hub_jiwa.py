"""Tests for Jiwa senses integration into sensor_hub.py — Task 1 & 2."""

import pytest

from brain_qa.sensor_hub import (
    _REGISTRY,
    SenseStatus,
    probe_all,
    health_summary,
    get_sense,
    mark_sense_used,
    _probe_emotional_tone,
    _probe_persona_voice,
    _probe_creative_imagination,
)


class TestJiwaSensesRegistered:
    def test_emotional_tone_registered(self):
        assert "emotional_tone" in _REGISTRY
        sense = _REGISTRY["emotional_tone"]
        assert sense.body_part == "heart"
        assert "detect_tone" in sense.capabilities or "detect_emotion" in sense.capabilities

    def test_persona_voice_registered(self):
        assert "persona_voice" in _REGISTRY
        sense = _REGISTRY["persona_voice"]
        assert sense.body_part == "voice"
        assert "voice_per_persona" in sense.capabilities

    def test_creative_imagination_registered(self):
        assert "creative_imagination" in _REGISTRY
        sense = _REGISTRY["creative_imagination"]
        assert sense.body_part == "mind"
        assert "poetry" in sense.capabilities

    def test_total_senses_count(self):
        # Should have at least 11 senses (Claude's + Kimi's 3)
        assert len(_REGISTRY) >= 11


class TestJiwaProbeFunctions:
    def test_probe_emotional_tone(self):
        ok, detail = _probe_emotional_tone()
        assert ok is True
        assert "ready" in detail.lower()
        assert "excited" in detail

    def test_probe_persona_voice(self):
        ok, detail = _probe_persona_voice()
        assert ok is True
        assert "ready" in detail.lower()

    def test_probe_creative_imagination(self):
        ok, detail = _probe_creative_imagination()
        assert ok is True
        assert "ready" in detail.lower()
        assert "haiku" in detail or "free_verse" in detail


class TestSensorHubIntegration:
    def test_probe_all_includes_jiwa(self):
        result = probe_all()
        slugs = {s["slug"] for s in result["senses"]}
        assert "emotional_tone" in slugs
        assert "persona_voice" in slugs
        assert "creative_imagination" in slugs

    def test_health_summary(self):
        summary = health_summary()
        assert "senses_total" in summary
        assert summary["senses_total"] >= 11
        assert "body_parts_active" in summary

    def test_get_sense(self):
        sense = get_sense("emotional_tone")
        assert sense is not None
        assert sense.slug == "emotional_tone"

    def test_get_sense_missing(self):
        assert get_sense("nonexistent") is None

    def test_mark_sense_used(self):
        mark_sense_used("emotional_tone")
        sense = get_sense("emotional_tone")
        assert sense.last_used_iso != ""

    def test_probe_updates_status(self):
        sense = get_sense("emotional_tone")
        sense.probe()
        assert sense.status in (SenseStatus.ACTIVE, SenseStatus.INACTIVE, SenseStatus.BROKEN)

    def test_emotional_tone_snapshot(self):
        sense = get_sense("emotional_tone")
        snap = sense.snapshot()
        assert snap["slug"] == "emotional_tone"
        assert snap["body_part"] == "heart"
        assert "capabilities" in snap
