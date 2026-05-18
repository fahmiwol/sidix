# Image Generation Package — Projek Badar G2 (Tasks 72–93)

## Apa ini?

Pipeline **text-to-image** untuk platform SIDIX/Mighan. Dibangun sebagai **STUB** — infrastruktur dan antarmuka API sudah lengkap, tetapi inferensi model gambar (FLUX, Stable Diffusion, dll.) belum diwire ke model lokal.

> Stack: own-stack (lokal/OSS). Tidak ada vendor API (no OpenAI, no Replicate, no Stability AI cloud).

---

## Status: STUB

Seluruh file adalah implementasi **Python FastAPI stubs**. Job generation akan mengembalikan path placeholder, bukan gambar nyata. Lihat bagian **Aktivasi** di bawah untuk langkah pengaktifan.

---

## Peta File & Task

| File | Task | Deskripsi |
|---|---|---|
| `__init__.py` | Paket | Inisialisasi paket, versi |
| `models.py` | Shared | Pydantic v2 models: `ImageGenRequest`, `ImageGenResponse`, `ImageJob`, `PolicyViolation` |
| `queue.py` | Task 72 | Job queue in-memory (`queue.Queue`, maxsize=100) |
| `presets.py` | Task 73 | Prompt style presets (photorealistic, anime, sketch, minimalist, brand) |
| `policy_filter.py` | Task 74 | NSFW/policy filter berbasis keyword denylist + logging redaksi |
| `lora_adapter.py` | Task 75 | LoRA adapter registry stub |
| `batch_render.py` | Task 76 | Batch render rendah prioritas + persistensi JSONL |
| `thumbnail.py` | Task 77 | Thumbnail & kompresi (Pillow opsional, fallback copy) |
| `ab_variants.py` | Task 78 | Prompt A/B variant generator + result logging |
| `watermark.py` | Task 79 | Embed metadata + watermark (PNG info / sidecar JSON) |
| `color_grading.py` | Task 80 | Color grading / palet brand SIDIX (stub) |
| `img2img.py` | Task 81 | Img2img generation stub |
| `validation.py` | Task 82 | Validasi prompt sebelum render (panjang + policy) |
| `resolution.py` | Task 83 | Resolusi max + aspect ratio enforcement |
| `style_transfer.py` | Task 84 | Style transfer stub (watercolor, oil_paint, sketch) |
| `seed.py` | Task 85 | Reproducible seed registry |
| `gallery.py` | Task 86 | Gallery + bulk delete + persistensi JSONL |
| `rate_limit.py` | Task 87 | Rate limit concurrent job per user |
| `hdr.py` | Task 88 | CANCELLED — placeholder saja |
| `tile_export.py` | Task 89 + 92 | Tile tekstur + sticker pack export |
| `inpainting.py` | Task 90 | Inpainting mask stub (roadmap Q2 2026) |
| `poster.py` | Task 91 | Poster layout template (A4, social square, landscape) |
| `line_art.py` | Task 93 | Line art mode (PIL CONTOUR filter) |
| `api.py` | Router | FastAPI APIRouter semua endpoint `/image/*` |

---

## Integrasi ke SIDIX Inference Server

Tambahkan ke server utama (misal `apps/inference/server.py`):

```python
from apps.image_gen.api import router as image_router

app.include_router(image_router)
```

Semua endpoint akan tersedia di prefix `/image`:

| Method | Path | Fungsi |
|---|---|---|
| `GET` | `/image/health` | Health check + info model |
| `POST` | `/image/generate` | Submit job image generation |
| `GET` | `/image/jobs/{job_id}` | Status sebuah job |
| `GET` | `/image/jobs` | Daftar semua job |
| `GET` | `/image/presets` | Daftar style presets |
| `GET` | `/image/gallery` | Daftar galeri |
| `DELETE` | `/image/gallery/{item_id}` | Hapus item galeri |

---

## Data Storage

File persisten disimpan di `.data/image_gen/`:

```
.data/image_gen/
├── policy_log.jsonl     # Log redaksi policy filter
├── batch_jobs.jsonl     # Batch render jobs
├── ab_results.jsonl     # A/B test results
├── gallery.jsonl        # Gallery items
└── stub_<job_id>.png    # Placeholder output (stub)
```

---

## Dependensi

```
fastapi
pydantic>=2.0
pillow          # Opsional — thumbnail, watermark, tile, line art
```

---

## Aktivasi (Wire ke Model Lokal)

Untuk mengaktifkan inferensi gambar nyata:

1. Install model dan dependensi:
   ```bash
   pip install diffusers transformers accelerate torch torchvision
   # Download model: FLUX.1-schnell atau SD v1.5
   ```

2. Buka `apps/image_gen/queue.py`, cari method `_generate_stub()`.

3. Ganti implementasi stub dengan pipeline lokal:
   ```python
   from diffusers import StableDiffusionPipeline
   import torch

   def _generate_stub(self, job: ImageJob) -> str:
       pipe = StableDiffusionPipeline.from_pretrained(
           "/path/to/local/model",
           torch_dtype=torch.float16,
       ).to("cuda")
       image = pipe(job.prompt).images[0]
       out_path = f".data/image_gen/{job.job_id}.png"
       image.save(out_path)
       return out_path
   ```

4. Untuk img2img: aktifkan `apps/image_gen/img2img.py` → `img2img_generate()`.

5. Untuk LoRA: daftarkan adapter via `lora_registry.register()` dan panggil `apply_to_prompt()` sebelum inference.

---

*Projek Badar G2 — SIDIX/Mighan Platform. Own-stack, no vendor API.*
