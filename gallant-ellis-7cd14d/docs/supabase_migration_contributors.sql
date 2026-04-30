-- Migration: contributors + user_profiles + user_onboarding + beta_testers
-- Run di Supabase SQL Editor: https://supabase.com/dashboard/project/fkgnmrnckcnqvjsyunla/sql

-- ── Contributors table ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contributors (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name         TEXT NOT NULL,
  email        TEXT NOT NULL UNIQUE,
  role         TEXT NOT NULL DEFAULT 'developer', -- developer | researcher | academic
  interest     TEXT,
  wants_newsletter BOOLEAN DEFAULT true,
  lang         TEXT DEFAULT 'id',
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- RLS: allow insert from frontend (anon + authenticated)
ALTER TABLE contributors ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can register as contributor"
  ON contributors FOR INSERT TO anon, authenticated WITH CHECK (true);
CREATE POLICY "Only authenticated can read contributors"
  ON contributors FOR SELECT TO authenticated USING (true);

-- ── User profiles table ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email           TEXT,
  full_name       TEXT,
  avatar_url      TEXT,
  role            TEXT DEFAULT 'user', -- user | developer | researcher
  onboarding_done BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile"
  ON user_profiles FOR SELECT TO authenticated USING (auth.uid() = id);
CREATE POLICY "Users can update own profile"
  ON user_profiles FOR ALL TO authenticated USING (auth.uid() = id);

-- ── User onboarding answers ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_onboarding (
  user_id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  ai_features_wanted   TEXT,
  ai_agents_used       TEXT,
  ai_liked             TEXT,
  ai_frustrations      TEXT,
  one_feature_request  TEXT,
  role                 TEXT DEFAULT 'user',
  contribute_interest  TEXT,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own onboarding"
  ON user_onboarding FOR ALL TO authenticated USING (auth.uid() = user_id);

-- ── Beta testers counter ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS beta_testers (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id    UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
  joined_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE beta_testers ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Authenticated can register as beta tester"
  ON beta_testers FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Anyone can count beta testers"
  ON beta_testers FOR SELECT TO anon, authenticated USING (true);

-- ── Developer profiles ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS developer_profiles (
  user_id      UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  github_url   TEXT,
  skills       TEXT,
  availability TEXT,
  motivation   TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE developer_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage own developer profile"
  ON developer_profiles FOR ALL TO authenticated USING (auth.uid() = user_id);

-- ── Existing: newsletter table (if not exists) ───────────────────────────────
CREATE TABLE IF NOT EXISTS newsletter (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email      TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE newsletter ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can subscribe"
  ON newsletter FOR INSERT TO anon, authenticated WITH CHECK (true);
