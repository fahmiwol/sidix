---
sanad_tier: peer_review
tags: [research, deployment, image-gen, comfyui, diffusers, sprint-3]
date: 2026-04-19
---

# 173 — Image Gen Deployment Pattern: ComfyUI vs Diffusers vs Custom FastAPI vs Cog

## 1. Opsi yang Dibandingkan

| Opsi | Apa itu | Typical deploy |
|------|---------|----------------|
| **A. ComfyUI + workflow JSON** | Node-based visual workflow engine. Save pipeline sebagai JSON, load via API. | ComfyUI server + `/prompt` API endpoint |
| **B. Diffusers library (Python)** | Huggingface Diffusers — Python class `DiffusionPipeline`. | FastAPI + `diffusers` di RunPod container |
| **C. Custom FastAPI + transformers raw** | Load model via `transformers` + custom forward pass. | FastAPI container, full control |
| **D. Replicate Cog** | Container spec + `cog.yaml` predictor. Bisa deploy ke Replicate atau self-host. | `cog run` atau `cog push` |

---

## 2. Kriteria Evaluasi

| Kriteria | Weight | Rationale untuk SIDIX |
|----------|--------|----------------------|
| Maintenance effort | 25% | Solo founder, minim waktu untuk debug |
| LoRA support | 20% | Sprint 4+ butuh LoRA Nusantara fine-tune |
| Memory efficiency | 15% | Target RunPod 4090 (16 GB effective) |
| Observability (logs, metrics) | 15% | Debug + cost tracking wajib |
| Community support | 10% | Kalau stuck, ada resource bantu |
| Portability (vendor independence) | 10% | Standing-alone principle |
| Learning curve | 5% | Tim = 1 founder + agent |

---

## 3. Komparasi Detail

### A. ComfyUI + workflow JSON

**Pros:**
- Node-based visual — mudah prototyping workflow complex (multi-stage refiner, ControlNet chain).
- LoRA loading matang, ecosystem plugin ribuan.
- Community sangat aktif (r/comfyui, Civitai integration).
- Workflow JSON portable antar instance.

**Cons:**
- [FACT] API ComfyUI kurang stable di edge cases (workflow parsing error hard to debug).
- [OPINION] Overhead monolith — 500+ MB runtime, boot 30–60s di cold start.
- Observability terbatas (logs tidak structured, metric terpisah).
- State management: workflow JSON bisa drift dengan versi node update.

**Use case cocok:** prototyping cepat + eksperimen ControlNet + multi-LoRA.

### B. Diffusers library (Python)

**Pros:**
- [FACT] Python-native, integration dengan SIDIX `brain_qa` seamless (same venv, same language).
- Dokumentasi Huggingface lengkap (tutorial + examples).
- LoRA support via `.load_lora_weights()` clean API.
- Memory efficient: `enable_model_cpu_offload()`, `enable_attention_slicing()`, `enable_xformers()`.
- Observability mudah (custom Python logging + OpenTelemetry).

**Cons:**
- Versioning: update diffusers kadang breaking change di pipeline config.
- Pipeline complex multi-stage (base+refiner+ControlNet) manual assembly.
- Kurang ecosystem plug-and-play seperti ComfyUI.

**Use case cocok:** production inference stable + integration native dengan backend Python.

### C. Custom FastAPI + transformers raw

**Pros:**
- Full control sampai layer internals (tensor manipulation custom).
- Minimal dependency.
- Best untuk research model yang tidak didukung diffusers.

**Cons:**
- [OPINION] **Effort tinggi**: reimplement scheduler, UNet forward, VAE decoder.
- Bug prone di attention mechanism.
- Tidak ada benefit untuk SIDIX saat ini (kita pakai model mainstream).

**Use case cocok:** bukan SIDIX Sprint 3. Mungkin Adolescent stage kalau custom architecture.

### D. Replicate Cog

**Pros:**
- Container spec simpel (`cog.yaml`).
- Bisa deploy ke Replicate.com (vendor) atau self-host (`cog serve`).
- Standard predictor interface.

**Cons:**
- [FACT] Replicate.com = vendor (violate standing-alone). Self-host mode OK tapi kurang maintained.
- Tooling cog-specific, lock-in mild.
- Ecosystem lebih kecil dari Diffusers + ComfyUI.

**Use case cocok:** kalau SIDIX ingin distribute model ke komunitas (bukan untuk inference internal).

---

## 4. Matrix Skoring

Skala 1–5 (5 = terbaik untuk SIDIX).

| Kriteria (bobot) | ComfyUI | Diffusers | Custom FastAPI | Cog |
|------------------|---------|-----------|----------------|-----|
| Maintenance (25%) | 3 | **5** | 2 | 3 |
| LoRA support (20%) | **5** | 4 | 2 | 3 |
| Memory efficiency (15%) | 3 | **5** | 4 | 3 |
| Observability (15%) | 2 | **5** | 5 | 3 |
| Community (10%) | **5** | 5 | 2 | 3 |
| Portability (10%) | 4 | **5** | 5 | 3 |
| Learning curve (5%) | 3 | **5** | 1 | 4 |
| **Weighted total** | 3.45 | **4.80** | 2.85 | 3.10 |

---

## 5. Rekomendasi

**Top 1: Diffusers library wrapped dalam FastAPI container.**

Pattern yang diusulkan:

```
apps/brain_qa/brain_qa/image_gen.py
  ├── ImageGenClient (interface abstraction)
  │   ├── call_flux(prompt, **kwargs) → bytes
  │   └── call_sdxl(prompt, **kwargs) → bytes (fallback)
  └── via HTTP ke RunPod container

runpod_handler/
  ├── Dockerfile (python:3.11 + CUDA + diffusers + torch)
  ├── handler.py (RunPod serverless runner)
  │   └── load FLUX pipeline sekali di init, reuse antar request
  └── requirements.txt
```

**Alasan pilih Diffusers:**
1. Integrasi native dengan SIDIX brain (Python end-to-end).
2. Memory management mature (`enable_model_cpu_offload` otomatis fit di 4090).
3. LoRA loading clean untuk fine-tune Nusantara di Sprint 4.
4. Observability full control (Python logging → journalctl/loki).
5. Portable: Docker image portable ke Vast/Modal tanpa rewrite.

**Top 2: ComfyUI untuk eksperimen sampingan (eksplorasi ControlNet Nusantara pose).**

Pattern: ComfyUI jalan di workstation lokal untuk prototyping, workflow produksi tetap di Diffusers.

**Reject:** Custom FastAPI raw (effort terlalu tinggi), Cog (vendor risk + ecosystem kecil).

---

## 6. Architecture Diagram (tekstual)

```
┌─────────────────────────────────────┐
│ SIDIX User (via app.sidixlab.com)  │
└──────────────┬──────────────────────┘
               │ POST /chat dengan intent "image"
               ▼
┌─────────────────────────────────────┐
│ SIDIX Brain (ctrl.sidixlab.com)     │
│  ├── Persona: MIGHAN (creative)     │
│  ├── ReAct loop                     │
│  │   ├── detect_nusantara_entities  │
│  │   ├── enrich_prompt              │
│  │   └── call tool: text_to_image   │
│  └── image_gen.py ImageGenClient    │
└──────────────┬──────────────────────┘
               │ HTTPS (RUNPOD_API_KEY)
               ▼
┌─────────────────────────────────────┐
│ RunPod Serverless (4090 GPU)        │
│  ├── Docker: diffusers + FLUX.1     │
│  ├── handler.py load once, reuse    │
│  └── return image bytes base64      │
└──────────────┬──────────────────────┘
               │ Image bytes
               ▼
┌─────────────────────────────────────┐
│ SIDIX Brain                         │
│  ├── Save to .data/generated/       │
│  ├── Log: latency, cost estimate    │
│  └── Return URL + sanad chain       │
└──────────────┬──────────────────────┘
               │ Response
               ▼
┌─────────────────────────────────────┐
│ SIDIX User (render image in chat)   │
└─────────────────────────────────────┘
```

---

## 7. Implementation Checklist untuk Sprint 3

- [ ] Week 1: Dockerfile + handler.py + local test di workstation GPU (atau Kaggle)
- [ ] Week 1: Push ke RunPod registry, create serverless endpoint
- [ ] Week 2: `image_gen.py` di brain_qa, env var config, unit test mock
- [ ] Week 2: Register `text_to_image` tool di agent_tools.py TOOL_REGISTRY
- [ ] Week 3: Integration test e2e: user prompt → generated image → response chat
- [ ] Week 3: Rate limit + cost cap + logging
- [ ] Week 4: Dengan Nusantara KB (note 172) — enriched prompt test, benchmark
- [ ] Week 4: UI SIDIX — display image dalam chat, download button, citation display

---

## Sanad

- Hugging Face Diffusers docs: https://huggingface.co/docs/diffusers
- Diffusers GitHub: https://github.com/huggingface/diffusers
- ComfyUI repo: https://github.com/comfyanonymous/ComfyUI
- ComfyUI API docs: https://github.com/comfyanonymous/ComfyUI/blob/master/server.py
- RunPod serverless handler pattern: https://docs.runpod.io/serverless/workers/handlers/overview
- Replicate Cog: https://github.com/replicate/cog
- FLUX.1-schnell quickstart: https://huggingface.co/black-forest-labs/FLUX.1-schnell
- Memory optimization Diffusers: https://huggingface.co/docs/diffusers/optimization/memory
- Akses referensi: 2025-Q4 sampai 2026-04-19

## Catatan Integrasi

- **Note 170** (RunPod): deployment target → `runpod_handler/` bagian dari proposal ini.
- **Note 171** (FLUX.1-schnell): model yang akan di-load di handler.py.
- **Note 172** (Nusantara KB): enrichment terjadi di SIDIX Brain sebelum kirim ke handler (CPU, instant lookup).
