# -*- coding: utf-8 -*-
"""
Skrip migrasi schema RAG brain_qa — satu perintah.

Cara menggunakan:
    python scripts/migrate_rag_schema.py --from-version 0 --to-version 1
    python scripts/migrate_rag_schema.py --from-version 0 --to-version 1 --dry-run
    python scripts/migrate_rag_schema.py --from-version 0 --to-version 1 --data-dir apps/brain_qa/.data

Apa yang dilakukan:
    - Membaca schema version dari bm25_index.json (atau index yang relevan)
    - Membuat backup sebelum migrasi (.bak)
    - Migrasi v0->v1: tambah field "schema_version": 1 ke metadata
    - Migrasi v1->v2: stub — placeholder untuk migrasi masa depan
    - Dry-run: preview tanpa menulis apapun
    - Aman: abort jika versi sudah sesuai target
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
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
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = "apps/brain_qa/.data"
INDEX_FILENAME = "bm25_index.json"

# Versi schema terbaru yang didukung
MAX_SCHEMA_VERSION = 2


# ── Utilitas JSON ──────────────────────────────────────────────────────────────
def load_json(path: Path) -> dict:
    """Load JSON dari file. Return dict kosong jika tidak ada atau invalid."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("JSON parse error di %s: %s", path.name, exc)
        return {}


def save_json(path: Path, data: dict) -> None:
    """Simpan dict ke file JSON dengan indentasi."""
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def make_backup(path: Path) -> Path:
    """Buat backup file ke <path>.bak. Return path backup."""
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(str(path), str(backup_path))
    logger.info("Backup dibuat: %s", backup_path)
    return backup_path


# ── Fungsi migrasi per versi ───────────────────────────────────────────────────
def migrate_v0_to_v1(data: dict, dry_run: bool) -> dict:
    """
    Migrasi v0 -> v1: tambah field "schema_version": 1 ke metadata indeks.

    Perubahan:
        - Tambah top-level key "schema_version": 1
        - Tambah top-level key "metadata" jika belum ada (dict kosong)
    """
    logger.info("Menjalankan migrasi v0 -> v1 ...")

    if dry_run:
        preview = dict(data)
        preview["schema_version"] = 1
        if "metadata" not in preview:
            preview["metadata"] = {}
        logger.info(
            "[DRY-RUN] Akan menambah: schema_version=1, metadata={}"
            if "metadata" not in data else
            "[DRY-RUN] Akan menambah: schema_version=1"
        )
        return preview

    data["schema_version"] = 1
    if "metadata" not in data:
        data["metadata"] = {}
        logger.info("  + Ditambah: metadata = {}")
    logger.info("  + Ditambah: schema_version = 1")
    return data


def migrate_v1_to_v2(data: dict, dry_run: bool) -> dict:
    """
    Migrasi v1 -> v2: STUB — placeholder untuk migrasi masa depan.

    Rencana v2:
        - Normalisasi field "corpus_entries" ke format baru
        - Tambah field "index_algorithm_version"
        - (implementasi belum final — tunggu keputusan arsitektur)
    """
    logger.info("Migrasi v1 -> v2 adalah STUB — belum ada perubahan nyata.")
    logger.info("Implementasi akan ditambah pada sprint berikutnya.")

    if dry_run:
        logger.info("[DRY-RUN] Tidak ada perubahan untuk v1->v2 saat ini.")
        return data

    # Update schema_version ke 2
    data["schema_version"] = 2
    logger.info("  + schema_version diupdate ke 2 (stub, tanpa perubahan struktural)")
    return data


# Peta fungsi migrasi
MIGRATION_MAP: dict[tuple[int, int], callable] = {
    (0, 1): migrate_v0_to_v1,
    (1, 2): migrate_v1_to_v2,
}


# ── Runner migrasi utama ───────────────────────────────────────────────────────
def run_migration(
    data_dir: Path,
    from_version: int,
    to_version: int,
    dry_run: bool,
) -> int:
    """
    Jalankan migrasi schema dari from_version ke to_version.

    Returns:
        0 jika sukses
        1 jika ada error
    """
    index_path = data_dir / INDEX_FILENAME

    # Buat direktori data jika belum ada
    if not data_dir.exists():
        if dry_run:
            logger.info("[DRY-RUN] Direktori tidak ada: %s (akan dibuat)", data_dir)
        else:
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Direktori dibuat: %s", data_dir)

    # Load atau inisialisasi index
    if index_path.exists():
        data = load_json(index_path)
    else:
        logger.info("File indeks belum ada — membuat baru: %s", index_path)
        data = {}

    # Cek schema version saat ini
    current_schema_version = data.get("schema_version", 0)
    logger.info(
        "Schema version saat ini : %d | Target: %d",
        current_schema_version,
        to_version,
    )

    # Validasi argumen
    if from_version != current_schema_version:
        logger.error(
            "Schema version tidak cocok: --from-version=%d tapi file punya schema_version=%d",
            from_version,
            current_schema_version,
        )
        logger.error(
            "Gunakan --from-version %d untuk melanjutkan.", current_schema_version
        )
        return 1

    if current_schema_version == to_version:
        logger.info("Schema sudah di versi %d — tidak ada yang perlu dimigrasikan.", to_version)
        return 0

    if to_version > MAX_SCHEMA_VERSION:
        logger.error(
            "Target versi %d melebihi versi maksimum yang didukung (%d).",
            to_version,
            MAX_SCHEMA_VERSION,
        )
        return 1

    # Buat backup sebelum migrasi
    if index_path.exists() and not dry_run:
        make_backup(index_path)
    elif dry_run and index_path.exists():
        logger.info("[DRY-RUN] Akan membuat backup: %s.bak", index_path)

    # Jalankan migrasi bertahap
    current = from_version
    while current < to_version:
        next_v = current + 1
        migration_fn = MIGRATION_MAP.get((current, next_v))

        if migration_fn is None:
            logger.error(
                "Tidak ada fungsi migrasi untuk v%d -> v%d.", current, next_v
            )
            return 1

        data = migration_fn(data, dry_run)
        logger.info("Migrasi v%d -> v%d: selesai.", current, next_v)
        current = next_v

    # Simpan hasil migrasi
    if not dry_run:
        save_json(index_path, data)
        logger.info("File indeks disimpan: %s", index_path)
        logger.info("Migrasi selesai: v%d -> v%d", from_version, to_version)
    else:
        logger.info(
            "[DRY-RUN] Migrasi selesai (simulasi). Tidak ada file yang ditulis."
        )
        logger.info(
            "[DRY-RUN] Preview data:\n%s",
            json.dumps(data, indent=2, ensure_ascii=False)[:500],
        )

    return 0


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migrate_rag_schema",
        description="Migrasi schema RAG brain_qa — satu perintah.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--from-version",
        type=int,
        required=True,
        help="Versi schema sumber (misal: 0)",
    )
    parser.add_argument(
        "--to-version",
        type=int,
        required=True,
        help="Versi schema target (misal: 1)",
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help=f"Direktori data RAG (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview perubahan tanpa menulis apapun ke disk",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    data_dir = REPO_ROOT / args.data_dir

    logger.info("=== Migrasi Schema RAG brain_qa ===")
    logger.info("Data dir    : %s", data_dir)
    logger.info("v%d -> v%d  %s", args.from_version, args.to_version,
                "(DRY-RUN)" if args.dry_run else "")

    return run_migration(
        data_dir=data_dir,
        from_version=args.from_version,
        to_version=args.to_version,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
