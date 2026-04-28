# 75 — Kaggle QLoRA Training Pipeline: Setup, Bug, Fix, Launch

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18
**Tag:** IMPL, FIX, DECISION

---

## Apa

Setup dan launch fine-tuning QLoRA Qwen2.5-7B-Instruct di Kaggle GPU menggunakan dataset `finetune_sft.jsonl` dari corpus SIDIX/Mighan.

---

## Bug yang Ditemukan dan Diperbaiki

### Bug 1 — Path dataset hardcode salah
**Error:** `FileNotFoundError: '/kaggle/input/datasets/mighan/sidix-sft-dataset/finetune_sft.jsonl'`

**Sebab:** Kaggle memotong prefix `datasets/<owner>/` saat dataset di-attach ke notebook. Path yang benar adalah `/kaggle/input/<dataset-slug>/`.

**Fix:** Ganti hardcode path dengan auto-detect menggunakan `glob`:
```python
_candidates = [
    "/kaggle/input/sidix-sft-dataset",
    "/kaggle/input/datasets/mighan/sidix-sft-dataset",  # fallback
]
for _d in _candidates:
    _jsonl_files = sorted(glob.glob(f"{_d}/*.jsonl"))
    if _jsonl_files:
        break

# Last resort
if not _jsonl_files:
    _jsonl_files = sorted(glob.glob("/kaggle/input/**/*.jsonl", recursive=True))

if not _jsonl_files:
    raise FileNotFoundError("Dataset 'sidix-sft-dataset' belum di-attach ke notebook.")
```

### Bug 2 — Dataset di Kaggle tidak punya `finetune_sft.jsonl`
**Sebab:** Dataset `sidix-sft-dataset` (v2) hanya berisi `corpus_training_2026-04-17.jsonl` — format berbeda dari SFT.

**Fix:** Upload `finetune_sft.jsonl` sebagai dataset version baru via Kaggle CLI:
```bash
# Di local venv:
kaggle datasets version -p _kaggle_upload_tmp/ -m "Add finetune_sft.jsonl for QLoRA SFT training"
```

Dataset v3 sekarang hanya berisi `finetune_sft.jsonl` (1 MB, 998 KB).

### Bug 3 — Notebook masih pakai dataset v2
**Fix:** Di Kaggle notebook → Datasets → "..." → "Check for updates" → klik "Update" (v2 → v3).

---

## Perbedaan Format File

| File | Format | Cocok untuk SFT? |
|------|--------|-----------------|
| `corpus_training_2026-04-17.jsonl` | `{messages: [{0:..},{1:..}], domain, persona, source}` | ❌ Tidak |
| `finetune_sft.jsonl` | `{messages: [{role, content},...], source_id, tags}` | ✅ Ya |

---

## Setup Notebook SIDIX_GEN

**File:** `notebooks/sidix_gen_kaggle_train.ipynb`
**Kaggle URL:** `https://www.kaggle.com/code/mighan/sidix-gen`

### Stack
- Model: `Qwen/Qwen2.5-7B-Instruct`
- Quantization: 4-bit NF4 (BitsAndBytes)
- LoRA: r=16, alpha=32, target semua projection layers
- GPU: P100 (Kaggle free tier, 30 jam/minggu)
- Epochs: 3, batch=2, grad_accum=8

### Output
```
/kaggle/working/sidix-lora-adapter/    ← adapter files
/kaggle/working/sidix-lora-adapter.zip ← zipped untuk download
```

---

## Upload Dataset via Kaggle CLI

```bash
# Persiapkan folder
mkdir _kaggle_upload_tmp
cp brain/datasets/finetune_sft.jsonl _kaggle_upload_tmp/

# Buat metadata
echo '{"title":"SIDIX SFT Dataset","id":"mighan/sidix-sft-dataset","licenses":[{"name":"unknown"}]}' \
  > _kaggle_upload_tmp/dataset-metadata.json

# Push sebagai new version
kaggle datasets version -p _kaggle_upload_tmp/ -m "Add finetune_sft.jsonl for QLoRA SFT training"
```

**Kaggle CLI ada di:** `D:\MIGHAN Model\apps\brain_qa\.venv\Scripts\kaggle.exe`
**Credentials:** `C:\Users\ASUS\.kaggle\kaggle.json`

---

## Langkah Setelah Training Selesai (~2-4 jam)

1. Download `sidix-lora-adapter.zip` dari Kaggle Output tab
2. Upload ke VPS:
   ```bash
   scp sidix-lora-adapter.zip root@72.62.125.6:/tmp/sidix/apps/brain_qa/models/
   ```
3. Extract di VPS:
   ```bash
   cd /tmp/sidix/apps/brain_qa/models/
   unzip sidix-lora-adapter.zip
   ```
4. Register adapter ke Ollama sebagai model custom SIDIX
5. Update `OLLAMA_MODEL` di `.env` brain_qa

---

## Pelajaran Penting

- Kaggle path dataset SELALU `/kaggle/input/<slug>/` — TANPA prefix `datasets/<owner>/`
- Saat buat dataset version baru via CLI, file-file lama tidak otomatis ikut — hanya file yang ada di folder upload
- "Check for updates" di notebook perlu diklik manual setelah dataset diupdate
- Kaggle P100 free quota: ~30 jam/minggu. Training 3 epoch = ~2-4 jam
- Jangan hardcode path — selalu pakai auto-detect + fallback

---

## Status

✅ Training berjalan (session "Waiting for Jupyter..." → GPU boot)
⏳ Estimasi selesai: 2–4 jam dari launch
