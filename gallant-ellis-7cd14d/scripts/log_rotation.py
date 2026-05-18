"""
log_rotation.py — Task 42 (Al-Muddaththir / G5)
Rotasi dan retensi log SIDIX.
Hanya menggunakan stdlib: os, pathlib, argparse, datetime, sys.

Strategi:
1. Hapus file *.log / *.jsonl yang lebih tua dari --max-days hari (berdasarkan mtime)
2. Jika total size masih > --max-size-mb MB, hapus file terlama sampai di bawah threshold
3. --dry-run: hanya cetak, tidak hapus
"""

import argparse
import datetime
import os
import sys
from pathlib import Path
from typing import List, Tuple


def kumpulkan_file_log(log_dir: Path) -> List[Tuple[Path, float, int]]:
    """
    Kumpulkan semua file *.log dan *.jsonl di log_dir.
    Kembalikan list of (path, mtime_timestamp, size_bytes), diurutkan dari terlama.
    """
    pola = ["*.log", "*.jsonl"]
    file_list = []

    for pola_glob in pola:
        for filepath in log_dir.rglob(pola_glob):
            if filepath.is_file():
                stat = filepath.stat()
                file_list.append((filepath, stat.st_mtime, stat.st_size))

    # Urutkan dari terlama (mtime terkecil) ke terbaru
    file_list.sort(key=lambda x: x[1])
    return file_list


def format_bytes(n: int) -> str:
    """Format bytes ke satuan yang mudah dibaca."""
    for satuan in ("B", "KB", "MB", "GB"):
        if n < 1024 or satuan == "GB":
            return f"{n:.1f} {satuan}"
        n /= 1024


def hapus_file(filepath: Path, alasan: str, dry_run: bool) -> None:
    """Hapus satu file dan cetak informasi."""
    if dry_run:
        print(f"  [DRY-RUN] Akan dihapus ({alasan}): {filepath}")
    else:
        try:
            filepath.unlink()
            print(f"  [HAPUS] ({alasan}): {filepath}")
        except OSError as e:
            print(f"  [ERROR] Gagal menghapus {filepath}: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rotasi dan retensi log SIDIX"
    )
    parser.add_argument(
        "--log-dir", default="logs",
        help="Direktori log yang diproses (default: logs/)"
    )
    parser.add_argument(
        "--max-days", type=int, default=30,
        help="Hapus file lebih tua dari N hari (default: 30)"
    )
    parser.add_argument(
        "--max-size-mb", type=float, default=100.0,
        help="Batas total ukuran direktori log dalam MB (default: 100)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Hanya cetak daftar file yang akan dihapus, tidak benar-benar hapus"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    log_dir = Path(args.log_dir)

    # Validasi direktori
    if not log_dir.exists():
        print(f"[ERROR] Direktori log tidak ditemukan: {log_dir.resolve()}")
        sys.exit(1)

    if not log_dir.is_dir():
        print(f"[ERROR] Bukan direktori: {log_dir.resolve()}")
        sys.exit(1)

    mode_str = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode_str}[INFO] Memproses direktori: {log_dir.resolve()}")
    print(f"{mode_str}[INFO] Max usia: {args.max_days} hari | Max ukuran: {args.max_size_mb} MB")

    # Kumpulkan semua file log
    file_list = kumpulkan_file_log(log_dir)

    if not file_list:
        print("[INFO] Tidak ada file *.log atau *.jsonl ditemukan.")
        sys.exit(0)

    total_size_bytes = sum(size for _, _, size in file_list)
    print(f"[INFO] Ditemukan {len(file_list)} file log | Total: {format_bytes(total_size_bytes)}")
    print()

    # === TAHAP 1: Hapus file lebih tua dari --max-days ===
    sekarang = datetime.datetime.now().timestamp()
    batas_mtime = sekarang - (args.max_days * 86400)  # 86400 detik per hari

    print(f"[TAHAP 1] Hapus file lebih tua dari {args.max_days} hari:")
    dihapus_tahap1 = 0
    ukuran_dihapus = 0

    for filepath, mtime, size in file_list[:]:  # iterasi salinan
        if mtime < batas_mtime:
            usia_hari = (sekarang - mtime) / 86400
            alasan = f"usia {usia_hari:.0f} hari"
            hapus_file(filepath, alasan, args.dry_run)
            dihapus_tahap1 += 1
            ukuran_dihapus += size

    if dihapus_tahap1 == 0:
        print("  Tidak ada file yang melampaui batas usia.")

    # Update list setelah tahap 1 (jika tidak dry-run)
    if not args.dry_run:
        file_list = kumpulkan_file_log(log_dir)
        total_size_bytes = sum(size for _, _, size in file_list)
    else:
        # Simulasi: kurangi ukuran secara virtual
        file_list_sisa = [
            (fp, mt, sz) for fp, mt, sz in file_list if mt >= batas_mtime
        ]
        total_size_bytes = sum(sz for _, _, sz in file_list_sisa)
        file_list = file_list_sisa

    # === TAHAP 2: Hapus file terlama jika total masih > max-size-mb ===
    max_size_bytes = args.max_size_mb * 1024 * 1024
    print(f"\n[TAHAP 2] Cek total ukuran: {format_bytes(int(total_size_bytes))} / batas {args.max_size_mb} MB:")

    if total_size_bytes <= max_size_bytes:
        print("  Total ukuran dalam batas. Tidak ada yang perlu dihapus.")
    else:
        print(f"  Melebihi batas! Akan hapus file terlama sampai < {args.max_size_mb} MB.")
        dihapus_tahap2 = 0

        for filepath, mtime, size in file_list:  # sudah diurutkan dari terlama
            if total_size_bytes <= max_size_bytes:
                break
            alasan = f"kurangi ukuran, saat ini {format_bytes(int(total_size_bytes))}"
            hapus_file(filepath, alasan, args.dry_run)
            total_size_bytes -= size
            dihapus_tahap2 += 1

        print(f"  Selesai. Estimasi ukuran akhir: {format_bytes(int(total_size_bytes))}")

    # Ringkasan
    print("\n[RINGKASAN]")
    print(f"  File dihapus tahap 1 (usia)   : {dihapus_tahap1}")
    if not args.dry_run:
        file_akhir = kumpulkan_file_log(log_dir)
        total_akhir = sum(sz for _, _, sz in file_akhir)
        print(f"  File tersisa                  : {len(file_akhir)}")
        print(f"  Total ukuran akhir            : {format_bytes(int(total_akhir))}")
    else:
        print(f"  [DRY-RUN] Tidak ada file yang benar-benar dihapus.")
