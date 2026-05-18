"""
Table Extraction — Projek Badar Task 100 (G3, optional)
Ekstraksi tabel dari gambar.
Status: STUB — pipeline opsional, wire ke table detection model.
"""
from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    """Satu sel dalam tabel yang diekstrak."""
    row: int
    col: int
    text: str
    confidence: float = 0.0


@dataclass
class TableResult:
    """Hasil ekstraksi tabel dari gambar."""
    success: bool
    rows: int
    cols: int
    cells: list[TableCell] = field(default_factory=list)
    csv_output: str = ""
    model: str = "stub"


def extract_table(image_path: str) -> TableResult:
    """
    Ekstrak tabel dari gambar.

    Args:
        image_path: Path ke file gambar yang mengandung tabel.

    Returns:
        TableResult berisi sel-sel tabel yang diekstrak.

    Notes:
        # TODO: gunakan table detection model, contoh:
        #   - table-transformer (Microsoft): huggingface.co/microsoft/table-transformer-detection
        #   - PaddleOCR dengan table recognition: pip install paddleocr
        #   - Camelot/Tabula untuk PDF (bukan gambar)
        #   Pipeline umum:
        #   1. Deteksi region tabel dengan table-transformer
        #   2. Crop region tabel
        #   3. OCR per sel dengan PaddleOCR / pytesseract
        #   4. Rekonstruksi struktur baris/kolom
    """
    logger.warning(
        "[STUB] extract_table: model table extraction belum terpasang untuk '%s'.",
        image_path,
    )
    return TableResult(
        success=False,
        rows=0,
        cols=0,
        cells=[],
        csv_output="",
        model="stub",
    )


def table_to_csv(result: TableResult) -> str:
    """
    Konversi hasil TableResult ke format CSV.

    Args:
        result: TableResult dari extract_table().

    Returns:
        String CSV, atau string kosong jika tabel tidak berhasil diekstrak.
    """
    if not result.success or not result.cells:
        logger.info("[Table] table_to_csv: tidak ada sel untuk dikonversi.")
        return ""

    # Inisialisasi grid kosong
    grid: list[list[str]] = [
        [""] * result.cols for _ in range(result.rows)
    ]

    for cell in result.cells:
        if 0 <= cell.row < result.rows and 0 <= cell.col < result.cols:
            grid[cell.row][cell.col] = cell.text

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(grid)
    csv_str = output.getvalue()

    logger.info(
        "[Table] table_to_csv: %d baris x %d kolom → %d karakter CSV.",
        result.rows, result.cols, len(csv_str),
    )
    return csv_str


def table_to_markdown(result: TableResult) -> str:
    """
    Konversi hasil TableResult ke format Markdown table.

    Args:
        result: TableResult dari extract_table().

    Returns:
        String Markdown table, atau pesan kosong jika gagal.
    """
    if not result.success or not result.cells:
        return "_Tabel tidak dapat diekstrak (model stub)._"

    # Inisialisasi grid
    grid: list[list[str]] = [
        [""] * result.cols for _ in range(result.rows)
    ]
    for cell in result.cells:
        if 0 <= cell.row < result.rows and 0 <= cell.col < result.cols:
            grid[cell.row][cell.col] = cell.text

    lines: list[str] = []

    for row_idx, row in enumerate(grid):
        row_str = "| " + " | ".join(str(cell) for cell in row) + " |"
        lines.append(row_str)
        # Tambahkan separator setelah header (baris pertama)
        if row_idx == 0:
            separator = "| " + " | ".join(["---"] * result.cols) + " |"
            lines.append(separator)

    md = "\n".join(lines)
    logger.info(
        "[Table] table_to_markdown: %d baris × %d kolom dikonversi.",
        result.rows, result.cols,
    )
    return md
