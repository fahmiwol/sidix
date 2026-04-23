"""
harvest_all_research_notes.py — Backfill 144+ Notes ke Training Pairs

Growth-Hack #4 (note 145): SIDIX punya 144+ research notes existing
yang belum diekstrak jadi training pairs. Estimasi 5-8 pair per note ×
144 = ~1000 pair instant — langsung lulus LoRA threshold (500).

Usage:
  python3 apps/brain_qa/scripts/harvest_all_research_notes.py [--dry-run]

Output:
  apps/brain_qa/.data/training_generated/harvest_research_notes_<date>.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]   # repo root (dinamis)
sys.path.insert(0, str(ROOT / "apps" / "brain_qa"))

from brain_qa.skill_builder import extract_lessons_from_note
from brain_qa.paths import default_data_dir


SYS_PROMPT = (
    "Kamu SIDIX — AI dari Mighan Lab dengan fondasi epistemologi Islam. "
    "Jawab dengan jujur, runut, berbasis sumber, Bahasa Indonesia. "
    "WAJIB pakai label 4-epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Tidak menulis file output")
    parser.add_argument("--limit", type=int, default=0, help="Limit jumlah note (0 = semua)")
    args = parser.parse_args()

    notes_dir = ROOT / "brain" / "public" / "research_notes"
    if not notes_dir.exists():
        print(f"[harvest] notes dir not found: {notes_dir}")
        return

    note_files = sorted(notes_dir.glob("*.md"))
    if args.limit > 0:
        note_files = note_files[: args.limit]
    print(f"[harvest] found {len(note_files)} note files")

    out_dir = default_data_dir() / "training_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = out_dir / f"harvest_research_notes_{today}.jsonl"

    total_pairs = 0
    note_count = 0
    skipped_count = 0
    errors: list[str] = []

    out_handle = None if args.dry_run else out_path.open("a", encoding="utf-8")

    for nf in note_files:
        try:
            result = extract_lessons_from_note(str(nf))
            if not result.get("ok"):
                skipped_count += 1
                continue
            pairs = result.get("training_pairs", [])
            title = result.get("title", nf.stem)
            if not pairs:
                skipped_count += 1
                continue

            note_count += 1
            for i, pair in enumerate(pairs):
                q = pair["q"]
                a = pair["a"]
                if len(a) < 80:
                    continue
                training_pair = {
                    "messages": [
                        {"role": "system",    "content": SYS_PROMPT},
                        {"role": "user",      "content": q},
                        {"role": "assistant", "content": a},
                    ],
                    "domain":        _infer_domain(nf.name),
                    "persona":       "MIGHAN",
                    "source":        f"backfill:research_notes:{nf.name}",
                    "template_type": "extracted_section",
                    "pair_id":       f"bk_{nf.stem}_{i}",
                    "title":         title,
                }
                if out_handle:
                    out_handle.write(json.dumps(training_pair, ensure_ascii=False) + "\n")
                total_pairs += 1
        except Exception as e:
            errors.append(f"{nf.name}: {e}")
            skipped_count += 1

    if out_handle:
        out_handle.close()

    print(f"\n=== HARVEST DONE ===")
    print(f"Notes processed:   {note_count}")
    print(f"Notes skipped:     {skipped_count}")
    print(f"Total pairs:       {total_pairs}")
    print(f"Output file:       {out_path if not args.dry_run else '(dry-run)'}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  - {e}")


def _infer_domain(filename: str) -> str:
    """Heuristik infer domain dari nama file."""
    f = filename.lower()
    if "coding" in f or "python" in f or "javascript" in f or "fullstack" in f:
        return "coding"
    if "islamic" in f or "ihos" in f or "quran" in f or "hafidz" in f or "sanad" in f:
        return "islamic_epistemology"
    if "ai" in f or "llm" in f or "lora" in f or "agent" in f:
        return "ai_engineering"
    if "design" in f or "image" in f or "visual" in f:
        return "design"
    if "audio" in f or "tts" in f or "asr" in f:
        return "audio_ai"
    if "research" in f or "method" in f or "epistem" in f:
        return "research_methodology"
    if "growth" in f or "manifesto" in f or "roadmap" in f:
        return "strategy"
    if "sidix" in f or "mighan" in f:
        return "sidix_meta"
    return "general"


if __name__ == "__main__":
    main()
