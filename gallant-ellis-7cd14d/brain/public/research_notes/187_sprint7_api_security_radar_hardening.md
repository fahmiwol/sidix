> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
name: Sprint 7 API Security & Social Radar Hardening
description: Dokumentasi fix keamanan endpoint /social/radar/scan dan penguatan modul social_radar.py — mencakup Pydantic validation, payload cap, dan perbaikan logika advice.
type: project
sanad-tier: peer_review
date: 2026-04-23
---

# Sprint 7 — API Security & Social Radar Hardening

## Apa

Sesi review menyeluruh menemukan beberapa kelemahan di endpoint Social Radar MVP yang perlu
diperbaiki sebelum lanjut ke Sprint 8. Semua fix bersifat lokal, tanpa dependensi eksternal,
sesuai prinsip standing-alone SIDIX.

---

## Mengapa

### Kelemahan yang ditemukan

**1. Endpoint tidak tervalidasi (`body: dict[str, Any]`)**
Endpoint `POST /social/radar/scan` menerima `dict` mentah tanpa Pydantic schema.
Risiko: payload berukuran arbitrer bisa dikirim, tidak ada type safety.

**2. Payload DoS via `recent_comments`**
Extension bisa mengirim list komentar sangat panjang (ribuan item). `" ".join()`
terhadap list besar bisa memperlambat server secara signifikan.

**3. Keyword sentimen terlalu sempit**
MVP hanya punya 7 kata positif dan 6 kata negatif. Tidak mencakup slang UMKM Indonesia
yang umum: "worth", "zonk", "gacor", "nyesel", "sip", dll.

**4. Advice logic ada gap (mutual exclusion)**
Kondisi `sentiment < -0.2` dan `er > 5.0` diperiksa terpisah secara linear. Kasus keduanya
terjadi bersamaan (kompetitor viral + krisis) tidak ditangani — ini adalah sinyal terpenting.

**5. Error message bocor internals**
`return {"ok": False, "error": str(e)}` mengembalikan pesan exception mentah ke client,
yang bisa mengandung path file, nama modul, atau info sistem internal.

---

## Bagaimana

### Fix 1 — Pydantic `RadarScanRequest` di `agent_serve.py`

```python
class RadarScanRequest(BaseModel):
    url: str = ""
    metadata: dict = {}

    model_config = {"extra": "ignore"}

    def validated_metadata(self) -> dict:
        raw = self.metadata or {}
        if len(str(raw)) > 10_000:
            raise ValueError("Payload metadata melebihi batas 10KB.")
        comments = raw.get("recent_comments", [])
        if isinstance(comments, list):
            raw = dict(raw)
            raw["recent_comments"] = comments[:200]
        return raw
```

Endpoint berubah dari:
```python
def social_radar_scan(body: dict[str, Any]):
    url = body.get("url", "")
    metadata = body.get("metadata", {})
    result = social_radar.analyze_social_context(url, metadata)
```

Menjadi:
```python
def social_radar_scan(body: RadarScanRequest):
    clean_meta = body.validated_metadata()
    result = social_radar.analyze_social_context(body.url, clean_meta)
```

Error handling: `ValueError` → `HTTP 413`, exception lain → `HTTP 500` dengan pesan generik.

---

### Fix 2 — `social_radar.py` hardening

**Guard payload:**
```python
_MAX_COMMENTS_SAMPLE = 200
_MAX_METADATA_STR_LEN = 10_000

if len(str(metadata)) > _MAX_METADATA_STR_LEN:
    return {"status": "error", "reason": "Payload metadata melebihi batas ukuran (10KB)."}
```

**Cap komentar sebelum join:**
```python
sample_comments = raw_comments[:_MAX_COMMENTS_SAMPLE]
sample_text = " ".join(str(c) for c in sample_comments).lower()
```

**Regex diperluas (14 positif, 14 negatif):**
```python
_POS_RE = re.compile(r"(bagus|keren|mantap|rekomendasi|beli|puas|cepat|worth|oke|sip|jos|juara|memuaskan|...)")
_NEG_RE = re.compile(r"(jelek|lambat|kecewa|mahal|cacat|penipu|zonk|nyesel|mengecewakan|...)")
```

**Double signal advice (kasus terpenting):**
```python
if er > 5.0 and sentiment < -0.2:
    return "Window peluang langka: kompetitor punya audiens besar tapi sedang krisis..."
```

---

## Formula Engagement Rate

```
ER = (likes + comments) / followers × 100
```

Benchmark IG (referensi industri):
- < 1%: rendah
- 1–3%: rata-rata
- 3–6%: baik
- > 6%: viral / sangat loyal

Threshold tier SIDIX (dikalibrasi untuk UMKM Indonesia):
- `followers > 100.000` → leader
- `followers > 10.000` → emerging
- lainnya → micro

---

## Keterbatasan (untuk Sprint 8)

1. **Sentimen berbasis keyword** — tidak menangkap sarkasme atau konteks. Fase selanjutnya: model sentimen ringan (SentenceTransformers lokal).
2. **Tidak ada autentikasi endpoint** — `/social/radar/scan` bisa diakses tanpa token. Pertimbangkan header `x-client-id` atau rate limit per-IP lebih ketat.
3. **`recent_comments` masih plain text** — belum ada sanitasi HTML/script tags. Tambah `html.escape()` sebelum proses.
4. **URL tidak divalidasi** — field `url` menerima string apapun. Untuk fase real scrape, validasi format domain yang diizinkan (allowlist: instagram.com, tiktok.com, dll).

---

## Contoh Nyata

Request:
```json
POST /social/radar/scan
{
  "url": "https://www.instagram.com/p/C_abc123/",
  "metadata": {
    "likes": 1200,
    "comments": 45,
    "followers": 50000,
    "recent_comments": ["Bagus banget!", "Keren", "Beli dimana?", "Lambat kecewa"]
  }
}
```

Response:
```json
{
  "status": "ok",
  "url": "https://www.instagram.com/p/C_abc123/",
  "metrics": {
    "engagement_rate": 2.49,
    "sentiment": 0.5,
    "tier": "emerging",
    "sample_size": 4
  },
  "advice": "Kompetitor sedang tumbuh (10k–100k followers). Pertahankan kecepatan respon dan konsistensi konten.",
  "maqashid_check": "passed (PII-free, public-aggregate only)"
}
```

---

## Kaitan dengan Prinsip SIDIX

- **Maqashid — Menjaga Mal**: Analisis pasar yang jujur membantu UMKM membuat keputusan bisnis yang lebih baik.
- **Standing-alone**: Semua analisis heuristik lokal. Tidak ada panggilan ke layanan eksternal.
- **Privacy-first**: `maqashid_check: "passed (PII-free)"` — hanya sinyal publik agregat yang diproses.
- **Sanad**: Data publik agregat (bukan opini personal) = tier `aggregator`. Tidak perlu diklaim lebih.
