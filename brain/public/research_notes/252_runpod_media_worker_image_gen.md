# 252 — Sprint 14b SHIPPED: RunPod mighan-media-worker wired untuk hero image generation

**Date**: 2026-04-27 (sesi-baru, post-Sprint 14)
**Sprint**: 14b (Sprint 14 extension)
**Status**: ✅ SHIPPED + DEPLOYED (LIVE test pending — see follow-up)
**Authority**: Note 248 hero use-case — full visual deliverable

---

## Apa yang di-ship

Sprint 14 kasih 8 production-ready prompts. Sprint 14b **render 3 hero asset langsung ke PNG file** via RunPod `mighan-media-worker` (48GB GPU SDXL/Flux unified worker).

Hero asset rendered:
1. **Hero Mascot** — full body, white background, ready-for-cutout
2. **Logo Mark** — minimalist, single-color compatible
3. **Social Post** — square, brand color dominant

User opt-in via flag `gen_images=true` (default False supaya stage chain murni LLM tetap fast/cheap).

### File baru
- `apps/brain_qa/brain_qa/runpod_media.py` (244 lines)

### File diubah
- `apps/brain_qa/brain_qa/creative_pipeline.py` (+gen_images flag, +rendered_images list, +image embed di report.md)
- `apps/brain_qa/brain_qa/agent_serve.py` (CreativeBriefRequest + endpoint accept gen_images)

### API contract mighan-media-worker (per `/root/mighantect-3d/runpod-media-worker/media_server.py`)

```
POST https://api.runpod.ai/v2/{RUNPOD_MEDIA_ENDPOINT_ID}/runsync
Authorization: Bearer {RUNPOD_API_KEY}
Body: {"input": {
  "tool": "image",
  "prompt": "...",
  "negative_prompt": "...",
  "width": 1024, "height": 1024,
  "num_inference_steps": 30,
  "guidance_scale": 7.5,
  "seed": null,
  "model": "sdxl"        # or "pollinations" (no-GPU fallback)
}}

Response: {"output": {
  "success": true,
  "image_base64": "<png>",
  "format": "png",
  "width": ..., "height": ...,
  "model": "sdxl",
  "generation_time": 12.5
}}
```

### ENV setup (production VPS)

```
RUNPOD_API_KEY              (existing, shared dengan vLLM)
RUNPOD_MEDIA_ENDPOINT_ID    (BARU, copied from /root/.env)
RUNPOD_MEDIA_TIMEOUT=300    (5 min, untuk cold start tolerance)
```

PM2 brain auto-load via `start_brain.sh` `set -a; source .env`.

---

## Smart prompt selection — `pick_hero_prompts()`

Dari 8 asset prompts stage 5, picker prioritas: **HERO MASCOT > LOGO MARK > SOCIAL POST** (3 deliverable visual paling impactful untuk demo brand identity).

Strip `[LABEL]` prefix dari prompt body sebelum kirim ke SDXL — supaya SDXL prompt clean. Label dipakai sebagai filename PNG.

Fallback: kalau prompt 8 stage 5 tidak match label hero, ambil top-N apa adanya.

---

## Mengapa flag opt-in (default False)

- Image gen + cold start mighan-media-worker = **+2-5 menit** per pipeline run
- LLM-only pipeline = ~3-5 menit
- Total dengan `gen_images=true`: 5-10 menit per brief
- Customer/dev sering iterate prompt-only dulu sebelum render → opt-in lebih efisien
- Cost: image render = GPU credit lebih mahal dari LLM call

---

## Compound stack (3 sprint sesi)

```
Sprint 12 CT 4-pilar     → cara berpikir UTZ
Sprint 14 5-stage         → 8 production prompts + UTZ voice
Sprint 14b mighan-media   → 3 actual rendered hero PNG
Sprint 15 Visioner        → autonomous trend sensing
```

= SIDIX dari research note jadi **AI agent yang accept brief → bundled visual deliverable** end-to-end.

---

## Architecture decisions

### Why hero=3 (mascot + logo + social), bukan render semua 8?

- 3 deliverable = brand identity essentials (visual identity + applications)
- Render 8 asset = 8x cost + 8x time, diminishing return
- Customer biasa pakai 3 hero untuk kickoff, sisanya by demand
- User adjustable via `gen_images_n` (cap 8 di logic)

### Why simpan PNG ke disk, bukan stream base64 to client?

- Public URL pattern: `app.sidixlab.com/static/creative_briefs/<slug>/images/<label>.png`
- Customer/UMKM bisa share URL langsung, no base64 paste
- Persisted artifact = audit trail untuk regenerasi
- File size 1024x1024 PNG = 1-3MB, base64 transport berat

### Why no SSE / async streaming?

- Sprint 14b minimal viable = sync runsync
- Future Sprint 14c: async via /run + polling /status (streaming progress to client) bila pipeline tumbuh > 10 menit
- For now, browser timeout 60s → API sync OK kalau via curl/server-side, tidak via direct browser

---

## Mandatory loop coverage

```
1. CATAT (start)        ✅
2. IMPL                 ✅ runpod_media.py + pipeline wire + endpoint update
3. TESTING (offline)    ✅ syntax pass, pick_hero_prompts pass, media_available
                            False without env (graceful)
4. ITERASI              (none — single pass)
5. REVIEW               ✅ diff bersih, boundary OK, security audit clean
6. CATAT                ✅
7. VALIDASI             🔄 pending — LIVE test gen_images=true running
8. QA                   ✅ no secrets in commit (ENV vars referenced by name only)
9. CATAT (note 252)     ✅ ini
10. DEPLOY              ✅ git pull on VPS + .env update + brain restart +
                            media_available verified True
```

---

## Production state

- VPS commit: `a77bc42` (was `8ac33f6`)
- ENV `/opt/sidix/.env`: `RUNPOD_MEDIA_ENDPOINT_ID` set, `RUNPOD_MEDIA_TIMEOUT=300` set
- Brain restart: pickup new env via start_brain.sh source
- Verification: `media_available()` returns True from brain context
- Endpoint: `POST /creative/brief` dengan `gen_images=true` flag

---

## Next sprint candidates

**Sprint 14c — Multi-persona post-pipeline enrichment** (3-4 jam):
- OOMAR commercial review post-creative
- ALEY trend research enrichment dari corpus + visioner cluster

**Sprint 14d — TTS persona voice** — wire mighan-media-worker `tool=tts` untuk audio version brand voice (UTZ persona voice ke MP3, hands-free brand identity demo).

**Sprint 14e — 3D mascot via TripoSR** — wire `tool=3d` (RUNPOD_3D_ENDPOINT_ID juga sudah set) untuk render 3D model dari rendered hero mascot 2D (image-to-3D pipeline).

**Sprint 13 (DoRA persona)** — masih defer 2-4 minggu sampai visioner corpus matang.

**Sprint 16-20 (Intuisi/Wisdom)** — post core arch.
