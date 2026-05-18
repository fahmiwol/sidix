"""
LoRA Adapter Integration — Projek Badar Task 75 (G2)
Integrasi adapter LoRA / style lokal untuk gambar.
Status: STUB — aktifkan bila stack mendukung.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# TODO: wire to diffusers pipeline when model is available
# from diffusers import StableDiffusionPipeline
# pipe.load_lora_weights(adapter.path)


@dataclass
class LoRAAdapter:
    """Representasi sebuah adapter LoRA lokal."""

    name: str
    path: str
    trigger_word: str
    weight: float = 0.8


class LoRARegistry:
    """
    Registry adapter LoRA yang tersedia di sistem lokal.

    Saat model diffusion lokal tersedia, panggil apply_to_pipeline()
    untuk memuat adapter ke dalam pipeline.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, LoRAAdapter] = {}

    def register(self, adapter: LoRAAdapter) -> None:
        """Daftarkan adapter baru ke registry."""
        self._adapters[adapter.name] = adapter
        logger.info("LoRA adapter '%s' didaftarkan dari path: %s", adapter.name, adapter.path)

    def get(self, name: str) -> Optional[LoRAAdapter]:
        """Ambil adapter berdasarkan nama. Kembalikan None bila tidak ditemukan."""
        return self._adapters.get(name)

    def list_adapters(self) -> list[str]:
        """Kembalikan daftar nama semua adapter terdaftar."""
        return list(self._adapters.keys())

    def apply_to_prompt(self, prompt: str, adapter_name: str) -> str:
        """
        Tambahkan trigger word adapter ke depan prompt.

        Bila adapter tidak ditemukan, kembalikan prompt asli dengan peringatan.

        TODO: wire to diffusers pipeline — saat model tersedia:
              pipe.load_lora_weights(adapter.path, weight=adapter.weight)
        """
        adapter = self.get(adapter_name)
        if adapter is None:
            logger.warning(
                "LoRA adapter '%s' tidak ditemukan di registry. Prompt tidak dimodifikasi.",
                adapter_name,
            )
            return prompt

        # STUB: hanya prepend trigger word, belum memuat weights ke pipeline
        modified = f"{adapter.trigger_word}, {prompt}"
        logger.debug(
            "LoRA '%s' trigger word ditambahkan ke prompt (stub — weights belum dimuat).",
            adapter_name,
        )
        return modified


# Instance global registry untuk penggunaan di seluruh aplikasi
lora_registry = LoRARegistry()
