# Sprint 14f — Shap-E Text-to-3D Fallback

**Date**: 2026-04-28
**Status**: SHIPPED (pushed to main, deploy pending — SSH key issue on Windows session)

## Apa
Tambah jalur generasi 3D yang **tidak butuh gambar** ke `creative_brief_pipeline`.
Mode baru `gen_3d_mode = "shape"` memanggil mighan-media-worker `tool=3d, mode=shape`
yang menjalankan **Shap-E** (OpenAI) — text-to-3D langsung dari prompt.

## Mengapa
Sprint 14e (TripoSR image-to-3D) wiring sudah live tapi runtime LIVE diblokir
karena **GPU supply RunPod throttled**. Risk: hero use-case "creative bundle 3D
mascot" stuck. Shap-E:
- Lebih ringan dari TripoSR (model lebih kecil, latency target ≤90s di GPU 24GB)
- Tidak butuh hero_mascot.png (dependensi image-gen yang juga rentan throttle)
- Sudah ter-implement di `mighan-media-worker` handler — wiring saja yang missing

## Bagaimana
3 file disentuh:

### 1. `apps/brain_qa/brain_qa/runpod_media.py`
Fungsi baru `generate_3d_from_text(prompt, *, output_dir, label, output_format,
num_inference_steps=32, frame_size=256)`. Polling pattern sama dengan
`generate_3d_from_image()` — beda di payload (no image, ada prompt+mode=shape).

### 2. `apps/brain_qa/brain_qa/creative_pipeline.py`
Param baru `gen_3d_mode: str = "auto"` di `creative_brief_pipeline()`.
Logic:
- `auto` → triposr kalau `hero_mascot.png` ada, else `shape`
- `triposr` → image-to-3D (existing path)
- `shape` → text-to-3D pakai `character_concept[:200] + brand_kit[:200] + brief[:200]`

### 3. `apps/brain_qa/brain_qa/agent_serve.py`
`CreativeBriefRequest.gen_3d_mode: str = "auto"` + passthrough ke pipeline.

## Contoh nyata
```bash
curl -X POST https://ctrl.sidixlab.com/creative/brief \
  -H "Content-Type: application/json" \
  -d '{"brief": "Maskot brand makanan ringan kawaii ulat kuning",
       "gen_3d": true, "gen_3d_mode": "shape"}'
```
Expected output: `.data/creative_briefs/<slug>/3d/hero_3d_shape.glb`.

## Keterbatasan
- Shap-E quality lebih kasar dari TripoSR untuk maskot detail
- Tetap butuh GPU (kalau RunPod throttle total, dua-duanya gagal)
- Prompt budget 600 char total — kompleksitas konsep terbatas
- Belum ada auto-retry shape kalau triposr fail di mode auto (TODO Sprint 14g)

## Compound dengan
- Sprint 14e (TripoSR) — sekarang co-exist via mode flag
- Sprint 21 RASA — RASA bisa scoring 3D output dari kedua mode
- Sprint 14d (TTS) — bundle multimodal tetap utuh

## Mandatory loop coverage
CATAT (pre-exec: cek note 248 hero use-case + GPU throttle handoff) → IMPL (3 files) →
TESTING (`ast.parse` 3/3 OK) → REVIEW (diff audit, no secret leak, persona LOCK ✓) →
CATAT (LIVING_LOG entry) → VALIDASI (deploy + curl test PENDING — SSH blocked) →
QA → CATAT (note 263 ini)

Commit: `89443a7` di main.
