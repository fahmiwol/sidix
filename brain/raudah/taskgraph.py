"""
taskgraph.py — Raudah v0.2 lightweight execution DAG

Mengelompokkan RaudahTask ke dalam gelombang (topological levels) berdasarkan:
  1. Dependency graph (explicit depends_on edges)
  2. Role-based fallback (implicit ordering)

Tidak memerlukan LLM: deterministik, ramah VPS, mudah diuji.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import RaudahTask


# Gelombang lebih rendah = lebih dulu dieksekusi (asyncio.gather per gelombang).
ROLE_WAVE: dict[str, int] = {
    "peneliti": 0,
    "analis": 1,
    "perekayasa": 1,
    "penulis": 2,
    "verifikator": 3,
}


def _build_dependency_graph(tasks: list[RaudahTask]) -> dict[str, set[str]]:
    """Build adjacency list dari depends_on relationships."""
    graph: dict[str, set[str]] = {t.task_id: set() for t in tasks}
    task_map = {t.task_id: t for t in tasks}
    for t in tasks:
        for dep_id in (t.depends_on or []):
            if dep_id in task_map:
                graph[t.task_id].add(dep_id)
    return graph


def _topological_levels(graph: dict[str, set[str]]) -> list[list[str]]:
    """Topological sort yang mengelompokkan node per level (parallelizable)."""
    in_degree = {node: 0 for node in graph}
    for node, deps in graph.items():
        for dep in deps:
            in_degree[node] = in_degree.get(node, 0) + 1

    levels: list[list[str]] = []
    remaining = set(graph.keys())

    while remaining:
        # Node dengan in_degree 0 (semua dependency sudah selesai)
        ready = [n for n in remaining if in_degree.get(n, 0) == 0]
        if not ready:
            # Cycle detected — break and return what we have
            if remaining:
                levels.append(list(remaining))
            break
        levels.append(ready)
        for node in ready:
            remaining.discard(node)
            # Decrease in_degree for nodes that depend on this node
            for other, deps in graph.items():
                if node in deps:
                    in_degree[other] = max(0, in_degree.get(other, 0) - 1)

    return levels


def build_execution_waves(tasks: list[RaudahTask]) -> list[list[RaudahTask]]:
    """
    Partisi task ke dalam list-of-list: setiap inner list boleh paralel,
    outer list dieksekusi berurutan.

    Priority:
      1. Explicit dependency edges (depends_on)
      2. Role-based implicit ordering (ROLE_WAVE fallback)
    """
    if not tasks:
        return []

    # Check if any task has explicit dependencies
    has_deps = any((t.depends_on or []) for t in tasks)

    if has_deps:
        # Use dependency-based topological sort
        graph = _build_dependency_graph(tasks)
        task_map = {t.task_id: t for t in tasks}
        levels = _topological_levels(graph)
        return [[task_map[tid] for tid in level if tid in task_map] for level in levels]

    # Fallback: role-based waves
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
