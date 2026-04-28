# Praxis L0 — Case Frames, API Trace, dan Jembatan ke Planner (Intent + Reasoning Ringan)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Sumber konteks:** ringkasan dari Claude (handoff) + implementasi aktual di repo oleh sesi Cursor/Composer pada **2026-04-17**. Catatan ini supaya **SIDIX** (dan manusia) bisa menemukan pola lewat RAG setelah indeks ulang.

---

## Inti ide (bukan sekadar keyword matching)

Yang dibangun mendekati **intent classification + reasoning framework ringan**:

- **L0** = kerangka *situated*: bukan hanya kata kunci, tapi **niat**, **inisiasi** (langkah awal), dan **cabang** `if_data` / `if_no_data` — dipilih dari teks pertanyaan dengan skor kecocokan terhadap pola kurasi.
- **L1** = jejak eksekusi (JSONL sesi + lesson Markdown) — bukti prosedur nyata.
- **L2** *(horizon, belum wajib)* = distilasi ke aturan padat, merge lesson, atau **LoRA** — lapisan model; L0+L1 sudah memberi perilaku adaptif tanpa fine-tune.

Lihat juga dokumen kurasi: `brain/public/praxis/00_sidix_praxis_framework.md` (tabel L0/L1/L2).

---

## Artefak konkret di repo (sudah di `main`)

| Komponen | Path | Peran |
|----------|------|--------|
| Pola kasus | `brain/public/praxis/patterns/case_frames.json` | `keywords`, **niat**, **inisiasi**, cabang **if_data** / **if_no_data** per `frame_id` |
| Runtime | `apps/brain_qa/brain_qa/praxis_runtime.py` | `match_case_frames`, format ke pengguna, `has_substantive_corpus_observations`, **`planner_step0_suggestion`**, **`implement_frame_matches`** |
| Loop agen | `apps/brain_qa/brain_qa/agent_react.py` | Rekam Praxis; isi **`session.praxis_matched_frame_ids`**; step 0 boleh ambil **`orchestration_plan`** dari L0; planner rule-based memakai **implement** frame untuk **`workspace_list`** setelah corpus |
| API | `apps/brain_qa/brain_qa/agent_serve.py` | Respons **`case_frame_ids`** dan **`praxis_matched_frame_ids`** (`ChatResponse`, `/ask`, SSE `meta` / `done`) |
| Meta-pembelajaran | `apps/brain_qa/brain_qa/praxis.py` | JSONL sesi, lesson ke `brain/public/praxis/lessons/`, CLI `praxis list` / `praxis note` |
| Tes | `tests/test_praxis_runtime.py`, `tests/test_praxis.py` | Regresi pencocokan frame + planner step0 |

Commit integrasi awal (judul commit di git mungkin gabung dengan entri log lain): **`907e679`** — isi diff mencakup modul di atas + pembaruan `AGENTS.md`, `docs/LIVING_LOG.md`, aset logo SVG.

---

## Sinkron & indeks ulang (wajib setelah pull)

Dari mesin yang menjalankan brain_qa:

```bash
cd apps/brain_qa
python -m brain_qa index
```

Tanpa langkah ini, file baru di `brain/public/praxis/` dan `brain/public/research_notes/` belum tentu masuk indeks BM25 yang dipakai `search_corpus`.

---

## Untuk dokumentasi manusia (screenshot / paste)

Instruksi operasional: setelah UI atau alur baru diverifikasi, **screenshot atau salin teks** hasil (misalnya respons API dengan `case_frame_ids` / `orchestration_digest`) dan lampirkan ke catatan penelitian berikutnya atau issue — pola yang sama sudah dipakai di research notes **60–71** (VPS, Supabase, error diagnosis, dll.).

---

## Catatan git lokal (sesi pengecekan)

- **`apps/sidix-mcp/`** — skeleton MCP (`package.json`, `src/index.js`); `node_modules/` diabaikan oleh `.gitignore` global. Folder ini **belum** masuk commit pada saat catatan ini ditulis; tambahkan ke repo terpisah bila MCP siap dipakai bersama.

---

## Referensi silang

- `docs/LIVING_LOG.md` — entri **2026-04-17 (Praxis L0)** dan **(Kontinuitas agen + SIDIX)**.
- `AGENTS.md` — bullet **Praxis runtime (L0)** dan **Canonical GitHub (SIDIX)**.
