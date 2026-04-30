"""
Image Job Queue — Projek Badar Task 72 (G2)
Pipeline text-to-image: antrian job + batas ukuran.
Menggunakan Python queue.Queue (in-memory, MVP).
Produksi: ganti dengan Redis/Celery.
"""
from __future__ import annotations

import logging
import queue
import uuid
from datetime import datetime
from typing import Optional

from .models import ImageGenRequest, ImageJob

logger = logging.getLogger(__name__)

MAX_JOB_QUEUE_SIZE: int = 100
MAX_CONCURRENT_PER_USER: int = 3


class ImageJobQueue:
    """
    Antrian job image generation in-memory.

    MVP menggunakan queue.Queue standar Python.
    Untuk produksi: ganti dengan Redis + Celery worker.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue(maxsize=MAX_JOB_QUEUE_SIZE)
        self._jobs: dict[str, ImageJob] = {}

    def submit(self, request: ImageGenRequest, user_id: str = "anonymous") -> ImageJob:
        """
        Tambahkan job baru ke antrian. Kembalikan ImageJob yang dibuat.

        Raises:
            queue.Full: bila antrian penuh (>MAX_JOB_QUEUE_SIZE).
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        job = ImageJob(
            job_id=job_id,
            prompt=request.prompt,
            status="queued",
            created_at=now,
            updated_at=now,
            result_path=None,
            user_id=user_id,
        )
        self._jobs[job_id] = job
        # Akan raise queue.Full bila antrian penuh
        self._queue.put_nowait(job_id)
        logger.info("Job %s submitted by user=%s", job_id, user_id)
        return job

    def get_job(self, job_id: str) -> Optional[ImageJob]:
        """Ambil job berdasarkan job_id. Kembalikan None bila tidak ditemukan."""
        return self._jobs.get(job_id)

    def list_jobs(self, user_id: Optional[str] = None) -> list[ImageJob]:
        """Daftar semua job, opsional filter per user_id."""
        jobs = list(self._jobs.values())
        if user_id is not None:
            jobs = [j for j in jobs if j.user_id == user_id]
        return jobs

    def process_next(self) -> Optional[ImageJob]:
        """
        Dequeue satu job dan jalankan _generate_stub().
        Kembalikan job yang diproses, atau None bila antrian kosong.
        """
        try:
            job_id = self._queue.get_nowait()
        except queue.Empty:
            return None

        job = self._jobs.get(job_id)
        if job is None:
            logger.warning("Job %s tidak ditemukan di _jobs store", job_id)
            return None

        job.status = "running"
        job.updated_at = datetime.utcnow().isoformat()
        logger.info("Processing job %s", job_id)

        try:
            result_path = self._generate_stub(job)
            job.status = "done"
            job.result_path = result_path
        except Exception as exc:
            logger.error("Job %s gagal: %s", job_id, exc)
            job.status = "failed"

        job.updated_at = datetime.utcnow().isoformat()
        return job

    def _generate_stub(self, job: ImageJob) -> str:
        """
        Placeholder untuk inferensi model text-to-image.

        TODO: wire actual model (FLUX / Stable Diffusion lokal)
              Contoh implementasi:
                pipe = StableDiffusionPipeline.from_pretrained("model_path")
                image = pipe(job.prompt).images[0]
                out = f".data/image_gen/{job.job_id}.png"
                image.save(out)
                return out
        """
        placeholder_path = f".data/image_gen/stub_{job.job_id}.png"
        logger.info(
            "STUB: image generation tidak diimplementasikan. "
            "Placeholder path: %s",
            placeholder_path,
        )
        return placeholder_path
