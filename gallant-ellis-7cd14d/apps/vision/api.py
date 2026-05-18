"""
Vision API — Projek Badar G3 (Tasks 94-104)
FastAPI router untuk semua endpoint image understanding.
Mount ke SIDIX inference server di /vision/ prefix.

Contoh mount di main.py:
    from apps.vision.api import router as vision_router
    app.include_router(vision_router)
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from .analysis_display import AnalysisReport, format_side_by_side, generate_html_report, to_markdown
from .caption import extract_text_ocr, generate_caption
from .chart_reader import read_chart, data_points_to_csv, data_points_to_markdown_table
from .classifier import classify_image
from .confidence import aggregate_confidence, format_report
from .detection import detect_faces, detect_objects
from .flowchart_ocr import detect_flowchart_text, to_mermaid
from .icon_detect import detect_icons, check_branding_compliance
from .image_compare import compare_images, diff_summary
from .image_quality import score_image_quality, format_quality_report
from .low_light import analyze_brightness
from .pdf_caption import caption_pdf, format_pdf_caption_report
from .pose_estimation import estimate_pose
from .preprocess import normalize_format, resize_image, validate_image
from .screenshot_detect import detect_screenshot, format_screenshot_info
from .similarity import compute_similarity, rank_by_similarity
from .sketch_to_svg import sketch_to_svg
from .slide_reader import read_slide, format_as_markdown as slide_to_markdown
from .street_sign_ocr import read_street_sign
from .table_extract import extract_table, table_to_csv, table_to_markdown

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["Vision — G3"])

# Daftar kapabilitas yang tersedia (untuk health check)
CAPABILITIES = [
    # G3 Tasks 94-104
    "caption", "ocr", "classify", "preprocess",
    "similarity", "detect-objects", "detect-faces",
    "table-extract", "flowchart-ocr", "analyze", "low-light",
    # G3 Tasks 105-114 (Batch Sisa)
    "icon-detect", "pdf-caption", "pose-estimation",
    "image-compare", "sketch-to-svg", "chart-reader",
    "image-quality", "slide-reader", "street-sign-ocr", "screenshot-detect",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _parse_body(body: dict[str, Any]) -> tuple[str, dict]:
    """Ekstrak image_path dan options dari request body."""
    image_path = body.get("image_path", "")
    options = body.get("options", {})
    return image_path, options


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint untuk pipeline vision.

    Returns:
        Status, keterangan model, dan daftar kapabilitas.
    """
    return {
        "status": "ok",
        "models": "stub",
        "note": "Semua model vision dalam status STUB. Wire ke model lokal untuk aktivasi.",
        "capabilities": CAPABILITIES,
    }


# ---------------------------------------------------------------------------
# Task 94: Caption + OCR
# ---------------------------------------------------------------------------

@router.post("/caption")
async def endpoint_caption(body: dict[str, Any]) -> dict:
    """
    Generate caption dan ekstraksi teks OCR dari gambar.

    Body: {"image_path": str, "options": {"include_ocr": bool}}
    """
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        caption_result = generate_caption(image_path)
        response: dict = {
            "task": "caption",
            "image_path": image_path,
            "caption": caption_result.caption,
            "confidence": caption_result.confidence,
            "language": caption_result.language,
            "model": caption_result.model,
        }

        if options.get("include_ocr", False):
            ocr_result = extract_text_ocr(image_path)
            response["ocr"] = {
                "text": ocr_result.text,
                "confidence": ocr_result.confidence,
                "blocks_count": len(ocr_result.blocks),
            }

        return response

    except Exception as exc:
        logger.error("[API /caption] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 95: Classify
# ---------------------------------------------------------------------------

@router.post("/classify")
async def endpoint_classify(body: dict[str, Any]) -> dict:
    """
    Klasifikasi jenis gambar (foto/diagram/sketsa/dll).

    Body: {"image_path": str, "options": {}}
    """
    try:
        image_path, _ = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        result = classify_image(image_path)
        return {
            "task": "classify",
            "image_path": image_path,
            "image_type": result.image_type.value,
            "confidence": result.confidence,
            "route_to": result.route_to,
            "reasoning": result.reasoning,
        }

    except Exception as exc:
        logger.error("[API /classify] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 96: Preprocess
# ---------------------------------------------------------------------------

@router.post("/preprocess")
async def endpoint_preprocess(body: dict[str, Any]) -> dict:
    """
    Resize dan normalisasi format gambar.

    Body: {
        "image_path": str,
        "options": {
            "max_pixels": int,      # default 4_000_000
            "target_format": str,   # default "PNG"
            "output_path": str      # opsional
        }
    }
    """
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        # Validasi terlebih dahulu
        valid, msg = validate_image(image_path)
        if not valid:
            return {"error": f"Validasi gambar gagal: {msg}"}

        max_pixels = options.get("max_pixels", 4_000_000)
        output_path = options.get("output_path", None)

        resize_result = resize_image(image_path, max_pixels=max_pixels, output_path=output_path)

        target_format = options.get("target_format", None)
        format_result = None
        if target_format:
            format_result = normalize_format(
                resize_result.output_path,
                target_format=target_format,
                output_path=output_path,
            )

        return {
            "task": "preprocess",
            "image_path": image_path,
            "resize": {
                "success": resize_result.success,
                "original_size": list(resize_result.original_size),
                "output_size": list(resize_result.output_size),
                "output_path": resize_result.output_path,
                "error": resize_result.error,
            },
            "format_conversion": {
                "success": format_result.success if format_result else None,
                "format": format_result.format if format_result else "tidak dilakukan",
                "output_path": format_result.output_path if format_result else None,
                "error": format_result.error if format_result else None,
            },
        }

    except Exception as exc:
        logger.error("[API /preprocess] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 97: Similarity
# ---------------------------------------------------------------------------

@router.post("/similarity")
async def endpoint_similarity(body: dict[str, Any]) -> dict:
    """
    Hitung similarity antara gambar dan teks query.

    Body: {
        "image_path": str,
        "options": {
            "query_text": str,
            "rank_images": list[str]   # opsional: daftar gambar untuk di-rank
        }
    }
    """
    try:
        image_path, options = _parse_body(body)
        query_text = options.get("query_text", "")
        rank_images = options.get("rank_images", [])

        if not image_path and not rank_images:
            return {"error": "image_path atau rank_images diperlukan."}

        if rank_images:
            results = rank_by_similarity(rank_images, query_text)
            return {
                "task": "similarity-rank",
                "query_text": query_text,
                "ranked": [
                    {"image_path": r.image_path, "score": r.score, "model": r.model}
                    for r in results
                ],
            }

        result = compute_similarity(image_path, query_text)
        return {
            "task": "similarity",
            "image_path": image_path,
            "query_text": query_text,
            "score": result.score,
            "model": result.model,
        }

    except Exception as exc:
        logger.error("[API /similarity] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 99: Detect
# ---------------------------------------------------------------------------

@router.post("/detect")
async def endpoint_detect(body: dict[str, Any]) -> dict:
    """
    Deteksi objek dan/atau wajah pada gambar.

    Body: {
        "image_path": str,
        "options": {
            "detect_objects": bool,   # default True
            "detect_faces": bool      # default False (privasi)
        }
    }
    """
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        do_objects = options.get("detect_objects", True)
        do_faces = options.get("detect_faces", False)

        obj_result = detect_objects(image_path, enabled=do_objects)
        face_result = detect_faces(image_path, enabled=do_faces)

        return {
            "task": "detect",
            "image_path": image_path,
            "objects": {
                "enabled": do_objects,
                "count": obj_result.count,
                "model": obj_result.model,
                "detections": [
                    {"label": b.label, "x": b.x, "y": b.y,
                     "width": b.width, "height": b.height,
                     "confidence": b.confidence}
                    for b in obj_result.objects
                ],
            },
            "faces": {
                "enabled": do_faces,
                "count": face_result.count,
                "model": face_result.model,
                "privacy_note": (
                    "Face detection dinonaktifkan secara default. "
                    "Aktifkan hanya dengan persetujuan eksplisit."
                    if not do_faces else "Aktif — pastikan kepatuhan privasi."
                ),
            },
        }

    except Exception as exc:
        logger.error("[API /detect] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 100: Table
# ---------------------------------------------------------------------------

@router.post("/table")
async def endpoint_table(body: dict[str, Any]) -> dict:
    """
    Ekstraksi tabel dari gambar.

    Body: {
        "image_path": str,
        "options": {"output_format": "json"|"csv"|"markdown"}
    }
    """
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        result = extract_table(image_path)
        output_format = options.get("output_format", "json")

        response: dict = {
            "task": "table-extract",
            "image_path": image_path,
            "success": result.success,
            "rows": result.rows,
            "cols": result.cols,
            "model": result.model,
        }

        if output_format == "csv":
            response["csv"] = table_to_csv(result)
        elif output_format == "markdown":
            response["markdown"] = table_to_markdown(result)
        else:
            response["cells"] = [
                {"row": c.row, "col": c.col, "text": c.text, "confidence": c.confidence}
                for c in result.cells
            ]

        return response

    except Exception as exc:
        logger.error("[API /table] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 102: Flowchart
# ---------------------------------------------------------------------------

@router.post("/flowchart")
async def endpoint_flowchart(body: dict[str, Any]) -> dict:
    """
    Deteksi teks dan struktur flowchart dari gambar.

    Body: {"image_path": str, "options": {}}
    """
    try:
        image_path, _ = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        result = detect_flowchart_text(image_path)
        mermaid = to_mermaid(result)

        return {
            "task": "flowchart-ocr",
            "image_path": image_path,
            "nodes_count": len(result.nodes),
            "edges_count": len(result.edges),
            "confidence": result.confidence,
            "mermaid": mermaid,
            "nodes": [
                {"id": n.node_id, "text": n.text,
                 "type": n.node_type, "bbox": n.bbox}
                for n in result.nodes
            ],
            "edges": result.edges,
        }

    except Exception as exc:
        logger.error("[API /flowchart] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Full Analysis: Tasks 94+95+101
# ---------------------------------------------------------------------------

@router.post("/analyze")
async def endpoint_analyze(body: dict[str, Any]) -> dict:
    """
    Analisis lengkap: caption + klasifikasi + OCR + confidence report.

    Body: {
        "image_path": str,
        "options": {
            "include_ocr": bool,       # default True
            "output_html": str,        # opsional: path file HTML
            "output_format": "json"|"markdown"
        }
    }
    """
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}

        # Jalankan semua komponen
        caption_result = generate_caption(image_path)
        class_result = classify_image(image_path)

        ocr_result = None
        if options.get("include_ocr", True):
            ocr_result = extract_text_ocr(image_path)

        # Hitung confidence report
        conf_report = aggregate_confidence(
            caption_conf=caption_result.confidence,
            ocr_conf=ocr_result.confidence if ocr_result else 0.0,
            class_conf=class_result.confidence,
        )

        # Low light check
        light_analysis = analyze_brightness(image_path)

        # Buat AnalysisReport
        report = AnalysisReport(
            image_path=image_path,
            caption=caption_result.caption,
            ocr_text=ocr_result.text if ocr_result else "",
            classification=class_result.image_type.value,
            objects=[],
            confidence=conf_report.overall,
        )

        response: dict = {
            "task": "analyze",
            "image_path": image_path,
            "caption": caption_result.caption,
            "classification": class_result.image_type.value,
            "route_to": class_result.route_to,
            "ocr_text": ocr_result.text if ocr_result else None,
            "confidence_report": {
                "overall": conf_report.overall,
                "grade": conf_report.grade,
                "caption": conf_report.caption_confidence,
                "ocr": conf_report.ocr_confidence,
                "classification": conf_report.classification_confidence,
                "recommendation": conf_report.recommendation,
            },
            "lighting": {
                "is_low_light": light_analysis.is_low_light,
                "average_brightness": light_analysis.average_brightness,
                "grade": light_analysis.brightness_grade,
                "suggestions": light_analysis.suggestions,
            },
            "confidence_report_text": format_report(conf_report),
        }

        # Generate HTML jika diminta
        if options.get("output_html"):
            html_path = generate_html_report(report, options["output_html"])
            response["html_report"] = html_path

        # Tambahkan Markdown jika diminta
        if options.get("output_format") == "markdown":
            response["markdown"] = to_markdown(report)

        return response

    except Exception as exc:
        logger.error("[API /analyze] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 105: Icon/Logo Detection
# ---------------------------------------------------------------------------

@router.post("/icon-detect")
async def endpoint_icon_detect(body: dict[str, Any]) -> dict:
    """Deteksi icon/logo untuk branding check. Body: {"image_path": str, "options": {}}"""
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        result = detect_icons(image_path, min_confidence=options.get("min_confidence", 0.5))
        compliance = check_branding_compliance(
            result,
            required_brands=options.get("required_brands"),
            forbidden_brands=options.get("forbidden_brands"),
        )
        return {
            "task": "icon-detect", "image_path": image_path,
            "icon_count": result.icon_count, "model": result.model,
            "logos": [{"label": l.label, "confidence": l.confidence} for l in result.logos],
            "compliance": compliance,
            "error": result.error,
        }
    except Exception as exc:
        logger.error("[API /icon-detect] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 106: PDF Caption Pipeline
# ---------------------------------------------------------------------------

@router.post("/pdf-caption")
async def endpoint_pdf_caption(body: dict[str, Any]) -> dict:
    """PDF halaman → gambar → caption. Body: {"image_path": str (path ke PDF), "options": {}}"""
    try:
        pdf_path, options = _parse_body(body)
        if not pdf_path:
            return {"error": "image_path (path ke file PDF) diperlukan."}
        max_pages = options.get("max_pages", 20)
        result = caption_pdf(pdf_path, max_pages=max_pages)
        return {
            "task": "pdf-caption", "pdf_path": result.pdf_path,
            "total_pages": result.total_pages, "processed_pages": result.processed_pages,
            "pages": [
                {"page": p.page_number, "caption": p.caption[:200],
                 "ocr_text": p.ocr_text[:200], "error": p.error}
                for p in result.pages
            ],
            "model": result.model, "error": result.error,
        }
    except Exception as exc:
        logger.error("[API /pdf-caption] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 107: Pose Estimation (opsional, OFF by default)
# ---------------------------------------------------------------------------

@router.post("/pose")
async def endpoint_pose(body: dict[str, Any]) -> dict:
    """Pose estimation. Body: {"image_path": str, "options": {"enabled": bool}}"""
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        enabled = options.get("enabled", False)
        result = estimate_pose(image_path, enabled=enabled)
        return {
            "task": "pose-estimation", "image_path": image_path,
            "enabled": result.enabled, "person_count": result.person_count,
            "model": result.model, "error": result.error,
        }
    except Exception as exc:
        logger.error("[API /pose] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 108: Image Compare (before/after)
# ---------------------------------------------------------------------------

@router.post("/compare")
async def endpoint_compare(body: dict[str, Any]) -> dict:
    """Bandingkan dua gambar. Body: {"image_path": str, "options": {"image_b": str}}"""
    try:
        image_a, options = _parse_body(body)
        image_b = options.get("image_b", "")
        if not image_a or not image_b:
            return {"error": "image_path (gambar A) dan options.image_b (gambar B) diperlukan."}
        result = compare_images(image_a, image_b)
        return {
            "task": "image-compare", "image_a": image_a, "image_b": image_b,
            "identical": result.identical,
            "pixel_diff_ratio": result.pixel_diff_ratio,
            "ssim_score": result.ssim_score,
            "histogram_similarity": result.histogram_similarity,
            "size_match": result.size_match,
            "summary": diff_summary(result),
            "notes": result.notes, "error": result.error,
        }
    except Exception as exc:
        logger.error("[API /compare] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 109: Sketch to SVG
# ---------------------------------------------------------------------------

@router.post("/sketch-to-svg")
async def endpoint_sketch_to_svg(body: dict[str, Any]) -> dict:
    """Konversi sketsa ke SVG. Body: {"image_path": str, "options": {"output_path": str}}"""
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        output_path = options.get("output_path", None)
        result = sketch_to_svg(image_path, output_path=output_path)
        return {
            "task": "sketch-to-svg", "image_path": image_path,
            "success": result.success, "method": result.method,
            "svg_path": result.svg_path, "notes": result.notes, "error": result.error,
        }
    except Exception as exc:
        logger.error("[API /sketch-to-svg] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 110: Chart Reader
# ---------------------------------------------------------------------------

@router.post("/chart")
async def endpoint_chart(body: dict[str, Any]) -> dict:
    """Baca data dari chart image. Body: {"image_path": str, "options": {"output_format": str}}"""
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        result = read_chart(image_path)
        output_format = options.get("output_format", "json")
        response: dict = {
            "task": "chart-reader", "image_path": image_path,
            "chart_type": result.chart_type.value,
            "title": result.title, "x_label": result.x_label, "y_label": result.y_label,
            "data_point_count": len(result.data_points),
            "model": result.model, "confidence": result.confidence, "error": result.error,
        }
        if output_format == "csv":
            response["csv"] = data_points_to_csv(result)
        elif output_format == "markdown":
            response["markdown"] = data_points_to_markdown_table(result)
        else:
            response["data_points"] = [
                {"label": dp.label, "value": dp.value} for dp in result.data_points
            ]
        return response
    except Exception as exc:
        logger.error("[API /chart] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 111: Image Quality Score
# ---------------------------------------------------------------------------

@router.post("/quality")
async def endpoint_quality(body: dict[str, Any]) -> dict:
    """Skor kualitas gambar. Body: {"image_path": str, "options": {}}"""
    try:
        image_path, _ = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        report = score_image_quality(image_path)
        return {
            "task": "image-quality", "image_path": image_path,
            "grade": report.grade.value,
            "overall_score": report.overall_score,
            "sharpness_score": report.sharpness_score,
            "noise_score": report.noise_score,
            "exposure_score": report.exposure_score,
            "contrast_score": report.contrast_score,
            "is_processable": report.is_processable,
            "recommendations": report.recommendations,
            "report_text": format_quality_report(report),
            "error": report.error,
        }
    except Exception as exc:
        logger.error("[API /quality] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 112: Slide Reader
# ---------------------------------------------------------------------------

@router.post("/slide")
async def endpoint_slide(body: dict[str, Any]) -> dict:
    """Baca slide → bullet points. Body: {"image_path": str, "options": {"output_format": str}}"""
    try:
        image_path, options = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        result = read_slide(image_path)
        output_format = options.get("output_format", "json")
        response: dict = {
            "task": "slide-reader", "image_path": image_path,
            "slide_title": result.slide_title,
            "bullet_count": len(result.bullet_points),
            "model": result.model, "confidence": result.confidence, "error": result.error,
        }
        if output_format == "markdown":
            response["markdown"] = slide_to_markdown(result)
        else:
            response["bullet_points"] = [
                {"level": bp.level, "text": bp.text, "is_heading": bp.is_heading}
                for bp in result.bullet_points
            ]
        return response
    except Exception as exc:
        logger.error("[API /slide] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 113: Street Sign OCR
# ---------------------------------------------------------------------------

@router.post("/street-sign")
async def endpoint_street_sign(body: dict[str, Any]) -> dict:
    """Baca papan nama jalan. Body: {"image_path": str, "options": {}}"""
    try:
        image_path, _ = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        result = read_street_sign(image_path)
        return {
            "task": "street-sign-ocr", "image_path": image_path,
            "primary_street_name": result.primary_street_name,
            "combined_text": result.combined_text,
            "signs": [
                {"text": s.text, "confidence": s.confidence,
                 "sign_type": s.sign_type, "language": s.language}
                for s in result.signs
            ],
            "model": result.model, "error": result.error,
        }
    except Exception as exc:
        logger.error("[API /street-sign] Error: %s", exc)
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Task 114: Screenshot Detection
# ---------------------------------------------------------------------------

@router.post("/screenshot")
async def endpoint_screenshot(body: dict[str, Any]) -> dict:
    """Deteksi screenshot UI app. Body: {"image_path": str, "options": {}}"""
    try:
        image_path, _ = _parse_body(body)
        if not image_path:
            return {"error": "image_path diperlukan."}
        info = detect_screenshot(image_path)
        return {
            "task": "screenshot-detect", "image_path": image_path,
            "is_screenshot": info.is_screenshot,
            "platform": info.platform.value,
            "visible_url": info.visible_url,
            "page_title": info.page_title,
            "model": info.model, "confidence": info.confidence,
            "summary": format_screenshot_info(info),
            "error": info.error,
        }
    except Exception as exc:
        logger.error("[API /screenshot] Error: %s", exc)
        return {"error": str(exc)}
