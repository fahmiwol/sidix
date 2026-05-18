"""
taskgraph.py — Raudah v0.2 lightweight execution DAG

Mengelompokkan RaudahTask ke dalam gelombang (topological levels) berdasarkan
peran specialist, sehingga peneliti selesai sebelum analis/penulis yang
mengandalkan konteks riset.

Tidak memerlukan LLM: deterministik, ramah VPS, mudah diuji.
"""

from __future__ import annotations

# Gelombang lebih rendah = lebih dulu dieksekusi (asyncio.gather per gelombang).
ROLE_WAVE: dict[str, int] = {
    "peneliti": 0,
    "analis": 1,
    "perekayasa": 1,
    "penulis": 2,
    "verifikator": 3,
}


def build_execution_waves(tasks: list[RaudahTask]) -> list[list[RaudahTask]]:
    """
    Partisi task ke dalam list-of-list: setiap inner list boleh paralel,
    outer list dieksekusi berurutan.
    """
    if not tasks:
        return []
    buckets: dict[int, list[RaudahTask]] = {}
    for t in tasks:
        wave = ROLE_WAVE.get(t.role, 99)
        buckets.setdefault(wave, []).append(t)
    order = sorted(buckets.keys())
    return [buckets[w] for w in order]


def dag_summary(waves: list[list[RaudahTask]]) -> dict:
    """Ringkasan untuk /metrics atau logging."""
    return {
        "wave_count": len(waves),
        "tasks_per_wave": [len(w) for w in waves],
        "roles_per_wave": [[t.role for t in w] for w in waves],
    }
