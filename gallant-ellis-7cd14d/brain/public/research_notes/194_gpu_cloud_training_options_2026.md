> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
sanad_tier: research_synthesis
tags: [research, gpu, training, lora, qlora, distillation, vps, sprint-8d]
date: 2026-04-24
sources:
  - https://www.gmicloud.ai/en/blog/best-free-gpu-trials-for-online-deep-learning-2026-guide
  - https://free.ai/gpu/
  - https://github.com/zszazi/Deep-learning-in-cloud
  - https://www.kaggle.com/discussions/questions-and-answers/496863
  - docs/14_VPS_TRAINING_GUIDE.md
---

# 194 — GPU Cloud untuk LLM Training SIDIX 2026

## Konteks

Note 170 membahas GPU untuk **inferensi** (image gen, Sprint 3).
Note ini khusus untuk **training** — LoRA fine-tuning, QLoRA distilasi, dan
synthetic data generation untuk roadmap Knowledge Distillation SIDIX.

Lihat juga: `193_vps_distillation_strategy.md` untuk strategi distilasi penuh.

---

## 1. Kebutuhan VRAM per Model

| Model Target | Method | Min VRAM | Comfortable |
|---|---|---|---|
| Qwen2.5-0.5B | LoRA full | 2 GB | 4 GB |
| Qwen2.5-1.5B | LoRA r=16 | 4 GB | 6 GB |
| Qwen2.5-3B | LoRA r=16 | 8 GB | 12 GB |
| Qwen2.5-7B | **QLoRA 4-bit** | 14 GB | 16 GB |
| Qwen2.5-7B | LoRA (fp16) | 22 GB | 28 GB |
| Qwen2.5-14B | QLoRA 4-bit | 24 GB | 32 GB |

[FACT] T4 (16GB) cukup untuk QLoRA Qwen2.5-7B — ini baseline hardware minimum.
[FACT] A100 (40/80GB) atau H100 diperlukan untuk 14B+ atau batch size lebih besar.

---

## 2. Opsi GPU Gratis (Zero Cost, No Card Required)

### 🥇 Kaggle — PILIHAN UTAMA

| Spesifikasi | Detail |
|---|---|
| GPU | T4 × 2 (masing-masing 16GB = total 32GB) |
| RAM | 30GB system RAM |
| Storage | 20GB disk |
| Kuota | **30 jam / minggu** |
| Session limit | 12 jam / session |
| Kartu kredit | ❌ Tidak perlu |
| Setup | Instant (notebook web) |

**Kenapa Kaggle = pilihan utama SIDIX:**
- [FACT] T4 16GB cukup untuk QLoRA Qwen2.5-7B (4-bit = ~9GB VRAM aktif)
- [FACT] 30 jam/minggu = ~4 sesi training penuh per minggu
- [FACT] Sesi 12 jam cukup untuk 3 epoch × Qwen2.5-7B × 1000 samples
- [OPINION] Paling stabil dibanding Colab untuk session panjang
- Dataset bisa diupload langsung atau pull dari HuggingFace Hub
- Output bisa push ke HuggingFace otomatis via `huggingface_hub`

**Workflow Kaggle untuk SIDIX:**
```
1. Buat notebook baru di kaggle.com
2. Enable GPU T4 di Settings → Accelerator
3. Run: pip install transformers peft bitsandbytes trl datasets
4. Load dataset dari HF: load_dataset("fahmiwol/sidix-synthetic-v1")
5. Train dengan QLoRA (lihat notebook di §7.3 Training Guide)
6. Save adapter → push ke HuggingFace
7. VPS pull adapter → deploy ke Ollama
```

---

### 🥈 Google Colab — Backup Gratis

| Spesifikasi | Detail |
|---|---|
| GPU | T4 16GB (kadang P100/K80) |
| RAM | 12–16GB system |
| Session limit | ~12 jam (disconnect otomatis) |
| Kartu kredit | ❌ Tidak perlu (free tier) |
| Reliability | ⚠️ Sering disconnect, GPU bisa dicabut |

[OPINION] Gunakan Colab sebagai backup Kaggle, bukan primary. Runtime sering
terputus di tengah training panjang.

---

### 🥉 Free.ai — Wild Card A100

| Spesifikasi | Detail |
|---|---|
| GPU | NVIDIA A100 20GB HBM |
| CUDA | 12.4 |
| Biaya | ~$0.81/jam (token-based) |
| Free signup | 10,000 tokens (~12 menit GPU) |
| Kartu kredit | ❌ Tidak perlu untuk trial |
| Pre-installed | PyTorch, transformers, diffusers, JupyterLab |

[FACT] A100 20GB = lebih dari cukup untuk QLoRA 7B dan LoRA 14B.
[OPINION] Free tier terlalu singkat untuk training penuh, tapi berguna untuk:
- Test konfigurasi LoRA sebelum training panjang di Kaggle
- Validasi script, cek memory usage, debug

---

## 3. Opsi Berbayar Murah (untuk Ketika Kuota Kaggle Habis)

| Provider | GPU | Harga/jam | Min Commit | Notes |
|---|---|---|---|---|
| **Vast.ai** | RTX 3090/4090, A100 | $0.20–$0.80 | Per jam | Cheapest, variable reliability |
| **RunPod** | RTX 4090, A100, H100 | $0.34–$1.89 | Per detik | Paling reliable untuk training burst |
| **Google Colab Pro** | T4/A100 | ~$0.33/hr efektif | $10/bulan | Worth it jika butuh >30 hr/minggu |
| **Lambda Cloud** | A10 24GB | $0.50/jam | Per jam | 48 jam max session, stabil |
| **Genesis Cloud** | 1080Ti 11GB | $0.30/jam | — | Ada 166 GPU-hours free trial |

**Rekomendasi prioritas berbayar untuk SIDIX:**
1. **Vast.ai** — termurah, pakai untuk training 7B penuh jika Kaggle penuh
2. **RunPod** — lebih reliable, pakai untuk fine-tuning kritikal/production
3. **Colab Pro** — $10/bulan, worth it jika aktif training setiap minggu

---

## 4. Opsi Free Credits (Perlu Kartu Kredit, Sekali Pakai)

| Provider | Credit | GPU Tersedia | Kadaluarsa |
|---|---|---|---|
| Google Cloud (GCP) | $300 | T4, A100, H100 | 90 hari |
| AWS SageMaker | 250 hr/bulan | ml.g4dn.xlarge (T4) | 2 bulan |
| Azure | $200 | NCsv3 (V100) | 30 hari |
| Alibaba Cloud | $300 | V100, A10 | 12 bulan |
| GMI Cloud | ~$100 | H100, H200 | Tergantung program |
| IBM Cloud | $200 | V100 | 30 hari |
| Nimblebox | $10 | T4 | — |

[OPINION] Ini senjata sekali pakai. Gunakan strategically untuk:
- Training batch besar (10K+ samples) yang butuh A100/H100
- Distilasi awal untuk milestone v0.9
- Jangan habiskan untuk eksperimen kecil yang bisa di Kaggle

---

## 5. Decision Tree: Pilih Platform Mana?

```
Query: Mau training apa?
│
├─ Test script / debug cepat (<30 menit)
│   └─ → Free.ai (A100 trial) atau Colab free
│
├─ Training standar (1000 samples, 3 epoch, model <7B)
│   └─ → KAGGLE (T4 × 2, gratis, 30hr/mgg)
│
├─ Training model 7B QLoRA (dataset standar)
│   └─ Kaggle T4 masih cukup (9GB VRAM aktif)
│   └─ → KAGGLE jika <12 jam, Vast.ai jika lebih lama
│
├─ Training model 14B atau batch besar (5K+ samples)
│   └─ → Vast.ai A100 ($0.80-1.40/jam) atau gunakan GCP credit
│
└─ Production fine-tuning, milestone v1.0+
    └─ → RunPod A100 80GB (reliable) atau simpan GCP/AWS credit
```

---

## 6. Estimasi Biaya Training SIDIX Per Fase

| Fase | Model | Samples | Platform | Estimasi Waktu | Biaya |
|---|---|---|---|---|---|
| Bulan 1 (now) | Qwen2.5-1.5B | 1000 | Kaggle (free) | 1-2 jam | **$0** |
| Bulan 1 (now) | Qwen2.5-7B | 1000 | Kaggle (free) | 8-10 jam | **$0** |
| Bulan 2-3 | Qwen2.5-7B | 3000 | Kaggle + Vast.ai | ~15 jam | **$3-8** |
| Bulan 4-6 | Qwen2.5-7B | 10K | Vast.ai A100 | ~20 jam | **$16-28** |
| Bulan 7-12 | Qwen2.5-14B | 10K | RunPod A100 80GB | ~30 jam | **$40-60** |

[FACT] 30 jam/minggu Kaggle = sekitar 120 jam/bulan GRATIS.
[OPINION] Untuk 6 bulan pertama, Kaggle gratis sudah lebih dari cukup.

---

## 7. Setup Kaggle untuk SIDIX (Step-by-Step)

```bash
# Step 1: Di Kaggle notebook, cell pertama
!pip install -q transformers accelerate peft bitsandbytes trl datasets huggingface_hub

# Step 2: Login HuggingFace (untuk push adapter)
from huggingface_hub import login
login(token="hf_xxx")  # ambil dari HF settings

# Step 3: Pull synthetic dataset SIDIX (setelah diupload)
from datasets import load_dataset
dataset = load_dataset("fahmiwol/sidix-synthetic-v1", split="train")

# Step 4: Jalankan notebook training (§7.3 di VPS Training Guide)
# ... (lihat sidix_kaggle_training.ipynb)

# Step 5: Push adapter hasil training
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="./sidix-adapter-final",
    repo_id="fahmiwol/sidix-adapter-v1",
    repo_type="model"
)
```

```bash
# Step 6: Di VPS, pull adapter baru
huggingface-cli download fahmiwol/sidix-adapter-v1 \
    --local-dir ./adapters/latest

# Step 7: Deploy ke Ollama
ollama create sidix -f Modelfile.sidix-distilled
ollama run sidix
```

---

## 8. Perbandingan vs Note 170 (Konteks Berbeda)

| Aspek | Note 170 (Inference) | Note 194 (Training) |
|---|---|---|
| Tujuan | Serve request user real-time | Fine-tune model sekali pakai |
| Frekuensi | 24/7 continuous | 1x per bulan (batch) |
| Billing ideal | Per-detik serverless | Per-jam, bisa spot/interruptible |
| GPU pilihan | RTX 4090, A10 (cepat, murah) | T4 16GB+ (cukup untuk QLoRA) |
| Platform utama | RunPod Serverless, Modal | **Kaggle (gratis)**, Vast.ai |
| Priority | Latency < cost | Cost = zero (Kaggle) |

---

## 9. Kesimpulan & Rekomendasi untuk SIDIX

**[FACT] Strategi optimal untuk SIDIX saat ini (v0.8 → v0.9):**

1. **Primary training**: Kaggle gratis (T4 ×2, 30hr/minggu) — cukup untuk semua training 1-3B dan QLoRA 7B
2. **Synthetic data**: DeepSeek API di VPS CPU (~$2 per 1000 samples)
3. **Deploy**: HuggingFace Hub (gratis) sebagai relay antara Kaggle dan VPS
4. **Inference**: VPS CPU dengan Ollama (sudah berjalan, $0)
5. **Paid backup**: Vast.ai jika Kaggle penuh (~$0.25-0.50/jam)

**[OPINION] SIDIX tidak perlu beli GPU dedicated sampai v1.5 (Bulan 12-18).**
Kombinasi Kaggle + Vast.ai sudah cukup untuk mencapai target v1.0.

**Total biaya estimasi 6 bulan pertama: $0–$30** (mayoritas dari Kaggle gratis).

---

## Referensi

- [GMI Cloud GPU Guide 2026](https://www.gmicloud.ai/en/blog/best-free-gpu-trials-for-online-deep-learning-2026-guide)
- [Free.ai GPU Service](https://free.ai/gpu/)
- [Deep Learning in Cloud — GitHub](https://github.com/zszazi/Deep-learning-in-cloud)
- Note 170: `170_gpu_provider_comparison_2026.md` (inference focus)
- Note 193: `193_vps_distillation_strategy.md` (distilasi strategy)
- `docs/14_VPS_TRAINING_GUIDE.md` (complete training guide)
