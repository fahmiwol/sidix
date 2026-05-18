"""
Shared Pydantic Models — Projek Badar G3 Vision Package
Model data bersama untuk seluruh modul vision.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class VisionRequest(BaseModel):
    """Request masukan untuk semua endpoint vision."""
    image_path: str
    task: str = "caption"  # caption|ocr|classify|detect|similarity|crop|table|flowchart|lowlight
    options: dict = Field(default_factory=dict)


class VisionResult(BaseModel):
    """Hasil umum dari pipeline vision."""
    task: str
    result: dict
    confidence: float = 0.0
    model: str = "stub"
    error: str | None = None


class BoundingBox(BaseModel):
    """Kotak pembatas (bounding box) untuk deteksi objek/region crop."""
    x: int
    y: int
    width: int
    height: int
    label: str = ""
    confidence: float = 0.0


class ImageClassification(BaseModel):
    """Hasil klasifikasi gambar."""
    label: str
    confidence: float
    categories: list[str] = Field(default_factory=list)


class DetectionResult(BaseModel):
    """Hasil deteksi objek."""
    objects: list[BoundingBox]
    count: int
    model: str = "stub"
