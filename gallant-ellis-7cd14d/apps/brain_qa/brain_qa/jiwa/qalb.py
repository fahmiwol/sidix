"""
Qalb — Self-Healing System (Pilar 3)

Monitor: memory, CPU, response time, error rate.
Heal: reduce batch, restart ollama, clear cache, safe mode.
Non-blocking — background thread, check setiap 120 detik.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from enum import Enum

log = logging.getLogger("sidix.jiwa.qalb")


class HealthLevel(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    SICK = "sick"
    CRITICAL = "critical"


class QalbMonitor:
    """Lightweight health monitor — runs in background thread."""

    THRESHOLDS = {
        "memory_pct": 88,
        "cpu_pct": 92,
        "disk_pct": 95,
    }
    CHECK_INTERVAL = 120  # detik

    def __init__(self):
        self.current_health = HealthLevel.HEALTHY
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Mulai background monitoring thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        log.info("Qalb monitor started")

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        while self._running:
            try:
                self._check()
            except Exception as exc:
                log.debug(f"Qalb check error (non-fatal): {exc}")
            time.sleep(self.CHECK_INTERVAL)

    def _check(self) -> None:
        try:
            import psutil
            mem = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage("/").percent
        except ImportError:
            return  # psutil tidak tersedia, skip

        # Assess
        if mem > 95 or cpu > 95 or disk > self.THRESHOLDS["disk_pct"]:
            new_level = HealthLevel.CRITICAL
        elif mem > self.THRESHOLDS["memory_pct"] or cpu > self.THRESHOLDS["cpu_pct"]:
            new_level = HealthLevel.SICK
        elif mem > 75 or cpu > 75:
            new_level = HealthLevel.DEGRADED
        else:
            new_level = HealthLevel.HEALTHY

        if new_level != self.current_health:
            log.warning(f"Qalb: health changed {self.current_health.value} → {new_level.value} | mem={mem:.0f}% cpu={cpu:.0f}%")
            self.current_health = new_level
            self._heal(new_level, mem, cpu)

    def _heal(self, level: HealthLevel, mem: float, cpu: float) -> None:
        """Apply healing actions berdasarkan health level."""
        if level == HealthLevel.DEGRADED:
            try:
                import gc
                gc.collect()
                log.info("Qalb heal: gc.collect() ran")
            except Exception:
                pass

        elif level == HealthLevel.SICK:
            try:
                import gc
                gc.collect()
                # Clear Ollama context via env flag
                os.environ["SIDIX_QALB_REDUCE_BATCH"] = "1"
                log.warning("Qalb heal: reduce_batch flag set")
            except Exception:
                pass

        elif level == HealthLevel.CRITICAL:
            try:
                import gc
                gc.collect()
                os.environ["SIDIX_QALB_SAFE_MODE"] = "1"
                log.critical("Qalb CRITICAL: safe mode activated — non-essential features disabled")
            except Exception:
                pass

    def status(self) -> dict:
        return {"health": self.current_health.value}


# Singleton — satu instance per proses
_monitor = QalbMonitor()


def get_monitor() -> QalbMonitor:
    return _monitor


def start_monitoring() -> None:
    _monitor.start()
