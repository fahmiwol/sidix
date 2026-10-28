"""Tests for emotional_tone_engine.py — Jiwa Sprint Phase 2."""

import pytest

from brain_qa.emotional_tone_engine import (
    EmotionalState,
    ToneAdaptation,
    Valence,
    Arousal,
    detect_emotion,
    adapt_tone,
    get_emotion_context,
)


class TestDetectEmotion:
    def test_angry_indonesian(self):
        state = detect_emotion("aku sangat marah dengan jawaban ini")
        assert state.dominant_emotion == "angry"
        assert state.valence == Valence.NEGATIVE
        assert state.arousal == Arousal.EXCITED
        assert state.confidence > 0.3
        assert "marah" in state.matched_keywords

    def test_frustrated_mixed(self):
        state = detect_emotion("gue stuck nih, frustasi banget")
        assert state.dominant_emotion == "frustrated"
        assert state.valence == Valence.NEGATIVE

    def test_sad_indonesian(self):
        state = detect_emotion("sedih rasanya gagal terus")
        assert state.dominant_emotion == "sad"
        assert state.valence == Valence.NEGATIVE
        assert state.arousal == Arousal.CALM

    def test_anxious_indonesian(self):
        state = detect_emotion("aku cemas nih takut salah")
        assert state.dominant_emotion == "anxious"
        assert state.valence == Valence.NEGATIVE

    def test_excited_indonesian(self):
        state = detect_emotion("wow keren banget, gak sabar coba!")
        assert state.dominant_emotion == "excited"
        assert state.valence == Valence.POSITIVE
        assert state.arousal == Arousal.EXCITED

    def test_grateful_indonesian(self):
        state = detect_emotion("alhamdulillah, terima kasih banyak ya")
        assert state.dominant_emotion == "grateful"
        assert state.valence == Valence.POSITIVE

    def test_curious_indonesian(self):
        state = detect_emotion("penasaran gimana caranya")
        assert state.dominant_emotion == "curious"
        assert state.valence == Valence.POSITIVE

    def test_confused_indonesian(self):
        state = detect_emotion("aku bingung nih, gak ngerti")
        assert state.dominant_emotion == "confused"
        assert state.valence == Valence.NEUTRAL

    def test_neutral_question(self):
        state = detect_emotion("jelaskan cara kerja docker")
        assert state.dominant_emotion == "neutral"
        assert state.confidence == 0.0

    def test_empty_text(self):
        state = detect_emotion("")
        assert state.dominant_emotion == "neutral"
        assert state.confidence == 0.0

    def test_english_angry(self):
        state = detect_emotion("I am so angry right now")
        assert state.dominant_emotion == "angry"

    def test_english_frustrated(self):
        state = detect_emotion("This is so frustrating, I'm stuck")
        assert state.dominant_emotion == "frustrated"

    def test_intensifier_boosts_confidence(self):
        without = detect_emotion("aku marah")
        with_int = detect_emotion("aku sangat marah")
        assert with_int.confidence >= without.confidence

    def test_multiple_emotions_pick_dominant(self):
        # Contains both sad and angry words — angry has more patterns matched
        state = detect_emotion("aku sedih tapi juga marah banget")
        assert state.dominant_emotion == "angry"


class TestAdaptTone:
    def test_angry_adaptation(self):
        state = detect_emotion("aku marah")
        adapt = adapt_tone(state)
        assert adapt.priority == "high"
        assert "tenang" in adapt.tone_hint.lower()
        assert adapt.style_modifier["depth"] < 0

    def test_sad_adaptation(self):
        state = detect_emotion("aku sedih")
        adapt = adapt_tone(state)
        assert adapt.priority == "high"
        assert "hangat" in adapt.tone_hint.lower()
        assert adapt.style_modifier["warmth"] > 0

    def test_excited_adaptation(self):
        state = detect_emotion("wow keren banget")
        adapt = adapt_tone(state)
        assert adapt.priority == "medium"
        assert "energik" in adapt.tone_hint.lower()

    def test_grateful_adaptation(self):
        state = detect_emotion("terima kasih")
        adapt = adapt_tone(state)
        assert adapt.priority == "low"
        assert "humble" in adapt.tone_hint.lower()

    def test_neutral_adaptation(self):
        state = detect_emotion("jelaskan docker")
        adapt = adapt_tone(state)
        assert adapt.priority == "low"
        assert adapt.tone_hint == ""


class TestGetEmotionContext:
    def test_structure(self):
        ctx = get_emotion_context("aku sangat marah")
        assert "emotional_state" in ctx
        assert "tone_adaptation" in ctx
        assert ctx["emotional_state"]["dominant_emotion"] == "angry"
        assert ctx["tone_adaptation"]["priority"] == "high"

    def test_neutral_structure(self):
        ctx = get_emotion_context("jelaskan docker")
        assert ctx["emotional_state"]["dominant_emotion"] == "neutral"
        assert ctx["tone_adaptation"]["tone_hint"] == ""


class TestDataclassDefaults:
    def test_emotional_state_defaults(self):
        s = EmotionalState(
            valence=Valence.NEUTRAL,
            arousal=Arousal.CALM,
            dominant_emotion="neutral",
            confidence=0.0,
            matched_keywords=[],
        )
        assert s.confidence == 0.0

    def test_tone_adaptation_defaults(self):
        t = ToneAdaptation(
            tone_hint="test",
            style_modifier={},
            priority="low",
        )
        assert t.priority == "low"
