"""
Reproducible Seed — Projek Badar Task 85 (G2)
Seed reproducible untuk debug gambar.
"""
from __future__ import annotations

import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


def generate_seed() -> int:
    """Buat seed acak dalam rentang 0 – 2^32 - 1."""
    return random.randint(0, 2**32 - 1)


def set_seed(seed: int) -> None:
    """
    Set seed untuk reproduktibilitas.

    Mengatur random.seed(). Bila PyTorch tersedia, set juga torch.manual_seed().

    TODO: aktifkan torch.manual_seed() saat PyTorch tersedia.
    """
    random.seed(seed)
    logger.info("Seed diatur ke %d", seed)

    # TODO: torch.manual_seed(seed) — aktifkan bila PyTorch tersedia
    try:
        import torch  # noqa: F401
        torch.manual_seed(seed)
        logger.debug("torch.manual_seed(%d) berhasil.", seed)
    except ImportError:
        logger.debug(
            "PyTorch tidak tersedia — hanya random.seed() yang diatur. "
            "TODO: install torch untuk reproducibility penuh."
        )


class SeedRegistry:
    """
    Registry untuk menyimpan dan mengambil seed per job.

    Digunakan untuk reproduktibilitas — generate ulang gambar dengan seed + prompt sama.
    """

    def __init__(self) -> None:
        self.record: dict[str, int] = {}

    def register(self, job_id: str, seed: int) -> None:
        """Daftarkan seed untuk sebuah job."""
        self.record[job_id] = seed
        logger.debug("Seed %d didaftarkan untuk job %s", seed, job_id)

    def get(self, job_id: str) -> Optional[int]:
        """Ambil seed untuk job tertentu. None bila tidak ditemukan."""
        return self.record.get(job_id)

    def reproduce_prompt(self, job_id: str) -> dict:
        """
        Kembalikan informasi yang diperlukan untuk mereproduksi hasil gambar.

        Returns:
            dict berisi job_id, seed, dan instruksi reproduksi.
        """
        seed = self.get(job_id)
        return {
            "job_id": job_id,
            "seed": seed,
            "note": "Use same seed + prompt to reproduce",
        }


# Instance global untuk penggunaan di seluruh aplikasi
seed_registry = SeedRegistry()
