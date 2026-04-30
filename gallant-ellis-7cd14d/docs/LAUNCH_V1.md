# SIDIX v1 — Panduan Launch Perdana (24 Jam)

> Status: **SIAP LAUNCH** — LoRA adapter sudah lokal, semua 114 artefak Projek Badar selesai.
> Tanggal persiapan: 2026-04-17 | Target go-live: dalam 24 jam dari persiapan ini.

---

## Ringkasan Situasi Saat Ini

| Komponen | Status | Catatan |
|---|---|---|
| LoRA Adapter | ✅ **Ada lokal** | `apps/brain_qa/models/sidix-lora-adapter/` |
| Inference Engine (FastAPI) | ✅ Selesai | port 8765, `agent_serve.py` |
| User Interface (SIDIX UI) | ✅ Selesai | port 3000, Vite + TypeScript |
| BM25 RAG | ✅ Selesai | `brain_qa index` sudah jalan |
| ReAct Agent | ✅ Selesai | rule-based planner, swap ke LLM setelah test |
| G1 Policy (safety) | ✅ Selesai | injeksi, toksik, PII, confidence, tipe jawaban |
| 5 Persona | ✅ Selesai | MIGHAN, TOARD, FACH, HAYFAR, INAN |
| Python deps (ML) | ⚠️ **Perlu install** | torch, transformers, peft, accelerate |
| Base model download | ⚠️ **Perlu internet** | Qwen2.5-7B ~14GB (HuggingFace) |

---

## Prasyarat Hardware

| Kebutuhan | Minimum | Rekomendasi |
|---|---|---|
| RAM | 16 GB | 32 GB |
| VRAM (GPU) | 8 GB (4-bit mode) | 16 GB (fp16) |
| Storage | 20 GB bebas | 40 GB |
| OS | Windows 10/11 | Windows 11 + WSL2 |
| Python | 3.10+ | 3.11/3.12 |

> **Tanpa GPU**: Set `SIDIX_DISABLE_4BIT=1` dan gunakan CPU (sangat lambat, ~60s/token).
> CPU-only hanya untuk verifikasi, bukan produksi.

---

## Step 1 — Install Dependensi ML

Buka PowerShell di root repo, jalankan:

```powershell
# Pindah ke folder brain_qa
cd apps\brain_qa

# Install core ML stack
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install transformers, peft, training libs
pip install transformers>=4.40.0 peft>=0.10.0 accelerate>=0.29.0

# Install bitsandbytes untuk 4-bit quantization (Windows: gunakan wheel pra-build)
pip install bitsandbytes

# Kembali ke root dan install semua requirements
cd ..\..
pip install -r apps\brain_qa\requirements.txt
```

> **Jika bitsandbytes gagal di Windows**: Set env `SIDIX_DISABLE_4BIT=1` sebelum start server.
> Inference tetap jalan dengan fp16 (butuh VRAM lebih banyak).

Verifikasi:
```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available(), 'Devices:', torch.cuda.device_count())"
python -c "from peft import PeftModel; print('peft OK')"
python -c "from transformers import AutoTokenizer; print('transformers OK')"
```

---

## Step 2 — Verifikasi Adapter Lokal

Adapter sudah ada di `apps/brain_qa/models/sidix-lora-adapter/`. Verifikasi:

```powershell
python -c "
from apps.brain_qa.brain_qa.local_llm import adapter_fingerprint, find_adapter_dir
print('Adapter dir:', find_adapter_dir())
print('Fingerprint:', adapter_fingerprint())
"
```

Atau dari folder `apps/brain_qa`:
```powershell
cd apps\brain_qa
python -c "
from brain_qa.local_llm import adapter_fingerprint, find_adapter_dir
d = find_adapter_dir()
fp = adapter_fingerprint()
print(f'Dir: {d}')
print(f'Config present: {fp[\"config_present\"]}')
print(f'Weights present: {fp[\"weights_present\"]}')
print(f'SHA prefix: {fp[\"config_sha256_prefix\"]}')
"
```

Hasil yang diharapkan:
```
Config present: True
Weights present: True
SHA prefix: <16 hex chars>
```

---

## Step 3 — Build Index RAG

```powershell
cd apps\brain_qa
python -m brain_qa index
```

Konfirmasi output mengandung `[OK] Index built` atau `chunk_count > 0`.

---

## Step 4 — Start Inference Engine

```powershell
# Dari root repo
.\scripts\tasks.ps1 serve
```

Atau manual:
```powershell
cd apps\brain_qa
python -m brain_qa serve --host 0.0.0.0 --port 8765
```

Server siap saat muncul: `Uvicorn running on http://0.0.0.0:8765`

Cek health endpoint:
```powershell
curl http://localhost:8765/health
```

Response yang diharapkan (saat model berhasil load):
```json
{
  "status": "ok",
  "model_mode": "local_lora",
  "model_ready": true,
  "adapter_fingerprint": { "weights_present": true, "config_present": true }
}
```

> **Note**: Load model pertama kali butuh ~5–10 menit (download Qwen2.5-7B base ~14GB + mount LoRA).
> Progress akan terlihat di terminal. Setelah cached di HuggingFace local, startup berikutnya ~30 detik.

---

## Step 5 — Start UI

Buka terminal baru:
```powershell
.\scripts\tasks.ps1 ui
```

Atau:
```powershell
cd SIDIX_USER_UI
npm run dev
```

Buka browser: `http://localhost:3000`

---

## Step 6 — Smoke Test End-to-End

### 6a. Health check
```powershell
curl http://localhost:8765/health
```
→ `"status":"ok"`, `"model_ready":true`

### 6b. Test generate langsung
```powershell
curl -X POST http://localhost:8765/agent/generate `
  -H "Content-Type: application/json" `
  -d '{"prompt":"Apa itu SIDIX?","system":"Kamu adalah SIDIX, AI berbasis prinsip kejujuran.","max_tokens":200}'
```
→ `"mode":"local_lora"`, response berisi teks tidak kosong

### 6c. Test QA via endpoint ask
```powershell
curl -X POST http://localhost:8765/ask `
  -H "Content-Type: application/json" `
  -d '{"query":"Apa tujuan SIDIX?","persona":"INAN"}'
```
→ `"answer"` tidak kosong, `"citations"` array

### 6d. Test ReAct agent
```powershell
curl -X POST http://localhost:8765/agent/chat `
  -H "Content-Type: application/json" `
  -d '{"question":"Jelaskan prinsip sidq dalam SIDIX","persona":"FACH"}'
```
→ `"answer_type":"fakta"`, `"confidence_score"` > 0, steps ReAct di trace

### 6e. Test dari UI
1. Buka `http://localhost:3000`
2. Pilih persona INAN
3. Ketik: "Apa itu SIDIX?"
4. Klik Kirim → respons muncul dalam ≤ 30 detik

---

## Konfigurasi Lingkungan (`.env` opsional)

Buat file `.env` di root repo (lihat `.env.sample`):

```env
# Model mode
BRAIN_QA_MODEL_MODE=local_lora
SIDIX_DISABLE_4BIT=0          # set 1 jika bitsandbytes tidak support

# Admin token (wajib untuk endpoint /agent/bluegreen, /agent/canary)
BRAIN_QA_ADMIN_TOKEN=ganti_ini_32_karakter_acak_minimum

# Rate limiting
BRAIN_QA_RATE_LIMIT_RPM=60
BRAIN_QA_ANON_DAILY_CAP=100

# HuggingFace token (opsional, tapi dianjurkan untuk avoid rate limit)
HF_TOKEN=hf_xxxxxxxxxxxx
```

---

## Detail Adapter LoRA (untuk referensi teknis)

| Parameter | Nilai |
|---|---|
| Base model | `Qwen/Qwen2.5-7B-Instruct` |
| LoRA rank (r) | **16** |
| LoRA alpha | **32** |
| Dropout | 0.1 |
| Target modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| Trainable params | 40,370,176 (0.5273% dari total 7.65B) |
| Adapter size | **80.79 MB** (safetensors) |
| Training dataset | `sidix-sft-dataset` — 641 train / 72 eval |
| Training time | ~84 menit (GPU T4 x2 di Kaggle) |
| PEFT version | 0.18.1 |
| Training run | Kaggle `mighan/sidix-gen` Run #312153659 |

---

## Yang Termasuk dalam v1

- [x] **5 Persona**: MIGHAN (Kreatif), TOARD (Perencanaan), FACH (Akademik), HAYFAR (Teknis), INAN (Sederhana)
- [x] **ReAct Agent**: Thought→Action→Observation→Final Answer loop
- [x] **BM25 RAG**: Pencarian korpus lokal dengan sitasi chunk
- [x] **G1 Safety**: Deteksi injeksi, toksisitas, PII redaksi, confidence score
- [x] **Tipe Jawaban**: Badge fakta/opini/spekulasi otomatis
- [x] **Multibahasa**: id/en/ar output eksplisit
- [x] **Eufemisme**: Deteksi dan normalisasi bahasa tidak langsung
- [x] **Wikipedia Fallback**: Fallback ke API Wikipedia jika korpus lemah
- [x] **Streaming (SSE)**: `/ask/stream` kirim token real-time ke UI
- [x] **Rate Limiting**: RPM + daily cap per user
- [x] **Security Headers**: X-Frame-Options, CSP, dll
- [x] **Blue-Green Deploy**: Slot switch tanpa downtime
- [x] **Canary Routing**: A/B test model versi berbeda
- [x] **114 Projek Badar Artefak**: G1+G2+G3+G4+G5 semua selesai

---

## Yang Belum Diaktifkan (v1.1+)

| Fitur | Blocker | Estimasi |
|---|---|---|
| G2 Text-to-Image | Wire FLUX/SD ke `apps/image_gen/queue.py` | v1.1 |
| G3 Vision Caption | Wire LLaVA/BLIP ke `apps/vision/caption.py` | v1.1 |
| G3 OCR nyata | Install Tesseract + pytesseract | v1.1 |
| G3 Pose estimation | Install MediaPipe/YOLOv8 | v1.2 |
| ReAct LLM planner | Ganti `_rule_based_plan()` dengan LLM call | v1.1 |
| Redis session store | Ganti in-memory dict di `agent_serve.py` | v2 |
| TLS / HTTPS | Setup nginx/Caddy reverse proxy | Produksi |
| Multi-user auth | Token per-user di `rate_limit.py` | v2 |

---

## One-Line Launch (Setelah Deps Terinstall)

```powershell
# Terminal 1: Backend
.\scripts\tasks.ps1 serve

# Terminal 2: UI
.\scripts\tasks.ps1 ui
```

Buka `http://localhost:3000` — SIDIX v1 live! 🎉

---

## Catatan untuk Iterasi Berikutnya

Setelah v1 live, langkah paling berdampak untuk kualitas model:

1. **Tambah data SFT** — expand `sidix-sft-dataset` ke 5000+ sampel (sekarang 713)
2. **Evaluasi IHOS** — buat eval set berbasis prinsip sidq/sanad/tabayyun
3. **ReAct LLM planner** — ganti rule-based planner dengan LLM untuk planning yang lebih fleksibel
4. **Fine-tune v2** — jalankan kembali Kaggle notebook dengan warmup_steps (bukan warmup_ratio) + HF_TOKEN

---

*SIDIX v1 — own-stack, self-hosted, MIT License*
*Projek Badar — 114 tugas, 0 vendor API default*
