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

### ⏳ Tahap C — Install Python 3.12 ke D:
**BELUM dieksekusi.**

Plan:
1. Download Python 3.12.x installer resmi dari python.org.
2. Install ke `D:\sidix-local\python312\`.
3. **Uncheck "Add to PATH"** (biar tidak tabrakan dengan Python 3.14 existing).
4. Aktifkan via path eksplisit: `D:\sidix-local\python312\python.exe`.

### ⏳ Tahap D — Python venv + test basic imports
**BELUM dieksekusi.**

Plan:
1. `D:\sidix-local\python312\python.exe -m venv D:\sidix-local\venv`.
2. Aktivasi venv: `D:\sidix-local\venv\Scripts\Activate.ps1`.
3. Test `import sys; print(sys.prefix)` — harus show venv path di D:.

### ⏳ Tahap E — Install PyTorch + diffusers
**BELUM dieksekusi.**

Plan:
```powershell
# Dalam venv aktif
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install diffusers transformers accelerate safetensors
```

Download ~3 GB → masuk ke `D:\sidix-local\venv\Lib\site-packages` (bukan C:).

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
