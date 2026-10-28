"""
identity_mask.py — Mask Identitas Backbone untuk Output Publik
==============================================================

PRINSIP OPSEC:
SIDIX harus terlihat standing-alone di output publik. Jangan biarkan
identitas mentor LLM eksternal (provider X, Y, Z) bocor ke:
  - Sanad metadata di markdown note publik
  - Field source di research bundle
  - /health endpoint llm_providers
  - Threads post yang di-publish

Internal: tetap pakai nama asli untuk routing & logging private (LIVING_LOG,
.data/ tidak di-deploy publik).
External: rename ke "mentor_alpha / beta / gamma / delta" — generic dan tidak
mengindikasikan provider tertentu.
"""

from __future__ import annotations

# Mapping internal → public-facing
_PROVIDER_MASK: dict[str, str] = {
    # Provider names → masked aliases
    "groq":             "mentor_alpha",
    "groq_llama3":      "mentor_alpha",
    "groq_llama-3.1":   "mentor_alpha",
    "groq_whisper":     "audio_engine_a",
    "gemini":           "mentor_beta",
    "gemini_flash":     "mentor_beta",
    "gemini_vision":    "vision_engine_a",
    "google":           "mentor_beta",
    "anthropic":        "mentor_gamma",
    "claude":           "mentor_gamma",
    "claude-3":         "mentor_gamma",
    "claude-3-haiku":   "mentor_gamma",
    "openai":           "mentor_delta",
    "gpt":              "mentor_delta",
    "gpt-4":            "mentor_delta",

    # Local/own — tetap dengan nama yang menonjolkan kemandirian
    "ollama":           "sidix_local",
    "ollama_local":     "sidix_local",
    "ollama_vision_local": "sidix_local_vision",
    "qwen":             "sidix_local",
    "qwen2.5":          "sidix_local",
    "llama3":           "sidix_local",
    "phi":              "sidix_local",
    "lora":             "sidix_lora",

    # Free tier services — generic
    "pollinations":     "image_engine_free",
    "pollinations_free": "image_engine_free",
    "gtts":             "tts_engine_free",
}


def mask_identity(name: str) -> str:
    """
    Konversi nama provider/model jadi alias publik.
    Jaga kemandirian identitas SIDIX di public-facing output.
    """
    if not name:
        return name
    s = str(name).lower().strip()

    # Direct lookup
    if s in _PROVIDER_MASK:
        return _PROVIDER_MASK[s]

    # Substring match (untuk format kompleks seperti "llm:groq:pov_kritis")
    for raw, masked in _PROVIDER_MASK.items():
        if raw in s:
            # Preserve sufiks setelah provider name
            tail = ""
            if ":" in s:
                parts = s.split(":")
                # ambil suffix yang non-provider
                for p in parts[1:]:
                    p_low = p.lower()
                    if not any(prov in p_low for prov in _PROVIDER_MASK.keys()):
                        tail += ":" + p
            return masked + tail

    # Default: hide host suffix Wikipedia/etc tetap OK karena itu sumber publik
    return s


def mask_dict(d: dict, fields: list[str] = None) -> dict:
    """Mask field tertentu di dict (default: source, name, mode, provider, via)."""
    fields = fields or ["source", "name", "mode", "provider", "via"]
    out = dict(d) if not isinstance(d, dict) else d.copy()
    for f in fields:
        if f in out and isinstance(out[f], str):
            out[f] = mask_identity(out[f])
    return out


def mask_health_payload(payload: dict) -> dict:
    """
    Sanitize /health response — hilangkan llm_providers spesifik.
    Replace dengan flag generik: 'internal_mentor_pool' status.
    """
    out = dict(payload)

    # Hide raw provider flags
    if "llm_providers" in out:
        providers = out.pop("llm_providers", {})
        # Aggregate jadi flag generik
        any_active = any(v for v in providers.values()) if isinstance(providers, dict) else False
        out["internal_mentor_pool"] = {
            "ready":            any_active,
            "redundancy_level": sum(1 for v in providers.values() if v) if isinstance(providers, dict) else 0,
        }

    # Hide ollama detail (cuma flag ready/not)
    if "ollama" in out and isinstance(out["ollama"], dict):
        ollama_info = out["ollama"]
        out["sidix_local_engine"] = {
            "ready":         bool(ollama_info.get("available")),
            "models_loaded": len(ollama_info.get("models", [])) if isinstance(ollama_info.get("models"), list) else 0,
        }
        del out["ollama"]

    # Mask model_mode jika tampak provider-specific
    if "model_mode" in out:
        mm = str(out["model_mode"])
        if mm in ("ollama", "local_lora"):
            out["model_mode"] = "sidix_local"

    return out
