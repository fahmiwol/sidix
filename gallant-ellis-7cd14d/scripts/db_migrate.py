"""
Apply SIDIX database schema ke PostgreSQL.

Usage:
    python scripts/db_migrate.py

Env:
    SIDIX_DB_URL=postgresql://user:pass@host:5432/sidix

Schema file: apps/brain_qa/brain_qa/db/schema.sql

Notes:
    - Script idempoten: semua tabel pakai CREATE TABLE IF NOT EXISTS.
    - Tidak menyentuh data yang sudah ada.
    - Untuk rollback, restore dari backup terlebih dahulu.
"""
import os
import sys
from pathlib import Path

SCHEMA_FILE = Path("apps/brain_qa/brain_qa/db/schema.sql")


def apply_schema(db_url: str | None = None) -> None:
    """
    Apply schema.sql ke database PostgreSQL.

    Args:
        db_url: Connection string PostgreSQL. Jika None, baca dari env SIDIX_DB_URL.

    Raises:
        SystemExit: Jika SIDIX_DB_URL tidak di-set atau file schema tidak ditemukan.
    """
    if db_url is None:
        db_url = os.getenv("SIDIX_DB_URL")
    if not db_url:
        print("ERROR: SIDIX_DB_URL tidak di-set.")
        print("Contoh: export SIDIX_DB_URL=postgresql://user:pass@localhost:5432/sidix")
        sys.exit(1)

    if not SCHEMA_FILE.exists():
        print(f"ERROR: Schema file tidak ditemukan: {SCHEMA_FILE}")
        print("Pastikan Anda menjalankan script dari root repo (C:\\SIDIX-AI).")
        sys.exit(1)

    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    print(f"[db_migrate] Schema file: {SCHEMA_FILE} ({len(sql)} chars)")

    try:
        import psycopg2  # type: ignore
    except ImportError:
        print("ERROR: psycopg2 tidak terinstall. Jalankan: pip install psycopg2-binary")
        sys.exit(1)

    conn = None
    try:
        print(f"[db_migrate] Connecting ke database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        with conn.cursor() as cur:
            print("[db_migrate] Applying schema...")
            cur.execute(sql)
        conn.commit()
        print("[db_migrate] Schema applied successfully.")
    except psycopg2.OperationalError as e:
        print(f"ERROR: Gagal connect ke database: {e}")
        sys.exit(1)
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print(f"ERROR: Gagal apply schema: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def verify_tables(db_url: str) -> list[str]:
    """
    Verifikasi tabel-tabel yang sudah ada di database.

    Returns:
        List nama tabel yang berhasil dibuat.
    """
    try:
        import psycopg2  # type: ignore
        conn = psycopg2.connect(db_url)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename;
                """
            )
            tables = [row[0] for row in cur.fetchall()]
        conn.close()
        return tables
    except Exception as e:
        print(f"WARN: Gagal verifikasi tabel: {e}")
        return []


if __name__ == "__main__":
    db_url = os.getenv("SIDIX_DB_URL")
    if not db_url:
        print("ERROR: SIDIX_DB_URL tidak di-set.")
        print("Contoh: set SIDIX_DB_URL=postgresql://user:pass@localhost:5432/sidix")
        sys.exit(1)

    apply_schema(db_url)

    print("\n[db_migrate] Verifikasi tabel:")
    tables = verify_tables(db_url)
    if tables:
        for t in tables:
            print(f"  - {t}")
        print(f"\nTotal: {len(tables)} tabel.")
    else:
        print("  (tidak ada tabel atau gagal verifikasi)")
