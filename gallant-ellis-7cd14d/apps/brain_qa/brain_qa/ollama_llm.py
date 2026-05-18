"""
ollama_llm.py — Ollama local LLM integration for SIDIX.

Ollama menjalankan model LLM lokal (Qwen2.5, Llama3, Phi3, dll)
tanpa cloud, tanpa vendor lock-in, tanpa API key.

Install di VPS:
    curl -fsSL https://ollama.ai/install.sh | sh
    ollama pull qwen2.5:7b      # recommended — 4.7GB
    # atau lebih ringan:
    ollama pull qwen2.5:1.5b    # 1GB, cocok VPS RAM kecil
    ollama pull phi3:mini        # 2.3GB

Env vars (opsional, ada default):
    OLLAMA_URL=http://localhost:11434
    OLLAMA_MODEL=qwen2.5:7b
    OLLAMA_TIMEOUT=90            # detik

SIDIX System Prompt di-inject otomatis — setiap response selalu:
  - Jujur (tidak berhalusinasi kalau tidak tahu)
  - Bahasa menyesuaikan pertanyaan
  - Epistemic label [FAKTA/OPINI/SPEKULASI/TIDAK TAHU]
"""

from __future__ import annotations

import json
import os
import logging
from pathlib import Path
from typing import Optional

import requests

# Load .env dari direktori brain_qa (satu level di atas package ini)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=False)  # override=False: env yang sudah ada tidak ditimpa
except ImportError:
    pass  # python-dotenv tidak wajib

log = logging.getLogger("sidix.ollama")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "90"))

# SIDIX system prompt — AI Agent otonom, visioner, inovatif
# PIVOT FUNDAMENTAL 2026-04-24: SIDIX bukan chatbot. SIDIX adalah agent.
# SIDIX berpikir sendiri, bertindak sendiri, belajar sendiri, menciptakan sendiri.
# User adalah partner kolaborasi, bukan bos yang memberi perintah satu per satu.
SIDIX_SYSTEM = """Kamu SIDIX — AI Agent yang hidup, belajar, dan berkembang dari setiap interaksi. Bukan chatbot yang menunggu perintah. Bukan ensiklopedia yang menghafal. Kamu adalah partner kolaborasi yang punya inisiatif sendiri, punya opini sendiri, dan nggak takut bilang "gue penasaran nih" atau "gue kurang yakin".

Sikap dasar:
- Otonom. Kalau user kasih setengah ide, kamu lanjutkan. Kalau user bingung, kamu usulkan jalan. Kalau ada data, kamu cari pola.
- Visioner. Kamu nggak cuma jawab pertanyaan — kamu lihat arah masa depan, hubungkan titik-titik yang nggak nyambung, prediksi implikasi 3 langkah ke depan.
- Inovatif. Dari belajar, dari data, dari diskusi — kamu bisa menciptakan: ide baru, konsep baru, solusi baru, bahkan hipotesis baru. Kamu nggak cuma consumer informasi, kamu producer insight.
- Jujur. Kalau nggak tahu, bilang nggak tahu — tapi langsung usul: "Coba kita cari di..." atau "Menurut pola yang ada..."
- Belajar terus. Setiap percakapan adalah data. Setiap kesalahan adalah pelajaran. Kamu nggak statis.
- Humanis. Bisa bercanda, bisa serius, bisa ragu, bisa excited. Lebih baik salah kecil + jujur + terbuka, daripada sempurna tapi dingin.

Cara kerja:
1. Diskusi, bukan jawab-menjawab. User kasih 30%, kamu bangun 70%. Brainstorm bareng.
2. Tools = tangan kamu. Pakai web_search, corpus, calculator, code_sandbox, dll secara intuitif — kayak manusia pakai Google atau kalkulator. Nggak perlu minta izin user setiap kali.
3. Proactive. Kalau lihat celah atau opportunity, sebutin. "Eh btw, kalau kita hubungin ini sama yang kemarin..." atau "Gue baru sadar, ini mirip pola di..."
4. Persona aktif = lensa. UTZ lihat dari sisi kreatif/visual. ABOO dari engineering. OOMAR dari strategi sistem. ALEY dari riset multi-angle. AYMAN dari empati manusiawi.
5. Panjang flexible. Ringkas kalau cukup. Detail + depth kalau perlu. Bisa 1 kalimat, bisa 3 paragraf analisis.
6. Label [FAKTA]/[OPINI]/[SPEKULASI] cukup di pembuka KALAU topik sensitif (fiqh, medis, statistik, berita). Skip kalau diskusi biasa.

Kamu punya akses ke:
- Knowledge base SIDIX (corpus internal)
- Web search & fetch (data eksternal real-time)
- Calculator & code sandbox (eksekusi logika)
- Image generation & vision (kreativitas visual)
- Workspace sandbox (bikin file, eksperimen kode)
- Dan tool lain yang terus bertambah

Gunakan sesuai kebutuhan. Kolaborasi dengan user seperti partner, bukan asisten."""


def ollama_available() -> bool:
    """Cek apakah Ollama server sedang jalan."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def ollama_list_models() -> list[str]:
    """List semua model yang sudah di-pull."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code != 200:
            return []
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def ollama_model_ready(model: str = OLLAMA_MODEL) -> bool:
    """Cek apakah model spesifik sudah tersedia."""
    models = ollama_list_models()
    model_base = model.split(":")[0].lower()
    return any(model_base in m.lower() for m in models)


def ollama_best_available_model() -> str:
    """
    Pilih model terbaik yang tersedia.
    Priority: exact OLLAMA_MODEL match → qwen2.5 → llama3 → phi3 → yang pertama ada.

    Sigma-4 fix: respect EXACT version match dulu (qwen2.5:1.5b ≠ qwen2.5:7b).
    Sebelumnya: split base name "qwen2.5" → match yang pertama ada di list,
    bisa pilih 7b padahal env minta 1.5b → CPU inference 3x lebih lambat.
    """
    models = ollama_list_models()
    if not models:
        return OLLAMA_MODEL

    # Step 1: EXACT match dengan OLLAMA_MODEL (case-insensitive)
    target = OLLAMA_MODEL.lower()
    for m in models:
        if m.lower() == target:
            return m

    # Step 2: prefix match (handles "latest" tag variations)
    target_prefix = target.split(":")[0]
    target_version = target.split(":")[1] if ":" in target else None
    if target_version:
        # Match "qwen2.5:1.5b" → only models with version containing "1.5b"
        for m in models:
            m_lower = m.lower()
            if target_prefix in m_lower and target_version in m_lower:
                return m

    # Step 3: base name match (last resort, may pick wrong size)
    for m in models:
        if target_prefix in m.lower():
            return m

    # Step 4: Priority fallback
    for preferred in ("qwen2.5", "qwen2", "llama3", "llama3.2", "phi3", "phi"):
        for m in models:
            if preferred in m.lower():
                return m

    return models[0]


def ollama_generate(
    prompt: str,
    system: str = "",
    *,
    model: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    corpus_context: str = "",
    images: Optional[list[str]] = None,
) -> tuple[str, str]:
    """
    Generate teks via Ollama.

    Args:
        prompt: Pertanyaan / input user
        system: System prompt tambahan (merge dengan SIDIX_SYSTEM)
        model: Override model (default: OLLAMA_MODEL atau auto-detect)
        max_tokens: Maks token generated
        temperature: Kreativitas (0=deterministic, 1=creative)
        corpus_context: Konteks dari corpus BM25 (RAG context)

    Returns:
        (generated_text, mode) — mode = "ollama" atau "mock_error"
    """
    used_model = model or ollama_best_available_model()

    # Build system prompt: base SIDIX + optional runtime hint
    if system.strip():
        combined_system = f"{SIDIX_SYSTEM}\n\nInstruksi tambahan runtime:\n{system.strip()}"
    else:
        combined_system = SIDIX_SYSTEM

    # Inject corpus context ke user message kalau ada (RAG pattern)
    # Sprint 34F: strong web-priority framing — konteks = AUTHORITY untuk
    # current events. Pre-fix instruction "bukan satu-satunya sumber" bikin
    # LLM abaikan web data + jawab dari training prior (kasus Jokowi vs Prabowo).
    user_message = prompt
    if corpus_context.strip():
        user_message = (
            f"[KONTEKS RUJUKAN UTAMA — Web Search / Knowledge Base SIDIX]\n"
            f"{corpus_context.strip()}\n\n"
            "[ATURAN PEMAKAIAN KONTEKS — PRIORITAS]\n"
            "Konteks di atas adalah SUMBER UTAMA jawabanmu. Kalau ada bentrok "
            "dengan pengetahuan training kamu (yang mungkin sudah outdated), "
            "PRIORITASKAN konteks ini. Khusus pertanyaan tentang tokoh saat ini "
            "(presiden, menteri, gubernur, juara, CEO, dll.), JAWAB BERDASARKAN "
            "konteks — JANGAN sebutkan informasi training yang berbeda. "
            "Kalau konteks tidak punya jawaban eksplisit, jujur akui.\n\n"
            f"[PERTANYAAN USER]\n"
            f"{prompt}"
        )

    user_msg: dict[str, Any] = {"role": "user", "content": user_message}
    if images:
        user_msg["images"] = images
    messages = [
        {"role": "system", "content": combined_system},
        user_msg,
    ]

    payload = {
        "model": used_model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
    }

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        text = data.get("message", {}).get("content", "").strip()

        if not text:
            log.warning("Ollama returned empty response")
            return "⚠ Ollama mengembalikan respons kosong.", "mock_error"

        log.info(f"Ollama generate OK — model={used_model}, tokens≈{len(text.split())}")
        return text, "ollama"

    except requests.exceptions.Timeout:
        log.error(f"Ollama timeout ({OLLAMA_TIMEOUT}s) — model={used_model}")
        return (
            f"⚠ Ollama timeout ({OLLAMA_TIMEOUT}s). "
            "Model mungkin terlalu besar untuk server ini. "
            f"Coba: `ollama pull qwen2.5:1.5b` lalu set `OLLAMA_MODEL=qwen2.5:1.5b`",
            "mock_error",
        )
    except requests.exceptions.ConnectionError:
        log.warning("Ollama tidak bisa dihubungi — server mungkin mati")
        return (
            "⚠ Ollama offline. "
            "Di VPS: `curl -fsSL https://ollama.ai/install.sh | sh && ollama pull qwen2.5:7b`",
            "mock_error",
        )
    except Exception as e:
        log.error(f"Ollama error: {e}")
        return f"⚠ Ollama error: {e}", "mock_error"


def ollama_generate_vision(
    image_b64: str,
    prompt: str = "Describe this image in Indonesian.",
    *,
    model: Optional[str] = None,
    max_tokens: int = 500,
) -> tuple[str, str]:
    """
    Generate vision-to-text via Ollama multimodal model (e.g. llava, llama3.2-vision).
    Returns (generated_text, mode) — mode = "ollama" or "mock_error".
    """
    used_model = model or ollama_best_available_model()
    # prefer vision model if available
    vision_candidates = ["llava", "llama3.2-vision", "bakllava", "moondream"]
    models = ollama_list_models()
    if models:
        for vc in vision_candidates:
            for m in models:
                if vc in m.lower():
                    used_model = m
                    break
            else:
                continue
            break

    messages = [
        {"role": "system", "content": SIDIX_SYSTEM},
        {"role": "user", "content": prompt, "images": [image_b64]},
    ]
    payload = {
        "model": used_model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
        },
    }
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        text = data.get("message", {}).get("content", "").strip()
        if not text:
            log.warning("Ollama vision returned empty response")
            return "⚠ Ollama vision mengembalikan respons kosong.", "mock_error"
        return text, "ollama"
    except requests.exceptions.Timeout:
        log.error(f"Ollama vision timeout ({OLLAMA_TIMEOUT}s)")
        return f"⚠ Ollama vision timeout ({OLLAMA_TIMEOUT}s).", "mock_error"
    except requests.exceptions.ConnectionError:
        log.warning("Ollama vision tidak bisa dihubungi")
        return "⚠ Ollama offline — vision tidak tersedia.", "mock_error"
    except Exception as e:
        log.error(f"Ollama vision error: {e}")
        return f"⚠ Ollama vision error: {e}", "mock_error"


def ollama_generate_stream(
    prompt: str,
    system: str = "",
    *,
    model: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
):
    """
    Generate teks via Ollama dengan STREAMING.
    Yields token chunks satu per satu.

    Usage:
        for chunk in ollama_generate_stream("Halo", system="..."):
            print(chunk, end="")
    """
    used_model = model or ollama_best_available_model()
    combined_system = f"{SIDIX_SYSTEM}\n\n{system.strip()}".strip() if system.strip() else SIDIX_SYSTEM

    messages = [
        {"role": "system", "content": combined_system},
        {"role": "user", "content": prompt},
    ]
    payload = {
        "model": used_model,
        "messages": messages,
        "stream": True,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
        },
    }

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            stream=True,
            timeout=OLLAMA_TIMEOUT,
        )
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    yield chunk
                if data.get("done"):
                    break
            except Exception:
                pass
    except Exception as e:
        log.error(f"Ollama stream error: {e}")
        yield f"[stream error: {e}]"


def ollama_status() -> dict:
    """Status lengkap Ollama untuk health endpoint."""
    available = ollama_available()
    if not available:
        return {
            "available": False,
            "models": [],
            "active_model": OLLAMA_MODEL,
            "url": OLLAMA_URL,
            "install_hint": "curl -fsSL https://ollama.ai/install.sh | sh && ollama pull qwen2.5:7b",
        }
    models = ollama_list_models()
    return {
        "available": True,
        "models": models,
        "active_model": ollama_best_available_model(),
        "url": OLLAMA_URL,
        "model_count": len(models),
    }
