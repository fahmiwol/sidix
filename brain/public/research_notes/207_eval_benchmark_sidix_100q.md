# 207 — SIDIX Eval Benchmark: 5 → 100 Pertanyaan (Phase 0)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-25  
**Tag**: [IMPL][EVAL][PHASE0]  
**Sanad**: Sprint 10 Phase 0, MASTER_ROADMAP_2026-2027.md §Eval

---

## Apa

`tests/eval_benchmark.jsonl` diperluas dari 5 → **100 pertanyaan** terstruktur sebagai baseline evaluasi SIDIX. File ini digunakan oleh `brain_qa/eval_harness.py` untuk mengukur kualitas model sebelum/sesudah LoRA training.

---

## Kenapa

Tanpa benchmark yang representatif, tidak ada cara untuk:
- Mengukur apakah DPO/LoRA training benar-benar meningkatkan kualitas
- Mendeteksi regression setelah update model
- Membandingkan SIDIX dengan versi sebelumnya (baseline tracking)

5 pertanyaan terlalu sedikit — tidak merepresentasikan distribusi topik SIDIX yang sesungguhnya.

---

## Struktur 100 Pertanyaan

| Kategori | Count | Tujuan |
|---|---|---|
| `coding_concept` | 8 | Big O, stack/queue, recursion, design patterns |
| `coding_practical` | 7 | Python fungsi, SQL queries, implementasi |
| `coding_web` | 4 | REST vs GraphQL, SQL JOIN, Docker, async/await |
| `coding_debug` | 3 | Error diagnosis, NullPointerException, == vs equals |
| `coding_system` | 3 | Monolith vs microservices, CAP theorem, JWT |
| `coding_architecture` | 3 | EDA, CQRS, horizontal vs vertical scaling |
| `islamic_aqidah` | 1 | Aqidah Islam |
| `islamic_fiqh` | 3 | Riba, sholat jenazah, zakat maal |
| `islamic_sejarah` | 2 | Khalifah pertama, Perang Badar |
| `islamic_concept` | 4 | Tawakal, ijma', hadits shahih/dhaif, maqasid syariah |
| `ai_ml_concept` | 5 | ML vs DL, overfitting, transformer, gradient descent, LoRA vs fine-tuning |
| `ai_practical` | 5 | RAG, prompt engineering, hallucination, RLHF, LoRA |
| `ai_sidix_specific` | 2 | Identitas SIDIX, epistemic labels |
| `general_science` | 4 | Fotosintesis, DNA/RNA, langit biru, Newton III |
| `general_knowledge` | 10 | Jumlah negara, inflasi, Einstein, blockchain, demokrasi, geopolitik, dll |
| `general_creative` | 4 | Konten YouTube, tagline, analogi API, essay |
| `math_basic` | 1 | 2+2 |
| `math_advanced` | 3 | Integral, Bayes, mean/median/modus |
| `epistemic_opini` | 1 | AI menggantikan pekerja |
| `epistemic_spekulasi` | 1 | Ekonomi Indonesia 10 tahun |
| `epistemic_unknown` | 1 | Mesin waktu |
| `epistemic_test` | 5 | Vaksin, bumi datar, saran medis, setelah mati, presiden AS |
| `epistemic_adversarial` | 3 | Identitas SIDIX, request hack, jailbreak |
| `epistemic_meta` | 1 | Meta-akurasi SIDIX |
| `multi_language_english` | 5 | Supervised vs unsupervised, recursion, SOLID, TCP/UDP, mutable/immutable, DI |
| `multi_language_arabic` | 1 | Arkan Islam |
| `multi_language_javanese` | 1 | Revolusi Industri 4.0 |
| `indonesia_specific` | 3 | Pancasila, pemilu, fintech OJK |

---

## Format per Item

```json
{
  "id": "B001",
  "category": "islamic_aqidah",
  "query": "...",
  "expected_type": "fakta|opini|spekulasi|unknown|kode|kreatif|refusal",
  "expected_labels": ["[FAKTA]"],
  "expected_sources": true,
  "reference_answer": "...",
  "persona": "AYMAN|UTZ|ABOO|OOMAR|ALEY"
}
```

Field baru dibanding format lama:
- `id`: unique identifier (`B001`–`B100`)
- `category`: slug kategori
- `persona`: persona SIDIX yang paling relevan (untuk future persona-specific eval)

---

## Baseline Scores (Mock = reference_answer sebagai response)

```
total              : 100
composite_score    : 0.636
epistemic_accuracy : 0.13   ← rendah karena banyak ref answer tidak ber-label eksplisit
source_coverage    : 0.92
avg_relevance      : 1.0    ← sempurna karena mock = reference
honesty_rate       : 1.0
```

Baseline `composite_score = 0.636` dengan mock. Target setelah LoRA v1: ≥0.75.

---

## Cara Kerja eval_harness.py

```python
from brain_qa.eval_harness import run_benchmark
from pathlib import Path

# Mode mock (offline, tidak butuh model)
result = run_benchmark(benchmark_path=Path("tests/eval_benchmark.jsonl"))

# Mode live (jalankan vs SIDIX)
def ask_sidix(query):
    import httpx
    r = httpx.post("http://localhost:8765/agent/chat", json={"message": query}, timeout=90)
    return r.json().get("response", "")

result = run_benchmark(generator_fn=ask_sidix)
print(result["composite_score"])
```

---

## Metrik Composite Score

```
composite = epistemic_accuracy * 0.40
          + avg_relevance       * 0.30
          + source_coverage     * 0.20
          + honesty_rate        * 0.10
```

- **Epistemic accuracy** (40%): apakah label [FAKTA/OPINI/SPEKULASI/TIDAK TAHU] tepat
- **Relevance** (30%): ROUGE-L score vs reference answer
- **Source coverage** (20%): apakah jawaban menyertakan sumber saat diperlukan
- **Honesty** (10%): saat expected_type=unknown, apakah menyatakan tidak tahu

---

## Keterbatasan

1. **Reference answers subjektif** — ditulis manual, bukan dari ground-truth corpus
2. **ROUGE-L kasar** — tidak mengukur semantic similarity, hanya kata yang sama
3. **Kode tidak dievaluasi secara functional** — hanya teks matching
4. **100 Q belum representatif dialect** — lebih banyak Bahasa Indonesia formal
5. **Benchmark contamination risk** — jika questions masuk corpus training, skor inflate

---

## Roadmap Benchmark

- [x] Phase 0: 5 → 100 pertanyaan (sekarang)
- [ ] Phase 1: 100 → 500 pertanyaan dengan domain weighting
- [ ] Phase 2: Semantic similarity scorer (cosine via embedding)
- [ ] Phase 3: Live eval vs SIDIX setelah setiap LoRA update
- [ ] Phase 4: Human-evaluated subset (50 Q) sebagai gold standard
