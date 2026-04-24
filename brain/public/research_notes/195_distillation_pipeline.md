# 195 — Distillation Pipeline SIDIX: Teacher → Student → GGUF → Ollama

**Tanggal**: 2026-04-24
**Status**: [FAKTA] Implementasi awal — scripts tersedia, belum dijalankan di GPU
**Sanad**: Dibuat berdasarkan kebutuhan VPS CPU deployment + literatur distilasi LLM

---

## Apa

Pipeline lengkap untuk mendistilasi model SIDIX dari teacher 7B ke student kecil (0.5B–3B)
agar bisa dijalankan di VPS CPU dengan latency acceptable (<5 detik per response).

Komponen:
1. **`generate_synthetic_data.py`** — Generate Q&A pairs dari corpus research notes
2. **`distill_sidix.py`** — QLoRA fine-tuning student model di GPU (Kaggle T4)
3. **`export_to_gguf.sh`** — Merge adapter + konversi ke GGUF + quantize
4. **`sidix_modelfile.txt`** — Ollama Modelfile untuk deploy model distilled

---

## Mengapa

### Masalah
- Model utama SIDIX: Qwen2.5-7B-Instruct + LoRA adapter
- 7B model butuh GPU untuk inference dengan latency <5 detik
- VPS SIDIX hanya punya CPU (RAM ~8-16GB) — terlalu lambat untuk 7B
- Solusi jangka pendek: API eksternal (Groq/Gemini) → tapi ini tidak "standing alone"

### Solusi: Distilasi
- Distilasi teacher-student: model 7B mengajar model kecil (0.5B-3B)
- Student yang terdistilasi lebih kecil tapi sudah "terlatih gaya SIDIX"
- GGUF + quantize (Q4_K_M) → bisa run di CPU dengan Ollama
- Target latency: 2-5 detik per token di CPU modern

### Mengapa ini bukan "mundur"
- Model 0.5B yang terdistilasi dengan data SIDIX spesifik > model 0.5B generik
- Distilasi bukan pengganti model besar — melainkan versi "lite" untuk edge deployment
- Model 7B tetap jalan di GPU untuk training dan high-quality inference

---

## Bagaimana

### Pipeline Lengkap

```
brain/public/research_notes/*.md
           │
           ▼
   generate_synthetic_data.py
   (mock mode ATAU via API)
           │
           ▼
data/distillation/synthetic_pairs_YYYYMMDD.jsonl
           │
           ▼ (Kaggle T4 / GPU)
   distill_sidix.py (QLoRA)
   base: Qwen2.5-0.5B-Instruct
           │
           ▼
   sidix-distilled-adapter/
           │
           ▼
   export_to_gguf.sh
   (merge + llama.cpp convert + quantize q4_k_m)
           │
           ▼
   sidix-distilled.gguf
           │
           ▼
   ollama create sidix-distilled
           │
           ▼
   VPS CPU: ollama run sidix-distilled
```

### Tiga Ukuran Target

| Model | VRAM Train | RAM Inference | Latency CPU | Quality |
|-------|-----------|---------------|-------------|---------|
| 0.5B  | ~4GB      | ~0.8GB        | ~1-2s/tok   | Basic   |
| 1.5B  | ~8GB      | ~1.5GB        | ~2-3s/tok   | Good    |
| 3B    | ~16GB     | ~2.5GB        | ~3-5s/tok   | Better  |

**Rekomendasi VPS**: mulai dengan 0.5B, evaluasi, upgrade ke 1.5B jika perlu.

### Synthetic Data Generation

**Mode mock** (tanpa API):
- Baca heading markdown → jadikan pertanyaan
- Baca isi paragraf → jadikan jawaban
- Output: `{"prompt": "...", "completion": "[FAKTA] ...\n\nSumber: xxx.md"}`
- Kualitas: cukup untuk memperkenalkan gaya SIDIX ke student

**Mode API** (dengan `DISTIL_API_KEY`):
- Kirim chunk ke LLM API (DeepSeek / compatible)
- Minta model generate Q&A pair dalam gaya SIDIX
- Kualitas: lebih baik, lebih natural

Target minimal: 500 pairs untuk 0.5B, 2000+ pairs untuk 3B.

### QLoRA Config

```python
TrainingConfig(
    base_model="Qwen/Qwen2.5-0.5B-Instruct",
    lora_r=16,           # rank — naik ke 32 untuk model lebih besar
    lora_alpha=32,
    num_epochs=3,
    batch_size=4,
    learning_rate=2e-4,
    max_seq_length=512,
    load_in_4bit=True,   # hemat VRAM
)
```

### GGUF Export

```bash
# Merge adapter + convert + quantize
QUANT_TYPE=q4_k_m ./export_to_gguf.sh \
    ./sidix-distilled-adapter \
    Qwen/Qwen2.5-0.5B-Instruct \
    sidix-0.5b
```

Ukuran hasil:
- 0.5B f16: ~1GB → q4_k_m: ~350MB
- 1.5B f16: ~3GB → q4_k_m: ~1GB
- 3B   f16: ~6GB → q4_k_m: ~2GB

---

## Contoh Nyata

```bash
# Step 1: generate 200 pairs dari semua notes
python scripts/distillation/generate_synthetic_data.py --count 200

# Step 2: upload ke Kaggle, jalankan di T4
python scripts/distillation/distill_sidix.py \
    --data_path data/distillation/synthetic_pairs_20260424.jsonl

# Step 3: export ke GGUF
./scripts/distillation/export_to_gguf.sh

# Step 4: deploy ke Ollama
cp sidix-distilled.gguf /opt/sidix/models/
ollama create sidix-distilled -f scripts/distillation/sidix_modelfile.txt
ollama run sidix-distilled "Apa itu aqidah?"
```

---

## Progressive Scaling Plan

```
Sprint 8 (sekarang):
  → 0.5B distilled, 200 pairs mock
  → Target: pipeline jalan end-to-end, bukan kualitas maksimal

Sprint 9-10:
  → 500+ pairs via API (DeepSeek murah)
  → Upgrade ke 1.5B
  → Evaluasi: BLEU vs teacher 7B, latency VPS

Sprint 11-12:
  → 2000+ pairs
  → 3B model
  → A/B test: distilled vs API fallback

Milestone:
  → Distilled model replace API fallback untuk query sederhana
  → Model 7B tetap untuk complex reasoning
```

---

## Keterbatasan

1. **Kaggle T4 limit**: 30 jam/minggu. Satu run training 0.5B ~1-2 jam. Hemat dengan batch training.
2. **Quality gap**: 0.5B student akan kalah dari 7B teacher untuk topik kompleks. Acceptable untuk FAQ.
3. **Mock data quality**: Mode mock menghasilkan data mekanis, bukan natural. Butuh review manual atau API mode untuk kualitas lebih baik.
4. **GGUF dependencies**: llama.cpp harus dikompilasi di server. Bisa pakai Docker image pre-built.
5. **Context window**: max_seq_length=512 di training → student tidak bisa handle percakapan panjang. Naik ke 1024+ dengan trade-off VRAM.
6. **Drift dari teacher**: Student tidak bisa mereplikasi ReAct loop atau tool use dari teacher. Student hanya distilasi *pengetahuan* dan *gaya*, bukan *capability*.

---

## File Terkait

- `scripts/distillation/generate_synthetic_data.py`
- `scripts/distillation/distill_sidix.py`
- `scripts/distillation/export_to_gguf.sh`
- `scripts/distillation/sidix_modelfile.txt`
- `data/distillation/` — output synthetic pairs
- `brain/public/research_notes/193_vps_distillation_strategy.md` — strategi VPS
- `brain/public/research_notes/170_gpu_provider_comparison_2026.md` — GPU options
