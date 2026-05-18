#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dataset_id_sea_collector.py — Sprint Fase B Prep

Harian collect open-data Indonesia/SEA untuk fine-tune SIDIX.
Output JSONL instruction-tuning format, siap pakai SFT/LoRA.

Path Fase B (research note 310):
- Sekarang: pakai open-source as-is (Qwen, FLUX, dll)
- 3-6 bulan ke depan: fine-tune dengan dataset ID/SEA ini
  -> SIDIX-Image v1, SIDIX-Voice v1, SIDIX-Text LoRA tier-2

Sumber (semua public domain / CC BY-SA / open):
1. Wikipedia ID — featured articles + recent changes (CC BY-SA 4.0)
2. UMKM corpus — Indonesian business knowledge dari Wikipedia kategori
3. Brand lokal — list brand Indonesia + deskripsi
4. Indonesia idioms/peribahasa — from Wikipedia + open dictionaries

Output:
    dataset/id_sea/<YYYY-MM-DD>/<source>.jsonl
    Format: {"instruction": "...", "input": "...", "output": "..."}

Cara pakai:
    python scripts/dataset_id_sea_collector.py             # all sources
    python scripts/dataset_id_sea_collector.py --source wikipedia_id
    python scripts/dataset_id_sea_collector.py --max 20    # limit per source

Cron (run harian jam 02:00 VPS):
    0 2 * * * cd /opt/sidix && python3 scripts/dataset_id_sea_collector.py >> /var/log/sidix/dataset_collector.log 2>&1

Author: Fahmi Ghani — Mighan Lab / Tiranyx
License: MIT
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

try:
    import requests
except ImportError:
    print("[ERROR] Install requests: pip install requests")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "dataset" / "id_sea"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

UA = "SIDIX-DatasetCollector/1.0 (https://sidixlab.com; contact@sidixlab.com)"
WIKI_ID_API = "https://id.wikipedia.org/w/api.php"

# Wikipedia categories untuk UMKM/bisnis ID
UMKM_CATEGORIES = [
    "Kategori:Perusahaan_Indonesia",
    "Kategori:Merek_Indonesia",
    "Kategori:Bisnis_Indonesia",
    "Kategori:Wirausaha_Indonesia",
]

# Featured articles seed (artikel pilihan / unggulan)
FEATURED_SEED = [
    "Indonesia",
    "Bahasa_Indonesia",
    "Sejarah_Indonesia",
    "Sastra_Indonesia",
    "Kebudayaan_Indonesia",
    "Pancasila",
    "Garuda_Pancasila",
    "Borobudur",
    "Wayang",
    "Batik",
    "Gamelan",
    "Rendang",
    "Soekarno",
    "Mohammad_Hatta",
    "Sultan_Hamengkubuwana_X",
]

# Brand lokal Indonesia (kategori bisnis populer)
BRAND_SEED = [
    "Gojek",
    "Tokopedia",
    "Traveloka",
    "Bukalapak",
    "Shopee_Indonesia",
    "Indomie",
    "Aqua_(perusahaan)",
    "Indofood",
    "Mayora_Indah",
    "Kopi_Kapal_Api",
    "Sariwangi",
    "Garuda_Indonesia",
    "Telkom_Indonesia",
    "Bank_Mandiri",
    "Bank_Central_Asia",
]


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _out_dir() -> Path:
    d = DATASET_DIR / _today()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _wiki_extract(title: str, sentences: int = 8) -> Optional[dict]:
    """Fetch plain-text extract dari Wikipedia ID untuk satu artikel."""
    try:
        r = requests.get(
            WIKI_ID_API,
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exsentences": sentences,
                "explaintext": 1,
                "redirects": 1,
                "titles": title,
            },
            headers={"User-Agent": UA},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            extract = (page.get("extract") or "").strip()
            real_title = page.get("title", title)
            if extract and len(extract) > 100:
                return {"title": real_title, "extract": extract}
    except Exception as e:
        print(f"[wiki] {title} fail: {e}")
    return None


def _wiki_category_members(category: str, limit: int = 30) -> list[str]:
    """List artikel anggota dari satu kategori Wikipedia ID."""
    try:
        r = requests.get(
            WIKI_ID_API,
            params={
                "action": "query",
                "format": "json",
                "list": "categorymembers",
                "cmtitle": category,
                "cmlimit": limit,
                "cmtype": "page",
            },
            headers={"User-Agent": UA},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        return [
            m["title"].replace(" ", "_")
            for m in data.get("query", {}).get("categorymembers", [])
            if m.get("ns") == 0
        ]
    except Exception as e:
        print(f"[wiki cat] {category} fail: {e}")
        return []


def _to_instruction_pair(title: str, extract: str, theme: str) -> dict:
    """Convert wiki extract → instruction-tuning pair.

    SIDIX akan dilatih untuk:
    - Jawab pertanyaan tentang topik Indonesia dengan akurat
    - Pakai bahasa Indonesia natural
    - Konteks budaya / bisnis lokal kuat
    """
    nice_title = title.replace("_", " ")
    instruction_templates = {
        "general": f"Jelaskan tentang {nice_title} dalam Bahasa Indonesia yang jelas.",
        "umkm": f"Apa itu {nice_title}? Berikan deskripsi singkat sebagai konteks bisnis Indonesia.",
        "brand": f"Ceritakan tentang brand {nice_title} — sejarah singkat dan kategorinya di pasar Indonesia.",
        "culture": f"Apa makna budaya dari {nice_title}? Jelaskan dalam konteks Indonesia.",
    }
    instruction = instruction_templates.get(theme, instruction_templates["general"])

    return {
        "instruction": instruction,
        "input": "",
        "output": extract,
        "source": f"wikipedia_id:{title}",
        "theme": theme,
        "lang": "id",
        "license": "CC BY-SA 4.0",
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def collect_wikipedia_id(max_per_seed: int = 15) -> list[dict]:
    """Collect from Wikipedia ID featured + culture seeds."""
    print(f"[wikipedia_id] start (max {max_per_seed} per seed)")
    pairs = []
    seeds = FEATURED_SEED[:max_per_seed]
    for i, title in enumerate(seeds, 1):
        ext = _wiki_extract(title, sentences=10)
        if ext:
            theme = "culture" if any(
                k in title.lower()
                for k in ["batik", "wayang", "gamelan", "rendang", "borobudur", "budaya"]
            ) else "general"
            pairs.append(_to_instruction_pair(ext["title"], ext["extract"], theme))
        if i % 5 == 0:
            print(f"[wikipedia_id] {i}/{len(seeds)}")
        time.sleep(0.4)  # be gentle to Wikipedia
    print(f"[wikipedia_id] done: {len(pairs)} pairs")
    return pairs


def collect_umkm(max_total: int = 30) -> list[dict]:
    """Collect from Wikipedia ID kategori bisnis/UMKM."""
    print(f"[umkm] start (max {max_total} total)")
    pairs = []
    seen = set()

    for cat in UMKM_CATEGORIES:
        if len(pairs) >= max_total:
            break
        members = _wiki_category_members(cat, limit=15)
        for title in members:
            if len(pairs) >= max_total:
                break
            if title in seen:
                continue
            seen.add(title)
            ext = _wiki_extract(title, sentences=6)
            if ext:
                pairs.append(_to_instruction_pair(ext["title"], ext["extract"], "umkm"))
            time.sleep(0.4)

    print(f"[umkm] done: {len(pairs)} pairs")
    return pairs


def collect_brand_lokal(max_total: int = 15) -> list[dict]:
    """Collect from brand seed list."""
    print(f"[brand_lokal] start (max {max_total})")
    pairs = []
    for title in BRAND_SEED[:max_total]:
        ext = _wiki_extract(title, sentences=8)
        if ext:
            pairs.append(_to_instruction_pair(ext["title"], ext["extract"], "brand"))
        time.sleep(0.4)
    print(f"[brand_lokal] done: {len(pairs)} pairs")
    return pairs


def collect_idioms() -> list[dict]:
    """Collect peribahasa & idiom Indonesia (from Wikipedia ID).

    Phase 1 = simpler approach: fetch artikel daftar peribahasa,
    parse extract sebagai context untuk SIDIX learn linguistic patterns.
    """
    print(f"[idioms] start")
    pairs = []
    targets = ["Daftar_peribahasa_Indonesia", "Peribahasa", "Idiom"]
    for title in targets:
        ext = _wiki_extract(title, sentences=10)
        if ext:
            pair = _to_instruction_pair(ext["title"], ext["extract"], "general")
            pair["instruction"] = (
                f"Jelaskan apa itu {ext['title'].replace('_', ' ').lower()} "
                f"dan berikan contoh pemakaiannya."
            )
            pairs.append(pair)
        time.sleep(0.4)
    print(f"[idioms] done: {len(pairs)} pairs")
    return pairs


def write_jsonl(pairs: Iterable[dict], path: Path) -> int:
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
            n += 1
    return n


SOURCES = {
    "wikipedia_id": collect_wikipedia_id,
    "umkm": collect_umkm,
    "brand_lokal": collect_brand_lokal,
    "idioms": collect_idioms,
}


def main():
    parser = argparse.ArgumentParser(description="Collect ID/SEA dataset for SIDIX fine-tune")
    parser.add_argument("--source", choices=list(SOURCES) + ["all"], default="all")
    parser.add_argument("--max", type=int, default=None,
                        help="override max pairs per source (default: source-specific)")
    args = parser.parse_args()

    out = _out_dir()
    print(f"[collector] output dir: {out}")

    sources_to_run = list(SOURCES) if args.source == "all" else [args.source]
    summary = {}

    for src in sources_to_run:
        fn = SOURCES[src]
        try:
            pairs = fn(args.max) if args.max and src != "idioms" else fn()
        except TypeError:
            pairs = fn()
        path = out / f"{src}.jsonl"
        n = write_jsonl(pairs, path)
        summary[src] = n
        print(f"[collector] {src} -> {path} ({n} pairs)")

    # Index file with run metadata
    index_path = out / "_index.json"
    index_path.write_text(
        json.dumps(
            {
                "date": _today(),
                "sources": summary,
                "total_pairs": sum(summary.values()),
                "format": "instruction-tuning",
                "phase": "Fase B prep — research note 310",
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    total = sum(summary.values())
    print(f"\n[collector] DONE: {total} pairs across {len(summary)} sources")
    print(f"[collector] index: {index_path}")


if __name__ == "__main__":
    main()
