"""
Flowchart OCR — Projek Badar Task 102 (G3)
Deteksi teks pada diagram alir (flowchart).
Status: STUB — wire ke OCR model atau vision-language model.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Tipe node yang dikenali dalam flowchart
VALID_NODE_TYPES = {"start", "end", "process", "decision", "io"}


@dataclass
class FlowchartNode:
    """Satu node dalam flowchart yang terdeteksi."""
    node_id: str
    text: str
    bbox: dict         # {"x": int, "y": int, "width": int, "height": int}
    node_type: str = "process"   # start|end|process|decision|io


@dataclass
class FlowchartResult:
    """Hasil deteksi flowchart lengkap."""
    nodes: list[FlowchartNode] = field(default_factory=list)
    edges: list[dict] = field(default_factory=list)   # [{"from": id, "to": id, "label": str}]
    mermaid_output: str = ""
    confidence: float = 0.0


def detect_flowchart_text(image_path: str) -> FlowchartResult:
    """
    Deteksi teks dan struktur pada gambar flowchart.

    Args:
        image_path: Path ke file gambar flowchart.

    Returns:
        FlowchartResult berisi node, edge, dan Mermaid output.

    Notes:
        # TODO: wire ke OCR + layout analysis model:
        #   Pipeline yang direkomendasikan:
        #   1. Segmentasi bentuk (rectangle, diamond, oval) dengan OpenCV contours
        #      atau model deteksi objek lokal
        #   2. OCR teks di dalam setiap bentuk (pytesseract / PaddleOCR)
        #   3. Deteksi panah/garis penghubung antar bentuk
        #   4. Rekonstruksi graph flowchart
        #   5. Konversi ke Mermaid / DOT format
        #
        #   Alternatif vision-language model:
        #   - Qwen-VL dengan prompt "Jelaskan struktur flowchart dalam gambar ini"
        #   - LLaVA dengan prompt serupa
    """
    logger.warning(
        "[STUB] detect_flowchart_text: model flowchart OCR belum terpasang untuk '%s'.",
        image_path,
    )
    return FlowchartResult(
        nodes=[],
        edges=[],
        mermaid_output="graph TD\n  A[Stub] --> B[Not Implemented]",
        confidence=0.0,
    )


def to_mermaid(result: FlowchartResult) -> str:
    """
    Konversi FlowchartResult ke sintaks diagram Mermaid.

    Args:
        result: FlowchartResult dari detect_flowchart_text().

    Returns:
        String dalam format Mermaid diagram (graph TD).
        Jika tidak ada node, mengembalikan template stub.
    """
    if not result.nodes:
        # Kembalikan Mermaid stub jika tidak ada node
        return result.mermaid_output or "graph TD\n  A[Tidak ada data flowchart]"

    lines = ["graph TD"]

    # Tambahkan definisi setiap node dengan format sesuai tipe
    for node in result.nodes:
        node_id = node.node_id
        text = node.text.replace('"', "'")  # Escape tanda petik

        if node.node_type == "start" or node.node_type == "end":
            # Oval/stadium untuk start/end
            lines.append(f'  {node_id}(["{text}"])')
        elif node.node_type == "decision":
            # Diamond untuk decision
            lines.append(f'  {node_id}{{"{text}"}}')
        elif node.node_type == "io":
            # Parallelogram untuk I/O
            lines.append(f'  {node_id}[/"{text}"/]')
        else:
            # Rectangle untuk process (default)
            lines.append(f'  {node_id}["{text}"]')

    # Tambahkan edge/koneksi antar node
    for edge in result.edges:
        src = edge.get("from", "")
        dst = edge.get("to", "")
        label = edge.get("label", "")
        if src and dst:
            if label:
                lines.append(f'  {src} -->|"{label}"| {dst}')
            else:
                lines.append(f"  {src} --> {dst}")

    mermaid_str = "\n".join(lines)
    logger.info(
        "[Flowchart] to_mermaid: %d node, %d edge → %d baris Mermaid.",
        len(result.nodes), len(result.edges), len(lines),
    )
    return mermaid_str
