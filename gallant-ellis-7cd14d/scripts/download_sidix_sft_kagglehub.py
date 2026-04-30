#!/usr/bin/env python3
"""
Unduh dataset SIDIX SFT dari Kaggle via kagglehub.

Prasyarat:
  pip install kagglehub

Autentikasi Kaggle (salah satu):
  - Env: `KAGGLE_USERNAME` + `KAGGLE_KEY` (token dari https://www.kaggle.com/settings )
  - Atau file `~/.kaggle/kaggle.json` (format resmi CLI Kaggle)

Bila muncul **403 / KaggleApiHTTPError**: akun belum login, dataset **private**, atau Anda bukan kolaborator —
periksa izin dataset `mighan/sidix-sft-dataset` di Kaggle.

Penggunaan:
  python scripts/download_sidix_sft_kagglehub.py
  python scripts/download_sidix_sft_kagglehub.py --dataset mighan/sidix-sft-dataset

Output: mencetak path lokal ke folder berisi berkas dataset (siap dipakai untuk fine-tune / inspeksi).
"""
from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="Download SIDIX SFT dataset from Kaggle (kagglehub).")
    parser.add_argument(
        "--dataset",
        default="mighan/sidix-sft-dataset",
        help="Slug dataset Kaggle owner/name (default: mighan/sidix-sft-dataset)",
    )
    args = parser.parse_args()

    try:
        import kagglehub
    except ImportError:
        print("Error: kagglehub tidak terpasang. Jalankan: pip install kagglehub", flush=True)
        return 1

    path = kagglehub.dataset_download(args.dataset)
    print("Path to dataset files:", path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
