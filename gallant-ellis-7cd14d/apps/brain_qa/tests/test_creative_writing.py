"""Tests for creative_writing.py — Jiwa Sprint Phase 3."""

import pytest

from brain_qa.creative_writing import (
    CreativeWritingEngine,
    CreativeForm,
    PoetryForm,
    NarrativeArc,
    PoetrySpec,
    SceneBeat,
    ScreenplaySpec,
    LoreCategory,
    CharacterArchetype,
    CreativeBrief,
    generate_creative_brief,
    _brief_to_dict,
)


class TestCreativeWritingEngine:
    def test_short_story_generation(self):
        engine = CreativeWritingEngine(persona="ABOO")
        brief = engine.generate(
            form=CreativeForm.SHORT_STORY,
            prompt="cerita tentang anak yang kehilangan rumah",
            title="Rumah di Ujung Jalan",
        )
        assert brief.form == CreativeForm.SHORT_STORY
        assert brief.title == "Rumah di Ujung Jalan"
        assert brief.narrative_arc is not None
        assert brief.narrative_arc.setup
        assert brief.narrative_arc.climax
        assert brief.narrative_arc.resolution
        assert brief.cqf_score > 0
        assert "casual" in brief.persona_voice.lower()

    def test_poetry_generation_pantun(self):
        engine = CreativeWritingEngine(persona="UTZ")
        brief = engine.generate(
            form=CreativeForm.POETRY,
            prompt="puisi tentang senja",
            extra_context={"poetry_form": "pantun"},
        )
        assert brief.poetry_spec is not None
        assert brief.poetry_spec.form == PoetryForm.PANTUN
        assert brief.poetry_spec.lines_target == 4
        assert brief.poetry_spec.rhyme_scheme == "AABB"

    def test_poetry_generation_haiku(self):
        engine = CreativeWritingEngine(persona="OOMAR")
        brief = engine.generate(
            form=CreativeForm.POETRY,
            prompt="haiku tentang salju",
        )
        assert brief.poetry_spec is not None
        assert brief.poetry_spec.form == PoetryForm.HAIKU
        assert brief.poetry_spec.lines_target == 3
        assert brief.poetry_spec.meter_hint == "syllable_5_7_5"

    def test_screenplay_generation(self):
        engine = CreativeWritingEngine(persona="AYMAN")
        brief = engine.generate(
            form=CreativeForm.SCREENPLAY_SCENE,
            prompt="adegan pertemuan pertama",
            extra_context={"location": "Rumah Tua", "time": "Night"},
        )
        assert brief.screenplay_spec is not None
        assert "RUMAH TUA" in brief.screenplay_spec.scene_heading
        assert "NIGHT" in brief.screenplay_spec.scene_heading
        assert len(brief.screenplay_spec.beats) > 0
        assert brief.screenplay_spec.emotional_arc

    def test_worldbuilding_generation(self):
        engine = CreativeWritingEngine(persona="ALEY")
        brief = engine.generate(
            form=CreativeForm.WORLDBUILDING_LORE,
            prompt="dunia di mana manusia berkomunikasi dengan hewan",
            extra_context={"lore_categories": ["geography", "magic_system"]},
        )
        assert len(brief.lore_categories) == 2
        assert brief.lore_categories[0].category == "geography"
        assert brief.lore_categories[1].category == "magic_system"

    def test_character_profile_generation(self):
        engine = CreativeWritingEngine(persona="ABOO")
        brief = engine.generate(
            form=CreativeForm.CHARACTER_PROFILE,
            prompt="karakter petani dengan rahasia",
            extra_context={"name": "Siti Aminah", "archetype": "The Caregiver"},
        )
        assert brief.character_profile is not None
        assert brief.character_profile.name == "Siti Aminah"
        assert brief.character_profile.archetype == "The Caregiver"
        assert brief.character_profile.motivation
        assert brief.character_profile.flaw

    def test_theme_extraction(self):
        engine = CreativeWritingEngine()
        theme = engine._extract_theme("cerita tentang cinta dan pengorbanan")
        assert theme in ("love", "redemption")

    def test_tone_inference_melancholic(self):
        engine = CreativeWritingEngine()
        tone = engine._infer_tone("cerita sedih dan tragis")
        assert tone == "melancholic"

    def test_tone_inference_humorous(self):
        engine = CreativeWritingEngine()
        tone = engine._infer_tone("cerita lucu komedi")
        assert tone == "humorous"

    def test_cqf_estimation(self):
        engine = CreativeWritingEngine()
        brief = engine.generate(
            form=CreativeForm.SHORT_STORY,
            prompt="test",
        )
        assert 0.5 <= brief.cqf_score <= 1.0

    def test_persona_voice_notes(self):
        engine = CreativeWritingEngine(persona="ABOO")
        assert "casual" in engine.voice_note.lower()

    def test_unknown_persona_defaults(self):
        engine = CreativeWritingEngine(persona="UNKNOWN")
        assert engine.voice_note == ""


class TestBriefToDict:
    def test_short_story_dict(self):
        engine = CreativeWritingEngine()
        brief = engine.generate(
            form=CreativeForm.SHORT_STORY,
            prompt="test",
        )
        d = _brief_to_dict(brief)
        assert d["form"] == "short_story"
        assert "narrative_arc" in d
        assert "setup" in d["narrative_arc"]

    def test_poetry_dict(self):
        engine = CreativeWritingEngine()
        brief = engine.generate(
            form=CreativeForm.POETRY,
            prompt="test",
            extra_context={"poetry_form": "haiku"},
        )
        d = _brief_to_dict(brief)
        assert d["poetry_spec"]["form"] == "haiku"
        assert d["poetry_spec"]["lines_target"] == 3

    def test_character_dict(self):
        engine = CreativeWritingEngine()
        brief = engine.generate(
            form=CreativeForm.CHARACTER_PROFILE,
            prompt="test",
            extra_context={"name": "Test"},
        )
        d = _brief_to_dict(brief)
        assert d["character_profile"]["name"] == "Test"


class TestConvenienceAPI:
    def test_generate_creative_brief(self):
        d = generate_creative_brief(
            form="poetry",
            prompt="haiku tentang salju",
            persona="OOMAR",
        )
        assert d["form"] == "poetry"
        assert d["poetry_spec"]["form"] == "haiku"
        assert "persona_voice" in d

    def test_generate_creative_brief_screenplay(self):
        d = generate_creative_brief(
            form="screenplay_scene",
            prompt="adegan konfrontasi",
            location="Kantor",
        )
        assert d["form"] == "screenplay_scene"
        assert "KANTOR" in d["screenplay_spec"]["scene_heading"]
