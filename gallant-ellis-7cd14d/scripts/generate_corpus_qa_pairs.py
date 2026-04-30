# -*- coding: utf-8 -*-
"""
generate_corpus_qa_pairs.py — Generate Q&A pairs dari corpus Markdown (Kimi)

Scan brain/public/*.md, extract headings sebagai questions + content sebagai answers.
Generate simple CoT reasoning traces. Output: JSONL untuk LoRA training.
"""
from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
CORPUS_DIR = ROOT / "brain" / "public"
OUTPUT_DIR = ROOT / "apps" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "Kamu adalah SIDIX, asisten AI dengan pendekatan Islamic Epistemology. "
    "Berpikir langkah demi langkah. Jawaban akurat, bermartabat, sertakan sanad."
)


def _extract_qa_from_md(text: str, source: str) -> list[dict]:
    """Extract Q&A pairs dari Markdown: heading = question, content = answer."""
    records = []
    # Split by headings (## or ###)
    sections = re.split(r"\n##+\s+", text)
    for section in sections[1:]:  # Skip first (title)
        lines = section.strip().split("\n")
        if not lines:
            continue
        heading = lines[0].strip()
        # Skip non-informative headings
        if any(x in heading.lower() for x in ["daftar isi", "table of contents", "referensi", "catatan"]):
            continue
        content = "\n".join(lines[1:]).strip()
        if len(content) < 30:
            continue

        # Generate simple reasoning
        reasoning = (
            f"User bertanya tentang '{heading}'. "
            f"Saya cari informasi di corpus SIDIX dan menemukan penjelasan. "
            f"Berdasarkan sumber '{source}', jawabannya adalah: {content[:150]}..."
        )

        record = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": heading},
                {
                    "role": "assistant",
                    "content": f"<think>\n{reasoning}\n</think>\n\n{content[:500]}",
                },
            ],
            "metadata": {
                "source": f"corpus:{source}",
                "category": "corpus_knowledge",
                "method": "heading_extraction",
            },
        }
        records.append(record)
    return records


def generate_corpus_qa() -> Path:
    """Generate Q&A pairs dari semua corpus .md files."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"corpus_qa_pairs_{date_str}.jsonl"

    all_records = []
    md_files = list(CORPUS_DIR.rglob("*.md"))

    for md_file in md_files:
        try:
            text = md_file.read_text(encoding="utf-8")
            rel_path = md_file.relative_to(CORPUS_DIR).as_posix()
            records = _extract_qa_from_md(text, rel_path)
            all_records.extend(records)
        except Exception as e:
            print(f"[WARN] Skip {md_file}: {e}")

    # Shuffle
    random.seed(42)
    random.shuffle(all_records)

    # Write
    with output_path.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[OK] Generated {len(all_records)} Q&A pairs from {len(md_files)} files -> {output_path}")
    return output_path


if __name__ == "__main__":
    print("=== Corpus Q&A Generator ===\n")
    output = generate_corpus_qa()
    print(f"\n[OK] Done: {output}")
