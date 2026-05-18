#!/usr/bin/env python3
"""
Baca docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md, urutkan baris checklist menurut
dependensi kasar (G1 → G5 → G4 → G2 → G3), lalu pecah:
  - Batch A (Cursor): 50 tugas
  - Batch B (Claude): 54 tugas (baris 51–104 setelah sort)
  - Batch C (sisa): 10 tugas (105–114)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "PROJEK_BADAR_AL_AMIN_114_LANGKAH.md"
OUT_A = ROOT / "docs" / "PROJEK_BADAR_BATCH_CURSOR_50.md"
OUT_B = ROOT / "docs" / "PROJEK_BADAR_BATCH_CLAUDE_54.md"
OUT_C = ROOT / "docs" / "PROJEK_BADAR_BATCH_SISA_10.md"

# Urutan goal: fondasi percakapan & RAG dulu, ops LLM, kualitas kode, gambar keluar, pemahaman gambar
GOAL_ORDER = {"G1": 0, "G5": 1, "G4": 2, "G2": 3, "G3": 4}
ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*\*\*(G\d)\*\*\s*\|"
)


def parse_rows(text: str) -> list[tuple[int, str, str, str, str]]:
    rows: list[tuple[int, str, str, str, str]] = []
    for line in text.splitlines():
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        num = int(m.group(1))
        surah = m.group(2).strip()
        makna = m.group(3).strip()
        tugas = m.group(4).strip()
        goal = m.group(5).strip()
        rows.append((num, surah, makna, tugas, goal))
    return rows


def sort_key(row: tuple[int, str, str, str, str]) -> tuple[int, int]:
    num, _s, _m, _t, goal = row
    return (GOAL_ORDER.get(goal, 99), num)


def md_table(title: str, rows: list[tuple[int, str, str, str, str]], start_rank: int) -> str:
    lines = [f"# {title}\n", "> Urutan = **dependensi kasar** (bukan DAG formal). Nomor asal surah tetap di kolom *Asal #*.\n\n"]
    lines.append("| # kerja | Asal # | Surah | Makna ringkas | Tugas teknis | Goal |\n")
    lines.append("|---:|---:|--------|---------------|--------------|------|\n")
    for i, (num, surah, makna, tugas, goal) in enumerate(rows, start=start_rank):
        lines.append(
            f"| {i} | {num} | **{surah}** | {makna} | {tugas} | **{goal}** |\n"
        )
    return "".join(lines)


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    rows = parse_rows(text)
    if len(rows) != 114:
        raise SystemExit(f"Expected 114 rows, got {len(rows)}")
    sorted_rows = sorted(rows, key=sort_key)
    batch_a = sorted_rows[:50]
    batch_b = sorted_rows[50:104]
    batch_c = sorted_rows[104:114]
    OUT_A.write_text(
        md_table("Projek Badar — Batch Cursor (50 tugas, urut dependensi)", batch_a, 1),
        encoding="utf-8",
    )
    OUT_B.write_text(
        md_table("Projek Badar — Batch Claude (54 tugas, urut dependensi)", batch_b, 51),
        encoding="utf-8",
    )
    OUT_C.write_text(
        md_table("Projek Badar — Batch sisa (10 tugas, setelah A+B)", batch_c, 105),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_A.name}, {OUT_B.name}, {OUT_C.name}")


if __name__ == "__main__":
    main()
