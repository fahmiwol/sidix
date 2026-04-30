"""
Region Crop — Projek Badar Task 98 (G3)
Bounding box / region crop untuk fokus analisis pada area tertentu gambar.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from .models import BoundingBox

logger = logging.getLogger(__name__)


@dataclass
class CropResult:
    """Hasil crop region gambar."""
    success: bool
    output_path: str
    bbox: BoundingBox
    error: str | None = None


def normalize_bbox(
    bbox: BoundingBox,
    image_width: int,
    image_height: int,
) -> BoundingBox:
    """
    Clamp bounding box agar tidak melebihi batas gambar.

    Args:
        bbox: BoundingBox yang akan di-clamp.
        image_width: Lebar gambar dalam piksel.
        image_height: Tinggi gambar dalam piksel.

    Returns:
        BoundingBox baru yang sudah di-clamp ke dalam batas gambar.
    """
    x = max(0, min(bbox.x, image_width - 1))
    y = max(0, min(bbox.y, image_height - 1))
    # Pastikan lebar & tinggi tidak melampaui batas kanan/bawah
    width = max(1, min(bbox.width, image_width - x))
    height = max(1, min(bbox.height, image_height - y))

    return BoundingBox(
        x=x,
        y=y,
        width=width,
        height=height,
        label=bbox.label,
        confidence=bbox.confidence,
    )


def crop_region(
    image_path: str,
    bbox: BoundingBox,
    output_path: str | None = None,
) -> CropResult:
    """
    Crop satu region dari gambar berdasarkan bounding box.

    Args:
        image_path: Path ke file gambar sumber.
        bbox: BoundingBox yang menentukan area crop.
        output_path: Path output opsional. Jika None, dibuat otomatis.

    Returns:
        CropResult dengan path output dan status.
    """
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_crop_{bbox.x}_{bbox.y}{ext}"

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            img_w, img_h = img.size
            norm_bbox = normalize_bbox(bbox, img_w, img_h)

            # PIL crop box: (left, upper, right, lower)
            crop_box = (
                norm_bbox.x,
                norm_bbox.y,
                norm_bbox.x + norm_bbox.width,
                norm_bbox.y + norm_bbox.height,
            )
            cropped = img.crop(crop_box)
            cropped.save(output_path)

        logger.info(
            "[Crop] Berhasil crop '%s' → '%s' (box=%s).",
            image_path, output_path, crop_box,
        )
        return CropResult(
            success=True,
            output_path=output_path,
            bbox=norm_bbox,
        )

    except ImportError:
        logger.warning("[STUB] PIL tidak tersedia. Crop tidak dapat dilakukan.")
        return CropResult(
            success=False,
            output_path=output_path,
            bbox=bbox,
            error="PIL tidak tersedia — install Pillow: pip install Pillow",
        )
    except Exception as exc:
        logger.error("[Crop] Gagal crop '%s': %s", image_path, exc)
        return CropResult(
            success=False,
            output_path=output_path,
            bbox=bbox,
            error=str(exc),
        )


def crop_to_regions(
    image_path: str,
    bboxes: list[BoundingBox],
    output_dir: str,
) -> list[CropResult]:
    """
    Crop beberapa region sekaligus dari satu gambar.

    Args:
        image_path: Path ke file gambar sumber.
        bboxes: Daftar BoundingBox yang akan di-crop.
        output_dir: Direktori output untuk file hasil crop.

    Returns:
        Daftar CropResult untuk setiap BoundingBox.
    """
    os.makedirs(output_dir, exist_ok=True)
    results: list[CropResult] = []

    basename = os.path.splitext(os.path.basename(image_path))[0]
    ext = os.path.splitext(image_path)[1]

    for idx, bbox in enumerate(bboxes):
        label_part = f"_{bbox.label}" if bbox.label else ""
        out_path = os.path.join(output_dir, f"{basename}_region{idx}{label_part}{ext}")
        result = crop_region(image_path, bbox, output_path=out_path)
        results.append(result)

    logger.info(
        "[Crop] crop_to_regions: %d region dari '%s', %d berhasil.",
        len(bboxes),
        image_path,
        sum(1 for r in results if r.success),
    )
    return results
