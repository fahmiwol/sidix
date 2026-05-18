"""
Watermark & Metadata — Projek Badar Task 79 (G2)
Watermark/metadata output gambar (provenansi SIDIX).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image as _PILImage, PngImagePlugin

    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning("Pillow tidak tersedia. Metadata disimpan sebagai sidecar .meta.json.")


@dataclass
class ImageMetadata:
    """Metadata provenansi gambar yang dihasilkan SIDIX."""

    prompt: str
    model: str
    seed: Optional[int]
    style: str
    generated_at: str
    generator: str = "SIDIX"
    version: str = "0.1.0"


def embed_metadata(image_path: str, metadata: ImageMetadata) -> bool:
    """
    Embed metadata ke dalam file gambar.

    Bila PIL tersedia: simpan di field 'Comment' (PNG metadata / EXIF).
    Fallback: tulis file sidecar <image_path>.meta.json.

    Returns:
        True bila berhasil.
    """
    meta_json = json.dumps(asdict(metadata), ensure_ascii=False)
    path = Path(image_path)

    if _PIL_AVAILABLE and path.exists():
        try:
            with _PILImage.open(str(path)) as img:
                if img.format == "PNG":
                    info = PngImagePlugin.PngInfo()
                    info.add_text("Comment", meta_json)
                    img.save(str(path), pnginfo=info)
                else:
                    # Untuk JPEG: gunakan EXIF UserComment via piexif bila tersedia
                    # TODO: tambahkan piexif untuk JPEG EXIF embedding
                    logger.warning(
                        "Format %s: EXIF embed belum diimplementasikan, fallback ke sidecar.",
                        img.format,
                    )
                    return _write_sidecar(image_path, meta_json)
            logger.info("Metadata di-embed ke %s", image_path)
            return True
        except Exception as exc:
            logger.error("Gagal embed metadata PIL: %s — fallback ke sidecar.", exc)

    return _write_sidecar(image_path, meta_json)


def _write_sidecar(image_path: str, meta_json: str) -> bool:
    """Tulis sidecar file <image_path>.meta.json."""
    sidecar_path = Path(image_path + ".meta.json")
    try:
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_path.write_text(meta_json, encoding="utf-8")
        logger.info("Metadata sidecar ditulis: %s", sidecar_path)
        return True
    except Exception as exc:
        logger.error("Gagal menulis sidecar metadata: %s", exc)
        return False


def read_metadata(image_path: str) -> Optional[ImageMetadata]:
    """
    Baca metadata dari file gambar atau sidecar.

    Urutan: coba EXIF/PNG comment dulu, lalu sidecar .meta.json.

    Returns:
        ImageMetadata atau None bila tidak ditemukan.
    """
    path = Path(image_path)

    # Coba dari PNG metadata
    if _PIL_AVAILABLE and path.exists():
        try:
            with _PILImage.open(str(path)) as img:
                info = img.info
                comment = info.get("Comment") or info.get("comment")
                if comment:
                    data = json.loads(comment)
                    return ImageMetadata(**data)
        except Exception as exc:
            logger.debug("Gagal baca metadata dari gambar: %s", exc)

    # Coba dari sidecar
    sidecar = Path(image_path + ".meta.json")
    if sidecar.exists():
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            return ImageMetadata(**data)
        except Exception as exc:
            logger.warning("Gagal baca sidecar metadata: %s", exc)

    return None


def add_text_watermark(image_path: str, text: str = "SIDIX") -> bool:
    """
    Tambahkan watermark teks ke gambar.

    STUB — TODO: gunakan PIL ImageDraw untuk menambahkan watermark
    semi-transparan di sudut gambar.

    Returns:
        False (belum diimplementasikan).
    """
    # TODO: implementasi watermark dengan PIL
    # from PIL import ImageDraw, ImageFont
    # with Image.open(image_path) as img:
    #     draw = ImageDraw.Draw(img)
    #     draw.text((10, 10), text, fill=(255, 255, 255, 128))
    #     img.save(image_path)
    logger.warning(
        "add_text_watermark() belum diimplementasikan (stub). "
        "TODO: gunakan PIL ImageDraw untuk watermark teks '%s'.",
        text,
    )
    return False
