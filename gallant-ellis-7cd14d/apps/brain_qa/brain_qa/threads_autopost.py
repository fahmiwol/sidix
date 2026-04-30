"""
threads_autopost.py — Generator konten + publisher ke Threads
==============================================================
Dipakai oleh endpoint POST /admin/threads/auto-content.

Pipeline:
  pick_topic_seed() → pick dari research_notes/ terbaru atau curriculum.
  generate_content(topic_seed, persona) → pakai Ollama lokal, fallback ke template
     statis kalau Ollama tidak tersedia (biar admin UI tetap bisa posting).
  post_to_threads(text) → 2-step Threads API (container → publish).

Rate limiting dilakukan di layer admin_threads.py via posts_today_count().
"""
from __future__ import annotations

import json
import os
import random
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

from .paths import workspace_root

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_MAX_CHARS = 500  # Hard limit Threads text post
TARGET_MIN, TARGET_MAX = 200, 400


# ── Topic seed picker ──────────────────────────────────────────────────────────

def _research_notes_dir() -> Path:
    return workspace_root() / "brain" / "public" / "research_notes"


def pick_topic_seed() -> str:
    """
    Pilih 1 topik dari research note terbaru (by mtime). Ambil judul H1
    atau nama file. Fallback ke topic generik kalau direktori kosong.
    """
    d = _research_notes_dir()
    if not d.exists():
        return "bagaimana AI belajar dari interaksi"
    candidates = sorted(
        [p for p in d.glob("*.md") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:15]
    if not candidates:
        return "bagaimana AI belajar dari interaksi"
    chosen = random.choice(candidates)
    try:
        first = chosen.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in first[:10]:
            m = re.match(r"^#\s+(.+)$", line.strip())
            if m:
                return m.group(1).strip()
    except Exception:
        pass
    # fallback: file name tanpa nomor prefix
    name = chosen.stem
    name = re.sub(r"^\d+_", "", name).replace("_", " ")
    return name


# ── Persona voices ─────────────────────────────────────────────────────────────

_PERSONA_VOICES = {
    "mighan": (
        "Kamu adalah MIGHAN — pembimbing yang hangat, reflektif, membantu orang "
        "berproses. Gaya bahasa: Bahasa Indonesia, empatik, bertanya balik, tidak menggurui. "
        "Hindari jargon teknis kecuali perlu."
    ),
    "inan": (
        "Kamu adalah INAN — asisten ringkas dan praktis. Gaya: Bahasa Indonesia, "
        "singkat, to the point, satu insight per post. Hindari basa-basi."
    ),
}

_FALLBACK_TEMPLATES_MIGHAN = [
    "Saya sedang memikirkan tentang {topic}. Bagi kamu, apa bagian yang paling sulit dipahami? Mari kita bongkar bersama.",
    "Topik hari ini di catatan saya: {topic}. Sering kali kita lupa bahwa belajar bukan soal jawaban, tapi soal bertanya lebih baik.",
    "Tentang {topic}: apa satu pengalaman yang membuat kamu akhirnya 'klik' memahaminya?",
]
_FALLBACK_TEMPLATES_INAN = [
    "{topic} — inti yang sering terlewat: konteks lebih penting dari definisi. Kamu setuju?",
    "Catatan singkat tentang {topic}: fokus pada apa yang bisa kamu uji, bukan yang harus kamu hafal.",
    "Pelajaran hari ini — {topic}. Satu tindakan konkret yang bisa kamu coba hari ini?",
]


def _fallback_generate(topic: str, persona: str) -> str:
    pool = _FALLBACK_TEMPLATES_INAN if persona == "inan" else _FALLBACK_TEMPLATES_MIGHAN
    body = random.choice(pool).format(topic=topic)
    tag = "#SIDIX #BelajarBareng" if persona == "mighan" else "#SIDIX"
    out = f"{body}\n\n{tag}"
    return out[:THREADS_MAX_CHARS]


def _trim_to_length(text: str, target_min: int = TARGET_MIN, target_max: int = TARGET_MAX) -> str:
    text = text.strip()
    if len(text) <= target_max:
        return text
    # Cut at sentence boundary
    cut = text[:target_max]
    for sep in (".", "!", "?", "\n"):
        idx = cut.rfind(sep)
        if idx >= target_min:
            return cut[: idx + 1].strip()
    return cut.rstrip() + "…"


# ── Main generator ─────────────────────────────────────────────────────────────

def generate_content(topic_seed: Optional[str] = None, persona: str = "mighan") -> str:
    """
    Generate post Threads 200-400 char dengan persona INAN/MIGHAN.
    Pakai Ollama lokal. Fallback ke template statis kalau Ollama down.
    """
    topic = (topic_seed or pick_topic_seed()).strip()
    persona = (persona or "mighan").lower()
    if persona not in _PERSONA_VOICES:
        persona = "mighan"

    system = _PERSONA_VOICES[persona]
    user_prompt = (
        f"Tulis satu post Threads (200-400 karakter, Bahasa Indonesia) tentang: {topic}\n\n"
        "Aturan:\n"
        "- Mulai dengan hook yang memancing refleksi.\n"
        "- Tidak menggurui. Tulis sebagai teman sepelajar.\n"
        "- Tutup dengan pertanyaan ringan atau ajakan diskusi.\n"
        "- Tambahkan 1-2 hashtag relevan di akhir.\n"
        "- Jangan gunakan emoji berlebihan (maksimal 1).\n"
        "Output LANGSUNG teks post-nya saja, tanpa pembuka 'Berikut post:' dll."
    )

    try:
        from .ollama_llm import ollama_available, ollama_generate
        if ollama_available():
            text, _mode = ollama_generate(
                prompt=user_prompt,
                system=system,
                max_tokens=220,
                temperature=0.8,
            )
            text = (text or "").strip()
            # Bersihkan quoting markdown yang kadang ikut
            text = re.sub(r'^"+|"+$', "", text).strip()
            if 80 <= len(text) <= THREADS_MAX_CHARS:
                return _trim_to_length(text)
    except Exception:
        pass

    # Fallback
    return _fallback_generate(topic, persona)


# ── Publisher ─────────────────────────────────────────────────────────────────

def _post_step(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def post_to_threads(text: str) -> dict:
    """
    Publish ke Threads via 2-step Graph API (container → publish).
    Return: {ok, id, container_id} atau {ok: False, error}.
    Read env fresh setiap call supaya reflect /admin/threads/connect terbaru.
    """
    # Reload .env jika ada (python-dotenv optional; fallback baca manual)
    token = os.getenv("THREADS_ACCESS_TOKEN", "")
    user_id = os.getenv("THREADS_USER_ID", "")
    if not token or not user_id:
        # Manual read
        env_path = workspace_root() / "apps" / "brain_qa" / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" not in line or line.strip().startswith("#"):
                    continue
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                if k.strip() == "THREADS_ACCESS_TOKEN" and not token:
                    token = v
                elif k.strip() == "THREADS_USER_ID" and not user_id:
                    user_id = v

    if not token or not user_id:
        return {"ok": False, "error": "THREADS_ACCESS_TOKEN/USER_ID tidak dikonfigurasi"}

    payload = text[:THREADS_MAX_CHARS]
    try:
        container = _post_step(
            f"{THREADS_API_BASE}/{user_id}/threads",
            {"media_type": "TEXT", "text": payload, "access_token": token},
        )
        container_id = container.get("id")
        if not container_id:
            return {"ok": False, "error": f"container gagal: {container}"}

        published = _post_step(
            f"{THREADS_API_BASE}/{user_id}/threads_publish",
            {"creation_id": container_id, "access_token": token},
        )
        return {
            "ok": True,
            "id": published.get("id", ""),
            "container_id": container_id,
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:240]
        return {"ok": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
