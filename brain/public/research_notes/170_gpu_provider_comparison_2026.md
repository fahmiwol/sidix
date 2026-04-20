---
sanad_tier: peer_review
tags: [research, gpu, infra, sprint-3, image-gen]
date: 2026-04-19
---

# 170 — GPU Provider Comparison untuk SIDIX Sprint 3

## 1. Kebutuhan SIDIX

- [FACT] SDXL base 1.0 minimum VRAM: 8 GB fp16, optimal 12–16 GB dengan refiner pipeline.
- [FACT] FLUX.1-schnell Apache-2.0 license (Black Forest Labs, 2024): ~24 GB fp16 optimal, bisa turun ke ~12 GB dengan fp8/4-bit quantization via `bitsandbytes` atau `torchao`.
- [FACT] Qwen2.5-VL-7B-Instruct: ~14–16 GB 4-bit (GPTQ/AWQ), ~28 GB fp16.
- [FACT] Pola workload SIDIX: user-triggered inference (bukan training 24/7), average ~5–30 request/jam di fase Baby→Child, burst saat content marketing push.
- [OPINION] Implikasi: serverless per-detik billing lebih efisien dibanding reserved instance untuk fase early. Baru switch ke reserved saat >100 req/jam sustained.

---

## 2. Kandidat Provider (Ranking per kriteria standing-alone)

| Provider | GPU Tersedia | Harga ~ (2025-Q4 kisaran, USD/jam) | Granularitas billing | Cold start | Region Asia | Catatan |
|----------|--------------|------------------------------------|----------------------|-----------|-------------|---------|
| **RunPod Serverless** | RTX 4090, A5000, A40, A100, L40S, H100 | 4090≈$0.34, A5000≈$0.26, A100 80GB≈$1.89, L40S≈$0.86 | per-detik | 3–15 s (warm pool) | Singapore, Jakarta (via community nodes) | Best for bursty inference; Docker container own |
| **Vast.ai Marketplace** | 4090, 3090, A40, A100 | 4090≈$0.20–0.35, A100 80GB≈$0.80–1.40 | per-jam (interruptible per-menit) | 30 s–beberapa menit | Globally distributed, banyak Asia node | Cheapest tapi reliability variable (host residential) |
| **Lambda Labs** | A100 40/80GB, H100, H200 | A100 80GB≈$1.29, H100≈$2.49 | per-menit | N/A (reserved) | US, not yet Asia direct | Reliability tinggi, latency Asia 150–250ms |
| **CoreWeave** | A100, H100, H200, MI300X | A100 80GB≈$2.21, H100≈$4.25 | per-jam reserved | N/A | US East/West, EU | Enterprise focus, ada SLA |
| **Modal** | A10G, A100, H100 | A10G≈$1.10, A100≈$3.40 | per-detik | 2–8 s | US, EU (Asia via proxy) | Serverless Python native, integrasi ML termudah |
| **Hugging Face Inference Endpoints** | T4, A10, A100 | A10≈$0.60, A100 40GB≈$3.20 | per-jam | 1–3 menit | US, EU (Asia via CloudFront) | Integrasi `diffusers` + model hub termudah |
| **Kaggle free** | T4×2, P100 | $0 (30 jam/mgg) | per-sesi manual | N/A | N/A | Hanya untuk training batch, tidak stable untuk inference prod |
| **Biznet Gio GPU** | A100, L40 (lokal Indonesia) | A100 40GB≈Rp 45k/jam (~$2.80) | per-jam reserved | N/A | Jakarta (lokal!) | Data residency Indonesia, tapi mahal + minimum commit |

[FACT] Harga di atas snapshot kisaran publik akhir 2025. Wajib verifikasi live via dashboard provider sebelum commit.

[SPECULATION] Trend 2026: harga 4090 dan A100 turun ~15–25% per tahun karena lonjakan supply H100/H200. Budget Sprint 3 aman pakai proyeksi 2025.

---

## 3. Rekomendasi per Fase Roadmap

### Baby Sprint 3 (MVP image gen, low traffic 5–30 req/jam)
**Pilihan 1: RunPod Serverless (4090 atau L40S)**
- Harga efektif: ~$0.34/jam × 1–2 jam aktif/hari = **~$15–25/bulan**
- Cold start 3–15 detik acceptable untuk MVP
- Docker container own infra SDXL/FLUX, maintain portability
- Billing per-detik → zero waste

**Alternatif: Modal dengan A10G**
- Integrasi Python native (decorator `@modal.function`)
- Cocok kalau prioritas dev speed > cost optimization

### Child Multi-model (SDXL + Qwen2.5-VL + TTS/ASR, medium traffic 50–200 req/jam)
**Mix strategy:**
- Image gen: RunPod Serverless A100 80GB (batch multi-user per warm instance)
- VLM: Hugging Face Endpoint A10 (reserved, latency konsisten)
- TTS/ASR: self-host CPU di VPS existing (whisper.cpp + Piper — ga butuh GPU)

Estimasi: **~$80–150/bulan** total untuk 200 req/jam average.

### Adolescent Self-evolving (retraining LoRA periodik)
**Spot/interruptible training:**
- Vast.ai A100 spot — cheapest untuk training yang bisa di-resume
- Kaggle free untuk validasi + early experiments (sudah dipakai SIDIX, keep)
- Checkpoint ke S3-compatible storage (Wasabi/R2 — $5/mo untuk 1 TB)

---

## 4. Setup Step Top 1: RunPod Serverless

```
1. Registrasi https://runpod.io, top up $20 credit minimum.
2. Build Docker image:
   FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04
   RUN pip install diffusers torch transformers safetensors
   COPY handler.py /
   CMD ["python", "-u", "handler.py"]
3. Push ke Docker Hub atau RunPod registry.
4. Buat serverless endpoint:
   - GPU: RTX 4090 (Start small)
   - Max workers: 3
   - Idle timeout: 60s
   - Container disk: 20 GB (model cache)
5. SIDIX brain_qa baru: apps/brain_qa/brain_qa/image_gen.py
   - Env var: RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID
   - Function call_image_gen(prompt, width, height, steps)
   - Return: image_url atau base64
6. Monitoring:
   - RunPod dashboard (built-in usage graph)
   - Custom: log request_id + latency + cost_estimate ke .data/image_gen_log.jsonl
   - Alert: cost > $50/bulan → Threads DM ke admin
```

[FACT] RunPod API docs: https://docs.runpod.io/serverless/overview (verified 2025).
[OPINION] Handler pattern lebih simple dibanding ComfyUI JSON workflow untuk MVP.

---

## 5. Risiko + Mitigasi

| Risiko | Likelihood | Dampak | Mitigasi |
|--------|-----------|--------|----------|
| Vendor lock-in RunPod | Medium | Medium | Docker image portable + abstraction layer `image_gen.py` interface |
| Cost runaway (abuse/bug) | Medium | High | Hard budget cap di RunPod dashboard + rate limit per user session di SIDIX |
| Region down | Low | Medium | Fallback ke Vast.ai workers (second Docker target) |
| Cold start >30s = UX buruk | Medium | Medium | Warm pool min_workers=1 (tambah ~$5/mo) atau "queued, notify when ready" pattern |
| GDPR / data residency Indonesia | Medium | Medium untuk enterprise | Fase Baby pakai RunPod (jurisdiksi global OK), fase Adult pindah ke Biznet Gio untuk enterprise Indonesia |
| Harga naik tiba-tiba | Low | Low | Auto-snapshot Docker + portable ke Vast.ai dalam 1 jam switch |

---

## 6. Keputusan

**Top 1: RunPod Serverless 4090 untuk Baby Sprint 3.**
- Alasan: per-detik billing, Singapore region (latency Asia OK), Docker portability, cost predictable untuk MVP traffic.
- Estimated Sprint 3 launch budget: **$20–40 untuk 2 minggu testing + 1 bulan soft launch**.

**Top 2: Modal untuk dev experience lebih smooth, trade-off 2× harga.**
- Pilih Modal kalau tim prefer Python-first deployment pattern dan budget cushion lebih lega.

**Reject untuk sekarang:** Lambda Labs (no Asia), CoreWeave (enterprise overhead), Biznet (mahal untuk MVP), Kaggle (tidak prod-grade).

---

## Sanad
- RunPod pricing: https://www.runpod.io/pricing (akses 2025-Q4)
- Vast.ai: https://vast.ai (akses 2025-Q4)
- FLUX.1 license: https://huggingface.co/black-forest-labs/FLUX.1-schnell (Apache-2.0)
- SDXL: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 (CreativeML Open RAIL++)
- Qwen2.5-VL: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct
- Lambda Labs: https://lambdalabs.com/service/gpu-cloud
- Modal: https://modal.com/pricing
- Biznet Gio: https://biznetgio.com/service/gpu
