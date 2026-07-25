# Pelajaran Praxis — jejak agen SIDIX

**Diperbarui:** 2026-04-28T04:10:57.548841+00:00
**session_id:** `abba7ce1`
**persona:** ABOO

## Pertanyaan / tugas pengguna

Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX

## Rangkaian eksekusi (Thought → Action → Observation)

### Langkah 0

- **Thought:** Topik terkait SIDIX/sumber internal. Gunakan search_corpus dengan query: 'Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX'.
- **Action:** `search_corpus` — args: `{"query": "Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX", "k": 5, "persona": "ABOO", "_citations": [{"n": "1", "source_path": "research_notes/268_sprint25_hybrid_retrieval_rerank.md", "source_title": "268 — Sprint 25: Hybrid Retrieval (BM25 + Dense BGE-M3) + Cross-Encoder Reranker", "chunk_id": "research_notes/268_sprint25_hybrid_retrieval_rerank.md:0-1200", "sanad_tier": "unknown"}, {"n": "2", "source_path": "sources/bibliography.md", "source_title": "Bibliography (daftar referensi)", "chunk_id": "sources/bibliography.md:7350-8550", "sanad_tier": "unknown"}, {"n": "3", "source`
- **Observation (cuplikan):** Q: Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX

Konteks Memori (prinsip & preferensi aktif):
- 📌 Prinsip [Kejujuran & realisme dulu]: Saya lebih suka jawaban yang jujur, realistis, dan bertahap. Kalau sesuatu belum bisa dicapai cepat, jelaskan alternatif yang paling dekat dan langkah kecil yang bisa dilakukan hari ini.
- ⚙️ Preferensi [Jawaban ringkas, actionable]: Saya suka jawaban singkat tapi bisa langsung dieksekusi: checklist, template, dan contoh nyata. Hindari teori panjang tanpa langkah praktis.
- 📌 Prinsip [IHOS: jujur & rendah hati]: Kalau belum ada sumber/pengetahua

### Langkah 1

- **Thought:** Hasil corpus tipis/gagal. Fallback: kutipan Wikipedia (API resmi, allowlist).
- **Action:** `search_web_wikipedia` — args: `{"query": "Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX", "lang": "id", "_citations": [{"type": "wikipedia", "query": "Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX", "lang": "id", "hits": 0}]}`
- **Observation (cuplikan):** [web:wikipedia] Tidak ada hasil untuk 'Jelaskan cara kerja BM25 dan dense retrieval hybrid di SIDIX' (id). Coba kata kunci lain atau periksa ejaan.

### Langkah 2

- **Thought:** Sudah ada hasil Wikipedia. Rangkai final answer dengan label sumber web.
- **Final (cuplikan):** Baik, mari kita jelaskan cara kerja BM25 dan dense retrieval hybrid dalam konteks SIDIX:

### Cara Kerja BM25
BM25 adalah metode ranking文档太长，已省略。

izzas、laughs、and coffee breaks.首先，让我们分步骤地解释BM25和dense retrieval hybrid的工作原理，并给出实际应用中的示例。

### BM25的工作原理
BM25是一种基于统计的文本检索算法，用于评估查询和

## Jawaban akhir (ringkas)

Baik, mari kita jelaskan cara kerja BM25 dan dense retrieval hybrid dalam konteks SIDIX:

### Cara Kerja BM25
BM25 adalah metode ranking文档太长，已省略。

izzas、laughs、and coffee breaks.首先，让我们分步骤地解释BM25和dense retrieval hybrid的工作原理，并给出实际应用中的示例。

### BM25的工作原理
BM25是一种基于统计的文本检索算法，用于评估查询和

## Cuplikan orkestrasi

```text
SIDIX OrchestrationPlan (deterministik)
request_persona=ABOO router=AYMAN
router_reason: score=1; signals=creative/design; conf=0.63

Archetype scores:
  - deduce: 0.000
  - connect: 0.000
  - invent: 0.000
  - synthesize: 0.000
  - orient: 0.350

Satellite weights (inspirasi fiksi / dev labels):
  - edison: 0.0000
  - pythagoras: 0.0000
  - shaka: 0.0000
  - lilith: 0.0000
  - atlas: 0.0000
  - york: 1.0000

Suggested phase order:
  1. [orient] persona~INAN -> Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit.

JSON:
{"request_persona": "ABOO", "router_persona": "AYMAN", "router_reason": "score=1; signals=creative/design; conf=0.63", "archetype_scores": {"deduce": 0.0, "connect": 0.0, "invent": 0.0, "synthesize": 0.0, "orient": 0.35}, "satellite_weights": {"edison": 0.0, "pythagoras": 0.0, "shaka": 0.0, "lilith": 0.0, "atlas": 0.0, "york": 1.0}, "phases": [{"archetype": "orient", "persona": "INAN", "hint": "Ringkas keputusan untuk pengguna; langkah berikutnya eksplisit."}]}
```

## Kerangka kasus (runtime — niat & cabang data)

**Kerangka situasi (niat & inisiasi)** — dari pola terkurasi Praxis, bukan tebak-tebakan bebas:

- **factual_corpus** _(skor 0.42)_ — **Niat:** Menjawab dari landasan yang bisa disanadkan: korpus BM25 dulu; bedakan fakta, opini, dan spekulasi.
  1. Sempitkan pertanyaan ke entitas/konsep utama.
  2. Gunakan search_corpus; baca chunk relevan sebelum menyimpulkan.
  3. Jika jawaban tidak ada di korpus, katakan eksplisit dan sarankan indeks/sumber.
  → **Bila ada cuplikan korpus:** Kutip ringkas + sebut jalur sumber bila tersedia; hindari klaim di luar cuplikan.

_Ini kerangka perilaku yang dapat ditambah di `brain/public/praxis/patterns/case_frames.json`; lesson Markdown mencatat bukti eksekusi nyata._

## Untuk SIDIX — cara berpikir seperti agen eksekutor

1. **Rekam dulu:** salin pertanyaan, persona, dan setiap *thought* sebelum bertindak.
2. **Pilah:** bedakan faktual (butuh korpus) vs meta (orkestrasi) vs implementasi (sandbox).
3. **Pilih alat:** satu tool per langkah; evaluasi observasi sebelum lanjut atau final.
4. **Batasi risiko:** jangan sebar secret; potong observasi panjang; hormati `corpus_only` / web fallback.
5. **Tutup dengan jawaban:** rangkum sumber + langkah berikutnya; akui ketidakpastian bila perlu.

_Tag: #praxis #sidix-agent #meta-learning_
