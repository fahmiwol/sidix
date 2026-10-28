"""
Shared Pydantic Models — Projek Badar G2 Tasks 72-93
Model data yang digunakan bersama di seluruh paket image_gen.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ImageGenRequest(BaseModel):
    """Request payload untuk text-to-image generation."""

    prompt: str
    negative_prompt: str = ""
    style: str = "default"
    aspect_ratio: str = "1:1"
    seed: Optional[int] = None
    width: int = 512
    height: int = 512


class ImageGenResponse(BaseModel):
    """Response setelah submit image generation job."""

    job_id: str
    status: str
    image_path: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ImageJob(BaseModel):
    """Representasi internal sebuah image generation job."""

    job_id: str
    prompt: str
    status: str = "queued"  # queued | running | done | failed
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    result_path: Optional[str] = None
    user_id: str = "anonymous"


class PolicyViolation(BaseModel):
    """Hasil pemeriksaan policy/NSFW filter."""

    violated: bool
    reason: str = ""
    categories: list[str] = Field(default_factory=list)
