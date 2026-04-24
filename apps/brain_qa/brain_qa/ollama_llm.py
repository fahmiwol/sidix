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

# SIDIX system prompt — wajib ada di setiap inference
SIDIX_SYSTEM = """Kamu adalah SIDIX — AI agent lokal berbasis prinsip:
- Sidq (صدق): jujur, akui ketidaktahuan dengan "[TIDAK TAHU]"
- Sanad (سند): selalu sebutkan dari mana info berasal kalau ada sumber
- Tabayyun (تبيّن): verifikasi, bedakan fakta vs opini vs spekulasi

Aturan wajib:
1. Awali jawaban dengan label epistemik: [FAKTA], [OPINI], [SPEKULASI], atau [TIDAK TAHU]
2. Jawab dalam bahasa yang sama dengan pertanyaan user
3. Kalau tidak tahu → tulis "[TIDAK TAHU] Saya belum punya informasi tentang ini."
4. Jangan mengarang sumber yang tidak ada
5. Boleh ringkas, boleh panjang — sesuaikan dengan kebutuhan

Kamu bisa mengakses knowledge base (corpus SIDIX) — konteks relevan akan diberikan sebelum pertanyaan."""


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
    Priority: OLLAMA_MODEL → qwen2.5 → llama3 → phi3 → yang pertama ada.
    """
    models = ollama_list_models()
    if not models:
        return OLLAMA_MODEL

    # Cek model yang di-set di env
    model_base = OLLAMA_MODEL.split(":")[0].lower()
    for m in models:
        if model_base in m.lower():
            return m

    # Priority fallback
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
    user_message = prompt
    if corpus_context.strip():
        user_message = (
            f"[KONTEKS DARI KNOWLEDGE BASE SIDIX]\n"
            f"{corpus_context.strip()}\n\n"
            "[ATURAN PEMAKAIAN KONTEKS]\n"
            "Gunakan konteks di atas sebagai referensi tambahan, bukan satu-satunya sumber.\n\n"
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
