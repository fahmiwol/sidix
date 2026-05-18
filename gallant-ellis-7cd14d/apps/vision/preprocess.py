"""
Vision Preprocess — Projek Badar Task 96 (G3)
Endpoint vision: resize, normalisasi format, batas piksel.
Validasi input gambar sebelum dikirim ke pipeline vision.
"""
from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Batas maksimal piksel (4 Megapixel)
MAX_PIXELS: int = 4_000_000

# Format file yang didukung
SUPPORTED_FORMATS: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


@dataclass
class PreprocessResult:
    """Hasil preprocessing gambar."""
    success: bool
    output_path: str
    original_size: tuple
    output_size: tuple
    format: str
    error: str | None = None


def validate_image(image_path: str) -> tuple[bool, str]:
    """
    Validasi format dan ukuran file gambar.

    Args:
        image_path: Path ke file gambar.

    Returns:
        Tuple (valid: bool, pesan: str).
    """
    if not os.path.exists(image_path):
        return False, f"File tidak ditemukan: {image_path}"

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return False, (
            f"Format tidak didukung: '{ext}'. "
            f"Format yang didukung: {', '.join(sorted(SUPPORTED_FORMATS))}"
        )

    file_size = os.path.getsize(image_path)
    if file_size == 0:
        return False, "File gambar kosong (0 bytes)."

    # Cek jumlah piksel jika PIL tersedia
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size
            total_pixels = w * h
            if total_pixels > MAX_PIXELS * 4:  # Hard limit: 4x MAX_PIXELS
                return False, (
                    f"Gambar terlalu besar: {total_pixels:,} piksel "
                    f"(hard limit {MAX_PIXELS * 4:,} piksel)."
                )
    except ImportError:
        pass  # PIL tidak tersedia, lewati pengecekan piksel
    except Exception as exc:
        return False, f"Gagal membuka gambar: {exc}"

    return True, "OK"


def resize_image(
    image_path: str,
    max_pixels: int = MAX_PIXELS,
    output_path: str | None = None,
) -> PreprocessResult:
    """
    Resize gambar jika total piksel melebihi max_pixels.

    Args:
        image_path: Path ke file gambar sumber.
        max_pixels: Batas maksimal piksel. Default MAX_PIXELS (4MP).
        output_path: Path output opsional. Jika None, overwrite input.

    Returns:
        PreprocessResult dengan ukuran asli dan ukuran output.

    Notes:
        Memerlukan Pillow: pip install Pillow
    """
    valid, msg = validate_image(image_path)
    if not valid:
        return PreprocessResult(
            success=False,
            output_path=image_path,
            original_size=(0, 0),
            output_size=(0, 0),
            format="unknown",
            error=msg,
        )

    out_path = output_path or image_path

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            original_size = img.size
            fmt = img.format or "PNG"
            total_pixels = original_size[0] * original_size[1]

            if total_pixels <= max_pixels:
                logger.info(
                    "[Preprocess] Gambar '%s' sudah dalam batas (%d piksel). Tidak perlu resize.",
                    image_path, total_pixels,
                )
                if output_path and output_path != image_path:
                    shutil.copy2(image_path, output_path)
                return PreprocessResult(
                    success=True,
                    output_path=out_path,
                    original_size=original_size,
                    output_size=original_size,
                    format=fmt,
                )

            # Hitung scale factor untuk mempertahankan aspek rasio
            scale = (max_pixels / total_pixels) ** 0.5
            new_w = int(original_size[0] * scale)
            new_h = int(original_size[1] * scale)
            new_size = (new_w, new_h)

            resized = img.resize(new_size, resample=Image.LANCZOS)
            resized.save(out_path, format=fmt)

            logger.info(
                "[Preprocess] Resize '%s': %s → %s (skala %.2f).",
                image_path, original_size, new_size, scale,
            )
            return PreprocessResult(
                success=True,
                output_path=out_path,
                original_size=original_size,
                output_size=new_size,
                format=fmt,
            )

    except ImportError:
        logger.warning("[STUB] PIL tidak tersedia. File disalin tanpa resize.")
        if output_path and output_path != image_path:
            shutil.copy2(image_path, output_path)
        return PreprocessResult(
            success=True,
            output_path=out_path,
            original_size=(0, 0),
            output_size=(0, 0),
            format="unknown",
            error="PIL tidak tersedia — resize tidak dilakukan, file disalin.",
        )
    except Exception as exc:
        logger.error("[Preprocess] Resize gagal untuk '%s': %s", image_path, exc)
        return PreprocessResult(
            success=False,
            output_path=image_path,
            original_size=(0, 0),
            output_size=(0, 0),
            format="unknown",
            error=str(exc),
        )


def normalize_format(
    image_path: str,
    target_format: str = "PNG",
    output_path: str | None = None,
) -> PreprocessResult:
    """
    Konversi gambar ke format target.

    Args:
        image_path: Path ke file gambar sumber.
        target_format: Format output (PNG, JPEG, WEBP, dll.). Default 'PNG'.
        output_path: Path output opsional.

    Returns:
        PreprocessResult dengan info konversi.

    Notes:
        Memerlukan Pillow: pip install Pillow
    """
    valid, msg = validate_image(image_path)
    if not valid:
        return PreprocessResult(
            success=False,
            output_path=image_path,
            original_size=(0, 0),
            output_size=(0, 0),
            format=target_format,
            error=msg,
        )

    # Tentukan path output berdasarkan format target
    if output_path is None:
        base = os.path.splitext(image_path)[0]
        output_path = f"{base}.{target_format.lower()}"

    try:
        from PIL import Image

        with Image.open(image_path) as img:
            original_size = img.size
            original_fmt = img.format or "unknown"

            # JPEG tidak mendukung transparansi; konversi ke RGB jika perlu
            if target_format.upper() in ("JPEG", "JPG") and img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            img.save(output_path, format=target_format.upper())

        logger.info(
            "[Preprocess] Format '%s' → '%s': '%s' → '%s'.",
            original_fmt, target_format, image_path, output_path,
        )
        return PreprocessResult(
            success=True,
            output_path=output_path,
            original_size=original_size,
            output_size=original_size,
            format=target_format.upper(),
        )

    except ImportError:
        logger.warning("[STUB] PIL tidak tersedia. Konversi format tidak dapat dilakukan.")
        return PreprocessResult(
            success=False,
            output_path=image_path,
            original_size=(0, 0),
            output_size=(0, 0),
            format=target_format,
            error="PIL tidak tersedia — install Pillow: pip install Pillow",
        )
    except Exception as exc:
        logger.error("[Preprocess] normalize_format gagal untuk '%s': %s", image_path, exc)
        return PreprocessResult(
            success=False,
            output_path=image_path,
            original_size=(0, 0),
            output_size=(0, 0),
            format=target_format,
            error=str(exc),
        )
