# Panduan Onboarding Admin Pertama SIDIX

> Task 11 — Ar-Rum (G1)

Dokumen ini memandu admin pertama dalam menyiapkan dan menjalankan server SIDIX Brain QA dari nol.

---

## Prasyarat

| Kebutuhan | Versi / Detail |
|-----------|----------------|
| Python | 3.10 atau lebih baru |
| pip packages | `fastapi`, `uvicorn`, `rank-bm25`, `Pillow` |
| OS | Windows 10/11, Linux, atau macOS |
| RAM | Minimal 4 GB (8 GB direkomendasikan) |

Instal dependensi:

```bash
pip install fastapi uvicorn rank-bm25 Pillow
```

Atau jika menggunakan `requirements.txt` di repo:

```bash
pip install -r apps/brain_qa/requirements.txt
```

---

## Setup Variabel Lingkungan (Environment Variables)

Sebelum menjalankan server, set variabel berikut di terminal atau di env manager (lihat bagian Keamanan):

| Variabel | Keterangan | Contoh Nilai |
|----------|------------|--------------|
| `BRAIN_QA_ADMIN_TOKEN` | Token rahasia untuk endpoint admin. **Wajib diisi.** | `ganti-dengan-token-acak-panjang` |
| `BRAIN_QA_ANON_DAILY_CAP` | Batas permintaan harian untuk pengguna anonim | `100` |
| `BRAIN_QA_RATE_LIMIT_RPM` | Batas request per menit (rate limit) | `30` |

### Cara set (Linux/macOS)

```bash
export BRAIN_QA_ADMIN_TOKEN="token-rahasia-anda"
export BRAIN_QA_ANON_DAILY_CAP="100"
export BRAIN_QA_RATE_LIMIT_RPM="30"
```

### Cara set (Windows PowerShell)

```powershell
$Env:BRAIN_QA_ADMIN_TOKEN = "token-rahasia-anda"
$Env:BRAIN_QA_ANON_DAILY_CAP = "100"
$Env:BRAIN_QA_RATE_LIMIT_RPM = "30"
```

---

## Menjalankan Server

Dari direktori root workspace:

```bash
python -m brain_qa serve
```

Server akan berjalan di `http://localhost:8765` secara default.

Untuk menentukan host dan port:

```bash
python -m brain_qa serve --host 127.0.0.1 --port 8765
```

Untuk mode production dengan uvicorn secara langsung:

```bash
uvicorn brain_qa.server:app --host 127.0.0.1 --port 8765 --workers 2
```

---

## Reindex Corpus

Setelah menambah atau mengubah dokumen di folder `brain/public/`, jalankan reindex:

```bash
curl -X POST http://localhost:8765/corpus/reindex \
  -H "X-Admin-Token: <token-anda>"
```

Atau pakai PowerShell:

```powershell
Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8765/corpus/reindex" `
  -Headers @{ "X-Admin-Token" = $Env:BRAIN_QA_ADMIN_TOKEN }
```

Respons sukses:

```json
{ "status": "ok", "doc_count": 142, "chunk_count": 891 }
```

---

## Rotasi Secret (Ganti Admin Token Tanpa Downtime)

Untuk mengganti `BRAIN_QA_ADMIN_TOKEN` tanpa menghentikan server:

1. Tentukan token baru yang kuat (minimal 32 karakter acak).
2. Update nilai di env manager / secret vault (jangan di `.env` yang di-commit).
3. Restart proses server dengan token baru:

```bash
# Hentikan proses lama
# Set token baru
export BRAIN_QA_ADMIN_TOKEN="token-baru-anda"
# Jalankan ulang
python -m brain_qa serve
```

> Strategi zero-downtime: gunakan reverse proxy (nginx/caddy) dengan blue-green deployment.
> Jalankan instance baru (dengan token baru) di slot "blue", alihkan traffic dari proxy,
> lalu matikan instance lama. Lihat endpoint `/agent/bluegreen/switch`.

---

## Daftar Endpoint Admin

| Endpoint | Metode | Header Wajib | Keterangan |
|----------|--------|--------------|------------|
| `/corpus/reindex` | `POST` | `X-Admin-Token` | Indeks ulang seluruh corpus dari `brain/public/` |
| `/agent/canary` | `GET` / `POST` | `X-Admin-Token` | Tes canary: jalankan query uji ke model aktif |
| `/agent/bluegreen/switch` | `POST` | `X-Admin-Token` | Alihkan slot aktif antara blue dan green |

Contoh canary check:

```bash
curl http://localhost:8765/agent/canary \
  -H "X-Admin-Token: <token-anda>"
```

---

## Tips Keamanan

1. **Jangan expose port 8765 langsung ke internet.** Selalu gunakan reverse proxy (nginx, Caddy, Traefik) yang menangani TLS.
2. **Simpan `BRAIN_QA_ADMIN_TOKEN` di secret vault** (misalnya Windows Credential Manager, HashiCorp Vault, atau env manager platform). Jangan simpan di file `.env` yang masuk git history.
3. Batasi akses ke endpoint admin hanya dari IP internal / VPN.
4. Aktifkan log access di reverse proxy untuk audit trail.
5. Rotasi token minimal setiap 90 hari, atau segera jika dicurigai bocor.

---

*Dokumen ini bagian dari G1 — Operasional SIDIX.*
