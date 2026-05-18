"""
Qalb — Self-Heal System (Pilar 3) — Syifa Healer

Monitors system health every 120s and auto-heals degradation.
Health levels: HEALTHY → DEGRADED → SICK → CRITICAL
"""

from __future__ import annotations

import gc
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ── Health levels ─────────────────────────────────────────────────────────────

class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    SICK = "sick"
    CRITICAL = "critical"


# ── Thresholds ────────────────────────────────────────────────────────────────

THRESHOLDS = {
    HealthLevel.DEGRADED:  {"memory": 75, "cpu": 80, "error_rate": 0.05},
    HealthLevel.SICK:      {"memory": 85, "cpu": 88, "error_rate": 0.15},
    HealthLevel.CRITICAL:  {"memory": 93, "cpu": 95, "error_rate": 0.30},
}


# ── Metrics snapshot ─────────────────────────────────────────────────────────

@dataclass
class HealthMetrics:
    memory_pct: float = 0.0
    cpu_pct: float = 0.0
    disk_pct: float = 0.0
    error_rate: float = 0.0
    avg_latency_ms: float = 0.0
    ollama_ok: bool = True
    timestamp: float = field(default_factory=time.time)


@dataclass
class HealingAction:
    level: HealthLevel
    action: str
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    note: str = ""


# ── SyifaHealer ──────────────────────────────────────────────────────────────

class SyifaHealer:
    """
    Background health monitor with auto-healing.

    Usage:
        healer = SyifaHealer()
        healer.start()
        # later:
        print(healer.current_level)
    """

    CHECK_INTERVAL = 120  # seconds

    def __init__(
        self,
        metrics_fn: Optional[Callable[[], HealthMetrics]] = None,
        ollama_check_fn: Optional[Callable[[], bool]] = None,
    ):
        self.metrics_fn = metrics_fn or self._collect_metrics
        self.ollama_check_fn = ollama_check_fn or self._check_ollama
        self.current_level = HealthLevel.HEALTHY
        self.last_metrics = HealthMetrics()
        self.history: list[HealingAction] = []
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="qalb-healer")
        self._thread.start()
        logger.info("Qalb: SyifaHealer started (interval %ds)", self.CHECK_INTERVAL)

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def health(self) -> str:
        return self.current_level.value

    def status_report(self) -> dict:
        m = self.last_metrics
        return {
            "level": self.current_level.value,
            "memory_pct": m.memory_pct,
            "cpu_pct": m.cpu_pct,
            "disk_pct": m.disk_pct,
            "error_rate": m.error_rate,
            "avg_latency_ms": m.avg_latency_ms,
            "ollama_ok": m.ollama_ok,
            "recent_actions": [
                {"action": a.action, "level": a.level.value, "success": a.success}
                for a in self.history[-5:]
            ],
        }

    # ── Monitor loop ──────────────────────────────────────────────────────────

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                logger.warning("Qalb: tick error: %s", e)
            self._stop_event.wait(timeout=self.CHECK_INTERVAL)

    def _tick(self) -> None:
        metrics = self.metrics_fn()
        self.last_metrics = metrics
        level = self._assess(metrics)
        prev_level = self.current_level
        self.current_level = level

        if level != HealthLevel.HEALTHY:
            self._heal(level, metrics)

        if level != prev_level:
            logger.info("Qalb: health %s → %s", prev_level.value, level.value)

    # ── Assessment ────────────────────────────────────────────────────────────

    def _assess(self, m: HealthMetrics) -> HealthLevel:
        for level in [HealthLevel.CRITICAL, HealthLevel.SICK, HealthLevel.DEGRADED]:
            t = THRESHOLDS[level]
            if (
                m.memory_pct >= t["memory"]
                or m.cpu_pct >= t["cpu"]
                or m.error_rate >= t["error_rate"]
            ):
                return level
        return HealthLevel.HEALTHY

    # ── Healing actions ───────────────────────────────────────────────────────

    def _heal(self, level: HealthLevel, metrics: HealthMetrics) -> None:
        actions_taken: list[str] = []

        if level >= HealthLevel.DEGRADED:
            gc.collect()
            actions_taken.append("gc_collect")

        if level >= HealthLevel.SICK:
            os.environ["SIDIX_QALB_REDUCE_BATCH"] = "1"
            actions_taken.append("reduce_batch")

        if level >= HealthLevel.CRITICAL:
            os.environ["SIDIX_QALB_SAFE_MODE"] = "1"
            actions_taken.append("safe_mode")
            logger.critical("Qalb: CRITICAL state — safe mode activated")

        for action in actions_taken:
            self.history.append(HealingAction(level=level, action=action))

        # Trim history
        if len(self.history) > 100:
            self.history = self.history[-100:]

    # ── Metrics collection ────────────────────────────────────────────────────

    @staticmethod
    def _collect_metrics() -> HealthMetrics:
        m = HealthMetrics()
        try:
            import psutil
            m.memory_pct = psutil.virtual_memory().percent
            m.cpu_pct = psutil.cpu_percent(interval=1)
            m.disk_pct = psutil.disk_usage("/").percent
        except ImportError:
            pass  # psutil optional
        return m

    @staticmethod
    def _check_ollama() -> bool:
        try:
            import urllib.request
            urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
            return True
        except Exception:
            return False
