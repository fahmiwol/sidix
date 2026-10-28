"""Tests for aesthetic_judgment.py — Jiwa Sprint Task 5."""

import pytest

from brain_qa.aesthetic_judgment import (
    AestheticJudgment,
    AestheticScore,
    judge_multimodal,
    _ARCHETYPE_TONE_COMPAT,
    _TEMPLATE_CHANNEL_COMPAT,
)


class TestAestheticJudgment:
    def test_strong_alignment_passes(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "kopi robusta pegunungan", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Kopi Robusta", "body": "Nikmati kopi robusta dari pegunungan.", "tone": "warm", "channel": "instagram"},
        )
        assert result.passes_threshold is True
        assert result.overall >= 0.6

    def test_weak_alignment_fails(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "kopi robusta", "archetype": "hero", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Teknologi AI", "body": "AI mengubah dunia.", "tone": "formal", "channel": "instagram"},
        )
        assert result.passes_threshold is False
        assert result.overall < 0.6

    def test_aspect_ratio_mismatch(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "kopi", "archetype": "caregiver", "template": "ig_feed", "width": 1920, "height": 1080},
            text={"headline": "Kopi", "body": "Kopi enak.", "tone": "warm", "channel": "instagram"},
        )
        assert result.channel_fit < 1.0

    def test_tone_harmony_good(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "kopi", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Kopi", "body": "Enak", "tone": "warm", "channel": "instagram"},
        )
        assert result.tone_harmony == 1.0

    def test_tone_harmony_weak(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "kopi", "archetype": "hero", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Kopi", "body": "Enak", "tone": "melancholic", "channel": "instagram"},
        )
        assert result.tone_harmony <= 0.5

    def test_custom_threshold(self):
        scorer = AestheticJudgment(threshold=0.9)
        result = scorer.judge(
            visual={"prompt": "kopi robusta pegunungan", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Kopi Robusta", "body": "Nikmati kopi robusta.", "tone": "warm", "channel": "instagram"},
        )
        # High threshold may fail even good content
        assert isinstance(result.passes_threshold, bool)

    def test_feedback_not_empty(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "kopi", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Kopi", "body": "Enak", "tone": "warm", "channel": "instagram"},
        )
        assert len(result.feedback) > 0

    def test_empty_visual_prompt(self):
        scorer = AestheticJudgment()
        result = scorer.judge(
            visual={"prompt": "", "archetype": "unknown", "template": "unknown", "width": 1024, "height": 1024},
            text={"headline": "Test", "body": "Body", "tone": "neutral", "channel": "instagram"},
        )
        assert isinstance(result.overall, float)


class TestConvenienceAPI:
    def test_judge_multimodal(self):
        d = judge_multimodal(
            visual={"prompt": "kopi", "archetype": "caregiver", "template": "ig_feed", "width": 1024, "height": 1024},
            text={"headline": "Kopi", "body": "Enak", "tone": "warm", "channel": "instagram"},
        )
        assert "overall" in d
        assert "passes_threshold" in d
        assert "feedback" in d
        assert d["threshold"] == 0.6


class TestCompatibilityTables:
    def test_archetype_tone_has_entries(self):
        assert len(_ARCHETYPE_TONE_COMPAT) > 0
        assert "caregiver" in _ARCHETYPE_TONE_COMPAT

    def test_template_channel_has_entries(self):
        assert len(_TEMPLATE_CHANNEL_COMPAT) > 0
        assert "ig_feed" in _TEMPLATE_CHANNEL_COMPAT
