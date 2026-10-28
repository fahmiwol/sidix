"""
Rate limit ringan (in-memory) untuk POST inference.
Cukup untuk fairness single-node; ganti Redis jika multi-instance.

Kuota harian: cek sebelum inferensi, catat penggunaan setelah inferensi sukses
(lihat `agent_serve` — hindari mengonsumsi kuota jika `run_react` gagal).
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

# RPM per IP untuk POST /ask, /ask/stream, /agent/chat, /agent/generate
_RPM = int(os.environ.get("BRAIN_QA_RATE_LIMIT_RPM", "120"))
_window: dict[str, deque[float]] = defaultdict(deque)

# Kuota harian per kunci (X-Client-Id atau IP). 0 = nonaktif.
_ANON_DAILY_CAP = int(os.environ.get("BRAIN_QA_ANON_DAILY_CAP", "500"))
_daily: dict[str, tuple[str, int]] = {}  # key -> (utc_date, count)


def _prune_window(ip: str, now: float) -> None:
    q = _window[ip]
    while q and now - q[0] > 60.0:
        q.popleft()


def check_rate_limit(client_ip: str) -> tuple[bool, str]:
    """Return (allowed, message)."""
    now = time.monotonic()
    ip = client_ip or "unknown"
    _prune_window(ip, now)
    q = _window[ip]
    if len(q) >= _RPM:
        return False, f"Rate limit: maks {_RPM} permintaan per menit per klien."
    q.append(now)
    return True, ""


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def daily_quota_enabled() -> bool:
    return _ANON_DAILY_CAP > 0


def daily_quota_cap() -> int | None:
    """Nilai untuk /health (None jika kuota nonaktif)."""
    return _ANON_DAILY_CAP if daily_quota_enabled() else None


def check_daily_quota_headroom(client_key: str) -> tuple[bool, str]:
    """True jika masih boleh memulai satu inferensi lagi (belum menyentuh cap)."""
    if not daily_quota_enabled():
        return True, ""
    day = _utc_day()
    k = client_key or "anon"
    d, c = _daily.get(k, (day, 0))
    if d != day:
        return True, ""
    if c >= _ANON_DAILY_CAP:
        return False, f"Kuota harian tercapai ({_ANON_DAILY_CAP} inferensi/hari per klien). Coba besok atau hubungi admin."
    return True, ""


def record_daily_use(client_key: str) -> None:
    """Panggil setelah satu inferensi selesai tanpa error server."""
    if not daily_quota_enabled():
        return
    day = _utc_day()
    k = client_key or "anon"
    d, c = _daily.get(k, (day, 0))
    if d != day:
        _daily[k] = (day, 1)
    else:
        _daily[k] = (d, c + 1)
