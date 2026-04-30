# Profil Inferensi Operator SIDIX

> Task 29 — Hud (G5)

Dokumen ini menjelaskan mode inferensi yang tersedia di SIDIX Brain QA, kebutuhan hardware, dan cara mengaktifkan model lokal berbasis QLoRA.

---

## Mode Inferensi

SIDIX mendukung dua mode inferensi utama yang dikontrol oleh konfigurasi runtime:

| Mode | Nilai `BRAIN_QA_MODEL_MODE` | Keterangan |
|------|-----------------------------|------------|
| **mock** | `mock` | Respons dummy — untuk pengembangan dan testing tanpa GPU. Biaya token = 0. |
| **local_lora** | `local_lora` | Inferensi lokal menggunakan model Qwen2.5-7B 4-bit + LoRA adapter. Membutuhkan GPU. |

Set mode melalui variabel lingkungan:

```bash
# Mode mock (default untuk dev)
export BRAIN_QA_MODEL_MODE=mock

# Mode lokal dengan LoRA
export BRAIN_QA_MODEL_MODE=local_lora
```

---

## Kebutuhan Hardware untuk `local_lora`

### Minimum

| Komponen | Spesifikasi |
|----------|-------------|
| GPU VRAM | 8 GB (Qwen2.5-7B kuantisasi 4-bit) |
| RAM sistem | 16 GB |
| Penyimpanan | 10 GB bebas untuk model + adapter |
| CUDA | 11.8 atau lebih baru |

### Direkomendasikan

| Komponen | Spesifikasi |
|----------|-------------|
| GPU VRAM | 16 GB atau lebih (RTX 3080 Ti, RTX 4070, A10, dll.) |
| RAM sistem | 32 GB |
| Penyimpanan | 20 GB SSD |

### Estimasi VRAM

| Komponen | Estimasi |
|----------|----------|
| Bobot model Qwen2.5-7B (4-bit) | ~4 GB |
| Activations + KV cache | ~2 GB |
| **Total minimum** | **~6 GB** |
| Buffer aman (overhead CUDA) | +2 GB |
| **Rekomendasi** | **8 GB** |

> Catatan: Pada batch size > 1 atau konteks panjang (>2048 token), kebutuhan VRAM meningkat.
> Gunakan 16 GB VRAM untuk beban produksi yang stabil.

---

## Setup QLoRA

SIDIX menggunakan kuantisasi 4-bit dengan LoRA untuk efisiensi memori.

### Konfigurasi LoRA

| Parameter | Nilai | Keterangan |
|-----------|-------|------------|
| Quantization | 4-bit (NF4) | Via `bitsandbytes` |
| LoRA rank | 16 | Keseimbangan kapasitas vs. ukuran adapter |
| LoRA alpha | 32 | Scaling factor (biasanya 2× rank) |
| LoRA target modules | `q_proj`, `v_proj` | Attention layers |
| LoRA dropout | 0.05 | Regularisasi ringan |

### Struktur File Adapter

```
adapters/
├── adapter_model.safetensors   # Bobot LoRA yang telah ditraining
└── adapter_config.json         # Konfigurasi PEFT (rank, alpha, target_modules)
```

Contoh `adapter_config.json`:

```json
{
  "base_model_name_or_path": "Qwen/Qwen2.5-7B-Instruct",
  "bias": "none",
  "fan_in_fan_out": false,
  "inference_mode": true,
  "lora_alpha": 32,
  "lora_dropout": 0.05,
  "modules_to_save": null,
  "peft_type": "LORA",
  "r": 16,
  "target_modules": ["q_proj", "v_proj"]
}
```

---

## Mengaktifkan Adapter LoRA

1. Buat atau salin folder `adapters/` di root workspace.
2. Taruh `adapter_model.safetensors` dan `adapter_config.json` di dalamnya.
3. Arahkan path adapter via env var (opsional, default = `adapters/`):

```bash
export BRAIN_QA_ADAPTER_DIR="adapters/"
```

4. Set mode ke `local_lora`:

```bash
export BRAIN_QA_MODEL_MODE=local_lora
```

5. Jalankan server — model akan dimuat saat startup:

```bash
python -m brain_qa serve
```

---

## Timeout Rekomendasi

Inferensi lokal lebih lambat dari API cloud. Gunakan timeout yang cukup:

```bash
export BRAIN_QA_TIMEOUT_S=30
```

| Situasi | Timeout Rekomendasi |
|---------|---------------------|
| Mode mock | 5 detik |
| local_lora, hardware minimum (8 GB) | 30–60 detik |
| local_lora, hardware kuat (16 GB+) | 15–30 detik |

---

## Cara Cek Status Model

Gunakan endpoint `/health` untuk mengecek kesiapan model:

```bash
curl http://localhost:8765/health
```

Respons contoh saat model siap:

```json
{
  "status": "ok",
  "model_ready": true,
  "model_mode": "local_lora",
  "corpus_doc_count": 142,
  "corpus_chunk_count": 891
}
```

Respons saat model belum siap (masih loading):

```json
{
  "status": "degraded",
  "model_ready": false,
  "model_mode": "local_lora",
  "corpus_doc_count": 0,
  "corpus_chunk_count": 0
}
```

Field kunci:

| Field | Tipe | Keterangan |
|-------|------|------------|
| `model_ready` | bool | `true` = model siap menerima permintaan |
| `model_mode` | string | `"mock"` atau `"local_lora"` |
| `corpus_doc_count` | int | Jumlah dokumen yang terindeks |

---

*Dokumen ini bagian dari G5 — Operator Pack SIDIX.*
