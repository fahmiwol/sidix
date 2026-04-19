# 143. Opsec Masking + LoRA Pipeline + Threads Consumer (Sprint 20 Menit)

> **Domain**: ai / arsitektur / opsec
> **Fase**: 5.5 (transisi menuju mandiri)
> **Tanggal**: 2026-04-18

---

## Konteks Sprint

User mandate baru di sprint ini:
1. Lanjut ke vision lokal (Ollama vision model — moondream/llava)
2. Auto-LoRA pipeline (kalau training_pairs cukup, siap upload Kaggle)
3. Threads queue consumer (picked up `growth_queue.jsonl` → post)
4. **Update progress publik untuk kontributor** (CHANGELOG + landing)
5. **Rahasia opsec**: SIDIX harus terlihat standing-alone, jangan bocor identitas
   backbone reasoning eksternal ke output publik

## Komponen Baru

### 1. `identity_mask.py`
Lapisan masking nama provider untuk output publik:
- `groq*` → `mentor_alpha`
- `gemini*` → `mentor_beta`
- `anthropic`/`claude*` → `mentor_gamma`
- `openai`/`gpt*` → `mentor_delta`
- `ollama`/`qwen*`/`llama3` → `sidix_local`
- `pollinations` → `image_engine_free`
- `gtts` → `tts_engine_free`

Fungsi:
- `mask_identity(name)` — convert satu nama
- `mask_dict(d, fields)` — mask field-field tertentu di dict
- `mask_health_payload(p)` — sanitize `/health` response

### 2. `multi_modal_router.py` — Ollama Vision Support
Tambah `_ollama_vision_ready()` + `_ollama_vision()` panggil Ollama
`/api/generate` dengan `images=[base64]`. Default model: `moondream`
(~2GB, ringan). Supported: `llava`, `bakllava`, `moondream`, `llava-llama3`,
`minicpm-v`.

`analyze_image(prefer_local=True)` — sesuai prinsip mandiri (note 142),
lokal dulu, cloud fallback hanya kalau lokal tidak available.

Tambah `_calculate_mandiri_score()` — skor 0-100% seberapa kapabilitas
SIDIX bisa jalan tanpa cloud:
- vision_local, ocr_local, image_gen_free, tts_local, llm_local, asr_local

### 3. `auto_lora.py`
Threshold 500 training pairs → ready untuk fine-tune baru.

API:
- `get_training_corpus_status()` — total pairs, files breakdown, pairs since last upload
- `prepare_upload_batch(force=False)` — konsolidasi semua jsonl → satu
  batch dir di `.data/lora_upload/<batch_id>/` dengan `training.jsonl`,
  `dataset-metadata.json`, `README.md`, marker `_last_upload.json`
- `try_kaggle_upload(batch_dir)` — opsional, kalau kaggle CLI + creds tersedia

Format batch siap pakai untuk Kaggle/Colab/RunPod tanpa konversi tambahan.

### 4. `threads_consumer.py`
Konsumsi `growth_queue.jsonl` ke Threads:
- `get_queue_status()` — count by status (queued/published/failed)
- `consume_one(dry_run)` — ambil 1 post terlama yang queued, post via
  `threads_oauth.create_text_post`, update status in-place
- `consume_batch(max_posts)` — batch dengan jeda 2 detik (rate-limit friendly)

Audit trail: tidak menghapus entry, hanya update status field.

## Endpoint Baru

| Endpoint | Tujuan |
|----------|--------|
| `GET /sidix/lora/status` | Status corpus training (total pairs, ready or not) |
| `POST /sidix/lora/prepare?force=` | Konsolidasi batch upload |
| `GET /sidix/threads-queue/status` | Hitung queued/published/failed |
| `POST /sidix/threads-queue/consume?max_posts=&dry_run=` | Ambil & post |

## Opsec — Apa yang Berubah di Public-Facing

### Sebelum
```json
{
  "isnad": [
    {"role": "mentor_llm", "name": "groq_llama3", "via": "multi_llm_router → groq_llama3"}
  ]
}
```

### Sesudah
```json
{
  "isnad": [
    {"role": "reasoning_engine", "name": "mentor_alpha", "via": "sidix.reasoning_pool → mentor_alpha"}
  ]
}
```

`/health` tidak lagi mengandung `llm_providers` array literal. Diganti
dengan agregat:
```json
"internal_mentor_pool": {"ready": true, "redundancy_level": 3}
```

## CHANGELOG.md + Landing Update

`CHANGELOG.md` di root repo (versi v0.1 sampai v0.5) — bahasa publik
"reasoning_pool", "internal mentor pool", "image engine free" — tanpa
nama provider spesifik.

`SIDIX_LANDING/index.html` roadmap section diupdate dengan 4 item NEW:
- Daily Continual Learning Engine
- Sanad + Hafidz untuk Setiap Note
- Multi-Modal: Vision + Image Gen + TTS + ASR
- Skill Modes + Decision Engine

## Hasil Sprint

| Item | Status |
|------|--------|
| `identity_mask.py` | ✅ Implementasi |
| `multi_modal_router.py` Ollama vision | ✅ Code support added |
| `auto_lora.py` | ✅ Implementasi + endpoint |
| `threads_consumer.py` | ✅ Implementasi + endpoint |
| `sanad_builder.py` apply mask | ✅ Updated |
| `agent_serve.py` /health mask | ✅ Updated |
| `CHANGELOG.md` publik | ✅ Created (v0.1-v0.5) |
| `SIDIX_LANDING` roadmap | ✅ Updated 4 NEW items |
| Commit + Push GitHub | ✅ `e9999d2` |
| Deploy server (pm2 restart) | ⏳ SSH key auth temporary issue, deploy via cron sync atau manual |
| Test endpoint live | ⏳ Setelah deploy |

## Insight Penting dari Server

Ollama di server punya 3 model:
- `sidix-lora:latest` (model SIDIX dengan LoRA adapter sendiri!)
- `qwen2.5:7b`
- `qwen2.5:1.5b`

Artinya **SIDIX sudah punya backbone lokal sendiri yang aktif**. Setiap
panggilan `multi_llm_router.route_generate()` dengan `skip_local=False`
akan default ke `sidix-lora:latest`. Itu sudah sesuai roadmap Fase Transisi
(target 40-60% query lokal).

## Keterbatasan Jujur

1. **Masking adalah security-through-obscurity** — kontributor yang baca
   kode di GitHub akan tetap lihat `multi_llm_router.py` dengan import
   `groq`, `gemini`, `anthropic`. Masking hanya melindungi output runtime
   dari user awam/casual scraper, bukan dari developer yang baca repo.
   *Mitigasi sebenarnya: percepat transisi ke LoRA lokal sehingga import
   provider eksternal bisa di-conditional/gated atau dihapus seluruhnya.*

2. **Sanad lama (note 138, 140) sudah punya nama provider literal** karena
   ditulis sebelum masking aktif. Untuk sekarang biarkan — masking aktif
   untuk note baru. Migrasi retroaktif bisa dilakukan dengan script.

3. **CHANGELOG public bahasa generik** — tapi commit message di GitHub
   masih sebut "groq_whisper", "gemini vision" dll. Tidak bisa rewrite
   history tanpa force-push (yang bermasalah untuk kontributor).

4. **Deploy via SSH manual** — sprint ini tidak sempat verify endpoint
   live karena SSH agent transient issue. Kode sudah pushed, perlu
   `git pull && pm2 restart sidix-brain` di server.

## Sumber

- note 142: SIDIX Entitas Mandiri (mandate)
- note 22, 41, 106, 115: Hafidz + Sanad architecture
- note 132: Multi-perspective autonomous research
- Fahmi Wolhuter — opsec mandate 2026-04-18:
  *"rahasia juga termasuk bahwa kita harus terlihat standing alone,
  jangan sampai hacker developer tau kalau diawal ini kita masih pake
  API model AI lain"*
- Implementasi:
  - `apps/brain_qa/brain_qa/identity_mask.py`
  - `apps/brain_qa/brain_qa/auto_lora.py`
  - `apps/brain_qa/brain_qa/threads_consumer.py`
  - `apps/brain_qa/brain_qa/multi_modal_router.py` (Ollama vision)
