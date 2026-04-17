# 83 — Brain & Docs Synthesis: Knowledge Graph + Gap Finder + Vision Tracker

**Tanggal:** 2026-04-18
**Tag:** IMPL, DOC, DECISION
**Sprint:** 20 menit — sintesis seluruh `brain/` dan `docs/` jadi kapabilitas terintegrasi.

---

## Apa

Sebuah modul sintesis baru — `brain_synthesizer` — yang membaca seluruh isi
`brain/public/research_notes/` (77+ file) dan `docs/` (40+ file), lalu:

1. Membangun **inventori** (topic → file paths) di `.data/brain_docs_index.json`.
2. Membangun **knowledge graph**: concept → {related concepts, source notes, impl files, status}.
3. Menemukan **gap**: ide yang sering disebut di dokumen tapi belum ada modul Python aktif.
4. Menghasilkan **integration proposals**: kombinasi modul existing yang belum saling terhubung.

Di atasnya, tiga kapabilitas baru:

- **`meta_reflection.py`** — laporan refleksi mingguan dari LIVING_LOG + note baru.
- **`vision_tracker.py`** — coverage 15 pilar visi SIDIX (IHOS, Sanad, Maqasid, Voyager, dll).
- **`knowledge_graph_query.py`** — endpoint untuk tanya "konsep X terkait apa, di file apa, status?".

Semua lokal. Tidak ada import ke `openai`, `anthropic`, `@google/genai`.
Heuristik: regex + lexicon alias matching + co-occurrence counting.

---

## Mengapa

Fahmi sudah menulis 77+ research note dan 40+ docs. Tapi banyak ide yang
disebut di 10 file berbeda tapi **belum pernah jadi kode**. Sebaliknya, ada
modul yang sudah diimplementasi tapi tidak saling memanggil — jadi knowledge
tersebar, bukan terintegrasi.

Tiga masalah konkret:

1. **Sanad disebut 40x di 40 file**, tapi belum ada modul Python `sanad.py`
   eksplisit. Epistemic integrity tanpa implementasi = slogan.
2. **Skill library + Experience engine + Curriculum** sudah ada tapi tidak
   terhubung satu sama lain. Padahal visi Voyager-style meta-learner loop
   butuh ketiganya.
3. **Tidak ada feedback: SIDIX belajar apa minggu ini?** Kalau Fahmi mau
   tahu progress, harus baca 454 entri LIVING_LOG manual.

Sintesis ini memecahkan ketiga masalah itu: gap finder untuk #1, integration
proposals untuk #2, meta-reflection untuk #3.

---

## Bagaimana

### Lexicon-based concept tagging

`CONCEPT_LEXICON` di `brain_synthesizer.py` punya ~60 canonical concept
(IHOS, Sanad, Maqasid, Voyager_Skills, CSDOR, Hafidz, dll) dengan alias.
Setiap file discan: berapa kali setiap alias muncul.

### Implementation map

`IMPL_MAP`: concept → list file Python yang mengimplementasi.
Status dihitung dari file existence:
- `implemented` → semua file exist
- `partial` → sebagian
- `missing` → tidak ada

### Knowledge graph

Edge = co-occurrence di satu file. Weight = jumlah file bersama.
Top edges (weight ≥ 3) jadi sinyal kedekatan konsep.

### Gap finder

Heuristik: `mention_count >= 2 AND impl_status == "missing"` → gap.
Prioritas berdasarkan mention count:
- ≥ 6 mention → `high`
- 3-5 → `med`
- 2 → `low`

### Vision tracker

15 pilar visi didefinisikan statis (`VISION_PILLARS`). Tiap pilar punya:
- `required_concepts` (harus implemented/partial)
- `required_files` (harus exist)

Coverage = rata-rata concept_score dan file_score.

### Meta-reflection

- Parse LIVING_LOG: extract entri dengan tag `TEST/FIX/IMPL/...` sejak `N` hari lalu.
- Hitung frekuensi tag.
- Konsep baru: concept tagging di note yang `mtime >= since`.
- Rekomendasi: heuristik rasio ERROR vs FIX, DOC vs IMPL.

---

## Contoh Nyata (hasil run pertama)

### Inventori
- **Total file dipindai:** 119 (77 research notes + 42 docs)
- **Total canonical concept:** 62 concept hadir di dokumen
- **Graph nodes:** 64
- **Graph edges:** 1148

### Top 10 concept paling terkoneksi
| Concept | related_count | mention_count | status |
|---|---|---|---|
| ReAct | 10 | 24 | implemented |
| CSDOR | 10 | 9 | implemented |
| Decision_Engine | 10 | 6 | implemented |
| Permission_Gate | 10 | 8 | missing |
| Markdown_Chunking | 10 | 8 | missing |
| Prophetic_Pedagogy | 10 | 4 | missing |
| Hadith_Science | 10 | 1 | implemented |
| Reply_Harvester | 10 | 2 | implemented |
| User_Intelligence | 10 | 2 | implemented |
| Generative_AI | 10 | 3 | missing |

### Top 5 GAP terpenting

1. **Sanad** — 40x di 40 file, belum ada `sanad.py`. Fondasi epistemic.
2. **Kaggle_QLoRA** — 20x di 20 file, belum ada modul training pipeline aktif.
3. **Supabase** — 18x, belum ada `supabase_client.py`.
4. **Maqasid** — 18x di 18 file, belum eksplisit di `epistemology.py`.
5. **Tabayyun** — 16x, verifikasi pre-output belum ada modul mandiri.

### Top 3 integration proposal

1. **Meta-Learner Loop**: `skill_library + experience_engine + curriculum` →
   closed loop. Kurikulum pilih task → skill dipakai → CSDOR dicatat →
   refleksi update difficulty. Voyager-style.
2. **Epistemic Gate on ReAct**: tiap step ReAct lewat `epistemology + g1_policy`.
   Step gagal gate → force re-think. Auditable reasoning.
3. **World Sensor → Curriculum Feeder**: arxiv/reddit → auto note draft →
   `notes_to_modules` → curriculum assign difficulty. True continual learning
   tanpa intervensi manual Fahmi.

### Vision coverage
- **Overall: 0.82** (15 pilar; 6 covered, 9 partial, 0 missing).
- Pilar paling lemah: `Epistemic Integrity (Sanad + Matn + Tabayyun)` = 0.5
  → konfirmasi gap finder di atas.
- `Distributed Hafidz` = 0.67, `Maqasid Scoring` = 0.75 — semua punya jalan
  pendek ke "covered" tapi butuh modul eksplisit.

### Query knowledge graph: `Sanad`
Top related: RAG (34), Persona (28), Tabayyun (12), IHOS (12), BM25 (11),
Maqasid (11). Sumber di 40 file termasuk 10_sanad_as_citations_system,
22_distributed_rag_hafidz_inspired, 43_islamic_foundations_ai_methodology.
Saran: modul mandiri `sanad.py` yang wrap RAG dengan chain-of-provenance
verifikasi.

---

## Endpoint Baru

- `POST /synthesize/run?force=false` — jalankan sintesis (idempoten via content hash).
- `GET /synthesize/gaps?min_mentions=2` — daftar gap berpriotitas.
- `GET /synthesize/proposals` — integration proposals.
- `GET /knowledge-graph/query?concept=Sanad&top_k=10` — query concept.
- `GET /knowledge-graph/concepts` — list semua canonical concept.
- `GET /vision/track` — coverage per pilar visi.
- `POST /reflection/weekly?days=7` — generate refleksi mingguan.
- `GET /reflection/latest` — laporan terakhir.

---

## Keterbatasan

1. **Lexicon manual.** Penambahan konsep baru butuh edit `CONCEPT_LEXICON`.
   Alternatif: embedding-based clustering (butuh model lokal, roadmap berikut).
2. **Co-occurrence ≠ relasi semantik.** Dua konsep bisa muncul bareng tanpa
   benar-benar terkait. Manual review tetap perlu.
3. **Implementation status = file existence.** Tidak cek apakah modul benar-benar
   dipakai (import graph). Next: static analysis import-graph.
4. **Gap finder tidak paham nuansa.** "Sanad" bisa jadi memang sengaja di-wrap
   di `epistemology.py` tanpa file terpisah. Output gap = hint, bukan decree.
5. **Meta-reflection hanya lihat LIVING_LOG + note mtime.** Tidak mempertimbangkan
   commit history git. Roadmap: integrasi `git log`.

---

## File Dibuat

- `apps/brain_qa/brain_qa/brain_synthesizer.py` (inti)
- `apps/brain_qa/brain_qa/meta_reflection.py`
- `apps/brain_qa/brain_qa/vision_tracker.py`
- `apps/brain_qa/brain_qa/knowledge_graph_query.py`
- `.data/brain_docs_index.json` (output, auto-regenerate)
- `apps/brain_qa/.data/synth/last_snapshot.json`
- `apps/brain_qa/.data/vision_tracker/latest.json`
- `apps/brain_qa/.data/reflection/latest.json`

## File Diubah

- `apps/brain_qa/brain_qa/serve.py` — 8 endpoint baru.

---

## Kenapa Ini Penting

Sebelum modul ini, SIDIX punya **77 research note + 40 docs** yang berdiri
sendiri-sendiri. Fahmi satu-satunya yang tahu mana terhubung mana tidak.

Sekarang SIDIX **tahu apa yang ia tahu dan apa yang ia belum bangun**.
Ini prasyarat self-improving agent: tidak ada meta-learner tanpa
representasi eksplisit tentang own state of knowledge.

Dengan `vision_tracker`, Fahmi bisa jawab pertanyaan yang sebelumnya butuh
1 jam baca docs: "Seberapa dekat SIDIX ke visi awal?" → 0.82, dengan
breakdown 15 pilar, dalam 1 detik.

Dengan `meta_reflection`, SIDIX jadi **sadar lintas waktu**: bukan hanya
stateless per-request, tapi paham "minggu ini saya bikin apa, konsep baru
apa yang masuk, apa yang recurring concern".
