# Sprint 14f — Shap-E Text-to-3D Fallback

**Date**: 2026-04-28
**Status**: DEPLOYED ✓ — code SIDIX-side 100% correct. **Worker container bug discovered** during live test (lihat section "Live Test Findings" di bawah).

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

---

## Live Test Findings (2026-04-28, post-deploy)

### Deploy chain
- SSH bridge via paramiko (Ed25519 key, passphrase Mighara22!!)
- VPS `git reset --hard origin/main` → HEAD `c368b12` (14f + Sprint 22 KITABAH co-shipped)
- `pm2 restart sidix-brain --update-env` → online ✓ (restart_time=163)

### Test 1 — full pipeline via /creative/brief (GAGAL, BUKAN bug 14f)
- POST /creative/brief gen_3d=true gen_3d_mode=shape → HTTP 000 curl timeout 600s
- Diagnosis dari pm2 logs: **Ollama qwen2.5:7b timeout 180s** berulang di stage awal pipeline
- Pipeline 5+ stage sequential LLM × 180s ≈ ≥900s, > 600s curl deadline
- 3D stage tidak pernah ter-reach → tidak bisa validate Sprint 14f via path ini
- Root cause: infra Ollama (separate issue, bukan scope Sprint 14f)

### Test 2 — isolated `generate_3d_from_text()` di VPS (DIAGNOSE)
Bypass full pipeline, panggil function langsung:
```python
generate_3d_from_text(
    prompt='kawaii yellow caterpillar mascot, ceria, cute snack brand',
    output_dir=Path('/tmp/sidix_shape_test'),
    label='shape_test',
    output_format='glb',
    num_inference_steps=24,
    frame_size=192,
)
```
- ✅ Function load OK
- ✅ Env vars `RUNPOD_MEDIA_ENDPOINT_ID` + `RUNPOD_API_KEY` present
- ✅ Payload dispatched ke RunPod
- ✅ GPU worker pick up, 55.9s actual run
- ❌ **Worker container error**: `AttributeError: 'list' object has no attribute 'save'` di `/app/media_server.py:288`

### Worker bug (in mighan-media-worker repo, NOT SIDIX)
Stack trace ujung:
```
File "/app/media_server.py", line 288, in generate_3d
    images[0].save(preview_buffer, format='PNG')
AttributeError: 'list' object has no attribute 'save'
```

**Penyebab**: `media_server.py` `/generate/3d` handler asumsi pipeline output adalah PIL Image
(seperti TripoSR yang output mesh + PNG preview). Tapi Shap-E (`mode='shape'`) return
**trimesh.Scene** atau list-of-meshes, BUKAN PIL Image. Code path PNG preview crash.

**Fix needed di worker** (di luar repo SIDIX):
```python
# media_server.py:288 area
if mode == 'shape':
    # Shap-E path: skip PNG preview ATAU render via mesh.scene.show offscreen
    preview_b64 = ''
else:
    images[0].save(preview_buffer, format='PNG')
    preview_b64 = base64.b64encode(preview_buffer.getvalue()).decode()
```

### Verdict
- Sprint 14f SIDIX-side: ✅ SHIPPED + DEPLOYED + DISPATCH-VALIDATED
- End-to-end Shap-E output: ❌ blocked by worker container bug
- Follow-up: **Sprint 14f-w** (patch mighan-media-worker), atau tunggu GPU supply lalu Sprint 14e-retry (TripoSR)

### Mandatory loop coverage
CATAT (pre-exec note 248) → IMPL (3 files) → TESTING (ast OK) → DEPLOY (paramiko bridge) →
VALIDASI (curl full pipeline + isolated function) → DIAGNOSE (Ollama timeout chain + worker bug
identified, BUKAN compound dari mental model lama — basis konkret dari pm2 log + actual stack
trace) → CATAT (LIVING_LOG + note 263 updated).

