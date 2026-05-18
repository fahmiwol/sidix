# API Keys, Environment Variables, dan Keamanan Credentials

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa itu API Key?

API Key adalah "password" yang digunakan aplikasi untuk membuktikan identitasnya ke layanan eksternal.
Berbeda dari password user biasa — API key digunakan antar-sistem (machine-to-machine), bukan oleh manusia.

```
Aplikasi SIDIX  ──[API Key]──→  Supabase
                               "Saya adalah SIDIX, izinkan akses"
```

---

## Jenis API Key di Supabase

Supabase memiliki dua jenis key dengan tingkat akses berbeda:

### 1. `anon` key (public)
- **Aman disimpan di frontend** (browser, JavaScript)
- Akses dibatasi oleh **Row Level Security (RLS)**
- Jika bocor: attacker hanya bisa akses data yang diizinkan RLS
- Gunakan untuk: operasi yang dilakukan user biasa (baca data publik, login, submit form)

### 2. `service_role` key (secret)
- **JANGAN pernah di frontend atau GitHub**
- Bypass semua RLS — akses penuh ke database
- Jika bocor: attacker bisa baca/hapus semua data
- Gunakan untuk: backend server yang trusted (Python FastAPI, dll)

```
Frontend (browser)     → anon key      → RLS memblokir akses berlebih
Backend Python server  → service key   → akses penuh (trusted environment)
```

---

## Environment Variables — Cara Menyimpan Credentials

**Jangan hardcode** API key di dalam kode:

```python
# ❌ SALAH — jangan begini
supabase_url = "https://xyz.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Jika file ini masuk ke GitHub → semua orang bisa lihat key-nya.

**Cara benar: gunakan environment variables**

```bash
# Di server (tambahkan ke ~/.bashrc atau /etc/environment)
export SUPABASE_URL="https://xyz.supabase.co"
export SUPABASE_ANON_KEY="eyJ..."
export SUPABASE_SERVICE_KEY="eyJ..."  # rahasia — hanya di backend
```

```python
# Di kode Python — baca dari environment
import os
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
```

```typescript
// Di kode TypeScript/Vite — prefix VITE_ agar ter-bundle ke frontend
// .env file (JANGAN commit ke git)
VITE_SUPABASE_URL=https://xyz.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

// Akses di kode:
const url = import.meta.env.VITE_SUPABASE_URL
```

---

## File `.env` dan `.gitignore`

Simpan credentials di file `.env` lokal:

```bash
# .env (TIDAK dicommit ke git)
VITE_SUPABASE_URL=https://fkgnmrnckcnqvjsyunla.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...

# .env.example (DICOMMIT — berisi placeholder, bukan nilai asli)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

File `.gitignore` wajib ada:
```
.env
.env.local
.env.production
*.secret
```

---

## Checklist Keamanan API Key

- [ ] Anon key boleh di frontend, service key JANGAN
- [ ] File `.env` masuk `.gitignore`
- [ ] Buat `.env.example` sebagai template untuk kontributor
- [ ] Aktifkan RLS di semua tabel Supabase
- [ ] Jika key bocor ke GitHub: **rotate/regenerate segera** di dashboard Supabase

---

## Cara Kerja di Arsitektur SIDIX

```
Browser (app.sidixlab.com)
  └── supabase-js dengan ANON KEY
        └── RLS memastikan user hanya akses data sendiri

VPS Backend (Python FastAPI, port 8765)
  └── supabase-py dengan SERVICE KEY (via env var)
        └── Akses penuh untuk operasi admin/corpus
```

Alur pengambilan API key dari Supabase Dashboard:
1. Masuk ke project → Settings → API
2. Salin "Project URL"
3. Salin "anon / public" key → simpan di `.env` frontend
4. Salin "service_role" key → simpan di server sebagai env var (JANGAN di repo)
