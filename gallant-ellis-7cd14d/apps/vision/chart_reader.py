# -*- coding: utf-8 -*-
"""
Bar Chart Reader — Projek Badar Task 110 (G3)
Surah Al-Layl (#92) — Tambah lapisan validasi input sebelum inferensi.

Baca dan ekstrak data dari gambar chart (bar chart, pie chart, line chart).
Status: STUB — wire ke model vision atau chart parsing library lokal.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    UNKNOWN = "unknown"


@dataclass
class DataPoint:
    """Satu titik data dari chart."""
    label: str
    value: float
    color: str = ""
    uncertainty: float = 0.0


@dataclass
class ChartReaderResult:
    """Hasil pembacaan chart dari gambar."""
    image_path: str
    chart_type: ChartType
    title: str
    x_label: str
    y_label: str
    data_points: list[DataPoint] = field(default_factory=list)
    raw_ocr_text: str = ""
    model: str = "stub"
    confidence: float = 0.0
    error: str | None = None


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def detect_chart_type(image_path: str) -> ChartType:
    """
    Deteksi jenis chart dari gambar.

    TODO: Wire ke model klasifikasi chart atau vision-language model.
    Saat ini: heuristik sederhana berbasis nama file.
    """
    name = image_path.lower()
    if any(kw in name for kw in ("bar", "batang", "column")):
        return ChartType.BAR
    if any(kw in name for kw in ("line", "garis", "trend")):
        return ChartType.LINE
    if any(kw in name for kw in ("pie", "donut", "kue")):
        return ChartType.PIE
    if any(kw in name for kw in ("scatter", "sebar", "plot")):
        return ChartType.SCATTER
    return ChartType.UNKNOWN


def read_chart(image_path: str) -> ChartReaderResult:
    """
    Baca dan ekstrak data dari gambar chart.

    Pipeline (stub):
    1. Deteksi jenis chart
    2. OCR untuk label sumbu dan judul
    3. Ekstraksi data point

    TODO: Implementasikan dengan salah satu pendekatan:
    - ChartQA / DePlot (Google): fine-tuned VLM untuk chart
    - OpenCV + kontur untuk bar chart sederhana
    - Qwen-VL / LLaVA dengan prompt khusus: "Extract data from this chart as CSV"
    - pix2struct (Google) untuk chart understanding
    """
    import os
    if not os.path.exists(image_path):
        return ChartReaderResult(
            image_path=image_path,
            chart_type=ChartType.UNKNOWN,
            title="", x_label="", y_label="",
            error=f"File tidak ditemukan: {image_path}",
        )

    chart_type = detect_chart_type(image_path)

    # Coba OCR untuk teks label
    raw_ocr = ""
    try:
        from .caption import extract_text_ocr
        ocr_result = extract_text_ocr(image_path)
        raw_ocr = ocr_result.text
    except ImportError as exc:
        logger.error("[chart_reader] Gagal import caption module: %s", exc)
    except Exception as exc:
        logger.error("[chart_reader] OCR gagal: %s", exc)

    logger.warning(
        "[STUB] chart_reader.read_chart() — ekstraksi data tidak diimplementasikan. "
        "Wire ke ChartQA, DePlot, atau OpenCV untuk pembacaan nyata."
    )

    return ChartReaderResult(
        image_path=image_path,
        chart_type=chart_type,
        title="[STUB] Judul tidak terdeteksi",
        x_label="[STUB]",
        y_label="[STUB]",
        data_points=[],
        raw_ocr_text=raw_ocr,
        model="stub",
        confidence=0.0,
        error="Chart data extraction not implemented: no model loaded",
    )


def data_points_to_csv(result: ChartReaderResult) -> str:
    """Konversi data points ke format CSV."""
    if not result.data_points:
        return "label,value\n# Tidak ada data (stub atau chart tidak terbaca)\n"
    lines = ["label,value"]
    for dp in result.data_points:
        lines.append(f"{dp.label},{dp.value}")
    return "\n".join(lines)


def data_points_to_markdown_table(result: ChartReaderResult) -> str:
    """Konversi data points ke tabel Markdown."""
    if not result.data_points:
        return "| Label | Nilai |\n|-------|-------|\n| (stub) | - |\n"
    header = "| Label | Nilai |"
    sep = "|-------|-------|"
    rows = [f"| {dp.label} | {dp.value} |" for dp in result.data_points]
    return "\n".join([header, sep] + rows)
