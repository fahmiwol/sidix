"""
Analysis Display — Projek Badar Task 103 (G3)
Side-by-side gambar asli vs analisis teks.
Output: teks ASCII, HTML, dan Markdown.
"""
from __future__ import annotations

import html
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """Laporan lengkap analisis satu gambar."""
    image_path: str
    caption: str
    ocr_text: str
    classification: str
    objects: list[str] = field(default_factory=list)
    confidence: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


def format_side_by_side(report: AnalysisReport) -> str:
    """
    Format laporan analisis sebagai tampilan ASCII side-by-side.
    Kolom kiri: info gambar. Kolom kanan: hasil analisis.

    Args:
        report: AnalysisReport yang akan ditampilkan.

    Returns:
        String tampilan teks terformat.
    """
    col_width = 36
    separator = "│"

    def pad(text: str, width: int = col_width) -> str:
        """Potong atau pad teks ke lebar tetap."""
        if len(text) > width:
            return text[:width - 3] + "..."
        return text.ljust(width)

    img_name = os.path.basename(report.image_path)
    img_size = ""
    try:
        size_bytes = os.path.getsize(report.image_path)
        img_size = f"{size_bytes / 1024:.1f} KB"
    except OSError:
        img_size = "tidak diketahui"

    left_lines = [
        "INFORMASI GAMBAR",
        "─" * col_width,
        f"Nama : {img_name}",
        f"Ukuran: {img_size}",
        f"Waktu : {report.generated_at[:19]}",
        "",
        f"Klasifikasi:",
        f"  {report.classification}",
        "",
        f"Objek ({len(report.objects)}):",
    ]
    left_lines += [f"  • {obj}" for obj in report.objects[:5]]
    if len(report.objects) > 5:
        left_lines.append(f"  ... +{len(report.objects) - 5} lainnya")
    left_lines += [""] * max(0, 14 - len(left_lines))

    right_lines = [
        "HASIL ANALISIS",
        "─" * col_width,
        f"Kepercayaan: {report.confidence:.1%}",
        "",
        "Caption:",
    ]
    # Bungkus caption ke baris pendek
    caption_words = report.caption.split()
    line = ""
    for word in caption_words:
        if len(line) + len(word) + 1 > col_width - 2:
            right_lines.append(f"  {line.strip()}")
            line = word
        else:
            line += " " + word
    if line.strip():
        right_lines.append(f"  {line.strip()}")

    right_lines += ["", "Teks OCR (cuplikan):"]
    ocr_preview = report.ocr_text[:80].replace("\n", " ") if report.ocr_text else "(tidak ada)"
    right_lines.append(f"  {ocr_preview}")
    if report.notes:
        right_lines += ["", f"Catatan: {report.notes}"]

    # Seimbangkan jumlah baris
    max_lines = max(len(left_lines), len(right_lines))
    left_lines += [""] * (max_lines - len(left_lines))
    right_lines += [""] * (max_lines - len(right_lines))

    top_border = "┌" + "─" * col_width + "┬" + "─" * col_width + "┐"
    bottom_border = "└" + "─" * col_width + "┴" + "─" * col_width + "┘"

    rows = [top_border]
    for left, right in zip(left_lines, right_lines):
        rows.append(f"{separator}{pad(left)}{separator}{pad(right)}{separator}")
    rows.append(bottom_border)

    return "\n".join(rows)


def generate_html_report(report: AnalysisReport, output_path: str) -> str:
    """
    Generate file HTML laporan analisis gambar side-by-side.
    HTML sederhana tanpa dependensi eksternal.

    Args:
        report: AnalysisReport yang akan di-render.
        output_path: Path file HTML output.

    Returns:
        Path file HTML yang dibuat.
    """
    img_name = html.escape(os.path.basename(report.image_path))
    caption_esc = html.escape(report.caption)
    ocr_esc = html.escape(report.ocr_text or "(tidak ada teks OCR)")
    classification_esc = html.escape(report.classification)
    notes_esc = html.escape(report.notes) if report.notes else ""

    objects_html = "".join(
        f"<li>{html.escape(obj)}</li>" for obj in report.objects
    ) or "<li>(tidak ada objek terdeteksi)</li>"

    # Path gambar relatif dari output HTML
    try:
        rel_img = os.path.relpath(report.image_path, os.path.dirname(output_path))
    except ValueError:
        rel_img = report.image_path
    rel_img_esc = html.escape(rel_img)

    html_content = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Analisis Vision — {img_name}</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      margin: 0; padding: 20px;
      background: #f5f5f5; color: #333;
    }}
    h1 {{ font-size: 1.4rem; color: #2c5282; border-bottom: 2px solid #2c5282; padding-bottom: 8px; }}
    .container {{ display: flex; gap: 24px; flex-wrap: wrap; }}
    .panel {{
      background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
      padding: 16px; flex: 1; min-width: 280px;
    }}
    .panel h2 {{ font-size: 1rem; color: #4a5568; margin: 0 0 12px; }}
    .panel img {{ max-width: 100%; border-radius: 4px; border: 1px solid #e2e8f0; }}
    .badge {{
      display: inline-block; padding: 2px 8px; border-radius: 12px;
      font-size: 0.8rem; font-weight: bold; background: #ebf8ff; color: #2b6cb0;
    }}
    .section {{ margin-bottom: 12px; }}
    .label {{ font-weight: bold; font-size: 0.85rem; color: #718096; text-transform: uppercase; }}
    .value {{ margin-top: 4px; white-space: pre-wrap; font-size: 0.95rem; }}
    .confidence-bar {{
      height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden; margin-top: 4px;
    }}
    .confidence-fill {{
      height: 100%; background: #48bb78;
      width: {min(report.confidence * 100, 100):.1f}%;
    }}
    footer {{ margin-top: 20px; font-size: 0.75rem; color: #a0aec0; }}
  </style>
</head>
<body>
  <h1>Laporan Analisis Vision — Projek Badar G3</h1>
  <div class="container">
    <div class="panel">
      <h2>Gambar Asli</h2>
      <img src="{rel_img_esc}" alt="{img_name}" onerror="this.alt='Gambar tidak dapat dimuat'">
      <div class="section" style="margin-top:12px">
        <div class="label">Nama File</div>
        <div class="value">{img_name}</div>
      </div>
      <div class="section">
        <div class="label">Waktu Analisis</div>
        <div class="value">{html.escape(report.generated_at[:19].replace('T', ' '))}</div>
      </div>
      <div class="section">
        <div class="label">Klasifikasi</div>
        <div class="value"><span class="badge">{classification_esc}</span></div>
      </div>
      <div class="section">
        <div class="label">Objek Terdeteksi</div>
        <ul>{objects_html}</ul>
      </div>
    </div>
    <div class="panel">
      <h2>Hasil Analisis</h2>
      <div class="section">
        <div class="label">Kepercayaan Keseluruhan</div>
        <div class="value">{report.confidence:.1%}</div>
        <div class="confidence-bar"><div class="confidence-fill"></div></div>
      </div>
      <div class="section">
        <div class="label">Caption</div>
        <div class="value">{caption_esc}</div>
      </div>
      <div class="section">
        <div class="label">Teks OCR</div>
        <div class="value">{ocr_esc}</div>
      </div>
      {"<div class='section'><div class='label'>Catatan</div><div class='value'>" + notes_esc + "</div></div>" if notes_esc else ""}
    </div>
  </div>
  <footer>
    Dibuat oleh SIDIX Vision Pipeline — Projek Badar G3 (Tasks 94-104) |
    Status: STUB — model vision belum aktif
  </footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("[Display] HTML report ditulis ke '%s'.", output_path)
    return output_path


def to_markdown(report: AnalysisReport) -> str:
    """
    Konversi AnalysisReport ke representasi Markdown.

    Args:
        report: AnalysisReport yang akan dikonversi.

    Returns:
        String dalam format Markdown.
    """
    img_name = os.path.basename(report.image_path)
    objects_md = "\n".join(f"- {obj}" for obj in report.objects) if report.objects else "_Tidak ada_"

    lines = [
        f"# Laporan Analisis Vision — {img_name}",
        "",
        f"**Waktu Analisis:** {report.generated_at[:19].replace('T', ' ')}",
        f"**Kepercayaan:** {report.confidence:.1%}",
        f"**Klasifikasi:** `{report.classification}`",
        "",
        "## Caption",
        "",
        report.caption or "_Tidak tersedia_",
        "",
        "## Teks OCR",
        "",
        f"```\n{report.ocr_text or '(tidak ada teks OCR)'}\n```",
        "",
        "## Objek Terdeteksi",
        "",
        objects_md,
    ]

    if report.notes:
        lines += ["", "## Catatan", "", report.notes]

    lines += [
        "",
        "---",
        "_Dibuat oleh SIDIX Vision Pipeline — Projek Badar G3 | Status: STUB_",
    ]

    return "\n".join(lines)
