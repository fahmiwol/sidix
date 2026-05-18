"""
generate_corpus_qa.py — Auto-generate QA pairs dari corpus chunks untuk M5 fine-tune.

Cara kerja:
1. Load semua chunks dari index BM25
2. Filter chunk berkualitas (panjang cukup, bukan header/nav)
3. Generate pertanyaan via template berbasis keyword extraction
4. Simpan ke brain/datasets/corpus_qa.jsonl (format sama dengan qa_pairs.jsonl)

Run:
  cd <WORKSPACE_ROOT>\\apps\\brain_qa
  .venv\\Scripts\\python.exe generate_corpus_qa.py

Output:
  <WORKSPACE_ROOT>\\brain\\datasets\\corpus_qa.jsonl  (auto-generated QA)
  <WORKSPACE_ROOT>\\brain\\datasets\\finetune_sft.jsonl (merged: manual + auto, ChatML format)
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
# Repo root (dinamis, tanpa mengikat path lokal tertentu)
ROOT = Path(__file__).parent.parent.parent
CHUNKS_FILE = Path(__file__).parent / ".data" / "chunks.jsonl"
QA_MANUAL = ROOT / "brain" / "datasets" / "qa_pairs.jsonl"
QA_AUTO = ROOT / "brain" / "datasets" / "corpus_qa.jsonl"
FINETUNE_SFT = ROOT / "brain" / "datasets" / "finetune_sft.jsonl"

# ── System prompt untuk SIDIX SFT ────────────────────────────────────────────
SYSTEM_PROMPT = (
    "Kamu adalah SIDIX, AI multipurpose yang dibangun di atas prinsip kejujuran (sidq), "
    "sitasi (sanad), dan verifikasi (tabayyun). Untuk setiap pertanyaan: "
    "jawab berdasarkan fakta yang bisa diverifikasi, bedakan fakta vs interpretasi vs hipotesis, "
    "sebutkan sumber jika tersedia, dan akui keterbatasan jika tidak tahu. "
    "Gunakan Bahasa Indonesia yang jelas dan ringkas."
)

# ── Template Q&A generator berbasis struktur teks ────────────────────────────

def extract_first_sentence(text: str) -> str:
    """Ambil kalimat pertama yang substantif dari chunk."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    for s in sentences:
        s = s.strip()
        if len(s) > 40 and not s.startswith('#') and not s.startswith('-'):
            return s
    return sentences[0].strip() if sentences else text[:200]


def extract_topic(chunk: dict) -> str:
    """Ekstrak topik dari section_heading atau awal teks."""
    heading = chunk.get("section_heading", "") or chunk.get("filename", "")
    # Bersihkan heading
    heading = re.sub(r'^#+\s*', '', heading).strip()
    if heading and len(heading) > 3:
        return heading
    # Fallback: ambil 5 kata pertama teks
    words = chunk["text"].split()[:5]
    return " ".join(words)


def generate_qa_from_chunk(chunk: dict, idx: int) -> list[dict]:
    """Generate hingga 4 QA pair dari satu chunk dengan template yang beragam."""
    text = chunk["text"].strip()
    if len(text) < 100:
        return []

    topic = extract_topic(chunk)
    first_sent = extract_first_sentence(text)
    source = chunk.get("source_path", chunk.get("filename", "corpus"))
    tl = text.lower()

    pairs = []

    def add(suffix, question, tag):
        pairs.append({
            "id": f"cqa-{idx:04d}{suffix}",
            "question": question,
            "ideal_answer": text[:800].strip(),
            "rubric": f"Jawaban berdasarkan sumber {source} tentang {topic}.",
            "tags": ["auto-generated", tag, source.replace(".md", "")],
            "source": source,
            "auto_generated": True
        })

    # Template 1: Definisi — trigger: kata "adalah/merupakan/artinya"
    if any(kw in tl for kw in ["adalah", "merupakan", "didefinisikan", "artinya", "berarti", "dikenal sebagai"]):
        add("a", f"Apa itu {topic}?", "definition")

    # Template 2: Proses/mekanisme — trigger: kata proses/langkah/cara/pipeline
    if any(kw in tl for kw in ["cara", "langkah", "proses", "tahap", "metode", "pipeline", "sistem", "alur", "flow"]):
        add("b", f"Bagaimana cara kerja {topic}?", "process")

    # Template 3: Relevansi/manfaat — trigger: penting/manfaat/tujuan/fungsi
    if any(kw in tl for kw in ["penting", "relevan", "manfaat", "tujuan", "fungsi", "kegunaan", "berguna"]):
        add("c", f"Mengapa {topic} penting dan apa manfaatnya?", "importance")

    # Template 4: Perbedaan/perbandingan — trigger: vs/dibanding/berbeda/lebih baik
    if any(kw in tl for kw in [" vs ", "dibanding", "berbeda", "lebih baik", "keunggulan", "kelebihan", "kekurangan", "tradeoff"]):
        add("d", f"Apa perbedaan atau perbandingan utama yang dibahas dalam konteks {topic}?", "comparison")

    # Template 5: Contoh/implementasi — trigger: contoh/misalnya/implementasi/penerapan
    if any(kw in tl for kw in ["contoh", "misalnya", "implementasi", "penerapan", "dalam praktik", "use case"]):
        add("e", f"Berikan contoh konkret atau implementasi dari {topic}.", "example")

    # Template 6: Selalu fire — ringkasan/penjelasan utama
    add("f", f"Jelaskan secara ringkas apa yang dibahas tentang {topic}.", "summary")

    # Template 7: Selalu fire — pelajaran/insight
    if len(text) >= 150:
        add("g", f"Apa insight atau poin kunci yang bisa dipelajari dari topik {topic}?", "insight")

    return pairs[:4]  # Maksimal 4 pair per chunk


def to_chatml(qa: dict, system_prompt: str = SYSTEM_PROMPT) -> dict:
    """Konversi QA pair ke format ChatML untuk SFT training."""
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": qa["question"]},
            {"role": "assistant", "content": qa["ideal_answer"]}
        ],
        "source_id": qa["id"],
        "tags": qa.get("tags", [])
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("  SIDIX — Corpus QA Generator (M5 prep)")
    print("=" * 50)

    # 1. Load chunks
    if not CHUNKS_FILE.exists():
        print(f"ERROR: {CHUNKS_FILE} tidak ditemukan.")
        print("Jalankan: python -m brain_qa index")
        sys.exit(1)

    chunks = []
    with open(CHUNKS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"Loaded {len(chunks)} chunks dari index.")

    # 2. Filter chunk berkualitas
    good_chunks = [
        c for c in chunks
        if len(c.get("text", "")) >= 100
        and not c.get("text", "").startswith("```")  # skip pure code blocks
    ]
    print(f"Chunk berkualitas: {len(good_chunks)} (filter panjang < 100 char)")

    # 3. Generate QA pairs
    auto_pairs = []
    seen_ids = set()

    for i, chunk in enumerate(good_chunks):
        pairs = generate_qa_from_chunk(chunk, i)
        for pair in pairs:
            # Deduplicate berdasarkan ID unik (chunk_index + template_suffix)
            # Bukan berdasarkan teks pertanyaan — supaya tiap chunk bisa kontribusi QA sendiri
            if pair["id"] not in seen_ids:
                seen_ids.add(pair["id"])
                auto_pairs.append(pair)

    print(f"Generated {len(auto_pairs)} auto QA pairs dari corpus.")

    # 4. Simpan corpus_qa.jsonl
    QA_AUTO.parent.mkdir(parents=True, exist_ok=True)
    with open(QA_AUTO, "w", encoding="utf-8") as f:
        for pair in auto_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print(f"Disimpan ke: {QA_AUTO}")

    # 5. Load manual QA pairs
    manual_pairs = []
    if QA_MANUAL.exists():
        with open(QA_MANUAL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        manual_pairs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    print(f"Manual QA pairs: {len(manual_pairs)}")

    # 6. Merge + convert ke ChatML format
    all_pairs = manual_pairs + auto_pairs
    print(f"Total dataset (manual + auto): {len(all_pairs)}")

    with open(FINETUNE_SFT, "w", encoding="utf-8") as f:
        for pair in all_pairs:
            f.write(json.dumps(to_chatml(pair), ensure_ascii=False) + "\n")
    print(f"SFT dataset disimpan ke: {FINETUNE_SFT}")

    # 7. Summary
    print()
    print("=" * 50)
    print(f"  SELESAI")
    print(f"  Manual QA     : {len(manual_pairs)} pairs")
    print(f"  Auto QA       : {len(auto_pairs)} pairs")
    print(f"  Total SFT     : {len(all_pairs)} samples")
    target = 500
    pct = len(all_pairs) / target * 100
    print(f"  Progress M5   : {len(all_pairs)}/{target} ({pct:.0f}%)")
    print("=" * 50)

    if len(all_pairs) < target:
        gap = target - len(all_pairs)
        print(f"\nMasih butuh {gap} samples lagi untuk M5.")
        print("Cara menambah:")
        print("  1. Tambah manual QA pairs di brain/datasets/qa_pairs.jsonl")
        print("  2. Publish lebih banyak dokumen ke corpus lalu re-index")
        print("  3. Jalankan script ini lagi setelah corpus bertambah")


if __name__ == "__main__":
    main()
