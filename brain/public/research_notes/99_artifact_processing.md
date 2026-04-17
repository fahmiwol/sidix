# 99 — Artifact Processing: File, Gambar, Dokumen dalam Messaging

**Tag:** IMPL / DOC  
**Tanggal:** 2026-04-18  
**Sumber analisis:** `D:\artifact` (TTS app Next.js) + `D:\WA API GATeway` (media handling)

---

## Apa Itu Artifact dalam Konteks Channel?

Artifact adalah setiap pesan non-teks yang dikirim user melalui channel komunikasi:
- **Gambar** (image/jpeg, image/png, image/webp)
- **Dokumen** (PDF, DOCX, XLSX, TXT)
- **Audio** (voice note, musik, podcast — ogg/mp3/m4a)
- **Video** (mp4, webm)
- **Sticker** (WebP animated — khusus WA)

---

## Pola Artifact yang Ditemukan

### 1. WhatsApp Meta Cloud API — Media Object

```json
// Payload inbound gambar
{
  "type": "image",
  "image": {
    "id": "MEDIA_ID",
    "mime_type": "image/jpeg",
    "sha256": "abc123...",
    "link": "https://lookaside.fbsbx.com/whatsapp/..."
  }
}

// Payload inbound dokumen
{
  "type": "document",
  "document": {
    "id": "MEDIA_ID",
    "filename": "laporan.pdf",
    "mime_type": "application/pdf",
    "link": "https://..."
  }
}
```

**Penting:** `link` di Meta API bersifat sementara (expire ~5 menit). Harus di-download segera.

### 2. Telegram — File ID System

Telegram menggunakan `file_id` (string opaque) yang harus di-resolve via API:
```
GET https://api.telegram.org/bot{TOKEN}/getFile?file_id={FILE_ID}
→ {"file_path": "photos/file_0.jpg"}

Download: https://api.telegram.org/file/bot{TOKEN}/{file_path}
```

File ID Telegram bersifat permanen (tidak expire) selama bot masih punya akses ke file.

### 3. TTS App Pattern (dari D:\artifact\TTS_Siapjala)

TTS (Text-to-Speech) app Next.js menunjukkan pola pemrosesan audio:

```typescript
// src/app/api/tts/openai/route.ts — pola umum
export async function POST(req: Request) {
  const { text, voice } = await req.json();
  // → kirim ke TTS provider
  // → return audio stream / URL
}

// src/app/api/tts/coqui/route.ts — fallback lokal
export async function POST(req: Request) {
  const { text } = await req.json();
  // → POST ke Coqui TTS server lokal
  // → return audio buffer
}
```

Pattern dua-layer: vendor API (OpenAI TTS) + fallback lokal (Coqui) — sesuai filosofi SIDIX.

---

## Pipeline Artifact Processing untuk SIDIX

```
User kirim artifact (gambar/dokumen/audio)
    │
    ▼
[1] Adapter mendeteksi tipe media
    ├── media_type = "image" | "document" | "audio" | "video"
    └── media_url = URL atau file_id
    │
    ▼
[2] Fetch / Download artifact
    ├── WA: GET link sementara (simpan ke storage dulu)
    └── TG: resolve file_id → getFile → download
    │
    ▼
[3] Pre-process berdasarkan tipe
    ├── image   → OCR (pytesseract) atau caption (LLaVA) atau hash
    ├── document→ extract text (PyMuPDF / pdfminer)
    ├── audio   → transcribe (Whisper lokal)
    └── video   → extract keyframes + audio transcribe
    │
    ▼
[4] Kirim teks hasil ekstraksi ke SIDIX brain_qa
    │
    ▼
[5] Return jawaban ke user
```

---

## Tipe MIME yang Relevan

| Kategori | MIME Types | Handler |
|----------|-----------|---------|
| Gambar | image/jpeg, image/png, image/webp | Pillow, OpenCV, pytesseract |
| Dokumen | application/pdf | PyMuPDF / pdfminer |
| Dokumen Office | application/vnd.openxmlformats-officedocument.* | python-docx, openpyxl |
| Audio | audio/ogg, audio/mpeg, audio/mp4 | ffmpeg + whisper |
| Audio WA | audio/ogg;codecs=opus | ffmpeg decode dulu |

---

## Storage Pattern

```
Artifact masuk
    → simpan ke storage lokal / S3 / Supabase Storage
    → generate stable URL atau path
    → proses dari stable path
    → hapus file temp setelah N jam (retention policy)
```

Supabase Storage endpoint SIDIX:  
`https://fkgnmrnckcnqvjsyunla.supabase.co/storage/v1/object/public/`

---

## Keterbatasan

- Gambar beresolusi tinggi butuh kompresi sebelum OCR
- Audio voice note WA ber-format OGG Opus — perlu konversi via ffmpeg ke WAV/MP3
- PDF scan (bukan digital) butuh OCR, bukan text extract
- Video processing sangat berat — perlu queue/worker (RQ)
- Rate limit: Meta membatasi download media 30 req/detik

---

## Status Implementasi di channel_adapters.py

`channel_adapters.py` saat ini sudah:
- Mendeteksi tipe media dari payload WA dan TG
- Menyimpan `media_url` dan `media_type` di `InboundMessage`
- Meneruskan ke `sidix_fn` untuk diproses

Yang belum (TODO untuk ekstensi):
- Download otomatis file sementara
- Pre-processing per tipe media
- Audio transcription
- Vision processing (sudah ada di `apps/vision/`)

**Ekstensi yang direkomendasikan:** wire `InboundMessage.media_url` ke `apps/vision/caption.py` atau `brain_qa/audio_capability.py`.
