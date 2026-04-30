> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
name: Sprint 8b — Generative Core Implementation
description: FLUX.1 image gen, Piper TTS, multi-lang code validator, project scaffold generator — arsitektur, keputusan desain, dan pola degradasi graceful
type: project
---

# Sprint 8b — Generative Core: FLUX.1 · TTS · Validator · Scaffold

**Tanggal**: 2026-04-24
**Status**: SELESAI — commit `cfcfaea`, 22 tests passed

## Apa yang Diimplementasikan

Sprint 8b menambahkan empat kapabilitas generatif baru ke SIDIX:

| Modul | File | Fungsi utama |
|---|---|---|
| FLUX.1 Image Gen | `apps/image_gen/flux_pipeline.py` | Generate gambar dari teks |
| Piper TTS | `apps/audio/tts_engine.py` | Convert teks ke audio WAV |
| Code Validator | `brain/tools/code_validator.py` | Validasi syntax + security scan |
| Scaffold Generator | `brain/tools/scaffold_generator.py` | Boilerplate project baru |

---

## FLUX.1 Image Generation Pipeline

### Arsitektur
- Model: `black-forest-labs/FLUX.1-schnell` (4-step, 8-12GB VRAM)
- Lazy load: pipeline TIDAK diload saat startup — hanya saat request pertama
- Device auto-detection: CUDA → MPS (Apple) → CPU
- Singleton pattern: satu instance `FluxPipeline` di-share semua request

### Strategi Degradasi
1. **FLUX.1 via diffusers** (torch+CUDA/MPS/CPU): kualitas penuh
2. **Mock SVG placeholder**: jika `diffusers`/`torch` tidak terinstall, atau `SIDIX_IMAGE_MOCK=1`

### Kontrol via Env
```
SIDIX_IMAGE_MODEL   — model ID (default: black-forest-labs/FLUX.1-schnell)
SIDIX_IMAGE_DEVICE  — "cuda"|"cpu"|"mps"|"auto"
SIDIX_IMAGE_MOCK    — "1" paksa mock mode
```

### Kenapa FLUX.1 bukan SDXL
- SDXL lama perlu URL server eksternal (`SIDIX_IMAGE_GEN_URL`) — melanggar prinsip Standing Alone
- FLUX.1-schnell: 4 steps vs 20-50 steps SDXL → 5-10x lebih cepat
- MIT license, bisa self-host
- Graceful fallback ke SVG sehingga agent tidak crash kalau GPU tidak ada

---

## Piper TTS Engine

### Arsitektur
- Backend: Piper CLI/Python package (CPU-capable, MIT license)
- 4 bahasa: `id` (Ariani), `en` (Lessac), `ar` (Kareem), `ms` (Kamarulzaman)
- Output: WAV 22050Hz mono 16-bit PCM

### Strategi Degradasi
1. **Piper CLI** (via subprocess): full TTS
2. **piper-tts Python package** (via import): alternatif jika CLI tidak ada
3. **Stub WAV** (valid RIFF header + silence): jika Piper tidak tersedia — player tidak crash

### Stub WAV Design
- Penting: stub harus WAV valid (RIFF header benar), bukan file kosong
- Player audio akan error kalau diterima file 0-byte atau header rusak
- Implementasi: `struct.pack('<4sI4s...')` mengisi RIFF/fmt/data chunks dengan benar

### Durasi Estimate
Dihitung dari word count tanpa menunggu synthesis selesai:
- Indonesia: ~150 kata/menit
- English: ~140 kata/menit
- Formula: `(words / wpm) * 60 / speed`

---

## Code Validator (Multi-Language)

### Bahasa yang Didukung
| Bahasa | Backend | Dependency |
|---|---|---|
| Python | `ast.parse` | stdlib (zero-dependency) |
| JavaScript | `node --input-type=module --check` | Node.js (opsional) |
| TypeScript | `tsc --noEmit` | TypeScript compiler (opsional) |
| SQL | Quote balance + semicolon count | stdlib |
| HTML | Tag balance stack (regex) | stdlib |

### Security Scan
Pattern berbahaya per bahasa:
- Python: `eval(`, `exec(`, `os.system(`, `__import__`, dll
- JavaScript: `eval(`, `innerHTML =`, `dangerouslySetInnerHTML`, dll
- SQL: `DROP TABLE`, `TRUNCATE`, `DELETE FROM`
- HTML: `<script>` inline, `onerror=`, `javascript:`

**Bukan pengganti SAST** (Semgrep/Bandit) — cukup untuk guard awal output agent.

### Return Format
```python
{
  "valid": True | False | None,  # None = validator tidak tersedia
  "errors": [{"line": int, "col": int, "msg": str, "type": str}],
  "warnings": [str],
  "security": [{"pattern": str, "severity": "warning", "msg": str}],
  "lang": str,
}
```

---

## Scaffold Generator

### Templates
| Template | Stack | Files |
|---|---|---|
| `fastapi` | Python FastAPI + uvicorn | main.py, router, requirements.txt, Dockerfile, .env.example |
| `react_ts` | React 18 + TypeScript + Vite + Tailwind | package.json, App.tsx, main.tsx, tsconfig.json, index.html |
| `landing` | Static HTML/CSS (Tailwind CDN) | index.html saja |

### Design Decision: `ScaffoldResult` sebagai Data Object
- Return `ScaffoldResult` (dataclass) bukan langsung tulis ke disk
- Agent yang menentukan apakah file ditulis atau hanya ditampilkan
- Memudahkan testing (tidak perlu mock filesystem)

---

## Wiring ke Agent System

### agent_tools.py Changes
1. `_tool_text_to_image`: drop SDXL URL dependency → pakai `FluxPipeline`
2. `_tool_code_validate`: Python-only → multi-lang + security scan
3. `_tool_scaffold_project`: tool baru (total 36 tools di registry)

### agent_serve.py Endpoints Baru
```
POST /generate/image   → ImageGenRequest → ImageGenResponse
POST /tts/synthesize   → TTSRequest      → TTSResponse
```

### Path Resolution Pattern
```python
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from apps.image_gen.flux_pipeline import generate_image
```
`parents[3]` dari `apps/brain_qa/brain_qa/agent_tools.py` = repo root `/opt/sidix/`.

---

## Keterbatasan

- FLUX.1 butuh 8-12GB VRAM untuk full quality — VPS biasanya CPU-only → mock mode default
- Piper models (~60MB per voice) harus didownload manual sebelum bisa TTS nyata
- Code validator JS/TS butuh Node.js/TypeScript terinstall di server
- Scaffold generator tidak menulis file ke disk — perlu tool terpisah untuk eksekusi scaffold

## Next Sprint
- Sprint 8c: DB connection pool async (`apps/brain_qa/brain_qa/db/connection.py`)
- Sprint 8c: `jariyah_collector.py` modul terpisah (saat ini masih inline di agent_serve)
- Sprint 8c: `branch_manager.py` untuk multi-tenant agency branches
- VPS: install Piper binary + download voice models id+en

**Why**: Konfigurasi produksi yang benar = TTS nyata bisa langsung aktif.
**How to apply**: Prioritas instalasi Piper di VPS sebelum sprint 8c dimulai.
