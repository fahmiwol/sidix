"""
video_gen_scaffold.py — Sprint Pencipta Phase 4 (Video Generation Scaffold)

Pattern wire untuk Stable Video Diffusion / CogVideoX / Mochi (open source,
self-hosted di RunPod GPU). Phase 4 actual GPU pipeline pending — sekarang
scaffold pattern + mock fallback.

Northstar: NO VENDOR API. RunPod = own infra (sewa GPU bare-metal),
bukan vendor seperti OpenAI Sora.

Models yang direncanakan support:
- Stable Video Diffusion (SVD) — image → 25 frame, 24GB VRAM
- CogVideoX-5B — text → 6s video, 24GB VRAM
- Mochi-1 — text → 5.4s video, 60GB VRAM (high quality)

Pattern (mirror flux_pipeline.py untuk image):
1. text_prompt + optional starting_image → encoded to latents
2. Diffusion sampling (25-50 steps)
3. Decode to frames
4. Encode to MP4 via ffmpeg
5. Return path + metadata

Phase 4 implementation sequence:
1. RunPod endpoint deploy (~1 sesi)
2. Wire ke /agent/chat_holistic saat output_type=video_storyboard
3. Frontend render <video> tag

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import logging
import os
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class VideoGenResult:
    success: bool
    path: Optional[str] = None
    url: Optional[str] = None
    duration_sec: float = 0.0
    width: int = 0
    height: int = 0
    fps: int = 0
    n_frames: int = 0
    model: str = ""
    mode: str = "mock"  # "mock" | "svd" | "cogvideox" | "mochi"
    error: Optional[str] = None


def _runpod_video_endpoint() -> Optional[dict]:
    """Get RunPod video gen endpoint config dari env."""
    endpoint = os.getenv("RUNPOD_VIDEO_ENDPOINT_ID", "").strip()
    api_key = os.getenv("RUNPOD_API_KEY", "").strip()
    if not endpoint or not api_key:
        return None
    return {
        "endpoint_id": endpoint,
        "api_key": api_key,
        "model": os.getenv("RUNPOD_VIDEO_MODEL", "stable-video-diffusion"),
    }


def generate_video(
    prompt: str,
    duration_sec: float = 4.0,
    width: int = 768,
    height: int = 768,
    fps: int = 24,
    starting_image_url: Optional[str] = None,
    seed: Optional[int] = None,
    out_dir: str = "/opt/sidix/generated_videos",
) -> VideoGenResult:
    """Generate video from text prompt (atau image2video).

    Phase 4 production: hit RunPod video endpoint.
    Phase 4 mock (sekarang): return placeholder MP4 + metadata.
    """
    cfg = _runpod_video_endpoint()

    # Hash filename dari prompt + params untuk caching
    cache_key = hashlib.md5(
        f"{prompt}|{duration_sec}|{width}x{height}|{fps}|{seed}".encode()
    ).hexdigest()[:12]
    out_path = Path(out_dir) / f"video_{cache_key}.mp4"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if cfg:
        # Phase 4 production: hit RunPod endpoint
        try:
            import httpx
            payload = {
                "input": {
                    "prompt": prompt,
                    "num_frames": int(duration_sec * fps),
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "seed": seed,
                }
            }
            if starting_image_url:
                payload["input"]["image_url"] = starting_image_url

            url = f"https://api.runpod.ai/v2/{cfg['endpoint_id']}/runsync"
            t0 = time.monotonic()
            with httpx.Client(timeout=600) as client:
                r = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {cfg['api_key']}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            elapsed = time.monotonic() - t0
            log.info(f"[video_gen] {cfg['endpoint_id']} {r.status_code} in {elapsed:.1f}s")
            r.raise_for_status()
            data = r.json()

            # Parse video URL/binary from response (vendor-specific format)
            output = data.get("output", {})
            video_url = output.get("video_url") or output.get("url") or ""

            if video_url:
                # Download to local
                with httpx.Client(timeout=120) as client:
                    vresp = client.get(video_url)
                    vresp.raise_for_status()
                    out_path.write_bytes(vresp.content)

            return VideoGenResult(
                success=True,
                path=str(out_path),
                url=f"/generated/videos/{out_path.name}",
                duration_sec=duration_sec,
                width=width,
                height=height,
                fps=fps,
                n_frames=int(duration_sec * fps),
                model=cfg["model"],
                mode="runpod_video",
            )
        except Exception as e:
            log.warning(f"[video_gen] runpod fail: {e}, falling back to mock")
            # Fall through to mock

    # Mock mode: write a tiny placeholder file
    mock_content = (
        f"# SIDIX Video Gen Mock Placeholder\n"
        f"prompt: {prompt}\n"
        f"duration: {duration_sec}s\n"
        f"resolution: {width}x{height}@{fps}fps\n"
        f"\n"
        f"Phase 4 actual video gen butuh:\n"
        f"- RUNPOD_VIDEO_ENDPOINT_ID env var (deploy SVD/CogVideoX worker dulu)\n"
        f"- RUNPOD_VIDEO_MODEL env var (default: stable-video-diffusion)\n"
        f"- GPU 24GB+ VRAM\n"
    )
    # Save as placeholder text (.mp4 extension just for routing)
    placeholder_path = out_path.with_suffix(".mp4.placeholder.txt")
    placeholder_path.write_text(mock_content, encoding="utf-8")

    return VideoGenResult(
        success=True,
        path=str(placeholder_path),
        url=f"/generated/videos/{placeholder_path.name}",
        duration_sec=duration_sec,
        width=width,
        height=height,
        fps=fps,
        n_frames=int(duration_sec * fps),
        model="mock",
        mode="mock",
        error="RUNPOD_VIDEO_ENDPOINT_ID not set — using placeholder",
    )


__all__ = ["VideoGenResult", "generate_video"]
