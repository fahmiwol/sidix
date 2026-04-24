"""Tests for multimodal_input.py — Jiwa Sprint 3 Fase E."""

import pytest

from brain_qa.multimodal_input import (
    MultimodalInputHandler,
    MultimodalInput,
    process_multimodal,
)


class TestMultimodalInputHandler:
    def test_text_only(self):
        handler = MultimodalInputHandler()
        result = handler.process(MultimodalInput(text="Apa itu ML?", persona="UTZ"))
        assert result.session.persona == "UTZ"
        assert result.session.final_answer is not None
        assert result.fused_context
        assert "text" in result.multimodal_metadata.get("sources", [])

    def test_text_plus_image(self):
        handler = MultimodalInputHandler()
        result = handler.process(MultimodalInput(
            text="Jelaskan gambar ini",
            image_path="/tmp/test.jpg",
            persona="ABOO",
        ))
        assert result.session.persona == "ABOO"
        assert result.vision_caption != ""
        assert "vision" in result.multimodal_metadata.get("sources", [])

    def test_emotional_detection(self):
        handler = MultimodalInputHandler()
        result = handler.process(MultimodalInput(text="aku sangat marah!"))
        assert result.emotional_state
        assert result.emotional_state.get("dominant_emotion") == "angry"

    def test_empty_input_fallback(self):
        handler = MultimodalInputHandler()
        result = handler.process(MultimodalInput(text=""))
        assert result.session is not None

    def test_multimodal_metadata_structure(self):
        handler = MultimodalInputHandler()
        result = handler.process(MultimodalInput(text="Test"))
        meta = result.multimodal_metadata
        assert "fused_context" in meta
        assert "sources" in meta
        assert "cross_modal_conflict" in meta


class TestConvenienceAPI:
    def test_process_multimodal(self):
        d = process_multimodal(text="Halo", persona="ALEY")
        assert d["persona"] == "ALEY"
        assert "session_id" in d
        assert "answer" in d
        assert "fused_context" in d
