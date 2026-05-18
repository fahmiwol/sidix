#!/usr/bin/env python3
"""
self_heal.py — SIDIX Self-Healing Recovery Monitor
==================================================

Jalankan secara berkala (cron setiap 5 menit, atau systemd timer, atau PM2):
    python scripts/self_heal.py

Apa yang dilakukan:
  1. Ping /health endpoint (local atau VPS)
  2. Cek proses kritikal (sidix-brain, sidix-ui di PM2)
  3. Kalau down: restart otomatis + notifikasi ringkas
  4. Log semua ke actions ke logfile (rotate harian)

Env:
    SIDIX_HEALTH_URL   — default: http://localhost:8765/health
    SIDIX_SELFHEAL_LOG — default: logs/self_heal.log
    SIDIX_SELFHEAL_PM2 — apakah pakai PM2? (auto-detect)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

HEALTH_URL = os.getenv("SIDIX_HEALTH_URL", "http://localhost:8765/health").rstrip("/")
LOG_PATH = Path(os.getenv("SIDIX_SELFHEAL_LOG", "logs/self_heal.log"))
PM2_ENABLED = os.getenv("SIDIX_SELFHEAL_PM2", "auto").lower() in ("1", "true", "yes", "auto")
TIMEOUT = int(os.getenv("SIDIX_SELFHEAL_TIMEOUT", "15"))

# Setup logger
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("sidix.heal")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ping_health() -> tuple[bool, dict[str, Any]]:
    try:
        r = requests.get(f"{HEALTH_URL}/health", timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            ok = data.get("ok", False) and data.get("model_ready", False)
            return ok, data
        return False, {"status_code": r.status_code}
    except Exception as e:
        return False, {"error": str(e)}


def pm2_list() -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(["pm2", "jlist"], text=True, timeout=10)
        return json.loads(out)
    except Exception:
        return []


def pm2_restart(name: str) -> bool:
    try:
        subprocess.check_call(["pm2", "restart", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        log.info("PM2 restart %s OK", name)
        return True
    except Exception as e:
        log.error("PM2 restart %s failed: %s", name, e)
        return False


def check_disk() -> dict[str, Any]:
    try:
        import shutil
        stat = shutil.disk_usage("/")
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        pct = (1 - free_gb / total_gb) * 100
        return {"free_gb": round(free_gb, 1), "total_gb": round(total_gb, 1), "used_pct": round(pct, 1)}
    except Exception as e:
        return {"error": str(e)}


def main() -> int:
    log.info("=== Self-heal check start ===")
    issues: list[str] = []

    # 1. Health endpoint
    healthy, health_data = ping_health()
    if not healthy:
        issues.append(f"health_fail: {health_data}")
        log.warning("Health check FAILED: %s", health_data)
    else:
        log.info("Health OK — model_ready=%s", health_data.get("model_ready"))

    # 2. PM2 processes (if available)
    pm2_procs = pm2_list()
    if pm2_procs:
        for proc in pm2_procs:
            name = proc.get("name", "unknown")
            status = proc.get("pm2_env", {}).get("status", "unknown")
            if name in ("sidix-brain", "sidix-ui") and status != "online":
                issues.append(f"pm2_down:{name}")
                log.warning("PM2 %s is %s — restarting", name, status)
                pm2_restart(name)
    elif PM2_ENABLED:
        log.info("PM2 not detected — skipping process check")

    # 3. Disk space
    disk = check_disk()
    if "used_pct" in disk and disk["used_pct"] > 90:
        issues.append(f"disk_critical:{disk['used_pct']}%")
        log.warning("Disk critical: %s%% used", disk["used_pct"])
    else:
        log.info("Disk OK: %s", disk)

    # 4. Summary log
    if issues:
        log.error("Self-heal found %s issue(s): %s", len(issues), "; ".join(issues))
    else:
        log.info("Self-heal: all green")

    log.info("=== Self-heal check end ===")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
