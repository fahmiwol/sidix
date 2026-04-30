# -*- coding: utf-8 -*-
"""
One-command runner untuk demo_miniapp SIDIX.

Jalankan:
    python run.py

Skrip ini akan:
1. Memeriksa apakah fastapi dan uvicorn sudah terinstall
2. Menginstall dependensi dari requirements.txt jika belum ada
3. Menjalankan app.py dengan uvicorn di port 8900
"""

import importlib.util
import logging
import subprocess
import sys
from pathlib import Path

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Konfigurasi ────────────────────────────────────────────────────────────────
APP_HOST = "0.0.0.0"
APP_PORT = 8900
APP_MODULE = "app:app"

# Paket yang wajib ada sebelum menjalankan server
REQUIRED_PACKAGES = {
    "fastapi": "fastapi>=0.111.0",
    "uvicorn": "uvicorn[standard]>=0.29.0",
}

THIS_DIR = Path(__file__).parent.resolve()
REQUIREMENTS_FILE = THIS_DIR / "requirements.txt"


# ── Pemeriksaan & instalasi dependensi ─────────────────────────────────────────
def is_package_installed(package_name: str) -> bool:
    """Periksa apakah paket Python sudah terinstall."""
    return importlib.util.find_spec(package_name) is not None


def install_dependencies() -> None:
    """Install dependensi dari requirements.txt jika belum ada."""
    missing = [
        spec
        for pkg, spec in REQUIRED_PACKAGES.items()
        if not is_package_installed(pkg)
    ]

    if not missing:
        logger.info("Semua dependensi sudah terinstall.")
        return

    logger.info("Menginstall dependensi yang belum ada: %s", missing)

    if REQUIREMENTS_FILE.exists():
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
    else:
        cmd = [sys.executable, "-m", "pip", "install"] + missing

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        logger.error("Gagal menginstall dependensi. Periksa koneksi internet atau pip.")
        sys.exit(1)

    logger.info("Instalasi selesai.")


# ── Runner utama ───────────────────────────────────────────────────────────────
def start_server() -> None:
    """Jalankan uvicorn server."""
    import uvicorn  # noqa: PLC0415 — diimport setelah install

    logger.info(
        "Memulai demo_miniapp di http://%s:%d ...", APP_HOST, APP_PORT
    )
    logger.info("Tekan Ctrl+C untuk menghentikan server.")

    uvicorn.run(
        APP_MODULE,
        host=APP_HOST,
        port=APP_PORT,
        reload=True,
        app_dir=str(THIS_DIR),
        log_level="info",
    )


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    install_dependencies()
    start_server()
