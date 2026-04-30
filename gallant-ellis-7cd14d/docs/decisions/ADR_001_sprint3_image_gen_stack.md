# ADR 001 — Sprint 3 Image Gen Stack

**Status:** Proposed (butuh user approval sebelum eksekusi Sprint 3)
**Tanggal:** 2026-04-19
**Pembuat:** Claude (berdasar sintesis note 170–173)

---

## Context

Sprint 3 target: SIDIX bisa generate image (tujuan: differensiator multimodal). 4 research note (170–173) sudah selesai. ADR ini mengunci keputusan teknis.

## Keputusan

| Area | Pilihan | Alasan |
|------|---------|--------|
| **GPU Provider** | RunPod Serverless 4090 | Per-detik billing, Singapore region, Docker portability, budget $20–40 untuk 2mgg testing |
| **Model** | FLUX.1-schnell (Apache-2.0) | License komersial, kualitas tertinggi, text rendering kaligrafi, prompt complex OK |
| **Deployment Pattern** | Diffusers lib di Docker FastAPI handler | Native Python, LoRA support, memory efficient, observability full |
| **Differentiator Layer** | Nusantara Knowledge Base (phase 1: 50 entry) | Prompt enricher yang big tech tidak punya, cultural accuracy |

## Konsekuensi

- **Positive:** Standing-alone principle preserved, commercial-ready license, cost predictable.
- **Negative:** RunPod = vendor risk (mitigasi: Docker portable ke Vast/Modal), FLUX LoRA ecosystem masih young (fallback: SDXL untuk specialty).
- **Budget Sprint 3:** $40–80 infrastructure + 40 jam development (Claude + Cursor).

## Fallback

- Kalau FLUX quality tidak mencukupi untuk Nusantara use case setelah benchmark → fallback SDXL 1.0 + train LoRA Nusantara.
- Kalau RunPod Singapore region tidak tersedia → Vast.ai 4090 (harga lebih murah, reliability lebih rendah).

## Referensi
- [Note 170 GPU Provider](../../brain/public/research_notes/170_gpu_provider_comparison_2026.md)
- [Note 171 Image Model](../../brain/public/research_notes/171_image_model_comparison_sdxl_flux_alternatif.md)
- [Note 172 Nusantara KB](../../brain/public/research_notes/172_nusantara_knowledge_base_design_prompt_enhancer.md)
- [Note 173 Deployment](../../brain/public/research_notes/173_image_gen_deployment_pattern.md)
