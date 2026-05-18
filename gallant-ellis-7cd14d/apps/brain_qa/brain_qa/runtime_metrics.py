"""
Ring counter tambahan di luar _METRICS FastAPI (hindari import siklik berat).
Dipakai untuk Maqashid gate, LearnAgent, dll.
"""

from __future__ import annotations

import threading

_lock = threading.Lock()
_extra: dict[str, int] = {}


def bump(key: str, delta: int = 1) -> None:
    with _lock:
        _extra[key] = _extra.get(key, 0) + delta


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_extra)
