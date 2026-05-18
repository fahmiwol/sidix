# SIDIX Local Workstation Setup — ASUS TUF Gaming A15

**Tanggal setup:** 2026-04-19
**Hardware:** ASUS TUF Gaming A15 FA506QM
**Tujuan:** Workstation lokal untuk dev + test Sprint 3 image gen tanpa mengisi drive C:

---

## 🎯 Prinsip

Semua workload ML (Python, model weights, cache) **dikerjakan di drive D:**. Drive C: hanya untuk Windows + aplikasi existing. Tidak ada install ke C: untuk SIDIX.

---

## 🖥️ Spek Hardware (baseline)

| Komponen | Spec |
|----------|------|
| CPU | AMD Ryzen 7 5800H, 8 core / 16 thread, 3.2 GHz |
| GPU dedicated | NVIDIA GeForce RTX 3060 Laptop, **6 GB VRAM** |
| GPU memory total | 13.8 GB (6 dedicated + 7.8 shared) |
| RAM | 15.6 GB |
| OS | Windows 11 Home Single Language (Build 26200) |
| GPU driver | NVIDIA 32.0.15.7270 (3/2025) |
| Disk C: | 475 GB (OS — hemat ruang) |
| Disk D: | 931 GB (workspace SIDIX) |

**Konsekuensi untuk model pilihan:**
- SDXL 1.0 fp16 → fit di 6 GB dengan `enable_model_cpu_offload` + `attention_slicing`
- FLUX.1-schnell → butuh fp8 quantization untuk fit 6 GB (tight), preferably cloud
- Qwen2.5-VL 7B → tidak fit lokal, via cloud only

---

## 📂 Struktur Folder D:\sidix-local

```
D:\sidix-local\
├── hf_cache\            # HuggingFace model cache (HF_HOME)
│   ├── hub\             # model weights downloaded
│   └── xet\             # xet backend logs
├── torch_cache\         # PyTorch cache (TORCH_HOME)
├── pip_cache\           # pip package cache (PIP_CACHE_DIR)
├── models\              # manual model downloads (SDXL, FLUX)
├── output\              # hasil generate image
├── tmp\                 # ML temp files (bukan Windows Temp)
├── logs\                # log file
└── scripts\             # script Python lokal
```

**Catatan:** `python312\` dan `venv\` akan ditambah di Tahap C & D.

---

## 🔧 Environment Variables (User-level, persistent)

```
HF_HOME            = D:\sidix-local\hf_cache
TRANSFORMERS_CACHE = D:\sidix-local\hf_cache
HF_HUB_CACHE       = D:\sidix-local\hf_cache\hub
TORCH_HOME         = D:\sidix-local\torch_cache
PIP_CACHE_DIR      = D:\sidix-local\pip_cache
SIDIX_LOCAL_ROOT   = D:\sidix-local
```

Set via PowerShell (sudah dilakukan 2026-04-19):
```powershell
[Environment]::SetEnvironmentVariable("HF_HOME", "D:\sidix-local\hf_cache", "User")
# ... (lihat tahap B pada LIVING_LOG)
```

**Verifikasi:** buka PowerShell baru → `$env:HF_HOME` harus return `D:\sidix-local\hf_cache`.

---

## 📋 Progress Setup (status per 2026-04-19)

### ✅ Tahap A — Safe Cleanup C: (DONE 2026-04-19)

Dibersihkan tanpa menghapus user content:

| Item | Sebelum | Dibersihkan | Status |
|------|---------|------------|--------|
| Windows Temp | 3.34 GB | ~3.0 GB dikosongkan (file locked skip) | ✅ |
| npm cache | 3.3 GB | `npm cache clean --force` | ✅ |
| pip cache | 0.4 GB | `pip cache purge` (570 files, 410 MB) | ✅ |
| HuggingFace cache C: | 1.25 GB | pindah ke D:\sidix-local\hf_cache via robocopy | ✅ |

**TIDAK disentuh:** Chrome User Data, Adobe, Downloads, OneDrive, VS Code, .cursor, .claude, .gemini, Documents, Projects.

**Hasil:** C: free `8.7 GB → 15.57 GB` (+6.87 GB).

### ✅ Tahap B — Setup Workspace D: (DONE 2026-04-19)

- Struktur folder `D:\sidix-local\` + 8 subfolder dibuat.
- 6 environment variables di-set level User (persistent setelah logout/restart).
- Verifikasi env var ter-set: semua ✅.

### ✅ Tahap C — Install Python 3.12 ke D: (DONE 2026-04-19)

**Keputusan:** pakai **embeddable zip** bukan installer.
- MSI installer gagal exit code 3 (error 0x80070003 "path not found") — ada remnant Package Cache dari install Python 3.12 sebelumnya. Tidak worth debug.
- Embeddable zip (10.6 MB) extract ke `D:\sidix-local\python312\` — works in 5 detik.
- Edit `python312._pth` untuk uncomment `import site` (biar site-packages aktif).
- Bootstrap pip via `get-pip.py` → pip 26.0.1 terinstall.

Python 3.12.8 jalan dari `D:\sidix-local\python312\python.exe`.

### ✅ Tahap D — venv BATAL (tidak perlu) (DONE 2026-04-19)

**Keputusan:** skip venv. Embeddable Python tidak include module `venv`, dan karena Python di D:\sidix-local\python312\ **dedicated untuk SIDIX** (tidak dishare), venv redundant.

Install semua package langsung ke site-packages Python 3.12 embeddable → isolasi otomatis.

### ✅ Tahap E — PyTorch + diffusers terpasang (DONE 2026-04-19)

Install command:
```powershell
D:\sidix-local\python312\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
D:\sidix-local\python312\python.exe -m pip install diffusers transformers accelerate safetensors
```

Versi terinstall:
- torch 2.5.1+cu121
- torchvision (latest)
- diffusers 0.37.1
- transformers 5.5.4
- accelerate 1.13.0
- safetensors 0.7.0
- numpy 2.4.4

**Semua di `D:\sidix-local\python312\Lib\site-packages\` — bukan C:.**

Total install size: ~10 GB (torch paling besar).

### ✅ GPU Smoke Test (DONE 2026-04-19)

```
CUDA available: True
CUDA version: 12.1
GPU: NVIDIA GeForce RTX 3060 Laptop GPU
VRAM: 6.4 GB
Matmul 2048×2048: 542.7 ms (first run, cold; subsequent ~5 ms)
diffusers StableDiffusionXLPipeline: import OK
```

**GPU pipeline siap untuk SDXL inference.**

### ⏳ Tahap F — Download SDXL + test generate image
**BELUM dieksekusi.**

Plan:
1. Script Python download SDXL base 1.0 (~7 GB) ke `D:\sidix-local\models\sdxl-base-1.0`.
2. Generate 1 gambar test: "SIDIX logo test".
3. Verifikasi GPU digunakan (bukan CPU fallback).

### ⏳ Tahap G — Expose via ngrok → integrasi SIDIX brain
**BELUM dieksekusi.**

Plan:
1. Install ngrok (free tier).
2. FastAPI server lokal expose `/generate` endpoint.
3. ngrok tunnel → URL publik.
4. SIDIX brain `image_gen.py` call URL tersebut.

---

## 🚨 Safety Rules (selalu)

1. **Tidak ada install ke C:** — kecuali absolutely unavoidable (Python installer options dicek).
2. **Cache models selalu ke D:** via env vars.
3. **Sebelum hapus apapun**, list dulu, konfirmasi user.
4. **Workload aktif >80% durasi** → pakai laptop cooler atau throttle power plan.
5. **GPU temp check:** jangan sustained >85°C. Saat ini idle 50°C (normal).
6. **RAM usage monitor:** 11.1/15.6 GB terpakai saat ini. ML workload bisa push ke 13-14 GB. Tutup Chrome tabs yang tidak perlu saat generate.

---

## 🔄 Rollback Plan

Kalau ada yang salah:

| Masalah | Fix |
|---------|-----|
| Env var bikin app lain error | `[Environment]::SetEnvironmentVariable("HF_HOME", $null, "User")` hapus satu-satu |
| `D:\sidix-local` mau dihapus | `Remove-Item D:\sidix-local -Recurse -Force` (setelah venv deactivated) |
| Python 3.12 vs 3.14 konflik | Python 3.14 global tetap ada, tidak diubah — cukup jangan aktifkan venv D: |
| Model weights terlalu besar | `Remove-Item D:\sidix-local\models\<model_name> -Recurse` (model bisa redownload) |

Rollback semua = 5 menit, data user di C: tidak kesentuh.

---

## 📚 Referensi

- [Note 170](../brain/public/research_notes/170_gpu_provider_comparison_2026.md) — GPU provider (RunPod untuk cloud phase)
- [Note 171](../brain/public/research_notes/171_image_model_comparison_sdxl_flux_alternatif.md) — SDXL vs FLUX
- [Note 173](../brain/public/research_notes/173_image_gen_deployment_pattern.md) — Deployment Diffusers
- [ADR-001](decisions/ADR_001_sprint3_image_gen_stack.md) — Sprint 3 decision

---

**Owner dokumen:** Claude (koordinator Sprint 3).
**Next review:** setelah Tahap C (install Python 3.12) selesai.
