"""
Image Gen API — Projek Badar G2 (Tasks 72-93)
FastAPI router yang menggabungkan semua endpoint image generation.
Mount ke SIDIX inference server di /image/ prefix.

Cara mount ke server utama:
    from apps.image_gen.api import router as image_router
    app.include_router(image_router)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from .gallery import Gallery, GalleryItem, gallery
from .models import ImageGenRequest, ImageGenResponse, ImageJob
from .policy_filter import PolicyFilter
from .presets import list_presets
from .queue import ImageJobQueue
from .rate_limit import RateLimiter, rate_limiter
from .validation import validate_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image-gen"])

# ---------------------------------------------------------------------------
# Singleton instances (bisa diganti dengan dependency injection)
# ---------------------------------------------------------------------------
_job_queue = ImageJobQueue()
_policy_filter = PolicyFilter()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/health")
def health_check() -> dict:
    """
    Health check endpoint untuk image generation service.

    Returns:
        Status service, info model (stub), dan ukuran antrian.
    """
    return {
        "status": "ok",
        "model": "stub",  # TODO: return actual model name when loaded
        "queue_size": _job_queue._queue.qsize(),
        "note": "Model inferensi belum dimuat. Semua job dikembalikan sebagai stub.",
    }


@router.post("/generate", response_model=ImageGenResponse)
def submit_generate(
    request: ImageGenRequest,
    user_id: str = Query(default="anonymous", description="User ID pengirim job"),
) -> ImageGenResponse:
    """
    Submit job image generation baru.

    Pipeline:
    1. Validasi prompt (panjang + policy).
    2. Cek rate limit user.
    3. Tambahkan ke job queue.

    Returns:
        ImageGenResponse berisi job_id dan status awal.
    """
    # 1. Validasi prompt
    validation = validate_prompt(request.prompt)
    if not validation.valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Prompt tidak valid",
                "violations": validation.violations,
                "warnings": validation.warnings,
            },
        )

    # Gunakan prompt yang sudah disanitasi
    request = request.model_copy(update={"prompt": validation.sanitized_prompt})

    # 2. Cek policy
    policy = _policy_filter.check_prompt(request.prompt)
    if policy.violated:
        _policy_filter.log_redaction(request.prompt, policy, user_id)
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Prompt melanggar kebijakan konten",
                "reason": policy.reason,
                "categories": policy.categories,
            },
        )

    # 3. Rate limit
    allowed, reason = rate_limiter.can_submit(user_id)
    if not allowed:
        raise HTTPException(status_code=429, detail={"error": reason})

    # 4. Submit ke queue
    try:
        rate_limiter.acquire(user_id)
        job = _job_queue.submit(request, user_id=user_id)
    except Exception as exc:
        rate_limiter.release(user_id)
        logger.error("Gagal submit job: %s", exc)
        raise HTTPException(status_code=503, detail={"error": "Antrian penuh. Coba lagi nanti."})

    logger.info("Job %s diterima dari user=%s", job.job_id, user_id)
    return ImageGenResponse(
        job_id=job.job_id,
        status=job.status,
        image_path=job.result_path,
        metadata={
            "prompt_preview": request.prompt[:60],
            "style": request.style,
            "width": request.width,
            "height": request.height,
        },
    )


@router.get("/jobs/{job_id}", response_model=ImageJob)
def get_job_status(job_id: str) -> ImageJob:
    """
    Ambil status sebuah job berdasarkan job_id.

    Returns:
        ImageJob berisi status terkini.

    Raises:
        404 bila job tidak ditemukan.
    """
    job = _job_queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' tidak ditemukan.")
    return job


@router.get("/jobs", response_model=list[ImageJob])
def list_jobs(
    user_id: Optional[str] = Query(default=None, description="Filter berdasarkan user_id"),
) -> list[ImageJob]:
    """
    Daftar semua job. Opsional filter berdasarkan user_id.

    Returns:
        list ImageJob.
    """
    return _job_queue.list_jobs(user_id=user_id)


@router.get("/presets")
def get_presets() -> list[dict]:
    """
    Daftar semua preset gaya visual yang tersedia.

    Returns:
        list dict berisi name, description, aspect_ratio.
    """
    return list_presets()


@router.get("/gallery")
def list_gallery(
    user_id: Optional[str] = Query(default=None, description="Filter berdasarkan user_id"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """
    Daftar item galeri dengan pagination.

    Returns:
        list dict representasi GalleryItem.
    """
    items = gallery.list_items(user_id=user_id, limit=limit, offset=offset)
    # Konversi dataclass ke dict untuk response
    from dataclasses import asdict
    return [asdict(item) for item in items]


@router.delete("/gallery/{item_id}")
def delete_gallery_item(
    item_id: str,
    user_id: str = Query(default="anonymous", description="User ID pemilik item"),
) -> dict:
    """
    Hapus satu item galeri dan file gambarnya.

    Returns:
        dict berisi status.

    Raises:
        404 bila item tidak ditemukan atau bukan milik user.
    """
    success = gallery.delete(item_id, user_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Item '{item_id}' tidak ditemukan atau bukan milik user '{user_id}'.",
        )
    return {"status": "deleted", "item_id": item_id}
