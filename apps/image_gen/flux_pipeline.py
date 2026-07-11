"""
FLUX.1 image generation pipeline for SIDIX.

Strategy:
1. Use FLUX.1 through diffusers when dependencies and GPU/MPS are available.
2. Fall back to a local SVG placeholder when FLUX cannot safely run.

Environment:
- SIDIX_IMAGE_MODEL: model id, default black-forest-labs/FLUX.1-schnell
- SIDIX_IMAGE_DEVICE: cuda | mps | cpu | auto, default auto
- SIDIX_IMAGE_MOCK: set 1/true/on/yes to force placeholder mode
- SIDIX_IMAGE_ALLOW_CPU: set 1 to allow CPU FLUX, which is very slow and RAM-heavy
- SIDIX_IMAGE_OUTPUT_DIR: output directory, default data/generated/images
"""

from __future__ import annotations

import html
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_ID = os.getenv("SIDIX_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
OUTPUT_DIR = Path(os.getenv("SIDIX_IMAGE_OUTPUT_DIR", "data/generated/images"))
_TRUTHY = {"1", "true", "on", "yes"}


def _detect_device(preference: str = "auto") -> str:
    preference = (preference or "auto").strip().lower()
    if preference != "auto":
        return preference
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def _module_available(name: str) -> bool:
    try:
        import importlib.util

        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def runtime_status() -> dict:
    """Return local FLUX readiness without loading model weights."""
    forced_mock = os.getenv("SIDIX_IMAGE_MOCK", "0").strip().lower() in _TRUTHY
    preferred_device = os.getenv("SIDIX_IMAGE_DEVICE", "auto").strip().lower() or "auto"
    device = _detect_device(preferred_device)
    allow_cpu = os.getenv("SIDIX_IMAGE_ALLOW_CPU", "0").strip().lower() in _TRUTHY
    deps = {
        "torch": _module_available("torch"),
        "diffusers": _module_available("diffusers"),
        "transformers": _module_available("transformers"),
        "accelerate": _module_available("accelerate"),
    }

    cuda_available = False
    cuda_devices = 0
    cuda_name = ""
    try:
        import torch

        cuda_available = bool(torch.cuda.is_available())
        cuda_devices = int(torch.cuda.device_count())
        if cuda_available:
            cuda_name = torch.cuda.get_device_name(0)
    except Exception:
        pass

    ready = True
    reason = ""
    if forced_mock:
        ready = False
        reason = "SIDIX_IMAGE_MOCK enabled"
    elif not deps["torch"] or not deps["diffusers"]:
        ready = False
        reason = "torch/diffusers not installed"
    elif device == "cpu" and not allow_cpu:
        ready = False
        reason = "GPU unavailable; CPU FLUX disabled by default"

    return {
        "ok": True,
        "mode": "flux" if ready else "mock",
        "ready": ready,
        "reason": reason,
        "model": MODEL_ID if ready else "mock",
        "configured_model": MODEL_ID,
        "device": device,
        "allow_cpu": allow_cpu,
        "output_dir": str(OUTPUT_DIR),
        "dependencies": deps,
        "cuda_available": cuda_available,
        "cuda_devices": cuda_devices,
        "cuda_name": cuda_name,
    }


class FluxPipeline:
    """Lazy FLUX.1 wrapper with safe placeholder fallback."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        device: str = "auto",
    ):
        self.model_id = model_id
        env_device = os.getenv("SIDIX_IMAGE_DEVICE", device).strip() or device
        self.device = _detect_device(env_device)
        self._pipe = None
        self._mock_mode = os.getenv("SIDIX_IMAGE_MOCK", "0").strip().lower() in _TRUTHY
        self._last_reason = "mock forced by SIDIX_IMAGE_MOCK" if self._mock_mode else ""

    def _load(self) -> None:
        if self._pipe is not None or self._mock_mode:
            return
        try:
            import torch

            allow_cpu = os.getenv("SIDIX_IMAGE_ALLOW_CPU", "0").strip().lower() in _TRUTHY
            if self.device == "cpu" and not allow_cpu:
                self._last_reason = "GPU unavailable; CPU FLUX disabled by default"
                logger.warning("%s - using mock mode", self._last_reason)
                self._mock_mode = True
                return

            from diffusers import FluxPipeline as _DiffusersPipeline

            dtype = torch.bfloat16 if self.device == "cuda" else torch.float32
            logger.info("Loading FLUX.1 pipeline on %s (dtype=%s)", self.device, dtype)
            self._pipe = _DiffusersPipeline.from_pretrained(
                self.model_id,
                torch_dtype=dtype,
            ).to(self.device)
            logger.info("FLUX.1 pipeline ready.")
        except ImportError:
            self._last_reason = "diffusers/torch not installed"
            logger.warning("%s - using mock mode", self._last_reason)
            self._mock_mode = True
        except Exception as exc:
            self._last_reason = f"FLUX.1 load failed: {exc}"
            logger.warning("%s - using mock mode", self._last_reason)
            self._mock_mode = True

    def _mock_generate(self, prompt: str, filename: str) -> Path:
        """Create a local placeholder SVG when real FLUX is unavailable."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / filename.replace(".png", ".svg")
        safe_prompt = html.escape(prompt[:120], quote=False)
        out_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">'
            '<rect width="512" height="512" fill="#1a1a2e"/>'
            '<text x="256" y="238" text-anchor="middle" fill="#6EAE7C" font-size="16">'
            "[SIDIX Image - Mock Mode]</text>"
            '<text x="256" y="280" text-anchor="middle" fill="#d8cbb3" font-size="12">'
            f"{safe_prompt}</text>"
            "</svg>",
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
        Generate an image from a text prompt.

        Returns:
        - path: saved file path
        - mode: flux | mock
        - model: model id or mock
        """
        if not filename:
            filename = f"{uuid.uuid4().hex}.png"

        self._load()

        if self._mock_mode:
            path = self._mock_generate(prompt, filename)
            return {"path": path, "mode": "mock", "model": "mock", "reason": self._last_reason}

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
            return {"path": out_path, "mode": "flux", "model": self.model_id, "device": self.device}
        except Exception as exc:
            self._last_reason = f"FLUX.1 generate failed: {exc}"
            logger.warning("%s - fallback mock", self._last_reason)
            path = self._mock_generate(prompt, filename)
            return {"path": path, "mode": "mock", "model": "mock", "reason": self._last_reason}


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
    """Generate without manual pipeline instantiation."""
    return get_pipeline().generate(
        prompt=prompt,
        width=width,
        height=height,
        steps=steps,
        seed=seed,
    )


def get_status() -> dict:
    """Public helper for health/status endpoints."""
    status = runtime_status()
    if _pipeline is not None:
        status["loaded"] = _pipeline._pipe is not None
        status["last_reason"] = _pipeline._last_reason
    else:
        status["loaded"] = False
        status["last_reason"] = ""
    return status
