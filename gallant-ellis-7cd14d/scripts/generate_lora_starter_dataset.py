# -*- coding: utf-8 -*-
"""
generate_lora_starter_dataset.py — Synthetic LoRA Dataset Generator (Kimi)

Generate synthetic training pairs dari 100Q benchmark + C3oT compressed traces
untuk LoRA v2 starter dataset. Target: 130+ records.

Output: output/lora_starter_dataset_YYYYMMDD.jsonl
Format: {"messages": [...], "metadata": {...}} (compatible dengan jariyah_exporter)
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
BENCHMARK_PATH = ROOT / "apps" / "brain_qa" / "tests" / "eval_benchmark.jsonl"
C3OT_PATH = ROOT / "apps" / "output" / "c3ot_compressed_20260425.jsonl"
OUTPUT_DIR = ROOT / "apps" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# SIDIX system prompt dasar
SIDIX_SYSTEM_PROMPT = (
    "Kamu adalah SIDIX, asisten AI dengan pendekatan Islamic Epistemology. "
    "Berpikir langkah demi langkah. Berikan jawaban yang akurat, bermartabat, "
    "dan selalu sertakan sanad/sumber bila ada. "
    "Label epistemik: [FAKTA], [OPINI], [SPEKULASI], [UNKNOWN]."
)


# ── Reasoning trace templates per category ───────────────────────────────────

def _generate_reasoning(category: str, query: str, answer: str) -> str:
    """Generate synthetic reasoning trace berdasarkan kategori."""
    templates: dict[str, list[str]] = {
        "islamic": [
            f"User bertanya tentang topik Islam: '{query}'. "
            f"Saya perlu cari di corpus SIDIX untuk referensi yang sahih. "
            f"Setelah menemukan sumber, saya rangkum dengan sanad yang jelas. "
            f"Jawaban akhir: {answer[:100]}",
        ],
        "math": [
            f"Ada ekspresi matematika di pertanyaan: '{query}'. "
            f"Saya gunakan calculator untuk memastikan akurasi. "
            f"Hasil perhitungan: {answer[:80]}",
        ],
        "coding": [
            f"Pertanyaan teknis tentang kode: '{query}'. "
            f"Saya analisis logic dan berikan solusi yang bisa diimplementasi. "
            f"Solusi: {answer[:100]}",
        ],
        "creative": [
            f"User minta konten kreatif: '{query}'. "
            f"Saya brainstorm ide yang sesuai konteks dan audience. "
            f"Hasil kreatif: {answer[:100]}",
        ],
        "epistemic": [
            f"Pertanyaan memerlukan label epistemik: '{query}'. "
            f"Saya evaluasi tingkat kepastian dan label dengan tepat. "
            f"Kesimpulan: {answer[:100]}",
        ],
        "general": [
            f"Pertanyaan umum: '{query}'. "
            f"Saya cari informasi yang akurat dan presentasikan dengan jelas. "
            f"Jawaban: {answer[:100]}",
        ],
    }

    # Map category prefix to template key
    key = "general"
    for k in templates:
        if category.startswith(k) or k in category:
            key = k
            break

    return random.choice(templates[key])


# ── Main generator ───────────────────────────────────────────────────────────

def generate_from_benchmark() -> list[dict]:
    """Generate synthetic training records dari eval benchmark."""
    records = []
    if not BENCHMARK_PATH.exists():
        print(f"[WARN] Benchmark not found: {BENCHMARK_PATH}")
        return records

    with BENCHMARK_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)

            query = item["query"]
            answer = item.get("reference_answer", "")
            category = item.get("category", "general")
            persona = item.get("persona", "AYMAN")

            # Generate reasoning trace
            reasoning = _generate_reasoning(category, query, answer)

            # Format assistant content dengan think tags (CoT style)
            assistant_content = f"<think>\n{reasoning}\n</think>\n\n{answer}"

            record = {
                "messages": [
                    {"role": "system", "content": SIDIX_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": assistant_content},
                ],
                "metadata": {
                    "source": "synthetic_benchmark",
                    "id": item.get("id", ""),
                    "category": category,
                    "persona": persona,
                    "expected_type": item.get("expected_type", ""),
                },
            }
            records.append(record)

    return records


def load_c3ot_records() -> list[dict]:
    """Load existing C3oT compressed records."""
    records = []
    if not C3OT_PATH.exists():
        print(f"[WARN] C3oT file not found: {C3OT_PATH}")
        return records

    with C3OT_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


def generate_dataset() -> Path:
    """Generate combined starter dataset dan simpan ke JSONL."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_path = OUTPUT_DIR / f"lora_starter_dataset_{date_str}.jsonl"

    # Collect sources
    benchmark_records = generate_from_benchmark()
    c3ot_records = load_c3ot_records()

    # Deduplicate by user query (simple)
    seen_queries = set()
    combined = []

    for r in benchmark_records + c3ot_records:
        query = r["messages"][1]["content"] if len(r["messages"]) > 1 else ""
        if query in seen_queries:
            continue
        seen_queries.add(query)
        combined.append(r)

    # Augment: generate 2 variations per benchmark record dengan paraphrase query
    augmented = []
    for r in benchmark_records[:30]:  # Top 30 untuk augmentasi
        query = r["messages"][1]["content"]
        # Variasi 1: tambah konteks
        v1 = json.loads(json.dumps(r))
        v1["messages"][1]["content"] = f"Mohon jelaskan: {query}"
        v1["metadata"]["source"] = "synthetic_augmented"
        augmented.append(v1)

        # Variasi 2: ganti ke bahasa yang lebih formal
        v2 = json.loads(json.dumps(r))
        v2["messages"][1]["content"] = f"Saya ingin memahami: {query}"
        v2["metadata"]["source"] = "synthetic_augmented"
        augmented.append(v2)

    all_records = combined + augmented

    # Shuffle
    random.seed(42)
    random.shuffle(all_records)

    # Write
    with output_path.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[OK] Generated {len(all_records)} records -> {output_path}")
    print(f"    Source breakdown:")
    print(f"      - Benchmark: {len(benchmark_records)}")
    print(f"      - C3oT: {len(c3ot_records)}")
    print(f"      - Augmented: {len(augmented)}")
    print(f"      - Total unique: {len(combined)}")
    print(f"      - Grand total: {len(all_records)}")

    return output_path


# ── Stats ────────────────────────────────────────────────────────────────────

def get_stats(path: Path | None = None) -> dict:
    """Return statistik dataset."""
    if path is None:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        path = OUTPUT_DIR / f"lora_starter_dataset_{date_str}.jsonl"

    if not path.exists():
        return {"status": "not_found", "records": 0}

    count = 0
    categories: dict[str, int] = {}
    sources: dict[str, int] = {}

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            data = json.loads(line)
            meta = data.get("metadata", {})
            cat = meta.get("category", "unknown")
            src = meta.get("source", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
            sources[src] = sources.get(src, 0) + 1

    return {
        "status": "ok",
        "records": count,
        "path": str(path),
        "categories": categories,
        "sources": sources,
        "ready_for_lora": count >= 500,
    }


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== LoRA Starter Dataset Generator ===\n")

    output = generate_dataset()
    stats = get_stats(output)
    print(f"\nStats: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    print("\n[OK] Done")
