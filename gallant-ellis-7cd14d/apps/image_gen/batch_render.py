"""
Batch Render — Projek Badar Task 76 (G2)
Batch render rendah prioritas (job malam).
MVP: simpan ke file JSON, jalankan via cron/scheduler.
"""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_BATCH_LOG_PATH = Path(".data/image_gen/batch_jobs.jsonl")


@dataclass
class BatchJob:
    """Representasi sebuah batch render job."""

    batch_id: str
    prompts: list[str]
    scheduled_at: str
    priority: int = 0
    status: str = "pending"  # pending | running | done | failed


class BatchRenderer:
    """
    Batch renderer untuk job gambar berprioritAS rendah.

    MVP: Menyimpan job ke JSONL. Untuk produksi: integrasikan
    dengan Celery beat atau scheduler cron.
    """

    def __init__(self) -> None:
        self._batches: dict[str, BatchJob] = {}
        self._load_from_disk()

    def submit_batch(
        self,
        prompts: list[str],
        scheduled_at: Optional[str] = None,
    ) -> BatchJob:
        """
        Buat dan antrekan sebuah batch job baru.

        Args:
            prompts: Daftar prompt yang akan dirender.
            scheduled_at: ISO timestamp jadwal eksekusi. Default: sekarang.
        """
        batch_id = str(uuid.uuid4())
        if scheduled_at is None:
            scheduled_at = datetime.utcnow().isoformat()

        job = BatchJob(
            batch_id=batch_id,
            prompts=prompts,
            scheduled_at=scheduled_at,
            priority=0,
            status="pending",
        )
        self._batches[batch_id] = job
        self._append_to_disk(job)
        logger.info(
            "Batch job %s dibuat dengan %d prompts, dijadwalkan: %s",
            batch_id,
            len(prompts),
            scheduled_at,
        )
        return job

    def list_batches(self) -> list[BatchJob]:
        """Kembalikan semua batch job."""
        return list(self._batches.values())

    def process_batch(self, batch_id: str) -> dict:
        """
        Proses sebuah batch job.

        STUB: Saat ini hanya menandai status sebagai done.
        TODO: Iterasi setiap prompt, panggil _generate_stub() atau
              antrekan ke ImageJobQueue dengan prioritas rendah.
        """
        job = self._batches.get(batch_id)
        if job is None:
            logger.warning("Batch job %s tidak ditemukan.", batch_id)
            return {"error": f"batch_id '{batch_id}' tidak ditemukan", "status": "failed"}

        job.status = "running"
        logger.info("STUB: memproses batch %s (%d prompts)", batch_id, len(job.prompts))

        # TODO: wire actual generation per prompt
        # for prompt in job.prompts:
        #     image_queue.submit(ImageGenRequest(prompt=prompt), user_id="batch")

        job.status = "done"
        self._append_to_disk(job)
        return {"processed": len(job.prompts), "status": "done", "batch_id": batch_id}

    def _append_to_disk(self, job: BatchJob) -> None:
        """Append job ke file JSONL persisten."""
        _BATCH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _BATCH_LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(job), ensure_ascii=False) + "\n")

    def _load_from_disk(self) -> None:
        """Muat batch job dari file JSONL saat init."""
        if not _BATCH_LOG_PATH.exists():
            return
        with _BATCH_LOG_PATH.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    job = BatchJob(**data)
                    # Hanya muat yang belum selesai agar tidak duplikat
                    self._batches[job.batch_id] = job
                except Exception as exc:
                    logger.warning("Gagal memuat baris batch_jobs.jsonl: %s", exc)
