"""Tests for audio tool wiring in agent_tools.py — Jiwa Sprint Phase 4."""

import pytest
from unittest.mock import patch, MagicMock

from brain_qa.agent_tools import (
    TOOL_REGISTRY,
    _tool_text_to_speech,
    _tool_speech_to_text,
    _tool_analyze_audio,
    ToolResult,
)


class TestAudioToolsRegistry:
    def test_text_to_speech_registered(self):
        assert "text_to_speech" in TOOL_REGISTRY
        spec = TOOL_REGISTRY["text_to_speech"]
        assert spec.permission == "open"
        assert "text" in spec.params

    def test_speech_to_text_registered(self):
        assert "speech_to_text" in TOOL_REGISTRY
        spec = TOOL_REGISTRY["speech_to_text"]
        assert spec.permission == "open"
        assert "path" in spec.params

    def test_analyze_audio_registered(self):
        assert "analyze_audio" in TOOL_REGISTRY
        spec = TOOL_REGISTRY["analyze_audio"]
        assert spec.permission == "open"
        assert "path" in spec.params

    def test_total_tool_count(self):
        # Verify we added 3 new tools
        assert len(TOOL_REGISTRY) >= 48


class TestTextToSpeech:
    @patch("brain_qa.audio_capability.synthesize_speech")
    def test_success(self, mock_synth):
        mock_synth.return_value = {
            "ok": True,
            "data": {"backend": "coqui-tts-xtts", "out_path": "out.wav", "text_len": 42},
            "fallback_instructions": "",
            "citations": [],
        }
        result = _tool_text_to_speech({"text": "Halo dunia", "lang": "id"})
        assert result.success is True
        assert "Halo dunia" in result.output or "Text-to-Speech" in result.output
        assert "coqui-tts-xtts" in result.output

    @patch("brain_qa.audio_capability.synthesize_speech")
    def test_fallback(self, mock_synth):
        mock_synth.return_value = {
            "ok": False,
            "data": None,
            "fallback_instructions": "Library TTS belum terpasang.",
            "citations": [],
        }
        result = _tool_text_to_speech({"text": "Halo"})
        assert result.success is False
        assert "Library TTS" in result.error

    def test_empty_text(self):
        result = _tool_text_to_speech({"text": ""})
        assert result.success is False
        assert "wajib diisi" in result.error


class TestSpeechToText:
    @patch("brain_qa.audio_capability.transcribe_audio")
    def test_success(self, mock_trans):
        mock_trans.return_value = {
            "ok": True,
            "data": {
                "backend": "faster-whisper",
                "language": "id",
                "duration": 12.5,
                "text": "Halo apa kabar",
                "segments": [{"start": 0.0, "end": 2.5, "text": "Halo"}],
            },
            "fallback_instructions": "",
            "citations": [],
        }
        result = _tool_speech_to_text({"path": "test.wav", "lang": "id"})
        assert result.success is True
        assert "Halo apa kabar" in result.output
        assert "faster-whisper" in result.output

    @patch("brain_qa.audio_capability.transcribe_audio")
    def test_fallback(self, mock_trans):
        mock_trans.return_value = {
            "ok": False,
            "data": None,
            "fallback_instructions": "File tidak ditemukan.",
            "citations": [],
        }
        result = _tool_speech_to_text({"path": "missing.wav"})
        assert result.success is False
        assert "File tidak ditemukan" in result.error

    def test_empty_path(self):
        result = _tool_speech_to_text({"path": ""})
        assert result.success is False
        assert "wajib diisi" in result.error


class TestAnalyzeAudio:
    @patch("brain_qa.audio_capability.analyze_audio")
    def test_success(self, mock_ana):
        mock_ana.return_value = {
            "ok": True,
            "data": {
                "backend": "librosa",
                "sample_rate": 22050,
                "duration_sec": 30.5,
                "tempo_bpm": 120.0,
                "n_beats": 64,
                "spectral_centroid_mean": 1500.0,
                "rms_mean": 0.05,
                "zcr_mean": 0.1,
            },
            "fallback_instructions": "",
            "citations": [],
        }
        result = _tool_analyze_audio({"path": "music.wav"})
        assert result.success is True
        assert "librosa" in result.output
        assert "120.0" in result.output
        assert "22050" in result.output

    @patch("brain_qa.audio_capability.analyze_audio")
    def test_fallback(self, mock_ana):
        mock_ana.return_value = {
            "ok": False,
            "data": None,
            "fallback_instructions": "librosa belum terpasang.",
            "citations": [],
        }
        result = _tool_analyze_audio({"path": "test.wav"})
        assert result.success is False
        assert "librosa" in result.error

    def test_empty_path(self):
        result = _tool_analyze_audio({"path": ""})
        assert result.success is False
        assert "wajib diisi" in result.error
