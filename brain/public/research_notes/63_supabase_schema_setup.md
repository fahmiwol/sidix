# Supabase Schema Setup — SIDIX Database

## Konteks

Catatan ini mendokumentasikan proses setup schema database Supabase untuk SIDIX.
Project: `sidix`, URL: `https://fkgnmrnckcnqvjsyunla.supabase.co`, region: Singapore (ap-southeast-1).

---

## Terminologi API Key Supabase (update 2025)

Supabase me-rename API key mereka:

| Nama Lama | Nama Baru | Kegunaan |
|---|---|---|
| `anon key` | **Publishable key** | Frontend/browser — aman dipublik, dibatasi RLS |
| `service_role key` | **Secret key** | Backend server — bypass RLS, JANGAN di frontend |

Prefix key baru: `sb_publishable_...` dan `sb_secret_...`

---

## Cara Mendapatkan API Keys

1. Buka Supabase Dashboard → project → **Settings** → **API Keys**
2. Tab: **Publishable and secret API keys**
3. Salin **Publishable key** → simpan di `.env` frontend
4. Scroll ke **Secret keys** → salin → simpan di server sebagai env var

---

## Schema SQL SIDIX

Jalankan di Supabase → **SQL Editor** → **New query**:

```sql
-- ══════════════════════════════════════════════
-- SIDIX Database Schema v1.0
-- ══════════════════════════════════════════════

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 1. Profiles (extend Supabase Auth) ────────
CREATE TABLE profiles (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role        TEXT NOT NULL DEFAULT 'public'
                CHECK (role IN ('public', 'developer', 'admin')),
  display_name TEXT,
  github_url  TEXT,
  bio         TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-create profile saat user baru register
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, display_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ── 2. Newsletter ──────────────────────────────
CREATE TABLE newsletter (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email       TEXT NOT NULL UNIQUE,
  confirmed   BOOLEAN NOT NULL DEFAULT FALSE,
  token       TEXT,  -- untuk email konfirmasi
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 3. Feedback & Feature Request ─────────────
CREATE TABLE feedback (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID REFERENCES profiles(id) ON DELETE SET NULL,
  type        TEXT NOT NULL DEFAULT 'saran'
                CHECK (type IN ('bug', 'saran', 'fitur')),
  message     TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'closed')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── 4. Plugins ────────────────────────────────
CREATE TABLE plugins (
  id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  author_id    UUID REFERENCES profiles(id) ON DELETE SET NULL,
  name         TEXT NOT NULL,
  slug         TEXT NOT NULL UNIQUE,  -- identifier unik, url-friendly
  description  TEXT,
  repo_url     TEXT NOT NULL,
  manifest     JSONB,  -- deklarasi kemampuan plugin
  status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'approved', 'rejected')),
  reviewed_by  UUID REFERENCES profiles(id) ON DELETE SET NULL,
  review_notes TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- ══════════════════════════════════════════════

ALTER TABLE profiles  ENABLE ROW LEVEL SECURITY;
ALTER TABLE newsletter ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback  ENABLE ROW LEVEL SECURITY;
ALTER TABLE plugins   ENABLE ROW LEVEL SECURITY;

-- Profiles: user bisa lihat & edit profil sendiri
CREATE POLICY "profiles_select_own" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_update_own" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Admin bisa lihat semua profil
CREATE POLICY "profiles_select_admin" ON profiles
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Newsletter: siapapun bisa subscribe (insert), hanya diri sendiri yang bisa lihat
CREATE POLICY "newsletter_insert_public" ON newsletter
  FOR INSERT WITH CHECK (true);

CREATE POLICY "newsletter_select_own" ON newsletter
  FOR SELECT USING (email = current_setting('request.jwt.claims', true)::jsonb->>'email');

-- Feedback: siapapun bisa submit (termasuk anonim)
CREATE POLICY "feedback_insert_public" ON feedback
  FOR INSERT WITH CHECK (true);

CREATE POLICY "feedback_select_own" ON feedback
  FOR SELECT USING (user_id = auth.uid() OR user_id IS NULL);

-- Admin bisa lihat semua feedback
CREATE POLICY "feedback_select_admin" ON feedback
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Plugins: developer bisa submit, semua bisa lihat yang approved
CREATE POLICY "plugins_insert_developer" ON plugins
  FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('developer', 'admin'))
  );

CREATE POLICY "plugins_select_approved" ON plugins
  FOR SELECT USING (status = 'approved');

CREATE POLICY "plugins_select_own" ON plugins
  FOR SELECT USING (author_id = auth.uid());

CREATE POLICY "plugins_select_admin" ON plugins
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );

CREATE POLICY "plugins_update_admin" ON plugins
  FOR UPDATE USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
  );
```

---

## Cara Menjalankan Migration

1. Supabase Dashboard → **SQL Editor** (ikon database di sidebar kiri)
2. Klik **+ New query**
3. Paste SQL di atas
4. Klik **Run** (Ctrl+Enter)
5. Verifikasi: sidebar kiri → **Table Editor** → harus muncul tabel `profiles`, `newsletter`, `feedback`, `plugins`

---

## Environment Variables yang Dibutuhkan

### Frontend (SIDIX_USER_UI/.env)
```bash
VITE_SUPABASE_URL=https://fkgnmrnckcnqvjsyunla.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
```

### Backend VPS (export di server)
```bash
export SUPABASE_URL="https://fkgnmrnckcnqvjsyunla.supabase.co"
export SUPABASE_SECRET_KEY="sb_secret_..."
```

File `.env` JANGAN dicommit ke GitHub — pastikan ada di `.gitignore`.

---

## Struktur Relasi Tabel

```
auth.users (Supabase internal)
    │
    └─→ profiles (role: public/developer/admin)
              │
              ├─→ plugins (author_id, reviewed_by)
              └─→ feedback (user_id, nullable)

newsletter (standalone, tidak perlu auth)
```
