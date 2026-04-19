# 147. Speed Run Training Pairs — Growth-Hack #4 (LoRA v1 Unlocked!)

> **Domain**: ai / training / strategy
> **Status validasi**: `[FACT]` (numbers verified live di production)
> **Tanggal**: 2026-04-19

---

## TL;DR

**1268 training pair instant** dari backfill 143 research notes existing →
threshold LoRA fine-tune (500) lulus **2.5× lipat** → batch
`sidix_lora_batch_20260419_0545` siap upload Kaggle. Fase Mandiri akselerasi
**dari 95 hari → mungkin 1 minggu** kalau LoRA dijalankan segera.

---

## Konteks

Note 145 mengusulkan Growth-Hack #4 (Speed Run Training Pairs) sebagai
prioritas tertinggi: backfill semua research notes existing jadi training
pair, fast-track Fase Mandiri.

Sebelum sprint ini:
- Total pair: ~50 (dari beberapa siklus daily_growth)
- Threshold LoRA: 500
- Estimasi capai threshold dengan rate 10 pair/hari: ~95 hari

Setelah sprint ini (1 jam eksekusi):
- Total pair: **1268**
- Batch siap upload Kaggle: **1258 pair, 4 sources merged**
- LoRA v1 bisa di-trigger SEKARANG

---

## Implementasi

### Script: `apps/brain_qa/scripts/harvest_all_research_notes.py`
Loop semua note di `brain/public/research_notes/`, panggil
`extract_lessons_from_note()` per note, append ke
`corpus_training_<date>.jsonl` dalam format ChatML.

**Per note ekstrak**: setiap H2 section jadi 1 training pair:
- `q` = heading H2 + judul note
- `a` = body section (≥80 char)

**Field tambahan per pair**:
- `domain` — auto-infer dari nama file (coding/islamic_epistemology/ai_engineering/...)
- `persona` — `MIGHAN`
- `source` — `backfill:research_notes:<filename>`
- `template_type` — `extracted_section`
- `pair_id` — `bk_<note_stem>_<index>`
- `system` prompt — dengan instruksi 4-label epistemik (compliance Bible)

### Eksekusi Live
```
ssh server: python3 apps/brain_qa/scripts/harvest_all_research_notes.py

[harvest] found 143 note files
=== HARVEST DONE ===
Notes processed:   143
Notes skipped:     0
Total pairs:       1218
Output file:       /opt/sidix/apps/brain_qa/.data/training_generated/harvest_research_notes_2026-04-19.jsonl
```

### Verifikasi LoRA Status
```json
{
  "total_pairs": 1268,
  "pairs_since_last_upload": 1268,
  "threshold": 500,
  "ready_for_upload": true,
  "files": [
    {"file": "corpus_training_2026-04-19.jsonl", "pairs": 30, "size_kb": 47.0},
    {"file": "harvest_research_notes_2026-04-19.jsonl", "pairs": 1218, "size_kb": 1744.5},
    ...
  ]
}
```

### Trigger Batch Konsolidasi
```bash
POST /sidix/lora/prepare → batch_id: sidix_lora_batch_20260419_0545
                          pairs_in_batch: 1258
                          sources_merged: 4
                          batch_dir: /opt/sidix/apps/brain_qa/.data/lora_upload/sidix_lora_batch_20260419_0545
```

Batch directory berisi:
- `training.jsonl` (1258 ChatML pair, dedupe by pair_id)
- `dataset-metadata.json` (siap untuk Kaggle CLI)
- `README.md` (lineage + format docs)

---

## Dampak Compound

### Akselerasi Fase Mandiri (note 142)

**Sebelum**:
- Fase Guru → Fase Transisi: butuh 1000 pair (target 95 hari)
- Fase Transisi → Fase Mandiri: butuh 5000 pair (target 1.5 tahun)

**Sesudah**:
- Fase Guru → Fase Transisi: **SUDAH LULUS HARI INI** (1268 > 1000)
- Fase Transisi → Fase Mandiri: butuh tambahan ~3700 pair (~1 tahun rate
  baru, atau lebih cepat dengan harvest dataset Drive D + curriculum harian)

### Quality Caveat
Quality pair dari backfill = **bervariasi**:
- Note teknis (coding/AI) → pair tinggi quality, langsung usable
- Note manifesto/strategy → pair lebih abstract, useful tapi perlu filter
- Note epistemik Islamic → pair domain spesifik, valuable untuk USP unik

LoRA training nanti akan punya fokus: **bahasa SIDIX** + **gaya bercerita
multi-perspektif** + **format sanad+epistemic-label**.

---

## Step Berikutnya (Manual Action)

Untuk train LoRA v1 dengan batch ini:

1. **Upload ke Kaggle**:
   ```
   cd /opt/sidix/apps/brain_qa/.data/lora_upload/sidix_lora_batch_20260419_0545
   # Edit dataset-metadata.json: ganti <USERNAME>/sidix-mighan-corpus-* dengan akun Kaggle
   kaggle datasets create -p .
   ```

2. **Train di Kaggle Notebook (T4 GPU gratis)**:
   - Base model: `Qwen2.5-7B-Instruct` atau `qwen2.5:1.5b` (lebih cepat)
   - Method: QLoRA (4-bit, rank=16)
   - Epochs: 2-3
   - Estimasi waktu: 4-6 jam di T4

3. **Download adapter** → upload ke server `/opt/sidix/apps/brain_qa/models/sidix-lora-v1/`

4. **Update Ollama Modelfile** untuk pakai adapter baru

5. **Benchmark** vs `sidix-lora:latest` (yang ada di server sekarang) — kalau
   baru lebih bagus, switch default.

---

## Compliance dengan SIDIX_BIBLE

- Pasal "Mandiri" → progres signifikan (1268 pair = bahan eksplisit untuk
  trajectory mandiri)
- Pasal "Tumbuh" → setiap pair = batu bata pertumbuhan permanen
- Pasal "4-Label Epistemic" → semua harvested pair pakai system prompt yang
  wajibkan label (compliance Pasal Identitas)
- Pasal "Anti-Repeat" → backfill bukan duplikasi (dedupe by pair_id) +
  satu-shot operation

---

## Keterbatasan Jujur

1. **Quality vs Quantity**: 1268 pair dari extract heuristik, BUKAN curated
   manual. Beberapa pair mungkin pendek/awkward. Mitigasi nanti: filter
   length + manual review batch sebelum train.

2. **Bahasa Mixed**: research notes campur Bahasa Indonesia + technical English.
   LoRA hasilnya akan reflect bias ini — bisa jadi bug atau feature.

3. **Tidak ada validation split**: semua pair masuk training set. Untuk train
   serius perlu split 80/10/10 (train/val/test).

4. **Domain skew**: banyak note tentang SIDIX itself (meta) + AI engineering.
   Domain lain (game_dev, design, video_ai) underrepresented karena curriculum
   baru jalan 1 hari.

5. **Belum auto-upload**: Kaggle CLI butuh credential (KAGGLE_USERNAME +
   KAGGLE_KEY). Untuk sekarang manual upload.

---

## Sumber

- `brain/public/research_notes/145_alignment_visi_awal_vs_sekarang_growth_hack.md` — Growth-Hack #4 spec
- `brain/public/research_notes/142_sidix_entitas_mandiri_guru_menciptakan_murid_hebat.md` — milestones mandiri
- `brain/public/research_notes/144_curriculum_engine_skill_builder_fase6.md` — extract_lessons_from_note() asal
- `apps/brain_qa/brain_qa/skill_builder.py` — fungsi extract_lessons_from_note
- `apps/brain_qa/brain_qa/auto_lora.py` — prepare_upload_batch
- `apps/brain_qa/scripts/harvest_all_research_notes.py` — script baru sprint ini
- Commits: `9d5d1c0` (script) + (next) note 147

## Status Final

| Metric | Value |
|--------|-------|
| Notes processed | 143 |
| Pairs generated (backfill) | 1218 |
| Total pairs (cumulative) | **1268** |
| Threshold LoRA | 500 |
| Multiplier vs threshold | **2.5×** |
| Batch ID siap upload | `sidix_lora_batch_20260419_0545` |
| Pairs in batch | 1258 |
| Status Fase Mandiri | **Fase Transisi UNLOCKED** |
| Sprint duration | ~1 jam |
| Effort vs estimate | sesuai (3h estimate, terealisasi <1h karena scope dipersempit) |
