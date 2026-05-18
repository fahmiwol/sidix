"""Tests for sensor_fusion.py — Jiwa Sprint 3 Fase C."""

import pytest

from brain_qa.sensor_fusion import (
    SensorFusionEngine,
    SenseInput,
    FusedContext,
    fuse_sense_inputs,
)


class TestSensorFusionEngine:
    def test_text_only(self):
        engine = SensorFusionEngine()
        inputs = [SenseInput(source="text", data="Apa itu ML?")]
        fused = engine.fuse(inputs)
        assert fused.primary_query == "Apa itu ML?"
        assert not fused.cross_modal_conflict
        assert "text" in fused.sources

    def test_text_plus_emotional(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Apa itu ML?"),
            SenseInput(source="emotional", data="User marah karena penjelasan tidak jelas"),
        ]
        fused = engine.fuse(inputs)
        assert fused.emotional_modifier
        assert "marah" in fused.emotional_modifier.lower() or "emosi" in fused.emotional_modifier.lower()

    def test_text_plus_vision(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Jelaskan grafik ini"),
            SenseInput(source="vision", data="Grafik batang penjualan naik 50%"),
        ]
        fused = engine.fuse(inputs)
        assert fused.vision_context
        assert "Grafik" in fused.unified_prompt

    def test_cross_modal_conflict(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Apa itu photosynthesis?"),
            SenseInput(source="vision", data="Kucing tidur di sofa merah"),
        ]
        fused = engine.fuse(inputs)
        assert fused.cross_modal_conflict is True
        assert len(fused.conflict_details) > 0

    def test_no_conflict_when_related(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Jelaskan grafik penjualan"),
            SenseInput(source="vision", data="Grafik batang penjualan naik"),
        ]
        fused = engine.fuse(inputs)
        assert fused.cross_modal_conflict is False

    def test_audio_context(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Halo"),
            SenseInput(source="audio", data="Halo SIDIX, tolong bantu"),
        ]
        fused = engine.fuse(inputs)
        assert fused.audio_context
        assert "Halo SIDIX" in fused.audio_context

    def test_empty_inputs(self):
        engine = SensorFusionEngine()
        fused = engine.fuse([])
        assert fused.primary_query == ""
        assert fused.unified_prompt == ""

    def test_multiple_text_highest_confidence_wins(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Low confidence", confidence=0.3),
            SenseInput(source="text", data="High confidence", confidence=0.9),
        ]
        fused = engine.fuse(inputs)
        assert fused.primary_query == "High confidence"

    def test_sources_list(self):
        engine = SensorFusionEngine()
        inputs = [
            SenseInput(source="text", data="Q"),
            SenseInput(source="vision", data="V"),
            SenseInput(source="audio", data="A"),
        ]
        fused = engine.fuse(inputs)
        assert set(fused.sources) == {"text", "vision", "audio"}


class TestConvenienceAPI:
    def test_fuse_sense_inputs(self):
        d = fuse_sense_inputs([
            {"source": "text", "data": "Hello"},
            {"source": "emotional", "data": "User happy"},
        ])
        assert d["primary_query"] == "Hello"
        assert "emotional" in d["sources"]
        assert "unified_prompt" in d
