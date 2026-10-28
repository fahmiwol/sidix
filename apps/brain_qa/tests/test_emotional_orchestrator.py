"""Tests for emotional_orchestrator.py — Jiwa Sprint Task 4."""

import pytest

from brain_qa.emotional_orchestrator import (
    EmotionalOrchestrator,
    SenseEmotion,
    orchestrate_emotions,
    _EMOTION_PRIORITY,
    _SOURCE_WEIGHT,
)
from brain_qa.emotional_tone_engine import detect_emotion, Valence


class TestEmotionalOrchestrator:
    def test_single_input(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("aku sangat marah"))
        adapt = orch.orchestrate()
        assert adapt.priority == "high"
        assert "marah" in adapt.tone_hint.lower() or "angry" in adapt.tone_hint.lower()

    def test_voice_wins_conflict(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("wow hebat!"))
        orch.add("voice", detect_emotion("aku kesel banget"))
        adapt = orch.orchestrate()
        assert adapt.priority == "high"

    def test_multiple_negative_boost(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("sedih rasanya"))
        orch.add("voice", detect_emotion("aku cemas nih"))
        adapt = orch.orchestrate()
        assert adapt.priority in ("high", "medium")

    def test_all_positive_low_priority(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("wow keren banget"))
        orch.add("voice", detect_emotion("makasih banyak ya"))
        adapt = orch.orchestrate()
        assert adapt.priority in ("low", "medium")

    def test_empty_inputs(self):
        orch = EmotionalOrchestrator()
        adapt = orch.orchestrate()
        assert adapt.priority == "low"
        assert adapt.tone_hint == ""

    def test_clear_inputs(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("aku marah"))
        orch.clear()
        adapt = orch.orchestrate()
        assert adapt.priority == "low"

    def test_merge_modifiers(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("aku marah"))
        orch.add("text", detect_emotion("aku marah"))
        adapt = orch.orchestrate()
        assert isinstance(adapt.style_modifier, dict)

    def test_summary_structure(self):
        orch = EmotionalOrchestrator()
        orch.add("text", detect_emotion("aku bingung"))
        summary = orch.summary()
        assert "inputs_count" in summary
        assert "inputs" in summary
        assert "global_priority" in summary


class TestSenseEmotion:
    def test_dataclass(self):
        state = detect_emotion("test")
        se = SenseEmotion(source="voice", state=state, weight=1.5)
        assert se.source == "voice"
        assert se.weight == 1.5


class TestConvenienceAPI:
    def test_orchestrate_emotions(self):
        result = orchestrate_emotions([
            {"source": "text", "emotion_text": "aku bingung nih"},
        ])
        assert "tone_hint" in result
        assert "priority" in result
        assert "style_modifier" in result
        assert "summary" in result

    def test_orchestrate_multiple(self):
        result = orchestrate_emotions([
            {"source": "text", "emotion_text": "wow keren"},
            {"source": "voice", "emotion_text": "terima kasih"},
        ])
        assert result["summary"]["inputs_count"] == 2


class TestPriorityConstants:
    def test_angry_highest_priority(self):
        assert _EMOTION_PRIORITY["angry"] > _EMOTION_PRIORITY["frustrated"]
        assert _EMOTION_PRIORITY["angry"] > _EMOTION_PRIORITY["sad"]

    def test_voice_weight_higher_than_text(self):
        assert _SOURCE_WEIGHT["voice"] > _SOURCE_WEIGHT["text"]
