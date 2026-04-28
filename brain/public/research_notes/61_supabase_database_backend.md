# Supabase sebagai Backend-as-a-Service — Panduan untuk Developer SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa itu Supabase?

Supabase adalah platform open-source yang menyediakan PostgreSQL database dengan fitur lengkap:
- **Auth** (email, GitHub OAuth, magic link, dll)
- **RESTful API otomatis** dari schema database
- **Row Level Security (RLS)** — kontrol akses data per-baris di level database
- **Realtime** subscriptions
- **Storage** untuk file
- **Edge Functions** (serverless)

Supabase bukan vendor lock-in — di baliknya adalah PostgreSQL standar. Bisa self-host kapan saja.

---

## Konsep Dasar Database Relasional

### Tabel & Relasi

Database relasional menyimpan data dalam **tabel** (seperti spreadsheet), dengan **relasi** antar tabel.

```
users                    plugins
-------                  -------
id (PK)  ←──────────── author_id (FK)
email                    name
role                     status
created_at               created_at
```

`PK` = Primary Key (identifier unik per baris)
`FK` = Foreign Key (referensi ke tabel lain)

### Row Level Security (RLS)

RLS memastikan user hanya bisa akses data miliknya sendiri, diatur di level database:

```sql
-- Policy: user hanya bisa lihat feedback miliknya sendiri
CREATE POLICY "user_own_feedback" ON feedback
  FOR SELECT USING (auth.uid() = user_id);
```

Ini jauh lebih aman dari validasi di aplikasi — walau ada bug di kode, database tetap memblokir.

---

## Arsitektur SIDIX + Supabase

```
Browser
  │
  ├── app.sidixlab.com (Vite UI)
  │     ├── Chat → brain_qa backend (port 8765, BM25 RAG)
  │     └── Auth/User → Supabase API
  │
  └── ctrl.sidixlab.com (Admin panel)
        ├── Corpus management → brain_qa backend
        └── Plugin review → Supabase API
```

### Tabel yang direncanakan:

```sql
-- Pengguna (dikelola Supabase Auth + profil tambahan)
profiles
  id          uuid (FK → auth.users.id)
  role        text ('public' | 'developer' | 'admin')
  github_url  text
  bio         text
  created_at  timestamptz

-- Plugin kontribusi developer
plugins
  id           uuid
  author_id    uuid (FK → profiles.id)
  name         text
  description  text
  repo_url     text
  manifest     jsonb  -- deklarasi kemampuan plugin
  status       text ('pending' | 'approved' | 'rejected')
  reviewed_by  uuid (FK → profiles.id)
  review_notes text
  created_at   timestamptz

-- Newsletter
newsletter
  id         uuid
  email      text UNIQUE
  confirmed  boolean
  token      text  -- untuk konfirmasi email
  created_at timestamptz

-- Feedback & Feature Request
feedback
  id         uuid
  user_id    uuid (FK → profiles.id, nullable — bisa anonim)
  type       text ('bug' | 'saran' | 'fitur')
  message    text
  status     text ('open' | 'in_progress' | 'closed')
  created_at timestamptz
```

---

## Plugin SIDIX — Konsep

Plugin adalah ekstensi yang menambah kemampuan SIDIX tanpa mengubah core. Format manifest:

```json
{
  "name": "plugin-ekonomi-islam",
  "version": "1.0.0",
  "author": "github.com/username",
  "description": "Corpus ekonomi Islam: fiqih muamalah, akad, perbankan syariah",
  "type": "corpus",
  "adds": {
    "corpus_source": "brain/public/plugins/ekonomi-islam/",
    "persona": null,
    "tools": []
  },
  "permissions": ["read_corpus"],
  "license": "MIT"
}
```

Tipe plugin yang mungkin:
- `corpus` — menambah knowledge base baru
- `persona` — menambah persona AI baru (karakter, gaya bahasa, bidang keahlian)
- `tool` — menambah kemampuan tool (kalkulator, konversi, API eksternal)

---

## Alur Kontribusi Plugin

```
1. Developer daftar akun → role: developer
2. Developer submit plugin → tabel plugins, status: pending
3. Admin review di ctrl.sidixlab.com
   - Cek keamanan: tidak ada kode berbahaya
   - Cek kualitas: corpus akurat, persona konsisten
4a. APPROVE → status: approved → plugin diintegrasikan
4b. REJECT  → status: rejected + review_notes → developer revisi
```

---

## Supabase Auth — Cara Kerja

### GitHub OAuth (untuk developer)

```javascript
// Login dengan GitHub
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
  options: { redirectTo: 'https://app.sidixlab.com/auth/callback' }
});
```

### Magic Link (untuk public user)

```javascript
// Kirim magic link ke email
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
  options: { emailRedirectTo: 'https://app.sidixlab.com' }
});
```

---

## Environment Variables yang Dibutuhkan

```bash
# Di server VPS (/tmp/sidix/.env atau export di shell)
SUPABASE_URL=https://fkgnmrnckcnqvjsyunla.supabase.co
SUPABASE_ANON_KEY=<anon key dari dashboard>
SUPABASE_SERVICE_KEY=<service role key — RAHASIA, hanya di backend>
```

`anon key` → aman di frontend (dibatasi RLS)
`service key` → JANGAN di frontend, hanya di Python backend yang trusted

---

## Referensi

- Dokumentasi resmi: https://supabase.com/docs
- Supabase JS client: https://github.com/supabase/supabase-js
- PostgreSQL RLS: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
