"""
runpod_connector.py — SIDIX RunPod Serverless Connector
========================================================
Connector ke RunPod GPU workers untuk inference 3D, image gen, TTS, design.

Endpoints yang ditarget:
  - mighan-media-worker: image gen, TTS, design, 3D (TripoSR)
  - mighan-3d-worker: 3D asset builder (TripoSR, Hunyuan3D)

Environment:
  RUNPOD_API_KEY — API key RunPod
  RUNPOD_MEDIA_ENDPOINT_ID — endpoint ID media worker
  RUNPOD_3D_ENDPOINT_ID — endpoint ID 3D worker

Research notes:
  - 318 cognitive expansion (RunPod GPU burst)
"""
from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path
from typing import Any, Optional


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
RUNPOD_MEDIA_ENDPOINT = os.environ.get("RUNPOD_MEDIA_ENDPOINT_ID", "")
RUNPOD_3D_ENDPOINT = os.environ.get("RUNPOD_3D_ENDPOINT_ID", "")


def _has_config() -> bool:
    return bool(RUNPOD_API_KEY and (RUNPOD_MEDIA_ENDPOINT or RUNPOD_3D_ENDPOINT))


def _call_runpod(endpoint_id: str, payload: dict, timeout: int = 120) -> dict:
    """Call RunPod serverless endpoint via HTTP."""
    if not RUNPOD_API_KEY:
        return _fallback("RUNPOD_API_KEY tidak di-set. Set di environment atau .env.")
    if not endpoint_id:
        return _fallback("Endpoint ID tidak di-set.")

    try:
        import urllib.request
        url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        req = urllib.request.Request(
            url,
            data=json.dumps({"input": payload}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {RUNPOD_API_KEY}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Poll for result
        job_id = data.get("id")
        if not job_id:
            return _fallback("Tidak ada job ID dari RunPod.", data=data)

        status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
        for _ in range(60):  # max 60 * 2s = 120s
            time.sleep(2)
            status_req = urllib.request.Request(
                status_url,
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
            )
            with urllib.request.urlopen(status_req, timeout=30) as status_resp:
                status_data = json.loads(status_resp.read().decode("utf-8"))
            if status_data.get("status") in {"COMPLETED", "FAILED"}:
                return status_data
        return _fallback("RunPod job timeout (120s).", data={"job_id": job_id})

    except ImportError:
        return _fallback("urllib tidak tersedia (stdlib harusnya ada).")
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"RunPod call gagal: {exc}")


def generate_image(prompt: str, negative_prompt: str = "", width: int = 1024, height: int = 1024,
                   num_inference_steps: int = 30, guidance_scale: float = 7.5) -> dict:
    """Generate image via RunPod media worker (SDXL/Flux)."""
    if not _has_config():
        return _fallback(
            "RunPod config belum di-set.\n"
            "Set environment variables:\n"
            "  RUNPOD_API_KEY=your_key\n"
            "  RUNPOD_MEDIA_ENDPOINT_ID=your_endpoint_id",
            data={"prompt": prompt},
        )

    result = _call_runpod(RUNPOD_MEDIA_ENDPOINT, {
        "endpoint": "/generate/image",
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
    })
    if result.get("status") == "COMPLETED":
        output = result.get("output", {})
        return _ok({
            "backend": "runpod-sdxl",
            "image_url": output.get("image_url", ""),
            "image_b64": output.get("image_b64", ""),
            "prompt": prompt,
            "generation_time": output.get("generation_time", 0),
        })
    return _fallback(result.get("error", "Image generation gagal"), data=result)


def generate_3d(image_path: str | None = None, prompt: str = "", mode: str = "triposr",
                remove_bg: bool = True, output_format: str = "glb") -> dict:
    """Generate 3D mesh via RunPod 3D worker (TripoSR / Hunyuan3D)."""
    if not _has_config():
        return _fallback(
            "RunPod config belum di-set.\n"
            "Set environment variables:\n"
            "  RUNPOD_API_KEY=your_key\n"
            "  RUNPOD_3D_ENDPOINT_ID=your_endpoint_id",
        )

    payload = {
        "mode": mode,
        "prompt": prompt,
        "remove_bg": remove_bg,
        "output_format": output_format,
    }
    if image_path and Path(image_path).exists():
        with open(image_path, "rb") as f:
            payload["image"] = base64.b64encode(f.read()).decode("utf-8")

    result = _call_runpod(RUNPOD_3D_ENDPOINT, payload, timeout=180)
    if result.get("status") == "COMPLETED":
        output = result.get("output", {})
        return _ok({
            "backend": f"runpod-{mode}",
            "mesh_url": output.get("mesh_url", ""),
            "thumbnail_url": output.get("thumbnail_url", ""),
            "vertices": output.get("vertices", 0),
            "faces": output.get("faces", 0),
            "generation_time": output.get("generation_time", 0),
        })
    return _fallback(result.get("error", "3D generation gagal"), data=result)


def generate_tts(text: str, voice: str = "default", lang: str = "id") -> dict:
    """Generate TTS via RunPod media worker."""
    if not _has_config():
        return _fallback("RunPod config belum di-set.")

    result = _call_runpod(RUNPOD_MEDIA_ENDPOINT, {
        "endpoint": "/generate/tts",
        "text": text,
        "voice": voice,
        "lang": lang,
    })
    if result.get("status") == "COMPLETED":
        output = result.get("output", {})
        return _ok({
            "backend": "runpod-tts",
            "audio_url": output.get("audio_url", ""),
            "audio_b64": output.get("audio_b64", ""),
            "duration": output.get("duration", 0),
        })
    return _fallback(result.get("error", "TTS generation gagal"), data=result)


def design_edit(image_path: str, operation: str = "remove_bg", **kwargs) -> dict:
    """Design operations via RunPod media worker: remove_bg, upscale, etc."""
    if not _has_config():
        return _fallback("RunPod config belum di-set.")

    payload = {
        "endpoint": "/generate/design",
        "operation": operation,
        **kwargs,
    }
    if image_path and Path(image_path).exists():
        with open(image_path, "rb") as f:
            payload["image"] = base64.b64encode(f.read()).decode("utf-8")

    result = _call_runpod(RUNPOD_MEDIA_ENDPOINT, payload)
    if result.get("status") == "COMPLETED":
        return _ok(result.get("output", {}))
    return _fallback(result.get("error", "Design operation gagal"), data=result)


def health_check() -> dict:
    """Check RunPod endpoints health."""
    if not _has_config():
        return _fallback("RunPod config belum di-set.")

    try:
        import urllib.request
        statuses = {}
        for name, endpoint in [("media", RUNPOD_MEDIA_ENDPOINT), ("3d", RUNPOD_3D_ENDPOINT)]:
            if endpoint:
                url = f"https://api.runpod.ai/v2/{endpoint}/health"
                req = urllib.request.Request(url, headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"})
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        statuses[name] = json.loads(resp.read().decode("utf-8"))
                except Exception as exc:  # noqa: BLE001
                    statuses[name] = {"error": str(exc)}
        return _ok({"endpoints": statuses})
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"Health check gagal: {exc}")
