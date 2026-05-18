# Checklist Rilis SIDIX

> Task 39 — Al-Hashr (G5)

Gunakan checklist ini setiap kali melakukan deployment baru ke environment produksi atau staging.
Centang setiap item sebelum melanjutkan ke tahap berikutnya.

---

## Pre-Deploy

- [ ] Semua unit test dan integration test lulus (`pytest apps/brain_qa/`)
- [ ] Lockfile dependensi diperbarui (`requirements.txt` atau `pip freeze > requirements.txt`)
- [ ] Semua environment variable wajib sudah di-set (lihat `ONBOARDING_ADMIN.md`)
  - [ ] `BRAIN_QA_ADMIN_TOKEN` terisi dan kuat (min. 32 karakter acak)
  - [ ] `BRAIN_QA_ANON_DAILY_CAP` terisi
  - [ ] `BRAIN_QA_RATE_LIMIT_RPM` terisi
  - [ ] `BRAIN_QA_MODEL_MODE` terisi (`mock` atau `local_lora`)
- [ ] Path adapter LoRA diverifikasi (jika `local_lora`):
  - [ ] `adapters/adapter_model.safetensors` ada dan tidak korup
  - [ ] `adapters/adapter_config.json` ada dan valid JSON
- [ ] Corpus terbaru sudah diindeks — `corpus_chunk_count > 0` di `/health`
- [ ] Versi kode (git tag / commit hash) dicatat di `LIVING_LOG.md`

---

## Security

- [ ] TLS aktif di reverse proxy (nginx / Caddy) — tidak ada traffic HTTP plain ke port 8765
- [ ] Admin token sudah dirotasi sejak rilis sebelumnya (jika > 90 hari atau ada insiden)
- [ ] CORS dikonfigurasi untuk produksi: hanya origin yang diizinkan, bukan wildcard `*`
- [ ] Header keamanan aktif di reverse proxy (`X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`)
- [ ] Tidak ada kredensial atau secret yang ter-commit ke git history

---

## Firewall & Jaringan

- [ ] Port 8765 **tidak** terbuka langsung ke internet publik
- [ ] Akses ke port 8765 hanya via reverse proxy (nginx / Caddy) atau tunnel internal
- [ ] Aturan firewall server dikonfirmasi: hanya port 80, 443 (dan SSH 22 dari IP terbatas) yang terbuka
- [ ] Jika menggunakan Docker: port 8765 tidak di-expose ke host publik (gunakan `127.0.0.1:8765:8765`)

---

## Secret Vault

- [ ] `BRAIN_QA_ADMIN_TOKEN` disimpan di env manager / secret vault, **bukan** di file `.env` yang di-commit
- [ ] File `.env` terdaftar di `.gitignore`
- [ ] Tidak ada secret yang hardcoded di source code atau konfigurasi teks biasa
- [ ] Akses ke secret vault dibatasi hanya untuk akun yang berwenang

---

## Monitoring

- [ ] Endpoint `/health` dapat dijangkau dari monitoring tool
- [ ] Skrip disk alarm terpasang: `python scripts/disk_alarm.py` berjalan via cron / scheduler
- [ ] Log rotation aktif: file log tidak tumbuh tak terbatas (logrotate atau konfigurasi uvicorn)
- [ ] Alert notifikasi dikonfigurasi jika `/health` mengembalikan status bukan `ok`
- [ ] Baseline performa dicatat (latency p50/p99 dari endpoint `/ask`)

---

## Rollback

- [ ] Slot blue-green siap: instance lama (slot "green") masih berjalan dan bisa menerima traffic
- [ ] Backup `.data/` terbaru tersedia dan terverifikasi di `.backups/`
- [ ] Perintah rollback blue-green didokumentasikan dan diuji:
  ```bash
  curl -X POST http://localhost:8765/agent/bluegreen/switch \
    -H "X-Admin-Token: <token>"
  ```
- [ ] Tim tahu cara restore dari backup jika rollback blue-green tidak cukup (lihat `OPERATOR_RESTORE_BACKUP.md`)

---

## Post-Deploy

- [ ] Smoke test `GET /health` → `status: "ok"` dan `model_ready: true`
- [ ] Smoke test `POST /ask` dengan pertanyaan sederhana:
  ```bash
  curl -X POST http://localhost:8765/ask \
    -H "Content-Type: application/json" \
    -d '{"query": "Apa itu SIDIX?"}'
  ```
  → Respons mengandung field `answer` yang tidak kosong
- [ ] Pastikan `corpus_doc_count` di `/health` sesuai jumlah dokumen yang diharapkan
- [ ] Catat hasil deployment di `LIVING_LOG.md` (versi, waktu, deployer, status)
- [ ] Notifikasi tim bahwa deployment selesai

---

*Dokumen ini bagian dari G5 — Operator Pack SIDIX.*
