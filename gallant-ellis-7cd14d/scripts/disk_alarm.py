"""
disk_alarm.py — Task 41 (Al-Haqqah / G5)
Alarm disk penuh untuk volume model SIDIX.
Hanya menggunakan stdlib: shutil, argparse, sys, os, datetime.

Contoh penggunaan sebagai cron:
    python scripts/disk_alarm.py --path D:\\MIGHAN\\ --threshold-pct 90

Exit code:
    0 = OK
    1 = WARN (penggunaan > --warn-pct)
    2 = ALARM (penggunaan > --threshold-pct)
"""

import argparse
import datetime
import os
import shutil
import sys
from typing import Optional


STATUS_OK = 0
STATUS_WARN = 1
STATUS_ALARM = 2


def format_bytes(n: int) -> str:
    """Format bytes ke satuan yang mudah dibaca."""
    for satuan in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or satuan == "TB":
            return f"{n:.1f} {satuan}"
        n /= 1024


def cek_disk(path: str, warn_pct: float, threshold_pct: float) -> dict:
    """
    Cek penggunaan disk di path yang diberikan.
    Kembalikan dict berisi status, persen_terpakai, dan detail.
    """
    try:
        usage = shutil.disk_usage(path)
    except FileNotFoundError:
        return {
            "error": f"Path tidak ditemukan: {path}",
            "status_kode": STATUS_ALARM,
            "status": "ALARM",
        }
    except PermissionError:
        return {
            "error": f"Akses ditolak: {path}",
            "status_kode": STATUS_ALARM,
            "status": "ALARM",
        }

    pct_terpakai = (usage.used / usage.total) * 100 if usage.total > 0 else 0

    if pct_terpakai >= threshold_pct:
        status = "ALARM"
        status_kode = STATUS_ALARM
    elif pct_terpakai >= warn_pct:
        status = "WARN"
        status_kode = STATUS_WARN
    else:
        status = "OK"
        status_kode = STATUS_OK

    return {
        "path": path,
        "status": status,
        "status_kode": status_kode,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "pct_terpakai": pct_terpakai,
        "warn_pct": warn_pct,
        "threshold_pct": threshold_pct,
    }


def tulis_log(path_log: str, pesan: str) -> None:
    """Append pesan ke file log dengan timestamp."""
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    with open(path_log, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {pesan}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Alarm disk penuh untuk volume model SIDIX"
    )
    parser.add_argument(
        "--path", default=".",
        help="Direktori yang dipantau (default: . yakni direktori saat ini)"
    )
    parser.add_argument(
        "--threshold-pct", type=float, default=85.0,
        help="Persentase terpakai untuk ALARM (default: 85)"
    )
    parser.add_argument(
        "--warn-pct", type=float, default=70.0,
        help="Persentase terpakai untuk WARN (default: 70)"
    )
    parser.add_argument(
        "--log", default=None,
        help="Path file log append-only (opsional)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Validasi argumen
    if args.warn_pct >= args.threshold_pct:
        print(
            f"[ERROR] --warn-pct ({args.warn_pct}) harus lebih kecil dari "
            f"--threshold-pct ({args.threshold_pct})"
        )
        sys.exit(STATUS_ALARM)

    hasil = cek_disk(args.path, args.warn_pct, args.threshold_pct)

    # Jika ada error (path tidak ditemukan, dll)
    if "error" in hasil:
        pesan = f"[{hasil['status']}] ERROR: {hasil['error']}"
        print(pesan)
        if args.log:
            tulis_log(args.log, pesan)
        sys.exit(hasil["status_kode"])

    # Format pesan output
    pct_str = f"{hasil['pct_terpakai']:.1f}%"
    free_str = format_bytes(hasil["free_bytes"])
    total_str = format_bytes(hasil["total_bytes"])
    used_str = format_bytes(hasil["used_bytes"])

    pesan = (
        f"[{hasil['status']}] Disk '{hasil['path']}' — "
        f"Terpakai: {pct_str} ({used_str} / {total_str}) — "
        f"Bebas: {free_str} — "
        f"Batas WARN: {hasil['warn_pct']}% | ALARM: {hasil['threshold_pct']}%"
    )

    print(pesan)

    # Informasi tambahan jika WARN atau ALARM
    if hasil["status_kode"] >= STATUS_WARN:
        sisa_sebelum_alarm = hasil["threshold_pct"] - hasil["pct_terpakai"]
        print(
            f"  => Sisa ruang sebelum ALARM: {sisa_sebelum_alarm:.1f}% "
            f"({format_bytes(int(hasil['free_bytes']))})"
        )

    # Tulis ke log jika diminta
    if args.log:
        tulis_log(args.log, pesan)

    sys.exit(hasil["status_kode"])
