# Sprint 9 — Plan (2026-04-25)

**Sprint sebelumnya:** 8a ✅ · 8b ✅ · 8c ✅ · 8d ✅

---

## Priority Sprint 9

### 1. Sociometer / Social Radar (TINGGI) — IMPL sprint ini ✅

- `tools/social_radar.py` sudah diimplementasi (2026-04-24)
- Tool `social_radar` terdaftar di `agent_tools.py` TOOL_REGISTRY
- Unit tests di `tests/test_social_radar.py` (13 test cases)
- Research note 195 dibuat

**Next sprint 9:**
- Integrasi dengan Instagram scraping (bukan login, gunakan public endpoint / Kimi Agent)
- Periodic trend report via LearnAgent (daily_growth fase SCAN)
- Tambah `social_radar` ke whitelist tool default persona CONTENT

### 2. Jariyah → LoRA Export (TINGGI)

- `jariyah_exporter.py` sudah dibuat (Sprint 8x)
- **Action**: Kumpulkan 500+ pairs dari VPS, lalu export + trigger Kaggle training
- Command: `POST /jariyah/export` → download output JSONL → upload ke Kaggle
- Target: minimal 500 pair jariyah berkualitas sebelum distilasi pertama
- Estimasi waktu: 2-3 hari pengumpulan data, 1 hari upload + queue Kaggle

### 3. Distilasi Model Pertama (SEDANG)

- `generate_synthetic_data.py` sudah ada
- **Action**: Jalankan dengan `--count 1000` dari corpus lokal (no API key needed)
- Upload ke Kaggle → run `distill_sidix.py` → download adapter → test di VPS
- Prerequisites: jariyah export selesai + 500+ pairs
- Metric sukses: loss < 0.8 di validation set, output SIDIX lebih koheren

### 4. Tiranyx Pilot — Agency OS Client Pertama (SEDANG)

- `branch_manager.py` sudah ready (Sprint 8x)
- **Action**: Buat branch config untuk Tiranyx (`agency_id="tiranyx"`)
- Persona + corpus filter + tool whitelist khusus Tiranyx
- Deliverable: endpoint `/agency/tiranyx/chat` aktif di VPS
- Uji: 3 skenario chat khas agency (brief, review, revisi konten)

### 5. PostgreSQL Live (RENDAH untuk sekarang)

- `db_migrate.py` sudah ada
- **Action**: Jalankan di VPS: `SIDIX_DB_URL=... python scripts/db_migrate.py`
- Bisa dilakukan setelah prioritas 1-3 selesai
- Notes: Supabase masih jadi fallback selama PostgreSQL belum live

---

## Backlog Sprint 10+

- **3D pipeline** (research note 184) — Three.js + SIDIX generative 3D brief
- **Instagram scraping advanced** — Kimi Agent integration untuk public post data
- **Multi-modal input** (gambar ke chat) — image understanding via CLIP/LLaVA layer
- **Social Radar v2** — real-time stream monitoring + alert system
- **LearnAgent periodic report** — weekly trend digest dikirim ke Jariyah queue

---

## Metrik Sprint 9

| Item | Target | Status |
|---|---|---|
| social_radar tool live | ✅ impl + tests | DONE |
| jariyah 500+ pairs | 500 pairs | TODO |
| LoRA distilasi pertama | 1 adapter | TODO |
| Tiranyx pilot endpoint | 1 client | TODO |

---

## Catatan Teknis

- Social Radar menggunakan DuckDuckGo HTML endpoint (standing-alone, no API key)
- Sentiment: rule-based Indonesia + English (~70% akurasi estimasi)
- Keywords: word frequency + stopword filter (no TF-IDF library, pure Python)
- Fallback graceful: jika web_search gagal, signal tetap dibuat dengan data kosong
- Test runner: `pytest apps/brain_qa/tests/test_social_radar.py -v`
