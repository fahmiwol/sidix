> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
title: SIDIX Folder Processor — Angkat D:\SIDIX Jadi Kapabilitas Aktif
created: 2026-04-18
tags: [sidix-folder, mcp-bridge, training-data, skill-library, corpus-enrichment, harvest, idempotent]
author: Fahmi (via Claude agent)
related:
  - 76_dokumen_ke_kode_konversi_lengkap.md
  - 77_sidix_kapabilitas_lengkap_april_2026.md
---

# Research Note 82 — SIDIX Folder Processor

## APA

Modul baru `apps/brain_qa/brain_qa/sidix_folder_processor.py` + companion
`sidix_folder_tools.py` + 3 endpoint HTTP:

| Endpoint                      | Method | Fungsi                                                     |
| ----------------------------- | ------ | ---------------------------------------------------------- |
| `/sidix-folder/audit`         | GET    | Hasil audit terakhir (klasifikasi per file)                |
| `/sidix-folder/process`       | POST   | Jalankan konversi (idempoten)                              |
| `/sidix-folder/stats`         | GET    | Counts + daftar tool yang bisa dipanggil runtime           |

Satu folder `D:\SIDIX` dikonversi ke **empat bentuk kapabilitas** dalam satu run:

1. **Training data** — Alpaca `{instruction, input, output, meta}` pairs di
   `.data/harvest/sidix_folder_pairs.jsonl` (siap dipakai
   `corpus_to_training.py` / upload ke Kaggle).
2. **Generative templates** — skill `PROMPT` di `skill_library` (retrievable
   lewat ReAct via `search_skills(query)`).
3. **Agent tools** — snippet Python di fenced code di-wrap jadi callable,
   disimpan sebagai file di `.data/sidix_folder_tools_snippets/` +
   registry JSON, dipanggil lewat `call_sidix_folder_tool(name, **kwargs)`.
4. **Corpus enrichment** — `.md` ber-frontmatter di
   `brain/public/sources/sidix_folder/{slug}_{hash}.md` → otomatis terindeks
   RAG BM25 di reindex berikutnya.

## MENGAPA

`D:\SIDIX` adalah **memori eksternal pre-framework**: MCPKnowledgeBridge
sudah mirror 48 sesi Claude (desktop/code/chat/mcp) sebagai JSON Q&A —
`{topic, instruction, output, tags, score}`. Data ini kaya tapi hanya
terendap di disk. Tanpa konversi, SIDIX tidak bisa:

- ingat keputusan arsitektur di sesi sebelumnya,
- reuse pattern (ReAct format, QLoRA config, Supabase RLS fix),
- learn dari Q&A yang sudah terstruktur.

Konversi ke 4 bentuk membuatnya **aktif**: masuk training corpus, masuk skill
library, bisa jadi tool, bisa di-search lewat RAG.

## BAGAIMANA

### Alur

```
D:\SIDIX\knowledge\queue\*.json   (48 file, MCPKnowledgeBridge)
D:\SIDIX\knowledge\index.json     (meta)
D:\SIDIX\knowledge\stats.json     (meta)
         │
         ▼
audit()  ── tulis .data/sidix_folder_audit.json
         │
         ▼
_iter_all_records()  ── normalisasi ke KnowledgeRecord
   │       ├─ _iter_mcp_bridge_entries() untuk queue/*.json
   │       └─ _iter_generic_knowledge() untuk .md/.txt/.ipynb/.pdf
         │
         ▼
 ┌───────┼────────────┬────────────────┐
 ▼       ▼            ▼                ▼
pairs  templates    tools           corpus
(JSONL) (skill_lib) (skill+snippet) (MD+FM)
         │
         ▼
report  ── tulis .data/sidix_folder_processing_report.json
```

### Idempotency

Content-hash tiap record/snippet disimpan di `.data/sidix_folder_processed.json`
dengan 4 bucket: `pairs`, `templates`, `tools`, `corpus`. Run berikutnya
otomatis skip yang hash-nya sudah ada. Verified: rerun menghasilkan
`{pairs_added:0, templates_added:0, tools_added:0, corpus_added:0}`.

### Keamanan / filter

- File > 50 MB → skip.
- Binary dengan ekstensi tidak dikenal → skip.
- PDF: pakai `pypdf` atau `PyPDF2` kalau ada; kalau tidak, log path saja.
- IPYNB: hanya sel markdown + code (tidak ambil base64 image output).
- Tidak ada panggilan ke vendor AI API; parsing murni regex + heuristic.

### Heuristik klasifikasi "template"

Record dianggap template (dikonversi ke skill PROMPT) bila salah satu:
- Tag-nya menyentuh `{prompt, template, pipeline, architecture, curriculum-learning, rag-analogy, constitutional-ai, spin, prophetic-pedagogy}`
- Head output matches regex `^(pipeline|template|format|pattern|recipe|arsitektur|struktur)`
- ≥ 3 tanda panah (`→` / `->`) di 400 karakter pertama (tanda alur repeatable)

## CONTOH NYATA (dari run pertama)

### 1 file → 1 training pair
`D:\SIDIX\knowledge\queue\f501149e2a2a4006.json` →
```json
{
  "instruction": "Bagaimana 7 metode mengajar Rasulullah SAW diterjemahkan menjadi arsitektur pembelajaran SIDIX?",
  "output": "7 METODE RASULULLAH SAW → PADANAN ARSITEKTUR SIDIX: 1. KETELADANAN → SPIN Imitation Learning...",
  "meta": {"topic": "Prophetic Pedagogy → SIDIX Learning Architecture (7 Metode Rasulullah SAW)",
           "tags": ["prophetic-pedagogy", "curriculum-learning", ...], "score": 5,
           "origin": "mcp_bridge"}
}
```

### 1 file → 1 skill PROMPT
Record yang sama (punya tag `prophetic-pedagogy, curriculum-learning, constitutional-ai`
dan head output punya banyak `→`) → ditambahkan ke `skill_library`
sebagai `tpl_prophetic_pedagogy_sidix_learning_architecture_7_<hash6>`
(retrievable dari ReAct).

### 1 file → 1 corpus item
`brain/public/sources/sidix_folder/prophetic_pedagogy_sidix_learning_arc_<hash6>.md`
(ber-frontmatter dengan `title`, `origin`, `source_path`, `tags`) → terindeks BM25.

## STATISTIK RUN PERTAMA

- Files di-audit: **50** (48 knowledge + 2 config)
- Training pairs: **48**
- Generative templates: **15**
- Agent tools: **0** (queue ini prose murni; belum ada fenced python code)
- Corpus items: **48**
- Total bytes processed: **~90 KB**

## 5 KAPABILITAS PALING MENARIK

1. **Prophetic Pedagogy → SIDIX Learning Architecture** — 7 metode Rasulullah
   dipetakan ke komponen training (SPIN, Curriculum, Constitutional AI, AmtsalLibrary)
2. **SIDIX Growth Manifesto — DIKW + Data Flywheel + Living Knowledge Graph**
   — blueprint self-evolving 7-stage pipeline
3. **SIDIX 7-Stage Autonomous Learning Pipeline** — detail implementasi tiap stage
4. **SIDIX Self-Evolving Architecture Blueprint** — arsitektur flywheel
5. **Filosofi sebagai Akar — Cara Berfikir SIDIX** — grounding filosofis dari
   pesan Fahmi, penanda bahwa SIDIX bukan produk teknis-saja tapi epistemologi

## KETERBATASAN

- **0 agent tools** dari run ini: queue JSON berisi narasi, belum mengandung
  fenced ```python. Kapabilitas snippet-wrap akan aktif begitu ada entri
  yang memasukkan kode (misalnya log sesi Claude Code dengan blok kode).
- **Heuristik template kasar**: false positive mungkin terjadi. Mitigasi:
  skill `verified=False` by default — perlu promosi manual.
- **Eksekusi snippet** di `sidix_folder_tools.py` pakai `exec()` di namespace
  terisolasi, tapi TIDAK di-sandbox. Dipakai hanya untuk snippet hasil sesi
  SIDIX sendiri (trust-on-first-write). Sebelum dipanggil dari ReAct
  production, perlu tambahan sandbox (AST whitelist / RestrictedPython).
- **Tidak scan sub-folder D:\SIDIX lain** selain `knowledge/` karena saat audit
  memang hanya itu yang ada; skeleton-nya sudah generic (`rglob("*")`) siap
  kalau nanti bertambah.
- **Corpus items belum di-reindex otomatis**: perlu `POST /corpus/reindex`
  setelah run agar BM25 memasukkannya.

## NEXT STEP (opsional)

1. Trigger `/corpus/reindex` setelah `/sidix-folder/process` supaya RAG
   langsung sadar item baru.
2. Pasang cron/hook: setiap kali MCPKnowledgeBridge tulis file baru di
   `D:\SIDIX\knowledge\queue`, panggil `/sidix-folder/process` otomatis.
3. Sandbox eksekusi `call_sidix_folder_tool` dengan AST-whitelist sebelum
   di-expose ke ReAct.
