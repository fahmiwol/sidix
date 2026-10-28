"""
TTS Engine — SIDIX Sprint 8b
Backend: Piper TTS (self-hosted, CPU-capable, MIT license)
         Fallback: espeak-ng → stub WAV jika Piper tidak terinstall

Voices yang didukung:
  id  → id_ID-ariani-medium  (Bahasa Indonesia)
  en  → en_US-lessac-medium  (English)
  ar  → ar_JO-kareem-low     (Arabic)

Install Piper:
  pip install piper-tts

Atau download binary:
  https://github.com/rhasspy/piper/releases
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/generated/audio")

PIPER_VOICES: dict[str, str] = {
    "id": "id_ID-ariani-medium",
    "en": "en_US-lessac-medium",
    "ar": "ar_JO-kareem-low",
    "ms": "ms_MY-kamarulzaman-medium",
}

# ── Availability check ────────────────────────────────────────────────────────

def piper_available() -> bool:
    """Cek apakah Piper CLI/Python tersedia."""
    # Cek piper CLI
    try:
        result = subprocess.run(
            ["piper", "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Cek piper-tts Python package
    try:
        import piper  # noqa: F401
        return True
    except ImportError:
        pass
    return False


# ── Core synthesize ───────────────────────────────────────────────────────────

def synthesize(
    text: str,
    language: str = "id",
    filename: Optional[str] = None,
    voice: Optional[str] = None,
    speed: float = 1.0,
) -> dict:
    """
    Convert teks ke audio WAV.

    Returns dict:
      path      — Path ke file WAV
      mode      — "piper" | "stub"
      language  — bahasa yang dipakai
      voice     — voice model ID
      duration_estimate — estimasi durasi (detik)
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = f"{uuid.uuid4().hex}.wav"
    out_path = OUTPUT_DIR / filename

    voice_id = voice or PIPER_VOICES.get(language.lower()[:2], PIPER_VOICES["id"])
    word_count = len(text.split())
    # ~150 kata/menit Indonesia, ~140 EN
    wpm = 140 if language == "en" else 150
    duration_estimate = round((word_count / wpm) * 60 / speed, 1)

    if piper_available():
        try:
            _synthesize_piper(text, voice_id, out_path, speed)
            return {
                "path": out_path,
                "mode": "piper",
                "language": language,
                "voice": voice_id,
                "duration_estimate": duration_estimate,
            }
        except Exception as exc:
            logger.warning("Piper synthesis gagal (%s) — fallback stub", exc)

    # Fallback: buat stub WAV (header valid, silent)
    _write_stub_wav(out_path, duration_estimate)
    return {
        "path": out_path,
        "mode": "stub",
        "language": language,
        "voice": voice_id,
        "duration_estimate": duration_estimate,
    }


def _synthesize_piper(text: str, voice_id: str, out_path: Path, speed: float) -> None:
    """Jalankan Piper CLI untuk synthesis."""
    cmd = ["piper", "--model", voice_id, "--output_file", str(out_path)]
    if speed != 1.0:
        cmd += ["--length_scale", str(round(1.0 / speed, 2))]
    process = subprocess.run(
        cmd,
        input=text.encode("utf-8"),
        capture_output=True,
        timeout=60,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Piper error: {process.stderr.decode()[:200]}")
    logger.info("Piper audio: %s", out_path)


def _write_stub_wav(out_path: Path, duration: float) -> None:
    """Tulis WAV header valid dengan 1 detik silence — agar player tidak error."""
    import struct, math
    sample_rate = 22050
    num_samples = max(1, int(sample_rate * min(duration, 5.0)))
    data = b'\x00\x00' * num_samples  # 16-bit PCM silence
    data_size = len(data)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size, b'WAVE',
        b'fmt ', 16, 1, 1,
        sample_rate, sample_rate * 2, 2, 16,
        b'data', data_size,
    )
    out_path.write_bytes(header + data)
    logger.info("Stub WAV written: %s", out_path)


# ── SSML helper ───────────────────────────────────────────────────────────────

def synthesize_ssml(ssml: str, language: str = "id") -> dict:
    """Strip SSML tags dan synthesize sebagai plain text."""
    plain = re.sub(r'<[^>]+>', '', ssml).strip()
    return synthesize(plain, language=language)
