"""
vision_analyzer.py — SIDIX Vision Analyzer
==========================================
VLM wrapper untuk analisis gambar dan video via Ollama vision models.
CPU-friendly dengan fallback chain: moondream → llava-phi3 → llava → text caption.

Research notes:
  - 318 cognitive expansion (multimodal input)
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


def _ollama_chat(model: str, prompt: str, image_path: str | None = None) -> dict:
    """Call Ollama /api/chat dengan image support."""
    try:
        import httpx  # type: ignore
        payload: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 512},
        }
        if image_path and Path(image_path).exists():
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            payload["messages"][0]["images"] = [b64]

        resp = httpx.post(
            "http://localhost:11434/api/chat",
            json=payload,
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"ok": True, "text": data.get("message", {}).get("content", ""), "model": model}
    except ImportError:
        return {"ok": False, "error": "httpx belum terpasang. Jalankan: pip install httpx"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Ollama call gagal: {exc}"}


VISION_MODELS = ["moondream:latest", "llava-phi3:latest", "llava:latest", "bakllava:latest"]


def _available_vision_model() -> str | None:
    """Cek Ollama list untuk vision model yang tersedia."""
    try:
        import httpx  # type: ignore
        resp = httpx.get("http://localhost:11434/api/tags", timeout=10.0)
        resp.raise_for_status()
        tags = resp.json().get("models", [])
        names = {t.get("name", "").lower() for t in tags}
        for m in VISION_MODELS:
            if m.lower() in names:
                return m
        return None
    except Exception:  # noqa: BLE001
        return None


def analyze_image(image_path: str, prompt: str = "") -> dict:
    """Analisis gambar via VLM Ollama. CPU-friendly (moondream 1.6B)."""
    if not os.path.exists(image_path):
        return _fallback(f"File tidak ditemukan: {image_path}")

    default_prompt = (
        "Deskripsikan gambar ini secara detail dalam Bahasa Indonesia. "
        "Sebutkan: objek utama, warna dominan, suasana/mood, teks yang terlihat, "
        "dan konteks visual apa pun."
    )
    prompt = (prompt or default_prompt).strip()

    model = _available_vision_model()
    if not model:
        # Fallback: describe via EXIF + file metadata (no VLM)
        return _fallback(
            "Vision model belum tersedia di Ollama. "
            "Jalankan: ollama pull moondream   # 1.6B, CPU-friendly\n"
            "atau: ollama pull llava-phi3      # 3.8B, lebih akurat\n"
            "atau: ollama pull llava           # 7B, paling akurat",
            data={"image_path": image_path, "prompt": prompt},
        )

    result = _ollama_chat(model, prompt, image_path)
    if result.get("ok"):
        return _ok({
            "backend": f"ollama-{model}",
            "model": model,
            "prompt": prompt,
            "description": result["text"],
            "image_path": image_path,
        }, note=f"Vision model: {model}")

    return _fallback(result.get("error", "VLM inference gagal"), data={"model": model})


def analyze_video(video_path: str, prompt: str = "") -> dict:
    """Analisis video: extract frame setiap 2 detik → analisis keyframes."""
    if not os.path.exists(video_path):
        return _fallback(f"File tidak ditemukan: {video_path}")

    default_prompt = (
        "Deskripsikan adegan video ini dalam Bahasa Indonesia. "
        "Sebutkan: aksi utama, objek, orang, lokasi, dan narasi visual."
    )
    prompt = (prompt or default_prompt).strip()

    # Extract frames via ffmpeg
    try:
        with tempfile.TemporaryDirectory(prefix="sidix_vid_") as tmp:
            frame_pattern = Path(tmp) / "frame_%04d.jpg"
            cmd = [
                "ffmpeg", "-i", video_path, "-vf", "fps=0.5,scale=480:-1",
                "-q:v", "2", str(frame_pattern), "-y"
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode != 0:
                return _fallback(f"ffmpeg gagal: {proc.stderr}", data={"cmd": cmd})

            frames = sorted(Path(tmp).glob("frame_*.jpg"))
            if not frames:
                return _fallback("Tidak ada frame yang bisa diekstrak.")

            # Analyze first, middle, last frame
            keyframes = [frames[0], frames[len(frames)//2], frames[-1]]
            descriptions = []
            model = _available_vision_model()
            if not model:
                return _fallback(
                    "Vision model belum tersedia. Jalankan: ollama pull moondream",
                    data={"frames_extracted": len(frames)},
                )

            for i, frame in enumerate(keyframes, 1):
                r = _ollama_chat(model, prompt, str(frame))
                desc = r["text"] if r.get("ok") else "(analisis frame gagal)"
                descriptions.append(f"[Frame {i}/{len(keyframes)}] {desc}")

            return _ok({
                "backend": f"ollama-{model}",
                "model": model,
                "video_path": video_path,
                "frames_extracted": len(frames),
                "keyframes_analyzed": len(keyframes),
                "descriptions": descriptions,
                "combined_description": "\n\n".join(descriptions),
            })
    except FileNotFoundError:
        return _fallback(
            "ffmpeg tidak ditemukan. Install: apt install ffmpeg (Linux) "
            "atau download dari https://ffmpeg.org/download.html",
        )
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"Video analysis gagal: {exc}")


def generate_image_prompt(image_path: str) -> dict:
    """Generate prompt untuk image-to-image / style transfer."""
    result = analyze_image(image_path, prompt="Buatkan deskripsi prompt detail untuk meregenerasi gambar ini dalam gaya yang sama.")
    if result.get("ok"):
        data = result["data"]
        data["purpose"] = "image_prompt_generation"
        return _ok(data)
    return result
