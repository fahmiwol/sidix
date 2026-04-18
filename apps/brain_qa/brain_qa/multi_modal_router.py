"""
multi_modal_router.py — SIDIX Multi-Modal Routing Engine
========================================================

Mirror dari multi_llm_router tapi untuk modality di luar teks:
  - image analyze (vision)     — Gemini Vision / Groq Llama Vision / Anthropic
  - image OCR                  — Tesseract lokal / Gemini Vision
  - image generate             — Gemini Imagen / Pollinations free / SDXL API
  - audio transcribe (ASR)     — Groq Whisper Large v3 (gratis) / Gemini
  - audio speak (TTS)          — Gemini TTS / piper lokal / gTTS

Prinsip: coba yang gratis dulu, fallback ke yang terbaik. Setiap modality
bisa dipanggil via satu interface: route_<modality>(...).
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Optional


# ── IMAGE: Analyze (Vision) ───────────────────────────────────────────────────

def analyze_image(
    image_data:  bytes | str,        # bytes OR path OR base64 str
    prompt:      str = "Describe this image in Indonesian.",
    max_tokens:  int = 500,
) -> dict:
    """
    Analisis gambar → teks. Fallback: Gemini → Groq Vision → Anthropic.
    Returns: {ok, text, mode, elapsed_ms}
    """
    img_bytes = _normalize_image(image_data)
    if not img_bytes:
        return {"ok": False, "error": "empty image data"}

    # Try Gemini first (multimodal + vision, free tier)
    if _gemini_ready():
        try:
            t0 = time.time()
            text = _gemini_vision(img_bytes, prompt, max_tokens)
            if text:
                return {
                    "ok":        True,
                    "text":      text,
                    "mode":      "gemini_vision",
                    "elapsed_ms": int((time.time() - t0) * 1000),
                }
        except Exception as e:
            print(f"[multi_modal] gemini vision error: {e}")

    # Groq Llama 3.2 Vision
    if _groq_ready():
        try:
            t0 = time.time()
            text = _groq_vision(img_bytes, prompt, max_tokens)
            if text:
                return {
                    "ok":        True,
                    "text":      text,
                    "mode":      "groq_llama_vision",
                    "elapsed_ms": int((time.time() - t0) * 1000),
                }
        except Exception as e:
            print(f"[multi_modal] groq vision error: {e}")

    # Anthropic fallback
    if _anthropic_ready():
        try:
            t0 = time.time()
            text = _anthropic_vision(img_bytes, prompt, max_tokens)
            if text:
                return {
                    "ok":        True,
                    "text":      text,
                    "mode":      "anthropic_vision",
                    "elapsed_ms": int((time.time() - t0) * 1000),
                }
        except Exception as e:
            print(f"[multi_modal] anthropic vision error: {e}")

    return {"ok": False, "error": "no vision provider available"}


def ocr_image(image_data: bytes | str) -> dict:
    """OCR — ekstrak teks dari gambar. Vision model dengan prompt OCR."""
    return analyze_image(
        image_data,
        prompt=(
            "Extract ALL text visible in this image, verbatim. "
            "Preserve line breaks and layout. If no text, return: <NO_TEXT>"
        ),
        max_tokens=1000,
    )


# ── IMAGE: Generate ────────────────────────────────────────────────────────────

def generate_image(
    prompt:     str,
    size:       str = "1024x1024",
    style:      Optional[str] = None,
) -> dict:
    """
    Generate image dari text prompt. Fallback chain:
      1. Pollinations.ai (free, tanpa API key)
      2. Gemini Imagen (butuh key, premium)

    Returns: {ok, image_url atau image_bytes, mode, elapsed_ms}
    """
    full_prompt = prompt if not style else f"{prompt}, style: {style}"

    # 1. Pollinations (free, cepat, tanpa API key)
    try:
        import httpx
        from urllib.parse import quote
        t0 = time.time()
        w, h = size.split("x")
        url = f"https://image.pollinations.ai/prompt/{quote(full_prompt)}?width={w}&height={h}&nologo=true"
        # Verify it resolves
        with httpx.Client(timeout=30.0) as client:
            r = client.get(url)
            r.raise_for_status()
            img_bytes = r.content
        return {
            "ok":          True,
            "image_bytes": base64.b64encode(img_bytes).decode("ascii"),
            "image_url":   url,
            "mode":        "pollinations_free",
            "elapsed_ms":  int((time.time() - t0) * 1000),
            "prompt":      full_prompt,
        }
    except Exception as e:
        print(f"[multi_modal] pollinations error: {e}")

    # 2. Gemini Imagen (placeholder — butuh google-genai SDK)
    # TODO: implement when needed

    return {"ok": False, "error": "no image gen provider available"}


# ── AUDIO: Transcribe (ASR) ────────────────────────────────────────────────────

def transcribe_audio(
    audio_data: bytes | str,
    language:   str = "id",
) -> dict:
    """
    Audio → teks. Groq Whisper (gratis, cepat ~300x realtime).
    Returns: {ok, text, mode, elapsed_ms}
    """
    audio_bytes = _normalize_audio(audio_data)
    if not audio_bytes:
        return {"ok": False, "error": "empty audio data"}

    if _groq_ready():
        try:
            t0 = time.time()
            import groq as groq_sdk
            client = groq_sdk.Groq(api_key=os.getenv("GROQ_API_KEY", ""))
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes),
                model="whisper-large-v3",
                language=language,
                response_format="text",
            )
            text = transcription if isinstance(transcription, str) else getattr(transcription, "text", "")
            return {
                "ok":         True,
                "text":       text,
                "mode":       "groq_whisper_v3",
                "elapsed_ms": int((time.time() - t0) * 1000),
            }
        except Exception as e:
            print(f"[multi_modal] groq whisper error: {e}")

    return {"ok": False, "error": "no ASR provider available"}


# ── AUDIO: Speak (TTS) ─────────────────────────────────────────────────────────

def synthesize_speech(
    text:      str,
    language:  str = "id",
    voice:     str = "default",
) -> dict:
    """
    Text → audio. Fallback chain:
      1. gTTS (Google TTS free, butuh network)
      2. Gemini TTS (kalau API key ada)

    Returns: {ok, audio_bytes (base64), mode, elapsed_ms, mime_type}
    """
    if not text or len(text.strip()) < 1:
        return {"ok": False, "error": "empty text"}

    # 1. gTTS — library Python gratis, panggil Google Translate TTS
    try:
        from gtts import gTTS
        import io
        t0 = time.time()
        buf = io.BytesIO()
        gTTS(text=text[:2000], lang=language, slow=False).write_to_fp(buf)
        audio_bytes = buf.getvalue()
        return {
            "ok":          True,
            "audio_bytes": base64.b64encode(audio_bytes).decode("ascii"),
            "mime_type":   "audio/mpeg",
            "mode":        "gtts",
            "elapsed_ms":  int((time.time() - t0) * 1000),
            "size_bytes":  len(audio_bytes),
        }
    except ImportError:
        print("[multi_modal] gTTS not installed — pip install gtts")
    except Exception as e:
        print(f"[multi_modal] gTTS error: {e}")

    return {"ok": False, "error": "no TTS provider available"}


# ── Provider Implementations ──────────────────────────────────────────────────

def _gemini_ready() -> bool:
    if not os.getenv("GEMINI_API_KEY", "").strip():
        return False
    try:
        import google.generativeai  # type: ignore  # noqa: F401
        return True
    except ImportError:
        try:
            from google import genai  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return False


def _groq_ready() -> bool:
    if not os.getenv("GROQ_API_KEY", "").strip():
        return False
    try:
        import groq  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


def _anthropic_ready() -> bool:
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        return False
    try:
        import anthropic  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


def _gemini_vision(image_bytes: bytes, prompt: str, max_tokens: int) -> str:
    """Gemini 1.5 Flash Vision — support multimodal."""
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        mime = _detect_image_mime(image_bytes)
        img_part = {"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode()}}
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt, img_part],
        )
        return (resp.text or "").strip()
    except ImportError:
        import google.generativeai as genai_old
        genai_old.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
        mime = _detect_image_mime(image_bytes)
        model = genai_old.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content([
            prompt,
            {"mime_type": mime, "data": image_bytes},
        ])
        return (resp.text or "").strip()


def _groq_vision(image_bytes: bytes, prompt: str, max_tokens: int) -> str:
    """Groq Llama 3.2 Vision."""
    import groq as groq_sdk
    client = groq_sdk.Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    b64 = base64.b64encode(image_bytes).decode("ascii")
    mime = _detect_image_mime(image_bytes)
    data_url = f"data:{mime};base64,{b64}"
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        max_tokens=max_tokens,
    )
    return (completion.choices[0].message.content or "").strip()


def _anthropic_vision(image_bytes: bytes, prompt: str, max_tokens: int) -> str:
    """Anthropic Claude vision."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    b64 = base64.b64encode(image_bytes).decode("ascii")
    mime = _detect_image_mime(image_bytes)
    msg = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=max_tokens,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return (msg.content[0].text or "").strip()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalize_image(data) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        if data.startswith(("http://", "https://")):
            import httpx
            with httpx.Client(timeout=20.0) as client:
                return client.get(data).content
        if data.startswith("data:"):
            data = data.split(",", 1)[1]
        try:
            return base64.b64decode(data)
        except Exception:
            # Treat as file path
            p = Path(data)
            if p.exists():
                return p.read_bytes()
    return b""


def _normalize_audio(data) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        if data.startswith(("http://", "https://")):
            import httpx
            with httpx.Client(timeout=30.0) as client:
                return client.get(data).content
        if data.startswith("data:"):
            data = data.split(",", 1)[1]
        try:
            return base64.b64decode(data)
        except Exception:
            p = Path(data)
            if p.exists():
                return p.read_bytes()
    return b""


def _detect_image_mime(data: bytes) -> str:
    """Deteksi MIME type gambar dari magic bytes."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


# ── Availability Report ────────────────────────────────────────────────────────

def get_modality_availability() -> dict:
    """Report modality apa yang siap dipakai saat ini."""
    try:
        import gtts  # noqa: F401
        gtts_ok = True
    except ImportError:
        gtts_ok = False

    return {
        "vision": {
            "gemini":    _gemini_ready(),
            "groq":      _groq_ready(),
            "anthropic": _anthropic_ready(),
        },
        "ocr":   _gemini_ready() or _groq_ready(),
        "image_gen": {
            "pollinations": True,
            "gemini":       _gemini_ready(),
        },
        "asr":   _groq_ready(),
        "tts":   {"gtts": gtts_ok},
    }
