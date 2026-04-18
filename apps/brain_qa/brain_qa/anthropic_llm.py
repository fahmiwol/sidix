"""
anthropic_llm.py — Wrapper hemat Anthropic API untuk SIDIX.

Filosofi:
  - Gunakan claude-3-haiku (PALING murah: $0.25/1M input, $1.25/1M output)
  - Batas output ketat: max 600 token per jawaban
  - System prompt ringkas agar tidak makan token
  - Hanya aktif jika ANTHROPIC_API_KEY di-set di env
  - TIDAK menyimpan history percakapan (stateless per request = hemat)

Dengan $4.93 dan rata2 500 input + 400 output per chat:
  → estimasi ~9,000+ percakapan sebelum habis.

Cara aktifkan:
  export ANTHROPIC_API_KEY="sk-ant-api03-..."
  # atau di .env file VPS

Mode ini HANYA dipakai kalau Ollama tidak tersedia.
"""

from __future__ import annotations

import os
import time
from typing import Optional

# ── Config ─────────────────────────────────────────────────────────────────────

# Model paling murah: $0.25/1M input, $1.25/1M output
ANTHROPIC_MODEL = os.getenv("SIDIX_ANTHROPIC_MODEL", "claude-3-haiku-20240307")

# Batas token output — hemat, tapi cukup untuk jawaban substantif
ANTHROPIC_MAX_TOKENS = int(os.getenv("SIDIX_ANTHROPIC_MAX_TOKENS", "600"))

# System prompt ringkas (hemat token)
SIDIX_SYSTEM_COMPACT = (
    "Kamu adalah SIDIX — AI assistant jujur berbasis epistemologi Islam. "
    "Jawab dalam Bahasa Indonesia (atau bahasa user). "
    "Tandai: [FAKTA] untuk fakta terverifikasi, [OPINI] untuk pendapat, [TIDAK TAHU] jika tidak yakin. "
    "Jawab padat dan akurat. Sebut sumber jika ada."
)

_anthropic_client = None
_client_error: Optional[str] = None


def _get_client():
    """Lazy-load Anthropic client. Return None jika tidak tersedia."""
    global _anthropic_client, _client_error

    if _client_error:
        return None  # Sudah gagal sebelumnya, skip

    if _anthropic_client is not None:
        return _anthropic_client

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        _client_error = "ANTHROPIC_API_KEY tidak di-set"
        return None

    try:
        import anthropic  # type: ignore
        _anthropic_client = anthropic.Anthropic(api_key=api_key)
        return _anthropic_client
    except ImportError:
        _client_error = "Package 'anthropic' belum install. Jalankan: pip install anthropic"
        return None
    except Exception as e:
        _client_error = str(e)
        return None


def anthropic_available() -> bool:
    """Cek apakah Anthropic API siap dipakai."""
    return _get_client() is not None


def anthropic_generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = ANTHROPIC_MAX_TOKENS,
    temperature: float = 0.7,
    context_snippets: Optional[list[str]] = None,
    model_override: Optional[str] = None,
) -> tuple[str, str]:
    """
    Generate teks via Anthropic API (hemat mode).

    Returns: (generated_text, mode)
    mode = "anthropic_haiku" | "error"

    context_snippets: hasil RAG — disertakan agar model bisa cite sumber
    tanpa perlu re-search (hemat API call).
    """
    client = _get_client()
    if not client:
        return "", "error"

    # Gabungkan context RAG ke dalam user prompt (lebih hemat daripada system)
    user_content = prompt
    if context_snippets:
        ctx = "\n\n---\n".join(context_snippets[:3])  # max 3 snippet, hemat token
        user_content = (
            f"Konteks dari knowledge base SIDIX:\n\n{ctx}\n\n"
            f"---\nPertanyaan: {prompt}"
        )

    # Batasi panjang prompt
    user_content = user_content[:4000]  # max ~1000 token input dari user

    sys_prompt = (system or SIDIX_SYSTEM_COMPACT)[:500]  # system prompt ringkas

    # Model override untuk sponsored tier (Sonnet)
    effective_model = model_override or ANTHROPIC_MODEL
    # Batasi max_tokens agar hemat (Sonnet tier bisa lebih banyak)
    max_cap = 1200 if "sonnet" in effective_model else ANTHROPIC_MAX_TOKENS
    actual_max = min(max_tokens, max_cap)

    t0 = time.time()
    try:
        message = client.messages.create(
            model=effective_model,
            max_tokens=actual_max,
            temperature=temperature,
            system=sys_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        text = message.content[0].text if message.content else ""
        elapsed = int((time.time() - t0) * 1000)

        # Log usage ke console (tidak ke file, hemat I/O)
        usage = message.usage
        inp = getattr(usage, "input_tokens", 0)
        out = getattr(usage, "output_tokens", 0)
        # Estimasi biaya per model
        if "sonnet" in effective_model:
            cost_usd = (inp * 0.000003) + (out * 0.000015)  # Sonnet-3.5
        else:
            cost_usd = (inp * 0.00000025) + (out * 0.00000125)  # Haiku
        mode_label = "anthropic_sonnet" if "sonnet" in effective_model else "anthropic_haiku"
        print(
            f"[{mode_label}] {inp}in+{out}out tokens "
            f"≈ ${cost_usd:.6f} | {elapsed}ms"
        )

        return text, mode_label

    except Exception as e:
        err_msg = str(e)
        print(f"[anthropic_llm] Error: {err_msg}")
        # Reset client kalau auth error
        if "auth" in err_msg.lower() or "api_key" in err_msg.lower():
            global _anthropic_client
            _anthropic_client = None
        return "", "error"


def get_api_status() -> dict:
    """Return status API untuk health check / dashboard."""
    client = _get_client()
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    return {
        "available": client is not None,
        "model": ANTHROPIC_MODEL,
        "max_tokens": ANTHROPIC_MAX_TOKENS,
        "key_set": bool(api_key),
        "key_prefix": api_key[:12] + "..." if api_key else None,
        "error": _client_error,
    }
