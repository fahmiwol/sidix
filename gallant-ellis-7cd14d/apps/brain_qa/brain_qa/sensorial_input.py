"""
sensorial_input.py — Multimodal Sensorial Foundation (Vision + Audio + Voice)
================================================================================

Per SIDIX_DEFINITION_20260426 Daily Capability #10:
> "Multitasking AI agent, semua indera aktif, melihat, mendengar, bicara,
>  merasakan, mampu menggerakan tangan, dan menyelesaikan banyak tugas sekaligus."

Plus DIRECTION_LOCK Q3-Q4 P2:
> "Sensorial multimodal (Step-Audio + Qwen-VL)"

Modul ini implementasi MINIMAL FOUNDATION — receive multimodal input + bridge
ke processing pipeline. Real model integration (Qwen2.5-VL, Step-Audio,
Whisper) akan attach via env config + worker, BUKAN inline di FastAPI.

3 channel sensorial:

1. **VISION (👁 melihat)** — image upload (base64 / URL):
   - Receive → save ke `.data/sensorial/images/` (temp, auto-delete 24h)
   - Pre-process: resize, format normalize, EXIF strip (privacy)
   - Forward ke VLM endpoint (kalau available) atau caption fallback
   - Future Q3: Qwen2.5-VL native integration

2. **AUDIO (👂 mendengar)** — audio upload (mp3/wav/webm):
   - Receive → save ke `.data/sensorial/audio/` (temp)
   - Pre-process: normalize sample rate, format convert (ffmpeg if available)
   - Forward ke STT endpoint (Whisper local atau Step-Audio)
   - Future Q3: Step-Audio bidirectional

3. **VOICE (🗣 bicara)** — text → speech:
   - Reuse existing `tts_engine.py` (Piper, 4 bahasa)
   - Future Q3: Step-Audio voice cloning + emotional prosody

**Privacy + Storage**:
- Auto-delete uploaded media setelah 24 jam (cron sweep)
- Strip EXIF metadata dari image (no GPS leak)
- Hash filename (no original filename leak)
- Size limit per upload: 5 MB image, 10 MB audio
- Per-user rate limit (Bearer JWT required)

**NO inline LLM call**: module ini coordinate input/output, actual
inference di worker yang attach via WebSocket atau worker queue. Untuk
vol 15 = STUB foundation, full integration Q3 2026.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import mimetypes
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class SensorialInput:
    """1 multimodal input record."""
    id: str
    ts: str
    user_id: str
    channel: str             # "vision" | "audio" | "voice_request"
    storage_path: str         # relative path
    size_bytes: int
    mime_type: str = ""
    duration_seconds: float = 0.0  # untuk audio
    width: int = 0                  # untuk image
    height: int = 0
    caption: str = ""               # hasil VLM / STT (kalau ready)
    processing_status: str = "received"  # received | processed | failed | expired
    error: str = ""


# ── Path helpers ───────────────────────────────────────────────────────────────

def _sensorial_dir() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data" / "sensorial"
    (d / "images").mkdir(parents=True, exist_ok=True)
    (d / "audio").mkdir(parents=True, exist_ok=True)
    return d


def _index_path() -> Path:
    return _sensorial_dir() / "_index.jsonl"


# ── Limits ─────────────────────────────────────────────────────────────────────

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB
TTL_HOURS = 24


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_filename(content_bytes: bytes, ext: str) -> str:
    """Generate filename dari content hash (no original name leak)."""
    h = hashlib.sha256(content_bytes).hexdigest()[:16]
    return f"{h}.{ext.lstrip('.')}"


def _detect_image_dims(image_bytes: bytes) -> tuple[int, int]:
    """Best-effort detect width/height dari image bytes (no PIL dep required)."""
    # PNG: \x89PNG... bytes 16-24 = width, height (big endian uint32)
    if image_bytes.startswith(b"\x89PNG"):
        try:
            import struct
            width = struct.unpack(">I", image_bytes[16:20])[0]
            height = struct.unpack(">I", image_bytes[20:24])[0]
            return width, height
        except Exception:
            pass
    # JPEG: scan for SOF markers
    if image_bytes.startswith(b"\xff\xd8"):
        try:
            i = 2
            while i < len(image_bytes) - 8:
                if image_bytes[i] == 0xFF and image_bytes[i + 1] in (0xC0, 0xC2):
                    import struct
                    height = struct.unpack(">H", image_bytes[i + 5:i + 7])[0]
                    width = struct.unpack(">H", image_bytes[i + 7:i + 9])[0]
                    return width, height
                i += 1
        except Exception:
            pass
    return 0, 0


def _strip_exif(image_bytes: bytes) -> bytes:
    """Strip EXIF dari JPEG (privacy). Best-effort, return original kalau gagal."""
    if not image_bytes.startswith(b"\xff\xd8"):
        return image_bytes  # not JPEG, no EXIF
    # Remove APP1 (EXIF) segment
    try:
        result = bytearray(image_bytes[:2])  # SOI marker
        i = 2
        while i < len(image_bytes) - 1:
            if image_bytes[i] == 0xFF:
                marker = image_bytes[i + 1]
                if marker == 0xE1:  # APP1 = EXIF
                    # Skip this segment
                    import struct
                    seg_len = struct.unpack(">H", image_bytes[i + 2:i + 4])[0]
                    i += 2 + seg_len
                    continue
                elif marker in (0xDA,):  # SOS = start of scan, copy rest
                    result.extend(image_bytes[i:])
                    return bytes(result)
            result.append(image_bytes[i])
            i += 1
        return bytes(result)
    except Exception:
        return image_bytes


# ── Vision channel ────────────────────────────────────────────────────────────

def receive_image(
    *,
    image_bytes: Optional[bytes] = None,
    image_base64: str = "",
    image_url: str = "",
    user_id: str = "",
    auto_strip_exif: bool = True,
) -> SensorialInput:
    """
    Receive image dari 3 source: bytes / base64 / URL fetch.
    Save ke `.data/sensorial/images/<hash>.<ext>` setelah strip EXIF.

    Returns SensorialInput record.
    """
    record = SensorialInput(
        id=f"sens_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
        user_id=user_id[:32],
        channel="vision",
        storage_path="",
        size_bytes=0,
        mime_type="",
    )

    # Resolve content
    content: Optional[bytes] = None
    if image_bytes:
        content = image_bytes
    elif image_base64:
        try:
            # Strip data URL prefix kalau ada
            cleaned = re.sub(r"^data:image/\w+;base64,", "", image_base64.strip())
            content = base64.b64decode(cleaned)
        except Exception as e:
            record.processing_status = "failed"
            record.error = f"base64 decode fail: {e}"
            return record
    elif image_url:
        try:
            import httpx
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                r = client.get(image_url, headers={"User-Agent": "SIDIX-Bot/2.0"})
                if r.status_code == 200:
                    content = r.content
                else:
                    record.processing_status = "failed"
                    record.error = f"URL fetch HTTP {r.status_code}"
                    return record
        except Exception as e:
            record.processing_status = "failed"
            record.error = f"URL fetch fail: {e}"
            return record

    if not content:
        record.processing_status = "failed"
        record.error = "no image content provided"
        return record

    # Size check
    if len(content) > MAX_IMAGE_BYTES:
        record.processing_status = "failed"
        record.error = f"size {len(content)} > {MAX_IMAGE_BYTES} max"
        return record

    record.size_bytes = len(content)

    # Detect format + EXIF strip
    if content.startswith(b"\x89PNG"):
        ext = "png"
        mime = "image/png"
    elif content.startswith(b"\xff\xd8"):
        ext = "jpg"
        mime = "image/jpeg"
        if auto_strip_exif:
            content = _strip_exif(content)
            record.size_bytes = len(content)
    elif content.startswith(b"GIF8"):
        ext = "gif"
        mime = "image/gif"
    elif content.startswith(b"RIFF") and b"WEBP" in content[:12]:
        ext = "webp"
        mime = "image/webp"
    else:
        record.processing_status = "failed"
        record.error = "unsupported image format (PNG/JPEG/GIF/WebP only)"
        return record

    record.mime_type = mime

    # Dims
    w, h = _detect_image_dims(content)
    record.width = w
    record.height = h

    # Save
    filename = _hash_filename(content, ext)
    save_path = _sensorial_dir() / "images" / filename
    try:
        save_path.write_bytes(content)
        record.storage_path = f"images/{filename}"
        record.processing_status = "received"
    except Exception as e:
        record.processing_status = "failed"
        record.error = f"save fail: {e}"
        return record

    # Stub caption (real VLM integration future)
    record.caption = (
        f"[{ext.upper()} image, {w}×{h}, {len(content)//1024}KB] "
        f"VLM caption pending — Qwen2.5-VL integration target Q3 2026."
    )

    _persist_record(record)
    return record


# ── Audio channel ─────────────────────────────────────────────────────────────

def receive_audio(
    *,
    audio_bytes: Optional[bytes] = None,
    audio_base64: str = "",
    user_id: str = "",
) -> SensorialInput:
    """
    Receive audio dari bytes atau base64.
    Save ke `.data/sensorial/audio/<hash>.<ext>`.
    """
    record = SensorialInput(
        id=f"sens_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
        user_id=user_id[:32],
        channel="audio",
        storage_path="",
        size_bytes=0,
    )

    content: Optional[bytes] = None
    if audio_bytes:
        content = audio_bytes
    elif audio_base64:
        try:
            cleaned = re.sub(r"^data:audio/\w+;base64,", "", audio_base64.strip())
            content = base64.b64decode(cleaned)
        except Exception as e:
            record.processing_status = "failed"
            record.error = f"base64 decode fail: {e}"
            return record

    if not content:
        record.processing_status = "failed"
        record.error = "no audio content"
        return record

    if len(content) > MAX_AUDIO_BYTES:
        record.processing_status = "failed"
        record.error = f"size {len(content)} > {MAX_AUDIO_BYTES} max"
        return record

    record.size_bytes = len(content)

    # Detect format dari magic bytes
    if content.startswith(b"ID3") or content[:2] == b"\xff\xfb":
        ext = "mp3"
        mime = "audio/mpeg"
    elif content.startswith(b"RIFF") and b"WAVE" in content[:12]:
        ext = "wav"
        mime = "audio/wav"
    elif content.startswith(b"OggS"):
        ext = "ogg"
        mime = "audio/ogg"
    elif content[:4] == b"\x1aE\xdf\xa3":  # WebM/Matroska
        ext = "webm"
        mime = "audio/webm"
    else:
        record.processing_status = "failed"
        record.error = "unsupported audio format (MP3/WAV/OGG/WebM)"
        return record

    record.mime_type = mime

    filename = _hash_filename(content, ext)
    save_path = _sensorial_dir() / "audio" / filename
    try:
        save_path.write_bytes(content)
        record.storage_path = f"audio/{filename}"
        record.processing_status = "received"
    except Exception as e:
        record.processing_status = "failed"
        record.error = f"save fail: {e}"
        return record

    # Stub transcription (real STT integration future)
    record.caption = (
        f"[{ext.upper()} audio, {len(content)//1024}KB] "
        f"STT pending — Step-Audio / Whisper integration target Q3 2026."
    )

    _persist_record(record)
    return record


# ── Voice synthesis (TTS) — reuse existing tts_engine ────────────────────────

def synthesize_voice(text: str, *, language: str = "id", user_id: str = "") -> dict:
    """
    Text → speech via existing tts_engine (Piper).
    Returns dict {ok, audio_path?, error?}.

    Future Q3: Step-Audio voice cloning + emotional prosody.
    """
    if not text or len(text) > 1000:
        return {"ok": False, "error": "text empty or too long (max 1000)"}

    try:
        from . import tts_engine
        result = tts_engine.synthesize(text=text, language=language)  # type: ignore
        if isinstance(result, dict) and result.get("audio_path"):
            return {"ok": True, "audio_path": result["audio_path"], "engine": "piper"}
        return {"ok": False, "error": "tts_engine returned invalid", "raw": str(result)[:200]}
    except ImportError:
        return {"ok": False, "error": "tts_engine not available"}
    except Exception as e:
        return {"ok": False, "error": f"synthesis fail: {e}"}


# ── Persistence + cleanup ─────────────────────────────────────────────────────

def _persist_record(record: SensorialInput) -> None:
    try:
        with _index_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
    except Exception:
        pass


def cleanup_expired(*, ttl_hours: int = TTL_HOURS) -> dict:
    """Sweep expired media files (cron-friendly)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)
    deleted_files = 0
    deleted_bytes = 0

    for sub in ["images", "audio"]:
        sub_dir = _sensorial_dir() / sub
        if not sub_dir.exists():
            continue
        for f in sub_dir.iterdir():
            if not f.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff:
                    deleted_bytes += f.stat().st_size
                    f.unlink()
                    deleted_files += 1
            except Exception:
                continue

    return {
        "deleted_files": deleted_files,
        "deleted_bytes": deleted_bytes,
        "ttl_hours": ttl_hours,
    }


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Untuk admin dashboard."""
    out = {"vision_count": 0, "audio_count": 0, "by_status": {}}
    path = _index_path()
    if not path.exists():
        return out

    by_status: dict[str, int] = {}
    by_channel: dict[str, int] = {}
    total_size = 0

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    s = e.get("processing_status", "?")
                    by_status[s] = by_status.get(s, 0) + 1
                    c = e.get("channel", "?")
                    by_channel[c] = by_channel.get(c, 0) + 1
                    total_size += int(e.get("size_bytes", 0))
                except Exception:
                    continue
    except Exception:
        return out

    return {
        "total": sum(by_channel.values()),
        "by_channel": by_channel,
        "by_status": by_status,
        "total_size_kb": total_size // 1024,
    }


__all__ = [
    "SensorialInput",
    "receive_image",
    "receive_audio",
    "synthesize_voice",
    "cleanup_expired",
    "stats",
]
