"""
FLUX.1 Image Generation Pipeline — SIDIX Sprint 8b
Model: black-forest-labs/FLUX.1-schnell (fast, 4-step) atau FLUX.1-dev (quality)

Strategi graceful degradation:
  1) FLUX.1 via diffusers (CUDA/MPS/CPU)
  2) Mock (kembalikan placeholder URL) jika diffusers tidak ada

Kontrol via env:
  SIDIX_IMAGE_MODEL   — model ID (default: black-forest-labs/FLUX.1-schnell)
  SIDIX_IMAGE_DEVICE  — "cuda"|"cpu"|"mps"|"auto" (default: auto)
  SIDIX_IMAGE_MOCK    — "1" paksa mock mode
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_ID = os.getenv("SIDIX_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
OUTPUT_DIR = Path("data/generated/images")


def _detect_device(preference: str = "auto") -> str:
    if preference != "auto":
        return preference
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


class FluxPipeline:
    """
    Wrapper FLUX.1 dengan lazy load dan graceful mock fallback.
    Tidak diload saat startup — diinstansiasi saat pertama kali dipakai.
    """

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: str = "auto",
    ):
        self.model_id = model_id
        self.device = _detect_device(device)
        self._pipe = None
        self._mock_mode = os.getenv("SIDIX_IMAGE_MOCK", "0").strip() in ("1", "true", "on", "yes")

    def _load(self) -> None:
        if self._pipe is not None or self._mock_mode:
            return
        try:
            import torch
            from diffusers import FluxPipeline as _DiffusersPipeline

            dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
            logger.info("Loading FLUX.1 pipeline on %s (dtype=%s)…", self.device, dtype)
            self._pipe = _DiffusersPipeline.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
            ).to(self.device)
            logger.info("FLUX.1 pipeline ready.")
        except ImportError:
            logger.warning("diffusers/torch tidak terinstall — menggunakan mock mode")
            self._mock_mode = True
        except Exception as exc:
            logger.warning("FLUX.1 load gagal (%s) — menggunakan mock mode", exc)
            self._mock_mode = True

    def _mock_generate(self, prompt: str, filename: str) -> Path:
        """Buat placeholder SVG jika model tidak tersedia."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / filename.replace(".png", ".svg")
        safe_prompt = prompt[:80].replace("<", "&lt;").replace(">", "&gt;")
        out_path.write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">'
            f'<rect width="512" height="512" fill="#1a1a2e"/>'
            f'<text x="256" y="240" text-anchor="middle" fill="#6EAE7C" font-size="16">'
            f'[SIDIX Image — Mock Mode]</text>'
            f'<text x="256" y="280" text-anchor="middle" fill="#888" font-size="12">'
            f'{safe_prompt}</text>'
            f'</svg>',
            encoding="utf-8",
        )
        logger.info("Mock image placeholder: %s", out_path)
        return out_path

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 4,
        seed: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> dict:
        """
        Generate image dari teks prompt.

        Returns dict:
          path   — Path objek ke file yang disimpan
          mode   — "flux" | "mock"
          model  — model ID yang digunakan
        """
        if not filename:
            filename = f"{uuid.uuid4().hex}.png"

        self._load()

        if self._mock_mode:
            path = self._mock_generate(prompt, filename)
            return {"path": path, "mode": "mock", "model": "mock"}

        try:
            import torch

            generator = None
            if seed is not None:
                generator = torch.Generator(self.device).manual_seed(seed)

            result = self._pipe(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                generator=generator,
            )
            image = result.images[0]
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            out_path = OUTPUT_DIR / filename
            image.save(out_path)
            logger.info("Image saved: %s", out_path)
            return {"path": out_path, "mode": "flux", "model": self.model_id}
        except Exception as exc:
            logger.warning("FLUX.1 generate gagal (%s) — fallback mock", exc)
            path = self._mock_generate(prompt, filename)
            return {"path": path, "mode": "mock", "model": "mock"}


# ── Singleton ──────────────────────────────────────────────────────────────────
_pipeline: Optional[FluxPipeline] = None


def get_pipeline() -> FluxPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FluxPipeline()
    return _pipeline


def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    steps: int = 4,
    seed: Optional[int] = None,
) -> dict:
    """Shortcut untuk generate tanpa instansiasi manual."""
    return get_pipeline().generate(
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
    )
