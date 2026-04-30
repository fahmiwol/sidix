# -*- coding: utf-8 -*-
"""
Snippet: Verifikasi integritas ledger brain_qa secara programatik.

Menggunakan subprocess untuk memanggil:
    python apps/brain_qa/ledger.py verify

Dependensi: tidak ada (stdlib only)

Cara menggunakan:
    python python_ledger_verify.py [--data-dir apps/brain_qa/.data]
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Default path ───────────────────────────────────────────────────────────────
# Sesuaikan jika direktori brain_qa berbeda
REPO_ROOT = Path(__file__).parent.parent.parent  # D:\MIGHAN Model\
DEFAULT_LEDGER_SCRIPT = REPO_ROOT / "apps" / "brain_qa" / "ledger.py"
DEFAULT_DATA_DIR = REPO_ROOT / "apps" / "brain_qa" / ".data"


# ── Fungsi verifikasi ──────────────────────────────────────────────────────────
def verify_ledger(
    ledger_script: Path = DEFAULT_LEDGER_SCRIPT,
    data_dir: Path = DEFAULT_DATA_DIR,
    timeout: int = 60,
) -> dict:
    """
    Jalankan perintah verifikasi ledger dan kembalikan hasilnya.

    Returns:
        dict dengan kunci:
            - success (bool): True jika verifikasi lulus
            - returncode (int): Exit code subprocess
            - stdout (str): Output standar
            - stderr (str): Output error
            - entries_verified (int | None): Jumlah entri yang diverifikasi
    """
    if not ledger_script.exists():
        logger.error("Script ledger tidak ditemukan: %s", ledger_script)
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"File tidak ditemukan: {ledger_script}",
            "entries_verified": None,
        }

    cmd = [
        sys.executable,
        str(ledger_script),
        "verify",
        "--data-dir", str(data_dir),
    ]

    logger.info("Menjalankan: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error("Timeout setelah %d detik", timeout)
        return {
            "success": False,
            "returncode": -2,
            "stdout": "",
            "stderr": f"Timeout setelah {timeout} detik",
            "entries_verified": None,
        }

    # Parse jumlah entri dari stdout (opsional, format bergantung pada ledger.py)
    entries_verified = None
    for line in result.stdout.splitlines():
        if "entries" in line.lower() and "verified" in line.lower():
            # Coba ekstrak angka dari baris seperti "42 entries verified"
            parts = line.split()
            for part in parts:
                if part.isdigit():
                    entries_verified = int(part)
                    break

    return {
        "success": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "entries_verified": entries_verified,
    }


def print_report(result: dict) -> None:
    """Cetak laporan verifikasi terformat."""
    sep = "=" * 60
    print(sep)
    print("LEDGER VERIFICATION REPORT")
    print(sep)

    status = "PASS" if result["success"] else "FAIL"
    print(f"Status       : {status}")
    print(f"Exit code    : {result['returncode']}")

    if result["entries_verified"] is not None:
        print(f"Entri diverif: {result['entries_verified']}")

    if result["stdout"].strip():
        print("\n[stdout]")
        for line in result["stdout"].strip().splitlines():
            print(" ", line)

    if result["stderr"].strip():
        print("\n[stderr]")
        for line in result["stderr"].strip().splitlines():
            print(" ", line)

    print(sep)


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python_ledger_verify",
        description="Verifikasi integritas ledger brain_qa secara programatik.",
    )
    parser.add_argument(
        "--ledger-script",
        default=str(DEFAULT_LEDGER_SCRIPT),
        help=f"Path ke ledger.py (default: {DEFAULT_LEDGER_SCRIPT})",
    )
    parser.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        help=f"Direktori data ledger (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output dalam format JSON",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout dalam detik (default: 60)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = verify_ledger(
        ledger_script=Path(args.ledger_script),
        data_dir=Path(args.data_dir),
        timeout=args.timeout,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
