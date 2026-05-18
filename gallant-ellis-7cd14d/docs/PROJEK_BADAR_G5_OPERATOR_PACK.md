# Projek Badar — paket operator (G5, ringkas)

Ringkasan operasional untuk batch G5 (inferensi, biaya, keamanan, DR). Detail implementasi mengikuti kode di `apps/brain_qa/brain_qa/`.

## Versi & jejak

- **`GET /health`**: `model_mode`, `model_ready`, `adapter_fingerprint`, `anon_daily_quota_cap` (null jika kuota nonaktif), `engine_build` (override env `BRAIN_QA_ENGINE_BUILD`).
- **Header `X-Trace-ID`**: di-set middleware; kirim ulang di header permintaan untuk korelasi log.

## Rate limit & kuota

- **RPM**: env `BRAIN_QA_RATE_LIMIT_RPM` (default 120), per IP.
- **Harian anon**: env `BRAIN_QA_ANON_DAILY_CAP` (default 500). Set `0` untuk menonaktifkan. Kunci = header `X-Client-Id` jika ada, selain itu IP klien. Pencatatan **setelah** inferensi sukses (bukan pada error 500).

## Admin & reindex

- **`POST /corpus/reindex`**: jika `BRAIN_QA_ADMIN_TOKEN` diset, wajib header `X-Admin-Token` yang cocok.

## Sesi & telemetri

- **`GET /agent/session/{id}/summary`**: ringkasan teks ringan dari sesi tersimpan.
- **`GET /agent/session/{id}/export`**: JSON dengan redaksi PII ringan.
- **`POST /agent/feedback`**: `up` / `down` (tanpa PII).
- **`GET /agent/metrics`**: penghitung permintaan & feedback.

## Golden set (regresi ringan)

- Data: `apps/brain_qa/tests/data/golden_qa.json`
- Skrip: `python apps/brain_qa/scripts/run_golden_smoke.py` (jalankan dari root repo atau sesuaikan `PYTHONPATH` ke `apps/brain_qa`).

## Smoke API (tanpa `uvicorn`)

- `python apps/brain_qa/scripts/run_api_smoke.py` — `TestClient`: `/health` (cek `X-Trace-ID`), `/agent/metrics`, `/agent/feedback`, `/agent/chat` singkat, ringkasan sesi, lalu `DELETE` sesi.

## DR / cadangan

- Indeks lokal: `apps/brain_qa/.data/` — cadangkan `chunks.jsonl` + artefak BM25 bersama volume model adapter.
- Korpus sumber kebenaran: `brain/public/` + `brain/manifest.json`.

## Item batch G5 yang masih manual / lanjutan

Beberapa poin (load test, canary route, dashboard biaya vendor, blue/green penuh) membutuhkan lingkungan deploy spesifik — gunakan checklist ini sebagai prompt kerja infra; implementasi kode tambahan dilakukan per lingkungan.
