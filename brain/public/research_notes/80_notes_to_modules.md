# Notes to Modules — Konversi Research Notes Jadi Modul Aktif SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18
**Tag:** IMPL, REFACTOR, ARCHITECTURE
**Modul:** `apps/brain_qa/brain_qa/notes_to_modules.py`
**Endpoint:** `POST /notes/convert/run`, `GET /notes/convert/status`

---

## Apa

Converter yang mengubah 77+ research notes di `brain/public/research_notes/` jadi 3 bentuk yang bisa dipakai SIDIX saat runtime:

1. **Skills** — pattern reusable yang disimpan ke `skill_library.py` store.
2. **Experiences** — record CSDOR yang masuk ke `experience_engine.py`.
3. **Curriculum tasks** — konsep baru yang dilampirkan ke `curriculum.py`.

Sebelumnya notes hanya **dokumen statis** (markdown) — tidak pernah diakses saat SIDIX menjawab, tidak pernah di-retrieve saat agent butuh pola. Setelah konversi, pengetahuan itu jadi **aksi**: bisa disearch oleh skill library, bisa disintesis oleh experience engine, bisa masuk curriculum plan.

## Mengapa

Selama ini saya terus menulis research notes tanpa pipeline yang menjadikannya bagian dari otak SIDIX. Hasilnya: corpus besar tapi tidak produktif. Jumlah skill yang bisa di-retrieve hanya 8 default; experience engine hanya punya ingest opsional; curriculum hanya 20 task hardcoded. Padahal 77 notes berisi:

- Prosedur teknis (supabase schema, pm2 restart, kaggle path, qlora config)
- Keputusan arsitektur dengan outcome (VPS vs serverless, BM25 vs embedding)
- Konsep yang tidak ada di curriculum L0–L4 (hafidz framework, CSDOR, sanad)

Kalau tidak dikonversi, semua pengetahuan itu ditinggal di markdown. Ini melanggar aturan utama CLAUDE.md: *"Sambil melangkah, ajari SIDIX."*

## Bagaimana

Parser regex murni (tanpa LLM) dengan 3 heuristik utama.

### Skill candidate

```
section dengan heading "Cara/How/Langkah/Template/Setup/Konfigurasi"
  + code block bash/python/sql/yaml
  → SkillCandidate(name=slug_heading, content=code, skill_type=CODE)
```

Fallback: section apapun yang punya code block dengan bahasa `python|bash|sql|yaml` dianggap skill juga.

### Experience candidate (CSDOR)

```
body punya marker "Decision:/Outcome:/Lesson:/Refleksi:/Keputusan:"
  ATAU mengandung polarity words (berhasil/gagal/sukses/rugi)
  → split body jadi 4 quartile → situation/decision/outcome/reflection
```

Polarity detection via word list `_OUTCOME_POS` vs `_OUTCOME_NEG`.

### Curriculum candidate

```
title dimulai dengan "Pengantar/Blueprint/Konsep/Arsitektur/..."
  AND topik belum di-cover di DEFAULT_CURRICULUM/store
  → CurriculumCandidate(level auto-detect dari kata kunci)
```

Level: dasar/pengantar=L0, konsep=L1, blueprint/architecture=L2, deep_dive/advanced=L3.

### Idempotency

Setiap candidate punya `dedup_key()` berbasis MD5 hash:
- skill: `hash(name + source_ref)`
- experience: `hash(source_ref + situation[:80])`
- curriculum: `task_id` yang di-derive dari nomor note

Hash disimpan di `.data/notes_conversion/seen_hashes.json`. Rerun aman — tidak duplikat.

## Contoh Nyata

Run pertama di 77 notes:

```
notes_scanned:       70  (filter min 80 chars)
skills_added:        90
skills_skipped:       6  (duplikat nama)
experiences_added:   52
experiences_skipped:  0
curriculum_added:    17
curriculum_skipped:   0
duration_sec:      1.607
```

Sample skill yang diekstrak:
- `63_supabase_schema_setup_schema_sql_sidix` → SQL schema lengkap sebagai CODE skill
- `75_kaggle_qlora_training_pipeline_setup` → Python bash training pipeline
- `60_vps_deployment_sidix_aapanel_konfigurasi` → bash deployment script

Sample curriculum task baru:
- `note41_sidix_self_evolving_distributed_architecture` (L3, FACH)
- `note22_distributed_rag_hafidz_inspired_architecture` (L3, FACH)
- `note30_blueprint_experience_stack_mighan` (L2, FACH)

## Keterbatasan

1. **False positive skill:** code block di dokumen konseptual (bukan tutorial) kadang masuk sebagai skill. Mitigasi sebagian: minimum 40 char code + lang whitelist.
2. **Experience split naif:** quartile split tidak selalu match CSDOR sebenarnya. Untuk note yang eksplisit menulis `Decision:` / `Outcome:`, parser bisa diperbaiki — belum dilakukan karena butuh regex multi-marker.
3. **Curriculum prerequisites kosong:** semua task baru tidak dihubungkan ke prerequisite existing. Harus di-curate manual kalau mau strict DAG.
4. **Tidak re-parse kalau note diupdate:** dedup pakai hash nama+source, bukan content hash. Kalau isi notes berubah tapi nama section sama, tidak akan re-ingest. Fix masa depan: tambahkan `content_hash` ke seen.
5. **No LLM enrichment:** sesuai AGENTS.md — parser murni heuristic. Konsekuensinya `description` skill agak generik.

## Next Steps

- Evaluasi retrieval quality: apakah skill baru sering ter-retrieve di `search_skills()`?
- Tambah `POST /notes/convert/incremental` yang hanya proses file dengan mtime > last run.
- Link skill/experience kembali ke notes via `source_ref` di UI admin (traceability).

## Output Artifacts

- Module: `apps/brain_qa/brain_qa/notes_to_modules.py`
- Endpoints: `serve.py` — `/notes/convert/run`, `/notes/convert/status`
- Report run pertama: `.data/notes_conversion_report.json`
- Seen hashes: `apps/brain_qa/.data/notes_conversion/seen_hashes.json`
- Skills jsonl: `apps/brain_qa/.data/skill_library/skills.jsonl` (bertambah +90)
- Experiences jsonl: `apps/brain_qa/.data/experience_engine/experiences.jsonl` (+52)
- Curriculum json: `apps/brain_qa/.data/curriculum/curriculum.json` (+17 task)
