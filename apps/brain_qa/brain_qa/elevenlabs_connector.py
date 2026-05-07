"""
elevenlabs_connector.py — SIDIX ElevenLabs Guru Trainer (TTS + Voice Clone)
===========================================================================
Integrasi ElevenLabs API untuk voice-based training content.

Env var:
  ELEVENLABS_API_KEY — API key dari https://elevenlabs.io/app/settings/api-keys

Fitur:
  1. TTS (Text-to-Speech) — generate audio dari text
  2. List Voices — daftar voice yang tersedia
  3. Voice Clone — upload audio untuk create custom voice guru
  4. Voice Library — browse community voices
  5. User Info — cek quota & usage

Guru Trainer use cases:
  - Generate audio lesson dalam berbagai bahasa
  - Clone voice guru untuk konsistensi
  - Sound effects untuk konten edukasi interaktif
  - Voice-over untuk video training

Security:
  - API key JANGAN di-commit ke repo
  - Gunakan env var atau .env file (masuk .gitignore)

Research notes:
  - 321 ElevenLabs Guru Trainer integration
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
SAFETY_MAX_CHARS = 5000  # TTS char limit safety


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


def _get_api_key() -> str | None:
    return os.environ.get("ELEVENLABS_API_KEY") or None


def _http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    data: bytes | None = None,
    json_data: dict | None = None,
    timeout: int = 60,
) -> dict | bytes:
    """HTTP request ke ElevenLabs API."""
    req_headers = headers or {}
    req_headers.setdefault("xi-api-key", _get_api_key() or "")

    body = data
    if json_data:
        body = json.dumps(json_data).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, method=method, headers=req_headers, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.read()
        if "application/json" in content_type:
            return json.loads(raw.decode("utf-8"))
        return raw  # binary audio


# ── 1. TTS (Text-to-Speech) ───────────────────────────────────────────────────


def generate_tts(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default: Rachel
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    use_speaker_boost: bool = True,
    output_format: str = "mp3_44100_128",
) -> dict:
    """Generate audio dari text menggunakan ElevenLabs TTS.

    Params:
      text: Text yang mau di-convert (max ~5000 chars)
      voice_id: ID voice (default Rachel). Use list_voices() untuk lihat semua.
      model_id: Model TTS (eleven_multilingual_v2 = best quality, multi-language)
      stability: 0.0-1.0 (higher = lebih stabil, less expressive)
      similarity_boost: 0.0-1.0 (higher = lebih mirip original voice)
      style: 0.0-1.0 (higher = lebih ekspresif)
      output_format: mp3_44100_128, mp3_44100_192, pcm_16000, dll
    """
    api_key = _get_api_key()
    if not api_key:
        return _fallback(
            "ELEVENLABS_API_KEY tidak di-set. Dapatkan di https://elevenlabs.io/app/settings/api-keys"
        )

    if not text.strip():
        return _fallback("text wajib diisi")

    if len(text) > SAFETY_MAX_CHARS:
        return _fallback(f"Text terlalu panjang ({len(text)} chars). Max: {SAFETY_MAX_CHARS}")

    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost,
        },
        "output_format": output_format,
    }

    try:
        audio_bytes = _http_request(url, method="POST", json_data=payload)
        if isinstance(audio_bytes, dict):
            # Error response (JSON)
            return _fallback(f"TTS error: {audio_bytes}")

        # Save to temp file
        ext = output_format.split("_")[0] if "_" in output_format else "mp3"
        output_path = f"dataset/tts_output_{hash(text) % 1000000:06d}.{ext}"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        return _ok({
            "voice_id": voice_id,
            "text_length": len(text),
            "model": model_id,
            "output_path": output_path,
            "size_bytes": len(audio_bytes),
            "format": output_format,
            "note": f"Audio saved to {output_path}",
        })
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return _fallback(f"TTS HTTP {e.code}: {body[:200]}")
    except Exception as exc:
        return _fallback(f"TTS error: {exc}")


# ── 2. List Voices ────────────────────────────────────────────────────────────


def list_voices() -> dict:
    """List semua voice yang tersedia (default + custom + community).

    Returns: voice_id, name, category (premade/cloned/community), language, gender, description
    """
    api_key = _get_api_key()
    if not api_key:
        return _fallback("ELEVENLABS_API_KEY tidak di-set")

    try:
        data = _http_request(f"{ELEVENLABS_BASE}/voices")
        voices = data.get("voices", [])
        result = []
        for v in voices:
            labels = v.get("labels", {})
            result.append({
                "voice_id": v.get("voice_id"),
                "name": v.get("name"),
                "category": v.get("category"),  # premade / cloned / generated / professional
                "description": v.get("description", ""),
                "gender": labels.get("gender", "unknown"),
                "age": labels.get("age", "unknown"),
                "accent": labels.get("accent", "unknown"),
                "language": labels.get("language", "unknown"),
                "use_case": labels.get("use_case", "unknown"),
                "preview_url": v.get("preview_url"),
            })

        # Group by category
        by_category = {}
        for v in result:
            cat = v.get("category", "other")
            by_category.setdefault(cat, []).append(v)

        return _ok({
            "total_voices": len(result),
            "by_category": by_category,
            "voices": result,
            "recommended_for_guru": [
                v for v in result
                if v.get("category") == "premade" and v.get("use_case") in ("narration", "education", "conversational")
            ][:10],
        })
    except Exception as exc:
        return _fallback(f"List voices error: {exc}")


# ── 3. Voice Clone ────────────────────────────────────────────────────────────


def clone_voice(
    name: str,
    description: str = "",
    file_paths: list[str] | None = None,
    labels: dict | None = None,
) -> dict:
    """Clone voice dari audio samples.

    Untuk create voice guru/trainer yang konsisten.
    Requires: 1+ audio file (MP3/WAV, ~30 detik per file, clear voice)

    Params:
      name: Nama voice (e.g. "Guru_Matematika_Pak_Joko")
      description: Deskripsi voice
      file_paths: List path ke audio files (MP3/WAV)
      labels: {"gender": "male", "age": "middle_aged", "accent": "indonesian"}
    """
    api_key = _get_api_key()
    if not api_key:
        return _fallback("ELEVENLABS_API_KEY tidak di-set")

    if not name.strip():
        return _fallback("name wajib diisi")

    if not file_paths:
        return _fallback("file_paths wajib diisi (minimal 1 audio file)")

    # Build multipart form data (manual, tanpa external libs)
    boundary = "----ElevenLabsBoundary"
    body_parts = []

    # name
    body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="name"\r\n\r\n{name}\r\n'.encode())

    # description
    if description:
        body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="description"\r\n\r\n{description}\r\n'.encode())

    # labels
    if labels:
        body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="labels"\r\n\r\n{json.dumps(labels)}\r\n'.encode())

    # files
    for fp in file_paths:
        if not os.path.exists(fp):
            return _fallback(f"File tidak ditemukan: {fp}")
        with open(fp, "rb") as f:
            file_data = f.read()
        filename = os.path.basename(fp)
        content_type = "audio/mpeg" if fp.endswith(".mp3") else "audio/wav"
        body_parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{filename}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'.encode()
        )
        body_parts.append(file_data)
        body_parts.append(b'\r\n')

    body_parts.append(f'--{boundary}--\r\n'.encode())
    body = b''.join(body_parts)

    url = f"{ELEVENLABS_BASE}/voices/add"
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "xi-api-key": api_key,
    }

    try:
        req = urllib.request.Request(url, method="POST", headers=headers, data=body)
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return _ok({
                "voice_id": result.get("voice_id"),
                "name": name,
                "description": description,
                "labels": labels,
                "files_uploaded": len(file_paths),
                "note": f"Voice '{name}' berhasil di-clone. Gunakan voice_id ini untuk TTS.",
            })
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return _fallback(f"Clone voice HTTP {e.code}: {body[:300]}")
    except Exception as exc:
        return _fallback(f"Clone voice error: {exc}")


# ── 4. User Info ──────────────────────────────────────────────────────────────


def get_user_info() -> dict:
    """Get user subscription info: quota, usage, tier."""
    api_key = _get_api_key()
    if not api_key:
        return _fallback("ELEVENLABS_API_KEY tidak di-set")

    try:
        data = _http_request(f"{ELEVENLABS_BASE}/user/subscription")
        return _ok({
            "tier": data.get("tier"),
            "character_count": data.get("character_count", 0),
            "character_limit": data.get("character_limit", 0),
            "character_usage_percentage": round(
                data.get("character_count", 0) / max(data.get("character_limit", 1), 1) * 100, 1
            ),
            "voice_limit": data.get("voice_limit"),
            "professional_voice_limit": data.get("professional_voice_limit"),
            "can_extend_character_limit": data.get("can_extend_character_limit", False),
            "allowed_to_extend_character_limit": data.get("allowed_to_extend_character_limit", False),
            "next_character_count_reset_unix": data.get("next_character_count_reset_unix"),
            "note": f"Usage: {data.get('character_count', 0)}/{data.get('character_limit', 0)} chars",
        })
    except Exception as exc:
        return _fallback(f"User info error: {exc}")


# ── 5. Sound Effects ──────────────────────────────────────────────────────────


def generate_sound_effect(
    text: str,
    duration_seconds: float | None = None,
    prompt_influence: float = 0.3,
) -> dict:
    """Generate sound effect dari text description.

    Examples:
      - "Rain falling on a tin roof"
      - "Classroom applause"
      - "Writing on chalkboard"
    """
    api_key = _get_api_key()
    if not api_key:
        return _fallback("ELEVENLABS_API_KEY tidak di-set")

    if not text.strip():
        return _fallback("text wajib diisi (deskripsi sound effect)")

    payload = {"text": text, "prompt_influence": prompt_influence}
    if duration_seconds:
        payload["duration_seconds"] = duration_seconds

    try:
        audio_bytes = _http_request(
            f"{ELEVENLABS_BASE}/sound-generation",
            method="POST",
            json_data=payload,
        )
        if isinstance(audio_bytes, dict):
            return _fallback(f"Sound effect error: {audio_bytes}")

        output_path = f"dataset/sfx_{hash(text) % 1000000:06d}.mp3"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        return _ok({
            "description": text,
            "output_path": output_path,
            "size_bytes": len(audio_bytes),
            "note": f"Sound effect saved to {output_path}",
        })
    except Exception as exc:
        return _fallback(f"Sound effect error: {exc}")


# ── 6. Health Check ───────────────────────────────────────────────────────────


def elevenlabs_health_check() -> dict:
    """Check ElevenLabs API connectivity dan quota."""
    api_key = _get_api_key()
    if not api_key:
        return _fallback(
            "ELEVENLABS_API_KEY tidak di-set.\n"
            "Dapatkan di https://elevenlabs.io/app/settings/api-keys"
        )

    try:
        user = get_user_info()
        voices = list_voices()
        return _ok({
            "connected": user.get("ok", False),
            "user": user.get("data") if user.get("ok") else None,
            "voices_available": len(voices.get("data", {}).get("voices", [])) if voices.get("ok") else 0,
            "api_key_valid": True,
        })
    except Exception as exc:
        return _fallback(f"Health check error: {exc}", data={"connected": False, "api_key_valid": False})
