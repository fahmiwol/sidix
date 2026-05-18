# 251 — Sprint 14 SHIPPED: Creative Pipeline Hero Use-Case

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-27 (sesi-baru, post-Sprint 15 deploy)
**Sprint**: 14
**Status**: ✅ SHIPPED + DEPLOYED to production
**Authority**: Note 248 line 178-198 (HERO USE-CASE)

---

## Apa yang di-ship

Hero use-case dari note 248: *"AI Agent yang nerima brief 'maskot brand kawaii ulat kuning' dan menghasilkan output END-TO-END: konsep + brand + copy + landing + ads — DALAM 1 ALUR, dengan suara persona UTZ yang berbeda fundamental dari ChatGPT/Midjourney/generic AI"*.

### Pipeline 5-stage

```
Brief teks
  → Stage 1 CONCEPT       (verbal vision + mood + visual direction)
  → Stage 2 BRAND         (color palette + typography + voice tone)
  → Stage 3 COPY          (5 variants: hook/feature/story/CTA/playful)
  → Stage 4 LANDING       (landing page outline markdown sections)
  → Stage 5 ASSET PROMPTS (8 SDXL/Midjourney/3D-tool ready prompts)

Output: bundled deliverable
  - .data/creative_briefs/<slug>/report.md
  - .data/creative_briefs/<slug>/metadata.json
  - .data/creative_briefs/<slug>/asset_prompts.txt
```

### Cognitive engine
- **UTZ creative-director persona** (voice: aku/kita, ekspresif, metaforis, Gaga method)
- **CT 4-pilar lens** dari Sprint 12 (dekomposisi → pattern → abstraksi → algoritma)
- Tiap stage = berbeda system prompt yang refine UTZ lens ke task-specific

### File baru
- `apps/brain_qa/brain_qa/creative_pipeline.py` (416 lines)
- `apps/brain_qa/brain_qa/agent_serve.py` (+32 endpoint, +6 model class)

### Endpoint
```
POST /creative/brief
Body: {"brief": "<text>", "skip_stages": [...], "persist": true}
```

---

## Differentiator vs competitor

| Tool | Output |
|---|---|
| ChatGPT | Satu jawaban teks generik |
| Midjourney | Satu image (tidak ada brand/copy/landing) |
| Adobe Firefly | Image + edit, mahal, no per-persona distinct |
| Canva AI | Template-based, tidak adaptive ke brief Indonesia |
| **SIDIX Sprint 14** | **5 deliverable terintegrasi (concept + brand + copy + landing + asset prompts) dari 1 brief, dengan UTZ voice distinct, BAHASA INDONESIA NATIVE** |

Pasar UMKM Indonesia: 5 juta brand butuh creative deliverable affordable, beda style per brand, no vendor lock. **SIDIX fit sempurna**.

---

## Architecture decisions

### Why output prompts daripada actual images?

- Image gen butuh GPU heavy (SDXL run di RunPod separate endpoint, 5-15 sec per image, 8 image = 1+ menit)
- Customer/user punya tool image gen sendiri (Midjourney subscription, Stable Diffusion local)
- **Output prompt = distinct value SIDIX**: cara berpikir UTZ, bukan cara render
- Stretch: wire ke RunPod SDXL endpoint kalau ada (Sprint 14b)

### Why 5 stages bukan 1 monolithic?

- Tiap stage punya focus berbeda (concept = visual thinking, brand = systematic, copy = voice modulation, landing = structure, prompts = technical specifier)
- Stage chaining = output stage N input stage N+1 → konsistensi
- Dapat skip stage untuk testing/cost-control (`skip_stages: ["copy","landing"]`)
- Lebih mudah iterasi per stage dibanding rewrite seluruh pipeline

### Why UTZ persona, bukan multi-persona?

- Hero use-case = **creative brief**. Domain UTZ.
- 5-persona democratic synthesis = dipakai untuk visioner foresight (Sprint 15) atau debate
- Untuk creative deliverable, single voice cohesive lebih bagus daripada 5 voice mencampur
- Future Sprint 16+: bisa add OOMAR market validation review atau ALEY trend research enrichment sebagai post-pipeline layer

---

## Iteration history (mandatory loop)

```
1. CATAT (start)         ✅
2. IMPL                  ✅ creative_pipeline.py + endpoint
3. TESTING (offline)     ✅ mock LLM, 5 stages, 8 prompts, 3 files - PASS
4. ITERASI #1            ✅ live deploy revealed FastAPI 422 (inline class
                            tidak resolve sebagai body) → moved class ke
                            module top-level → fix commit 18bab4b
5. REVIEW                ✅ diff bersih, security audit clean
6. CATAT                 ✅ post-impl + post-iterasi
7. VALIDASI (live VPS)   ✅ real LLM full pipeline 3 stages
8. QA                    ✅ no secrets in commit, endpoint reachable
9. CATAT (note 251)      ✅ ini
10. DEPLOY               ✅ git pull on VPS + pm2 restart
```

**Iteration #1 root cause**: Pydantic class defined inline inside `create_app()` function tidak ter-resolve sebagai body model — FastAPI default ke query parameter handling. Pattern existing model di file (ForesightRequest, ChatRequest, dll) semua di module top-level. Conformance ke pattern existing → fix.

---

## Production verified

VPS commit `18bab4b` (post-fix), endpoint live di:
- Internal: `http://localhost:8765/creative/brief`
- Public: `https://ctrl.sidixlab.com/creative/brief` (via nginx proxy)

---

## Compound dengan sprint sebelumnya

- **Sprint 12 (CT 4-pilar)** kasih cara berpikir UTZ → creative_pipeline pakai sebagai cognitive engine
- **Sprint 15 (Visioner)** kasih trending cluster → bisa di-feed sebagai brief input ("buatkan brand identity untuk topik trending: `agent`/`creative`/`generative`")
- **Sprint 14 ini** kasih artifact tangible → demo-able ke calon UMKM customer

3 sprint sesi ini bersama = full stack: trend sensing → cognitive engine → creative output.

---

## Next sprint candidates

**Sprint 13 (DoRA Persona)** — sekarang bisa shipped dengan training data yang JAUH lebih kaya:
- CT lens scaffolding (Sprint 12)
- Visioner weekly emerging topics (Sprint 15)
- Creative pipeline output sebagai per-persona voice samples (Sprint 14)
3 dataset source = synthetic Q&A 1000-2000 pasangan per persona qualitas tinggi.

**Sprint 14b (Image generation wire)** — tambah opsional `gen_images: true` flag yang trigger SDXL endpoint untuk render hero mascot + logo + social post (3 image dari prompt stage 5). 4-6 jam.

**Sprint 16-20 (Intuisi + Wisdom)** — aha moment + impact + risk + speculation layer.
