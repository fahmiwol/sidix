#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_coding_corpus.py — Ambil konten dari roadmap.sh GitHub & simpan ke corpus SIDIX.

Source: https://github.com/kamranahmedse/developer-roadmap (lisensi: CC BY-SA 4.0 / MIT)
Tujuan: memperkaya korpus coding SIDIX untuk meningkatkan kemampuan menjawab pertanyaan teknis.

Cara pakai:
    python scripts/fetch_coding_corpus.py              # semua roadmap prioritas
    python scripts/fetch_coding_corpus.py --roadmap python  # satu roadmap
    python scripts/fetch_coding_corpus.py --list       # daftar roadmap tersedia

Syarat: pip install requests
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ERROR] Install requests: pip install requests")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "brain" / "public" / "coding"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_API = "https://api.github.com/repos/kamranahmedse/developer-roadmap/contents"
RAW_BASE   = "https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master"

# Roadmap yang diprioritaskan untuk SIDIX (ordered by relevance)
PRIORITY_ROADMAPS = [
    "python",
    "backend",
    "javascript",
    "typescript",
    "datastructures-and-algorithms",
    "system-design",
    "git-github",
    "docker",
    "linux",
    "sql",
    "machine-learning",
    "nodejs",
    "react",
    "computer-science",
    "ai-engineer",
    "prompt-engineering",
    "api-design",
    "software-design-architecture",
]

HEADERS = {"Accept": "application/vnd.github.v3+json"}


def github_list_dir(path: str) -> list[dict]:
    """List directory contents via GitHub API. Returns list of file objects."""
    url = f"{GITHUB_API}/{path}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 403:
        print("[WARN] GitHub rate limit. Tunggu beberapa menit atau set GITHUB_TOKEN env.")
        return []
    r.raise_for_status()
    return r.json() if isinstance(r.json(), list) else []


def fetch_raw(download_url: str) -> str:
    """Fetch raw file content."""
    r = requests.get(download_url, timeout=20)
    r.raise_for_status()
    return r.text


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter if present."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text.strip()


def clean_link_badges(text: str) -> str:
    """Convert roadmap.sh link badges to plain markdown links."""
    # [@official@Title](url) → **[Official] Title** (url)
    text = re.sub(r"\[@official@([^\]]+)\]\(([^)]+)\)", r"- [Official] \1: \2", text)
    text = re.sub(r"\[@article@([^\]]+)\]\(([^)]+)\)", r"- [Article] \1: \2", text)
    text = re.sub(r"\[@video@([^\]]+)\]\(([^)]+)\)", r"- [Video] \1: \2", text)
    text = re.sub(r"\[@course@([^\]]+)\]\(([^)]+)\)", r"- [Course] \1: \2", text)
    text = re.sub(r"\[@opensource@([^\]]+)\]\(([^)]+)\)", r"- [Open Source] \1: \2", text)
    return text


def fetch_roadmap_content(roadmap: str, max_files: int = 100) -> str:
    """
    Fetch all content files for a roadmap and aggregate into one markdown string.
    Returns aggregated content.
    """
    print(f"  Fetching content list for: {roadmap}...")
    items = github_list_dir(f"src/data/roadmaps/{roadmap}/content")

    if not items:
        # Some roadmaps have nested structure
        items = github_list_dir(f"src/data/roadmaps/{roadmap}")
        items = [i for i in items if i.get("name") == "content"]
        if items and items[0]["type"] == "dir":
            items = github_list_dir(f"src/data/roadmaps/{roadmap}/content")

    md_files = [i for i in items if i.get("type") == "file" and i["name"].endswith(".md")]
    print(f"  Found {len(md_files)} topic files")

    sections: list[str] = []
    count = 0

    for item in md_files[:max_files]:
        if count >= max_files:
            break
        try:
            content = fetch_raw(item["download_url"])
            content = strip_frontmatter(content)
            content = clean_link_badges(content)
            if len(content.strip()) > 50:  # skip empty/stub files
                sections.append(content)
            count += 1
            time.sleep(0.15)  # avoid rate limit
        except Exception as e:
            print(f"  [SKIP] {item['name']}: {e}")

    print(f"  Fetched {count} topic files")
    return "\n\n---\n\n".join(sections)


def save_roadmap_corpus(roadmap: str) -> Path:
    """Fetch roadmap, save as markdown corpus file."""
    safe_name = roadmap.replace("-", "_")
    out_path = CORPUS_DIR / f"roadmap_{safe_name}.md"

    print(f"\n[{roadmap}] Starting fetch...")
    body = fetch_roadmap_content(roadmap)

    if not body.strip():
        print(f"  [WARN] No content fetched for {roadmap}")
        return out_path

    header = (
        f"# Roadmap: {roadmap.replace('-', ' ').title()}\n\n"
        f"> Sumber: roadmap.sh — https://roadmap.sh/{roadmap}\n"
        f"> Lisensi: CC BY-SA 4.0 (komunitas + tim roadmap.sh)\n"
        f"> Catatan: Konten ini untuk pengayaan corpus SIDIX. Tautan ke resource eksternal disertakan.\n\n"
        f"---\n\n"
    )
    out_path.write_text(header + body, encoding="utf-8")
    size_kb = out_path.stat().st_size / 1024
    print(f"  [OK] Saved: {out_path} ({size_kb:.1f} KB)")
    return out_path


def create_corpus_index(saved: list[Path]) -> None:
    """Create an index file listing all fetched roadmaps."""
    index_path = CORPUS_DIR / "INDEX.md"
    lines = [
        "# SIDIX Coding Corpus — Roadmap.sh Index\n",
        f"> Diambil dari: https://github.com/kamranahmedse/developer-roadmap\n",
        f"> Lisensi: CC BY-SA 4.0\n\n",
        "## File\n\n",
    ]
    for p in sorted(saved):
        size_kb = p.stat().st_size / 1024 if p.exists() else 0
        lines.append(f"- [{p.stem}]({p.name}) ({size_kb:.0f} KB)\n")

    index_path.write_text("".join(lines), encoding="utf-8")
    print(f"\n[OK] Index: {index_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch coding corpus dari roadmap.sh GitHub untuk SIDIX"
    )
    parser.add_argument("--roadmap", help="Nama roadmap spesifik (mis: python)")
    parser.add_argument("--list", action="store_true", help="Tampilkan daftar roadmap")
    parser.add_argument("--all", action="store_true", help="Fetch semua roadmap prioritas")
    parser.add_argument(
        "--max-files", type=int, default=80,
        help="Max file per roadmap (default: 80)"
    )
    args = parser.parse_args()

    if args.list:
        print("Roadmap prioritas SIDIX:")
        for r in PRIORITY_ROADMAPS:
            print(f"  - {r}")
        return

    saved: list[Path] = []

    if args.roadmap:
        p = save_roadmap_corpus(args.roadmap)
        saved.append(p)
    elif args.all:
        for roadmap in PRIORITY_ROADMAPS:
            p = save_roadmap_corpus(roadmap)
            saved.append(p)
            time.sleep(1)  # politeness delay between roadmaps
    else:
        # Default: fetch top 5 most important
        for roadmap in PRIORITY_ROADMAPS[:5]:
            p = save_roadmap_corpus(roadmap)
            saved.append(p)
            time.sleep(1)

    if saved:
        create_corpus_index(saved)
        print(f"\n✅ Selesai! {len(saved)} roadmap disimpan ke: {CORPUS_DIR}")
        print("\nLangkah berikutnya:")
        print(f"  1. cd apps\\brain_qa && python -m brain_qa index   (reindex corpus)")
        print(f"  2. Verifikasi di SIDIX UI: tanya tentang Python, Docker, dsb.")


if __name__ == "__main__":
    main()
