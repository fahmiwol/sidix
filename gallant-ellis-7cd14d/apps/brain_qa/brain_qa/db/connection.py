"""
DB Connection Pool — SIDIX Sprint 8c
Async PostgreSQL via asyncpg. Lazy-init, graceful fallback jika asyncpg tidak terinstall.

Env vars:
  SIDIX_DB_URL — postgresql://user:pass@host:port/dbname
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_pool: Any = None


async def get_pool():
    """Return pool asyncpg (lazy-init). None jika asyncpg tidak tersedia atau DB_URL kosong."""
    global _pool
    if _pool is not None:
        return _pool

    db_url = os.getenv("SIDIX_DB_URL", "").strip()
    if not db_url:
        logger.debug("SIDIX_DB_URL tidak di-set — DB pool tidak diinisialisasi")
        return None

    try:
        import asyncpg
        _pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10, command_timeout=30)
        logger.info("PostgreSQL pool ready — %s", db_url.split("@")[-1])  # sembunyikan credentials
        return _pool
    except ImportError:
        logger.warning("asyncpg tidak terinstall — jalankan: pip install asyncpg")
        return None
    except Exception as exc:
        logger.warning("DB pool gagal diinisialisasi: %s", exc)
        return None


async def close_pool() -> None:
    """Tutup pool (panggil saat shutdown)."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")


async def execute(query: str, *args) -> str | None:
    """Jalankan query tanpa return rows. Return None jika pool tidak tersedia."""
    pool = await get_pool()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)


async def fetch(query: str, *args) -> list[dict]:
    """Fetch rows sebagai list[dict]. Return [] jika pool tidak tersedia."""
    pool = await get_pool()
    if pool is None:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]


async def fetchrow(query: str, *args) -> dict | None:
    """Fetch satu row sebagai dict. Return None jika tidak ada atau pool tidak tersedia."""
    pool = await get_pool()
    if pool is None:
        return None
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None
