"""
export_feedback.py — Export feedback dari Supabase ke corpus SIDIX

Usage:
    python tools/export_feedback.py              # export status: in_progress
    python tools/export_feedback.py --all        # export semua feedback
    python tools/export_feedback.py --reindex    # export + re-index corpus

Env vars yang dibutuhkan (di server, JANGAN di .env yang di-commit):
    SUPABASE_URL
    SUPABASE_SECRET_KEY   ← service key, bukan publishable key

Setelah export, jalankan:
    python3 -m brain_qa index
agar feedback masuk ke corpus dan SIDIX bisa menjawab tentang itu.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── Dependency check ─────────────────────────────────────────────────────────
try:
    from supabase import create_client
except ImportError:
    print("ERROR: supabase-py belum install.")
    print("Jalankan: pip install supabase")
    sys.exit(1)

# ── Config ───────────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SECRET_KEY")  # service key — full access

OUTPUT_DIR = Path(__file__).parent.parent / "brain" / "public" / "feedback_learning"

TIPE_EMOJI = {"bug": "🐛", "saran": "💡", "fitur": "✨"}


def make_slug(text: str, max_len: int = 40) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9\s]", "", slug)
    slug = re.sub(r"\s+", "_", slug.strip())
    return slug[:max_len]


def render_feedback_md(fb: dict) -> str:
    tipe   = fb.get("type", "saran")
    msg    = fb.get("message", "")
    date   = fb.get("created_at", "")[:10]
    fid    = str(fb.get("id", ""))[:8]
    status = fb.get("status", "open")
    emoji  = TIPE_EMOJI.get(tipe, "📝")

    return f"""# {emoji} Feedback [{fid}] — {tipe.title()}: {msg[:60]}

**Tipe:** {tipe}
**Tanggal:** {date}
**ID:** {fb.get('id', '')}
**Status:** {status}

## Isi Feedback User

{msg}

## Catatan Pengembang

<!-- Admin: isi tindak lanjut di sini sebelum commit ke corpus -->

## Tindakan

- [ ] Jadikan research note
- [ ] Perbaiki bug di kode
- [ ] Tambah ke roadmap fitur
- [ ] Tidak relevan — tutup
"""


def export(filter_status: str | None = "in_progress") -> int:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL dan SUPABASE_SECRET_KEY harus di-set sebagai env var.")
        print("Contoh:")
        print('  export SUPABASE_URL="https://xxx.supabase.co"')
        print('  export SUPABASE_SECRET_KEY="sb_secret_..."')
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    query = supabase.table("feedback").select("*").order("created_at", desc=False)
    if filter_status:
        query = query.eq("status", filter_status)

    result = query.execute()
    feedbacks = result.data

    if not feedbacks:
        print(f"Tidak ada feedback dengan status: {filter_status or 'semua'}")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    exported = 0

    for fb in feedbacks:
        tipe = fb.get("type", "saran")
        msg  = fb.get("message", "")
        date = fb.get("created_at", "")[:10]
        slug = make_slug(msg)
        filename = f"{date}_{tipe}_{slug}.md"
        filepath = OUTPUT_DIR / filename

        if filepath.exists():
            print(f"  skip (sudah ada): {filename}")
            continue

        filepath.write_text(render_feedback_md(fb), encoding="utf-8")
        print(f"  ✓ exported: {filename}")
        exported += 1

    print(f"\nTotal exported: {exported} feedback")
    return exported


def main():
    parser = argparse.ArgumentParser(description="Export Supabase feedback ke corpus SIDIX")
    parser.add_argument("--all",     action="store_true", help="Export semua feedback (semua status)")
    parser.add_argument("--status",  default="in_progress", help="Filter status (default: in_progress)")
    parser.add_argument("--reindex", action="store_true", help="Jalankan brain_qa index setelah export")
    args = parser.parse_args()

    filter_status = None if args.all else args.status
    count = export(filter_status)

    if args.reindex and count > 0:
        print("\nRe-indexing corpus...")
        os.chdir(Path(__file__).parent.parent)
        ret = os.system("python3 -m brain_qa index")
        if ret == 0:
            print("✓ Corpus ter-index ulang")
        else:
            print("⚠ Re-index gagal — jalankan manual: python3 -m brain_qa index")


if __name__ == "__main__":
    main()
