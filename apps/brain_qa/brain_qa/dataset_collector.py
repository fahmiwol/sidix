"""
dataset_collector.py — SIDIX Dataset Collector
===============================================
Scan folder lokal untuk collect metadata gambar sebagai dataset training.
Read-only — tidak edit/move/delete file asli.

Supported sources:
  - Mighan-Web assets (NPC portraits)
  - Mighan-3D assets (sprites, textures)
  - NPC-Agent catalogue
  - SIDIX workspace uploads

Output:
  - JSONL dataset index (path, metadata, tags, dimensions)
  - Compatible dengan training pipeline (LoRA, fine-tune)

Research notes:
  - 318 cognitive expansion (dataset collection)
"""
from __future__ import annotations

import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


# Known dataset sources (read-only scan)
DATASET_SOURCES = {
    "mighan-web-agents": "C:/Mighan-Web/assets/agents",
    "mighan-web-sprites": "C:/Mighan-Web/assets/sprites",
    "mighan-3d-sprites": "C:/Mighan-3D/assets/sprites",
    "mighan-3d-design-studio": "C:/Mighan-3D/design-studio",
}


def _get_image_dimensions(path: str) -> tuple[int, int] | None:
    """Get image dimensions via PIL if available."""
    try:
        from PIL import Image  # type: ignore
        with Image.open(path) as img:
            return img.size
    except Exception:  # noqa: BLE001
        return None


def scan_folder(path: str, allowed_exts: set[str] | None = None, max_depth: int = 3) -> dict:
    """Scan folder untuk collect file metadata (read-only)."""
    if not os.path.exists(path):
        return _fallback(f"Folder tidak ditemukan: {path}")

    if allowed_exts is None:
        allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".svg"}

    files = []
    root = Path(path)
    for i, p in enumerate(root.rglob("*")):
        if i > 5000:  # safety limit
            break
        if p.is_file() and p.suffix.lower() in allowed_exts:
            stat = p.stat()
            dim = _get_image_dimensions(str(p))
            files.append({
                "path": str(p),
                "filename": p.name,
                "extension": p.suffix.lower(),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "width": dim[0] if dim else None,
                "height": dim[1] if dim else None,
                "relative": str(p.relative_to(root)),
            })

    return _ok({
        "source_path": path,
        "files_scanned": len(files),
        "total_size_mb": round(sum(f["size_bytes"] for f in files) / (1024 * 1024), 2),
        "files": files,
    })


def collect_dataset(sources: list[str] | None = None, tags: list[str] | None = None) -> dict:
    """Collect dataset dari multiple sources."""
    if sources is None:
        sources = list(DATASET_SOURCES.values())

    all_files = []
    source_stats = []
    for src in sources:
        result = scan_folder(src)
        if result.get("ok"):
            data = result["data"]
            files = data.get("files", [])
            for f in files:
                f["source"] = src
                f["tags"] = tags or []
            all_files.extend(files)
            source_stats.append({
                "source": src,
                "count": len(files),
                "size_mb": data.get("total_size_mb", 0),
            })

    if not all_files:
        return _fallback("Tidak ada file gambar ditemukan di sources.", data={"sources_checked": sources})

    return _ok({
        "total_files": len(all_files),
        "total_size_mb": round(sum(f["size_bytes"] for f in all_files) / (1024 * 1024), 2),
        "sources": source_stats,
        "files": all_files,
        "export_formats": ["jsonl", "csv", "parquet"],
    })


def export_dataset_jsonl(files: list[dict], output_path: str) -> dict:
    """Export collected dataset ke JSONL format untuk training."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for item in files:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return _ok({
            "output_path": output_path,
            "records_written": len(files),
            "format": "jsonl",
        })
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"Export gagal: {exc}")


def get_available_sources() -> dict:
    """List available dataset sources dengan existence check."""
    sources = []
    for name, path in DATASET_SOURCES.items():
        exists = os.path.exists(path)
        count = 0
        if exists:
            count = sum(1 for _ in Path(path).rglob("*") if _.is_file())
        sources.append({
            "name": name,
            "path": path,
            "exists": exists,
            "file_count": count,
        })
    return _ok({"sources": sources})


def auto_tag_by_folder(files: list[dict]) -> list[dict]:
    """Auto-tag files berdasarkan folder name."""
    tag_rules = {
        "agents": ["npc", "portrait", "character"],
        "sprites": ["sprite", "ui", "2d"],
        "design-studio": ["design", "asset", "creative"],
        "npc-generator": ["npc", "generator", "character"],
        "photo": ["photo", "image"],
        "canvas": ["canvas", "art"],
    }
    for f in files:
        path_lower = f.get("path", "").lower()
        tags = set(f.get("tags", []))
        for folder, folder_tags in tag_rules.items():
            if folder in path_lower:
                tags.update(folder_tags)
        f["tags"] = sorted(tags)
    return files
