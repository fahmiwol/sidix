# -*- coding: utf-8 -*-
"""
Skrip pengecekan keamanan dependensi mingguan — SIDIX/Mighan project.

Run weekly: python scripts/check_deps.py

Memeriksa:
    - Python: apps/brain_qa/requirements.txt (via pip index versions)
    - npm   : SIDIX_USER_UI/package.json (via npm outdated --json)

Exit code:
    0 = semua dependensi up-to-date
    1 = ada paket yang perlu diupdate

Cara menjalankan:
    python scripts/check_deps.py
    python scripts/check_deps.py --python-only
    python scripts/check_deps.py --npm-only
    python scripts/check_deps.py --json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Path konfigurasi ───────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
PYTHON_REQ_FILES = [
    REPO_ROOT / "apps" / "brain_qa" / "requirements.txt",
    REPO_ROOT / "apps" / "demo_miniapp" / "requirements.txt",
    REPO_ROOT / "apps" / "demo_tool" / "requirements.txt",
]
NPM_UI_DIR = REPO_ROOT / "SIDIX_USER_UI"

TIMEOUT_PIP = 30   # detik per paket
TIMEOUT_NPM = 60   # detik total


# ── Tipe data ──────────────────────────────────────────────────────────────────
class PackageStatus:
    def __init__(
        self,
        name: str,
        current: str,
        latest: str,
        source_file: str,
        ecosystem: str = "python",
    ):
        self.name = name
        self.current = current
        self.latest = latest
        self.source_file = source_file
        self.ecosystem = ecosystem
        self.is_outdated = current != latest and latest != "unknown"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current": self.current,
            "latest": self.latest,
            "outdated": self.is_outdated,
            "source": self.source_file,
            "ecosystem": self.ecosystem,
        }


# ── Parser requirements.txt ────────────────────────────────────────────────────
def parse_requirements(req_file: Path) -> list[tuple[str, str]]:
    """
    Parse requirements.txt dan kembalikan list (nama_paket, versi_pinned).

    Mendukung format:
        fastapi>=0.111.0
        uvicorn[standard]>=0.29.0
        httpx==0.27.0
        numpy  (tanpa versi)
    """
    packages: list[tuple[str, str]] = []

    if not req_file.exists():
        logger.warning("File requirements tidak ditemukan: %s", req_file)
        return packages

    with open(req_file, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            # Lewati komentar dan baris kosong
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Pisahkan nama paket dari versi
            match = re.match(r"^([A-Za-z0-9_\-\.\[\]]+)\s*([><=!~]+)\s*([^\s,]+)?", line)
            if match:
                pkg_name = re.sub(r"\[.*?\]", "", match.group(1))  # hapus extras
                version = match.group(3) or "any"
                packages.append((pkg_name, version))
            else:
                # Paket tanpa versi constraint
                pkg_name = re.sub(r"\[.*?\]", "", line)
                packages.append((pkg_name, "any"))

    return packages


# ── Cek versi terbaru via pip ──────────────────────────────────────────────────
def get_latest_pip_version(package_name: str) -> str:
    """
    Ambil versi terbaru paket dari PyPI menggunakan `pip index versions`.

    Returns versi terbaru sebagai string, atau "unknown" jika gagal.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", package_name],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_PIP,
        )
        # Format output pip index versions:
        # "package (latest: X.Y.Z, ...)"  atau  "Available versions: X.Y.Z, ..."
        output = result.stdout + result.stderr
        match = re.search(r"Available versions:\s*([\d\.]+)", output)
        if match:
            return match.group(1)
        match = re.search(r"latest:\s*([\d\.]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)
        return "unknown"
    except subprocess.TimeoutExpired:
        logger.warning("Timeout saat cek versi: %s", package_name)
        return "unknown"
    except Exception as exc:  # noqa: BLE001
        logger.debug("Error cek versi %s: %s", package_name, exc)
        return "unknown"


# ── Python dependency check ────────────────────────────────────────────────────
def check_python_deps(req_files: list[Path]) -> list[PackageStatus]:
    """Periksa semua requirements.txt dan kembalikan status setiap paket."""
    all_statuses: list[PackageStatus] = []

    for req_file in req_files:
        if not req_file.exists():
            continue

        logger.info("Memeriksa: %s", req_file)
        packages = parse_requirements(req_file)

        for pkg_name, pinned_version in packages:
            logger.info("  Cek %s (pinned: %s) ...", pkg_name, pinned_version)
            latest = get_latest_pip_version(pkg_name)

            status = PackageStatus(
                name=pkg_name,
                current=pinned_version,
                latest=latest,
                source_file=str(req_file.relative_to(REPO_ROOT)),
                ecosystem="python",
            )
            all_statuses.append(status)

    return all_statuses


# ── npm dependency check ───────────────────────────────────────────────────────
def check_npm_deps(ui_dir: Path) -> list[PackageStatus]:
    """
    Jalankan `npm outdated --json` di direktori UI dan parse hasilnya.

    Returns list PackageStatus untuk setiap paket npm yang outdated.
    """
    if not ui_dir.exists():
        logger.warning("Direktori UI tidak ditemukan: %s", ui_dir)
        return []

    logger.info("Memeriksa npm deps di: %s", ui_dir)

    try:
        result = subprocess.run(
            ["npm", "outdated", "--json"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_NPM,
            cwd=str(ui_dir),
        )
    except FileNotFoundError:
        logger.warning("npm tidak ditemukan di PATH — lewati pengecekan npm")
        return []
    except subprocess.TimeoutExpired:
        logger.error("Timeout saat npm outdated")
        return []

    if not result.stdout.strip():
        logger.info("npm: semua paket up-to-date (atau npm outdated kosong)")
        return []

    try:
        outdated: dict = json.loads(result.stdout)
    except json.JSONDecodeError:
        logger.error("Gagal parse output npm outdated: %s", result.stdout[:200])
        return []

    statuses: list[PackageStatus] = []
    for pkg_name, info in outdated.items():
        statuses.append(PackageStatus(
            name=pkg_name,
            current=info.get("current", "?"),
            latest=info.get("latest", "?"),
            source_file="SIDIX_USER_UI/package.json",
            ecosystem="npm",
        ))

    return statuses


# ── Reporter ───────────────────────────────────────────────────────────────────
def print_report(all_statuses: list[PackageStatus]) -> bool:
    """
    Cetak laporan ke stdout.

    Returns True jika ada paket outdated, False jika semua up-to-date.
    """
    outdated = [s for s in all_statuses if s.is_outdated]
    uptodate = [s for s in all_statuses if not s.is_outdated]

    print("\n" + "=" * 70)
    print("DEPENDENCY SECURITY REPORT — SIDIX/Mighan")
    print("=" * 70)
    print(f"Total diperiksa : {len(all_statuses)} paket")
    print(f"Up-to-date      : {len(uptodate)}")
    print(f"Perlu update    : {len(outdated)}")
    print()

    if outdated:
        print("PERLU DIUPDATE:")
        print("-" * 70)
        for s in outdated:
            print(
                f"  [{s.ecosystem:6}] {s.name:<30} "
                f"{s.current:<15} -> {s.latest:<15} ({s.source_file})"
            )
        print()
    else:
        print("Semua dependensi up-to-date.")

    print("=" * 70)
    return len(outdated) > 0


def print_json_report(all_statuses: list[PackageStatus]) -> bool:
    """Output laporan dalam format JSON."""
    outdated = [s for s in all_statuses if s.is_outdated]
    report = {
        "total": len(all_statuses),
        "outdated_count": len(outdated),
        "all_up_to_date": len(outdated) == 0,
        "packages": [s.to_dict() for s in all_statuses],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return len(outdated) > 0


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_deps",
        description="Pengecekan dependensi mingguan SIDIX/Mighan.",
    )
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="Hanya periksa dependensi Python",
    )
    parser.add_argument(
        "--npm-only",
        action="store_true",
        help="Hanya periksa dependensi npm",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output dalam format JSON",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    all_statuses: list[PackageStatus] = []

    if not args.npm_only:
        all_statuses.extend(check_python_deps(PYTHON_REQ_FILES))

    if not args.python_only:
        all_statuses.extend(check_npm_deps(NPM_UI_DIR))

    if args.json:
        has_outdated = print_json_report(all_statuses)
    else:
        has_outdated = print_report(all_statuses)

    return 1 if has_outdated else 0


if __name__ == "__main__":
    sys.exit(main())
