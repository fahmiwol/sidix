"""
multi_modal_router.py — SIDIX Multi-Modal Router (Local-only)

Standing Alone rule:
- Tidak boleh memakai vendor AI API untuk vision/ASR/TTS/image-gen.
- Modul ini hanya menyediakan jalur lokal (best-effort) atau mengembalikan
  error yang jelas kalau capability belum terpasang.
"""

from __future__ import annotations

import base64
import logging
import os
import time
from pathlib import Path

from .ollama_llm import ollama_available, ollama_generate_vision

log = logging.getLogger("sidix.multimodal")


def analyze_image(
    image_data: bytes | str,
    prompt: str = "Describe this image in Indonesian.",
    max_tokens: int = 500,
    prefer_local: bool = True,
) -> dict:
    """
    Vision → text (lokal).

    Current implementation:
    - Uses Ollama vision if available via `ollama_llm.ollama_generate_vision`.
    - Otherwise returns a consistent error.
    """
    _ = prefer_local
    img_bytes = _normalize_image(image_data)
    if not img_bytes:
        return {"ok": False, "error": "empty image data"}

    if not ollama_available():
        return {"ok": False, "error": "Ollama offline — vision tidak tersedia. Install: https://ollama.ai"}

    b64 = base64.b64encode(img_bytes).decode("utf-8")
    try:
        text, mode = ollama_generate_vision(
            image_b64=b64,
            prompt=prompt,
            max_tokens=max_tokens,
        )
        if mode == "mock_error":
            return {"ok": False, "error": text}
        return {"ok": True, "text": text, "mode": mode}
    except Exception as e:
        log.exception("Vision error")
        return {"ok": False, "error": str(e)}


def ocr_image(image_data: bytes | str) -> dict:
    """OCR via local vision prompt."""
    return analyze_image(
        image_data,
        prompt=(
            "Extract ALL text visible in this image, verbatim. "
            "Preserve line breaks and layout. If no text, return: <NO_TEXT>"
        ),
        max_tokens=1000,
    )


def transcribe_audio(audio_data: bytes | str) -> dict:
    """
    ASR (lokal) — belum terpasang.

    Disediakan sebagai interface; implementasi diarahkan ke Whisper.cpp lokal
    atau pipeline internal (tanpa vendor API).
    """
    _ = audio_data
    return {"ok": False, "error": "local ASR not installed"}


def speak_text(text: str, voice: str = "id") -> dict:
    """
    TTS (lokal) — belum terpasang.

    Disediakan sebagai interface; implementasi diarahkan ke Piper TTS lokal.
    """
    _ = voice
    if not (text or "").strip():
        return {"ok": False, "error": "empty text"}
    return {"ok": False, "error": "local TTS not installed"}


def capabilities() -> dict:
    """Expose capability flags untuk health/UX."""
    return {
        "vision": {"local": False},
        "ocr": {"local": False},
        "asr": {"local": False},
        "tts": {"local": False},
    }


def _normalize_image(image_data: bytes | str) -> bytes:
    """
    Normalize inputs:
    - bytes: returned as-is
    - path: read bytes
    - base64 string: decode (supports data URLs)
    """
    if isinstance(image_data, (bytes, bytearray)):
        return bytes(image_data)

    s = (image_data or "").strip()
    if not s:
        return b""

    # data URL
    if s.startswith("data:") and "base64," in s:
        s = s.split("base64,", 1)[1]

    # file path
    p = Path(s)
    if p.exists() and p.is_file():
        try:
            return p.read_bytes()
        except Exception:
            return b""

    # base64
    try:
        return base64.b64decode(s, validate=True)
    except Exception:
        return b""

