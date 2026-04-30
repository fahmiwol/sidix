"""
Unit tests untuk multi_modal_router — isolated, no Ollama required.
"""

from __future__ import annotations

import pytest

from brain_qa.multi_modal_router import analyze_image, ocr_image


def test_analyze_image_offline_returns_error():
    """Kalau Ollama tidak jalan, analyze_image return ok=False."""
    result = analyze_image(b"fake_image_bytes", prompt="describe")
    assert result["ok"] is False
    assert "Ollama offline" in result["error"] or "vision" in result["error"].lower()


def test_analyze_image_empty_data():
    result = analyze_image(b"")
    assert result["ok"] is False
    assert "empty" in result["error"].lower()


def test_ocr_image_offline_returns_error():
    result = ocr_image(b"fake_image_bytes")
    assert result["ok"] is False
