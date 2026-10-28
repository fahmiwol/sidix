"""
Tile Export — Projek Badar Task 89 (G2)
Tile tekstur untuk game/edu asset.

Juga menggabungkan Task 92: Sticker Pack Export.
"""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


@dataclass
class TileConfig:
    """Konfigurasi ekspor tile tekstur."""

    tile_size: int = 256
    output_format: str = "PNG"
    seamless: bool = False


def export_as_tile(
    image_path: str,
    output_dir: str,
    config: Optional[TileConfig] = None,
) -> dict:
    """
    Ekspor gambar sebagai tile tekstur ke output_dir.

    STUB: copy gambar ke output_dir dengan penamaan tile_{size}x{size}.png.
    TODO: implementasikan dengan PIL:
    - Resize ke tile_size x tile_size.
    - Bila seamless=True: terapkan seamless tiling (mirroring edges).
    - Simpan dengan format yang ditentukan.

    Returns:
        dict berisi output_path, tile_size, dan status.
    """
    if config is None:
        config = TileConfig()

    src = Path(image_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tile_name = f"tile_{config.tile_size}x{config.tile_size}.{config.output_format.lower()}"
    out_path = out_dir / tile_name

    if _PIL_AVAILABLE and src.exists():
        try:
            with _PILImage.open(str(src)) as img:
                img = img.resize((config.tile_size, config.tile_size))
                img.save(str(out_path), format=config.output_format)
            logger.info("Tile diekspor: %s", out_path)
            return {
                "output_path": str(out_path),
                "tile_size": config.tile_size,
                "status": "ok",
            }
        except Exception as exc:
            logger.error("Gagal ekspor tile dengan PIL: %s", exc)

    # Fallback: copy file
    if src.exists():
        shutil.copy2(str(src), str(out_path))
    else:
        logger.warning("Source file tidak ditemukan: %s", image_path)

    return {
        "output_path": str(out_path),
        "tile_size": config.tile_size,
        "status": "stub — TODO: implement tiling with PIL",
    }


def export_sticker_pack(
    image_paths: list[str],
    output_dir: str,
    size: int = 512,
) -> dict:
    """
    Ekspor pack stiker dari daftar gambar.

    Task 92 consolidation: resize square + simpan ke output_dir.
    STUB: copy gambar dengan penamaan stiker standar.
    TODO: implementasikan square crop + resize dengan PIL.

    Returns:
        dict berisi jumlah exported, output_dir, dan status.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    exported_count = 0
    for i, img_path in enumerate(image_paths):
        src = Path(img_path)
        out_name = f"sticker_{i+1:03d}_{size}x{size}.png"
        out_path = out_dir / out_name

        if _PIL_AVAILABLE and src.exists():
            try:
                with _PILImage.open(str(src)) as img:
                    # Square crop dari tengah
                    w, h = img.size
                    min_dim = min(w, h)
                    left = (w - min_dim) // 2
                    top = (h - min_dim) // 2
                    img = img.crop((left, top, left + min_dim, top + min_dim))
                    img = img.resize((size, size))
                    img.save(str(out_path), format="PNG")
                exported_count += 1
                continue
            except Exception as exc:
                logger.warning("Gagal proses stiker %s: %s", img_path, exc)

        # Fallback copy
        if src.exists():
            shutil.copy2(str(src), str(out_path))
            exported_count += 1
        else:
            logger.warning("Source stiker tidak ditemukan: %s", img_path)

    logger.info(
        "Sticker pack diekspor: %d/%d gambar ke %s",
        exported_count,
        len(image_paths),
        output_dir,
    )
    return {
        "exported": exported_count,
        "output_dir": str(out_dir),
        "status": "stub",
    }
