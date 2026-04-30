"""
Rate Limit — Projek Badar Task 87 (G2)
Limit concurrent image job per user.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter untuk image generation job per user.

    Melacak:
    - Jumlah job aktif (concurrent) per user.
    - Jumlah job harian per user.

    Untuk produksi: ganti dengan Redis-backed counter agar state
    tidak hilang saat restart dan bisa dishare antar proses.
    """

    MAX_CONCURRENT_PER_USER: int = 3
    MAX_DAILY_PER_USER: int = 50

    def __init__(self) -> None:
        self._active_jobs: dict[str, int] = {}    # user_id -> concurrent count
        self._daily_counts: dict[str, int] = {}   # user_id -> daily count

    def can_submit(self, user_id: str) -> tuple[bool, str]:
        """
        Periksa apakah user diizinkan mengirim job baru.

        Returns:
            (True, "") bila diizinkan.
            (False, alasan) bila ditolak.
        """
        concurrent = self._active_jobs.get(user_id, 0)
        daily = self._daily_counts.get(user_id, 0)

        if concurrent >= self.MAX_CONCURRENT_PER_USER:
            reason = (
                f"Batas concurrent tercapai: {concurrent}/{self.MAX_CONCURRENT_PER_USER} "
                f"job aktif untuk user '{user_id}'."
            )
            logger.info(reason)
            return False, reason

        if daily >= self.MAX_DAILY_PER_USER:
            reason = (
                f"Batas harian tercapai: {daily}/{self.MAX_DAILY_PER_USER} "
                f"job hari ini untuk user '{user_id}'."
            )
            logger.info(reason)
            return False, reason

        return True, ""

    def acquire(self, user_id: str) -> bool:
        """
        Increment counter job aktif user.

        Returns:
            True bila berhasil (user masih dalam batas).
            False bila sudah melebihi batas.
        """
        allowed, reason = self.can_submit(user_id)
        if not allowed:
            return False

        self._active_jobs[user_id] = self._active_jobs.get(user_id, 0) + 1
        self._daily_counts[user_id] = self._daily_counts.get(user_id, 0) + 1
        logger.debug(
            "Job acquired untuk user '%s'. Active: %d, Daily: %d",
            user_id,
            self._active_jobs[user_id],
            self._daily_counts[user_id],
        )
        return True

    def release(self, user_id: str) -> None:
        """Decrement counter job aktif user setelah job selesai/gagal."""
        current = self._active_jobs.get(user_id, 0)
        if current > 0:
            self._active_jobs[user_id] = current - 1
        logger.debug(
            "Job released untuk user '%s'. Active sekarang: %d",
            user_id,
            self._active_jobs.get(user_id, 0),
        )

    def get_stats(self, user_id: str) -> dict:
        """
        Kembalikan statistik rate limit untuk user.

        Returns:
            dict berisi active_jobs, daily_count, dan batas maksimum.
        """
        return {
            "user_id": user_id,
            "active_jobs": self._active_jobs.get(user_id, 0),
            "daily_count": self._daily_counts.get(user_id, 0),
            "max_concurrent": self.MAX_CONCURRENT_PER_USER,
            "max_daily": self.MAX_DAILY_PER_USER,
        }


# Instance global
rate_limiter = RateLimiter()
