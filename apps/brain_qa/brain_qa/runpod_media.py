"""
runpod_media.py — Sprint 14b: Bridge ke RunPod mighan-media-worker

Endpoint: mighan-media-worker (48GB GPU, unified worker SDXL + TTS + 3D + design)
Hub spec: /root/mighantect-3d/.runpod/hub.json (per VPS)
Handler:  /root/mighantect-3d/runpod-media-worker/media_worker.py

API contract image:
  POST https://api.runpod.ai/v2/{MEDIA_ENDPOINT_ID}/runsync
  Authorization: Bearer {RUNPOD_API_KEY}
  Content-Type: application/json
  {"input": {
     "tool": "image",
     "prompt": "...",
     "negative_prompt": "",
     "width": 1024, "height": 1024,
     "num_inference_steps": 30,
     "guidance_scale": 7.5,
     "seed": null,
     "model": "sdxl"        # atau "pollinations" fallback (no-GPU)
  }}

Response:
  {"output": {
     "success": true,
     "image_base64": "<png base64>",
     "format": "png", "width":..., "height":...,
     "model": "sdxl",
     "generation_time": 12.5
  }}

ENV yang dibutuhkan (di /opt/sidix/.env atau pm2 ecosystem):
  RUNPOD_API_KEY            (sudah ada untuk vLLM, shared)
  RUNPOD_MEDIA_ENDPOINT_ID  (BARU — endpoint mighan-media-worker)

Public API:
  media_available() -> bool
  generate_image(prompt, **kwargs) -> dict    # save PNG ke disk + return path
"""

from __future__ import annotations

import base64
import logging
import os
import time
import urllib.error
import urllib.request
import json
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

_API_BASE = "https://api.runpod.ai/v2"
_DEFAULT_TIMEOUT = 300  # 5 min — image gen + cold start


def _media_config() -> Optional[dict]:
    api_key = os.getenv("RUNPOD_API_KEY", "").strip()
    endpoint_id = os.getenv("RUNPOD_MEDIA_ENDPOINT_ID", "").strip()
    if not api_key or not endpoint_id:
        return None
    return {
        "api_key": api_key,
        "endpoint_id": endpoint_id,
        "timeout": int(os.getenv("RUNPOD_MEDIA_TIMEOUT", str(_DEFAULT_TIMEOUT))),
    }


def media_available() -> bool:
    """True kalau env configured. Healthcheck via /health endpoint."""
    cfg = _media_config()
    if not cfg:
        return False
    try:
        url = f"{_API_BASE}/{cfg['endpoint_id']}/health"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception as e:
        log.debug(f"[runpod_media] healthcheck fail: {e}")
        return False


def _runsync(payload: dict, cfg: dict) -> dict:
    """POST runsync ke RunPod media endpoint."""
    url = f"{_API_BASE}/{cfg['endpoint_id']}/runsync"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {cfg['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=cfg["timeout"]) as r:
        return json.loads(r.read().decode("utf-8"))


def generate_image(
    prompt: str,
    *,
    output_dir: Path | str,
    label: str = "asset",
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    guidance: float = 7.5,
    negative_prompt: str = (
        "blurry, low quality, distorted, watermark, text, logo overlay, "
        "extra limbs, bad anatomy, ugly, deformed"
    ),
    seed: Optional[int] = None,
    model: str = "sdxl",
) -> dict[str, Any]:
    """
    Generate satu image via mighan-media-worker.
    Save PNG ke output_dir/<label>.png. Returns metadata dict.
    """
    cfg = _media_config()
    if not cfg:
        return {
            "success": False,
            "error": "RUNPOD_MEDIA_ENDPOINT_ID belum di-set di env",
            "label": label,
        }

    payload = {
        "input": {
            "tool": "image",
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": int(width),
            "height": int(height),
            "num_inference_steps": int(steps),
            "guidance_scale": float(guidance),
            "seed": seed,
            "model": model,
        }
    }

    t0 = time.time()
    try:
        resp = _runsync(payload, cfg)
    except urllib.error.HTTPError as e:
        return {"success": False, "label": label, "error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"success": False, "label": label, "error": f"runpod call fail: {e}"}

    elapsed_ms = int((time.time() - t0) * 1000)

    out = resp.get("output") or {}
    if not out.get("success"):
        return {
            "success": False, "label": label,
            "error": out.get("error", "no image returned"),
            "elapsed_ms": elapsed_ms,
            "raw_status": resp.get("status"),
        }

    img_b64 = out.get("image_base64", "")
    if not img_b64:
        return {"success": False, "label": label, "error": "image_base64 missing", "elapsed_ms": elapsed_ms}

    out_path = Path(output_dir) / f"{label}.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_path.write_bytes(base64.b64decode(img_b64))
    except Exception as e:
        return {"success": False, "label": label, "error": f"decode/write fail: {e}", "elapsed_ms": elapsed_ms}

    return {
        "success": True,
        "label": label,
        "path": str(out_path),
        "filename": out_path.name,
        "size_bytes": out_path.stat().st_size,
        "width": out.get("width", width),
        "height": out.get("height", height),
        "model": out.get("model", model),
        "generation_time_s": out.get("generation_time"),
        "elapsed_ms": elapsed_ms,
        "prompt": prompt[:200],
    }


# ── Hero asset generation helpers ────────────────────────────────────────────

def pick_hero_prompts(asset_prompts: list[str], n: int = 3) -> list[tuple[str, str]]:
    """
    Dari 8 asset prompts stage 5 creative_pipeline, pilih top-N hero asset
    yang patut di-render. Return list of (label, prompt) pairs.

    Default pick: HERO MASCOT, LOGO MARK, SOCIAL POST (3 deliverable visual
    paling impactful untuk demo brand identity).
    """
    priority_labels = ["HERO MASCOT", "LOGO MARK", "SOCIAL POST"]
    picked: list[tuple[str, str]] = []
    for label_target in priority_labels:
        for line in asset_prompts:
            if label_target in line.upper() and not any(p[0] == label_target for p in picked):
                # Strip [LABEL] prefix kalau ada
                clean = line
                if line.startswith("[") and "]" in line:
                    clean = line.split("]", 1)[1].strip()
                picked.append((_safe_filename(label_target), clean))
                break
        if len(picked) >= n:
            break

    # Fallback: kalau gak match, ambil top-N apa adanya
    if len(picked) < n and asset_prompts:
        for i, line in enumerate(asset_prompts):
            if len(picked) >= n:
                break
            label = f"asset_{i+1}"
            clean = line.split("]", 1)[1].strip() if line.startswith("[") and "]" in line else line
            picked.append((label, clean))

    return picked[:n]


def _safe_filename(name: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "_", name.lower())
    return s.strip("_") or "asset"


if __name__ == "__main__":
    import sys
    if not media_available():
        print("[runpod_media] not available — RUNPOD_MEDIA_ENDPOINT_ID belum di-set?")
        sys.exit(1)
    test_prompt = sys.argv[1] if len(sys.argv) > 1 else (
        "kawaii yellow caterpillar mascot, full body, white background, chibi style, soft lighting"
    )
    result = generate_image(test_prompt, output_dir="/tmp/runpod_media_test", label="test_hero")
    print(json.dumps(result, indent=2))
