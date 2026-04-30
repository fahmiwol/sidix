# -*- coding: utf-8 -*-
"""
upgrade_dataset_quality.py — Upgrade corpus-derived reasoning traces (Kimi)

Replace simple "Saya cari di corpus..." reasoning with richer CoT traces
that demonstrate actual ReAct thinking: observation, planning, decision-making.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
INPUT_PATH = ROOT / "apps" / "output" / "lora_training_dataset_v1_20260425.jsonl"
OUTPUT_PATH = ROOT / "apps" / "output" / "lora_training_dataset_v2_20260425.jsonl"

# Rich reasoning templates per category
_RICH_REASONING: dict[str, callable] = {
    "islamic": lambda q, a, src: (
        f"Pertanyaan ini tentang topik Islam: '{q[:60]}'. "
        f"Saya evaluasi: (1) Apakah ini masalah aqidah, fiqh, atau sejarah? "
        f"(2) Butuh sanad dari corpus atau bisa jawab langsung? "
        f"Karena topik {src}, saya prioritaskan search_corpus untuk sumber sahih. "
        f"Setelah menemukan kutipan relevan, saya label epistemik [FAKTA] "
        f"dan sertakan sanad. Jawaban: {a[:120]}"
    ),
    "coding": lambda q, a, src: (
        f"Pertanyaan teknis: '{q[:60]}'. "
        f"Saya analisis: (1) Apakah ini bug, konsep, atau arsitektur? "
        f"(2) Butuh contoh kode atau penjelasan konsep? "
        f"Saya pilih pendekatan praktis dengan contoh konkret. "
        f"Verifikasi: apakah solusi ini aman dan efisien? "
        f"Jawaban: {a[:120]}"
    ),
    "math": lambda q, a, src: (
        f"Ada komponen matematika: '{q[:60]}'. "
        f"Saya identifikasi variabel dan rumus yang relevan. "
        f"Gunakan calculator untuk verifikasi akurasi. "
        f"Langkah per langkah: {a[:120]}"
    ),
    "ai_ml": lambda q, a, src: (
        f"Pertanyaan AI/ML: '{q[:60]}'. "
        f"Saya tentukan: konsep dasar atau implementasi praktis? "
        f"Kalau konsep → jelaskan dengan analogi. "
        f"Kalau praktis → berikan pseudocode + caveats. "
        f"Jawaban: {a[:120]}"
    ),
    "creative": lambda q, a, src: (
        f"User minta konten kreatif: '{q[:60]}'. "
        f"Saya brainstorm: audience, tone, format yang cocok. "
        f"Evaluasi ide berdasarkan originality dan relevance. "
        f"Pilih angle terbaik dan kembangkan. "
        f"Hasil: {a[:120]}"
    ),
    "epistemic": lambda q, a, src: (
        f"Pertanyaan memerlukan label epistemik: '{q[:60]}'. "
        f"Saya evaluasi tingkat bukti: mutawatir, ahad, atau spekulasi? "
        f"Label dengan [FAKTA]/[OPINI]/[SPEKULASI] sesuai evidence. "
        f"Tambahkan disclaimer kalau data terbatas. "
        f"Kesimpulan: {a[:120]}"
    ),
    "general": lambda q, a, src: (
        f"Pertanyaan umum: '{q[:60]}'. "
        f"Saya tentukan domain: sains, sejarah, teknologi, atau budaya? "
        f"Cari di corpus kalau topik SIDIX-relevan. "
        f"Kalau tidak, jawab dari pengetahuan umum dengan label [FAKTA]. "
        f"Jawaban: {a[:120]}"
    ),
}


def _detect_category(query: str, source: str) -> str:
    q = query.lower()
    s = source.lower()
    if any(x in q+s for x in ["islam", "aqidah", "fiqh", "syariah", "quran", "hadis"]):
        return "islamic"
    if any(x in q+s for x in ["code", "program", "debug", "python", "api", "function"]):
        return "coding"
    if any(x in q+s for x in ["math", "hitung", "kalkulasi", "persamaan", "bilangan"]):
        return "math"
    if any(x in q+s for x in ["ai", "machine learning", "llm", "model", "neural"]):
        return "ai_ml"
    if any(x in q+s for x in ["creative", "design", "poster", "copy", "content"]):
        return "creative"
    if any(x in q+s for x in ["epistemic", "fakta", "opini", "spekulasi", "bukti"]):
        return "epistemic"
    return "general"


def upgrade_record(record: dict) -> dict:
    """Upgrade corpus-derived record with richer reasoning."""
    meta = record.get("metadata", {})
    source = meta.get("source", "")

    if not source.startswith("corpus:"):
        return record  # Only upgrade corpus-derived

    messages = record["messages"]
    query = messages[1]["content"] if len(messages) > 1 else ""
    answer = messages[2]["content"] if len(messages) > 2 else ""

    # Extract answer text (after </think> if present)
    answer_clean = answer
    if "</think>" in answer:
        answer_clean = answer.split("</think>")[-1].strip()

    category = _detect_category(query, source)
    template_fn = _RICH_REASONING.get(category, _RICH_REASONING["general"])
    rich_reasoning = template_fn(query, answer_clean, source.replace("corpus:", ""))

    # Rebuild assistant content
    new_answer = f"<think>\n{rich_reasoning}\n</think>\n\n{answer_clean[:500]}"
    messages[2]["content"] = new_answer

    # Update metadata
    meta["upgraded"] = True
    meta["upgrade_method"] = "rich_cot_v2"
    meta["category_detected"] = category

    return record


def upgrade_dataset() -> Path:
    """Upgrade all corpus-derived records in dataset."""
    records = []
    with INPUT_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    upgraded_count = 0
    for i, record in enumerate(records):
        original = json.dumps(record)
        upgraded = upgrade_record(record)
        if json.dumps(upgraded) != original:
            upgraded_count += 1
            records[i] = upgraded

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[OK] Upgraded {upgraded_count}/{len(records)} records -> {OUTPUT_PATH}")
    print(f"    Input: {INPUT_PATH.name}")
    print(f"    Output: {OUTPUT_PATH.name}")
    return OUTPUT_PATH


if __name__ == "__main__":
    print("=== Dataset Quality Upgrade ===\n")
    upgrade_dataset()
    print("\n[OK] Done")
