# Vision Package — Projek Badar G3 (Tasks 94–104)

Pipeline **image understanding** untuk platform SIDIX. Semua file dalam paket ini adalah **STUB** — struktur dan antarmuka sudah siap, tetapi model vision lokal belum dipasang.

---

## Status

> **STUB — Tidak ada model vision yang dimuat.**
> Semua endpoint akan mengembalikan respons placeholder.
> Lihat bagian "Cara Mengaktifkan" untuk mengintegrasikan model lokal.

---

## Struktur File & Mapping Task

| File | Task | Deskripsi |
|------|------|-----------|
| `__init__.py` | — | Package init, versi |
| `models.py` | — | Pydantic v2 shared models (`VisionRequest`, `VisionResult`, `BoundingBox`, dll.) |
| `caption.py` | **Task 94** | Image → caption (deskripsi) + OCR opsional via pytesseract |
| `classifier.py` | **Task 95** | Klasifikasi jenis gambar (foto/diagram/sketsa) + routing ke handler |
| `preprocess.py` | **Task 96** | Resize (batas 4MP), validasi format, normalisasi ke PNG/JPEG |
| `similarity.py` | **Task 97** | Image-text similarity (stub CLIP) untuk retrieval hybrid |
| `region_crop.py` | **Task 98** | Crop region/bounding box dari gambar untuk fokus analisis |
| `detection.py` | **Task 99** | Deteksi objek (YOLO stub) + face detection (nonaktif default, privasi) |
| `table_extract.py` | **Task 100** | Ekstraksi tabel dari gambar → JSON/CSV/Markdown |
| `confidence.py` | **Task 101** | Agregasi confidence score (caption 50% + OCR 25% + klasifikasi 25%), grade A–F |
| `flowchart_ocr.py` | **Task 102** | Deteksi teks & struktur flowchart → output Mermaid diagram |
| `analysis_display.py` | **Task 103** | Side-by-side display: ASCII, HTML, Markdown |
| `low_light.py` | **Task 104** | Deteksi gambar low-light + saran preprocessing (CLAHE, histogram eq.) |
| `api.py` | **Tasks 94–104** | FastAPI `APIRouter` prefix `/vision` — semua endpoint terkumpul di sini |

---

## Endpoint API

Mount router ke SIDIX inference server:

```python
# Di main.py / inference_server.py
from apps.vision.api import router as vision_router
app.include_router(vision_router)
```

| Method | Endpoint | Task | Deskripsi |
|--------|----------|------|-----------|
| `GET` | `/vision/health` | — | Status + daftar kapabilitas |
| `POST` | `/vision/caption` | 94 | Caption + OCR opsional |
| `POST` | `/vision/classify` | 95 | Klasifikasi jenis gambar |
| `POST` | `/vision/preprocess` | 96 | Resize + normalisasi format |
| `POST` | `/vision/similarity` | 97 | Image-text similarity / ranking |
| `POST` | `/vision/detect` | 99 | Deteksi objek + face (nonaktif default) |
| `POST` | `/vision/table` | 100 | Ekstraksi tabel (JSON/CSV/Markdown) |
| `POST` | `/vision/flowchart` | 102 | Flowchart OCR → Mermaid |
| `POST` | `/vision/analyze` | 94+95+101 | Full pipeline: caption + klasifikasi + confidence |

**Format request umum:**
```json
{
  "image_path": "/absolute/path/to/image.jpg",
  "options": {}
}
```

---

## Cara Mengaktifkan (Wire ke Model Lokal)

### Caption (Task 94) — LLaVA / BLIP-2 / Qwen-VL

```bash
pip install transformers torch Pillow
```

Edit `caption.py`, fungsi `generate_caption()`:

```python
from transformers import BlipProcessor, BlipForConditionalGeneration
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
# ... run inference
```

### OCR (Task 94) — pytesseract

```bash
pip install pytesseract Pillow
# Install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki
```

OCR via pytesseract sudah tersedia secara kondisional di `caption.py` — aktif otomatis jika pytesseract terinstal.

### Similarity (Task 97) — CLIP Lokal

```bash
pip install git+https://github.com/openai/CLIP.git torch
```

Edit `similarity.py`, fungsi `compute_similarity()` sesuai komentar TODO.

### Object Detection (Task 99) — YOLOv8

```bash
pip install ultralytics
```

Edit `detection.py`, fungsi `detect_objects()` sesuai komentar TODO.

### Table Extraction (Task 100) — PaddleOCR / table-transformer

```bash
pip install paddlepaddle paddleocr
# atau: pip install transformers  # untuk table-transformer
```

---

## Catatan Privasi — Face Detection

- `FACE_DETECTION_ENABLED = False` secara **default**
- Face detection memproses data biometrik yang sensitif
- Aktifkan (`enabled=True`) **hanya** jika:
  - Ada persetujuan eksplisit dari subjek
  - Sesuai regulasi privasi yang berlaku (GDPR, UU PDP Indonesia, dll.)
  - Hasil tidak disimpan tanpa keperluan yang jelas
- Fungsi `privacy_warning()` akan mencetak peringatan setiap kali diaktifkan

---

## Dependensi Opsional

| Paket | Fungsi | Cara Install |
|-------|--------|--------------|
| `Pillow` | Resize, crop, format, brightness | `pip install Pillow` |
| `pytesseract` | OCR via Tesseract | `pip install pytesseract` + install Tesseract |
| `transformers` | BLIP/LLaVA/table-transformer | `pip install transformers torch` |
| `ultralytics` | YOLOv8 object detection | `pip install ultralytics` |
| `clip` | Image-text similarity | `pip install git+https://github.com/openai/CLIP.git` |
| `paddleocr` | OCR + table recognition | `pip install paddlepaddle paddleocr` |

Semua dependensi bersifat **opsional** — package tetap berjalan (mode stub) tanpa mereka.

---

*Projek Badar G3 | SIDIX Vision Pipeline | Status: STUB*
