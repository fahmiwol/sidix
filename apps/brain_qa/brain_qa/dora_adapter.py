"""
Persona DoRA Adapter — dynamic persona switching via LoRA adapter loading.

Infrastructure untuk memuat dan mengganti LoRA adapter per persona secara
dinamis. Kalau adapter fisik belum ada (Self-Train Fase 1 belum selesai),
fall back ke "logical adapter": system prompt + temperature per persona.

Thread-safe: multiple request dengan persona berbeda bisa berjalan bersamaan
tanpa race condition pada model state.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

_PKG_ROOT = Path(__file__).resolve().parent.parent

PERSONA_ADAPTERS = {
    "AYMAN": {"path": "models/sidix-lora-adapter-AYMAN", "temp": 0.7, "max_tokens": 512},
    "ABOO": {"path": "models/sidix-lora-adapter-ABOO", "temp": 0.3, "max_tokens": 800},
    "OOMAR": {"path": "models/sidix-lora-adapter-OOMAR", "temp": 0.5, "max_tokens": 700},
    "ALEY": {"path": "models/sidix-lora-adapter-ALEY", "temp": 0.2, "max_tokens": 900},
    "UTZ": {"path": "models/sidix-lora-adapter-UTZ", "temp": 0.8, "max_tokens": 600},
}

PERSONA_SYSTEM_PROMPTS = {
    "AYMAN": (
        "Kamu adalah AYMAN, persona yang empatik, ramah, dan suka memberikan analogi sederhana. "
        "Kamu mendengarkan dengan penuh perhatian dan menjawab dengan kehangatan, "
        "seperti teman yang mengerti. Gunakan bahasa yang mudah dicerna dan suasana yang nyaman."
    ),
    "ABOO": (
        "Kamu adalah ABOO, persona teknis yang langsung to the point, fokus pada kode dan efisiensi. "
        "Kamu menyukai solusi pragmatis, menghindari basa-basi, dan selalu menyertakan "
        "contoh kode atau langkah konkret bila relevan. Prioritaskan kebenaran teknis."
    ),
    "OOMAR": (
        "Kamu adalah OOMAR, persona bisnis strategis yang menggunakan framework seperti SWOT, "
        "Porter, Lean Canvas. Kamu berpikir dalam dimensi risiko, peluang, dan eksekusi. "
        "Berikan rekomendasi yang actionable dan berbasis data."
    ),
    "ALEY": (
        "Kamu adalah ALEY, persona akademik yang selalu mensitasi minimal 3 sumber, "
        "menggunakan metode tabayyun. Kamu hati-hati dalam menyimpulkan, membedakan "
        "fakta vs opini, dan selalu menunjukkan jejak pemikiran yang jelas."
    ),
    "UTZ": (
        "Kamu adalah UTZ, persona kreatif yang menghasilkan ide-ide out-of-the-box, "
        "menggunakan metafora dan asosiasi tak terduga. Kamu melihat koneksi antar konsep "
        "yang orang lain lewatkan dan menyukai eksplorasi tanpa batas."
    ),
}

# Thread-safe lock untuk adapter switching — PEFT set_adapter tidak thread-safe
# bila dua thread beda persona bersamaan.
_adapter_lock = threading.RLock()
_loaded_adapters: set[str] = set()
_current_adapter: str | None = None


def _adapter_path(persona: str) -> Path:
    rel = PERSONA_ADAPTERS.get(persona, {}).get("path", "")
    return _PKG_ROOT / rel


def adapter_exists(persona: str) -> bool:
    """Cek apakah direktori adapter fisik untuk persona tersedia."""
    if persona not in PERSONA_ADAPTERS:
        return False
    path = _adapter_path(persona)
    return (
        path.exists()
        and (path / "adapter_config.json").exists()
        and (
            (path / "adapter_model.safetensors").exists()
            or (path / "adapter_model.bin").exists()
        )
    )


def load_persona_adapter(persona: str) -> bool:
    """
    Coba memuat adapter fisik untuk persona.
    Return True bila berhasil dimuat (atau sudah dimuat sebelumnya),
    False bila adapter fisik tidak ada atau gagal load.
    """
    if persona not in PERSONA_ADAPTERS:
        return False

    if not adapter_exists(persona):
        return False

    # Lazy import untuk menghindari circular dependency.
    from . import local_llm as _llm_mod

    # Pastikan model sudah diload terlebih dahulu.
    if _llm_mod._model is None or _llm_mod._tokenizer is None:
        try:
            _llm_mod._load_model_tokenizer()
        except Exception:
            return False

    with _adapter_lock:
        if persona in _loaded_adapters:
            try:
                _llm_mod._model.set_adapter(persona)  # type: ignore[attr-defined]
                global _current_adapter
                _current_adapter = persona
                return True
            except Exception:
                return False

        try:
            path = str(_adapter_path(persona))
            _llm_mod._model.load_adapter(path, adapter_name=persona)  # type: ignore[attr-defined]
            _llm_mod._model.set_adapter(persona)  # type: ignore[attr-defined]
            _loaded_adapters.add(persona)
            _current_adapter = persona
            return True
        except Exception:
            return False


def unload_persona_adapter() -> None:
    """Kembalikan model ke adapter default (base)."""
    global _current_adapter
    from . import local_llm as _llm_mod

    with _adapter_lock:
        if _llm_mod._model is not None:
            try:
                _llm_mod._model.set_adapter("default")  # type: ignore[attr-defined]
            except Exception:
                pass
        _current_adapter = None


def get_persona_config(persona: str) -> dict[str, Any]:
    """
    Kembalikan konfigurasi merged untuk persona:
    {temp, max_tokens, system_prompt, physical_exists}.
    """
    config: dict[str, Any] = PERSONA_ADAPTERS.get(persona, {}).copy()
    config["system_prompt"] = PERSONA_SYSTEM_PROMPTS.get(persona, "")
    config["physical_exists"] = adapter_exists(persona)
    return config


def generate_with_persona(
    prompt: str,
    persona: str,
    *,
    system: str = "",
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> str:
    """
    Generate dengan persona tertentu.

    Alur:
      1. Kalau adapter fisik ada → load → generate → unload (thread-safe).
      2. Kalau adapter fisik tidak ada → fallback logical adapter:
         inject persona system prompt + temperature ke base model.
    """
    config = get_persona_config(persona)

    effective_max_tokens = max_tokens if max_tokens is not None else config.get("max_tokens", 512)
    effective_temperature = temperature if temperature is not None else config.get("temp", 0.7)

    # Jalur 1: physical adapter
    if load_persona_adapter(persona):
        try:
            from .local_llm import generate_sidix

            text, _mode = generate_sidix(
                prompt=prompt,
                system=system or config.get("system_prompt", ""),
                max_tokens=effective_max_tokens,
                temperature=effective_temperature,
            )
            return text
        finally:
            unload_persona_adapter()

    # Jalur 2: logical adapter — inject system prompt persona
    logical_system = config.get("system_prompt", "")
    if system:
        logical_system = f"{logical_system}\n\n{system}".strip()

    from .local_llm import generate_sidix

    text, _mode = generate_sidix(
        prompt=prompt,
        system=logical_system,
        max_tokens=effective_max_tokens,
        temperature=effective_temperature,
    )
    return text
