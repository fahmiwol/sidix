"""Fix Supabase RLS warnings via Management API."""
import urllib.request
import urllib.error
import json
import sys

# Supabase project
PROJECT_REF = "fkgnmrnckcnqvjsyunla"
# Service role key needed for SQL execution via API
# We'll use the publishable key for a connectivity check first
ANON_KEY = "sb_publishable_ZGcdlsaf-ghUqKvkZn3HQg_GE1CFUWM"
BASE_URL = f"https://{PROJECT_REF}.supabase.co"


def check_anon_connection():
    """Test connectivity dengan anon key."""
    url = f"{BASE_URL}/rest/v1/"
    req = urllib.request.Request(url, headers={
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"Supabase REST API: {resp.status} OK")
            return True
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        return False
    except Exception as ex:
        print(f"Error: {ex}")
        return False


def check_tables():
    """List tables yang available via REST."""
    tables = ["user_profiles", "contributors", "feedback", "newsletter", "plugins", "profiles"]
    print("\nChecking table accessibility...")
    for table in tables:
        url = f"{BASE_URL}/rest/v1/{table}?limit=1"
        req = urllib.request.Request(url, headers={
            "apikey": ANON_KEY,
            "Authorization": f"Bearer {ANON_KEY}",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                print(f"  {table}: accessible (rows: {len(data)})")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"  {table}: HTTP {e.code} — {body[:100]}")
        except Exception as ex:
            print(f"  {table}: Error — {ex}")


def check_auth_config():
    """Check Supabase Auth configuration."""
    url = f"{BASE_URL}/auth/v1/settings"
    req = urllib.request.Request(url, headers={
        "apikey": ANON_KEY,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            external = data.get("external", {})
            google_enabled = external.get("google", False)
            print(f"\nAuth Config:")
            print(f"  Google OAuth: {'ENABLED' if google_enabled else 'DISABLED'}")
            site_url = data.get("site_url", "NOT SET")
            print(f"  Site URL: {site_url}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"Auth settings: HTTP {e.code} — {body[:200]}")
    except Exception as ex:
        print(f"Auth settings error: {ex}")


def main():
    print("=" * 60)
    print("SUPABASE CONNECTIVITY CHECK")
    print(f"Project: {PROJECT_REF}")
    print("=" * 60)

    check_anon_connection()
    check_tables()
    check_auth_config()

    print("\n" + "=" * 60)
    print("SQL YANG PERLU DIJALANKAN DI SUPABASE SQL EDITOR")
    print("URL: https://supabase.com/dashboard/project/fkgnmrnckcnqvjsyunla/sql/new")
    print("=" * 60)

    sql = """
-- ═══════════════════════════════════════════════════════
-- SIDIX Supabase Security Fixes
-- Run in: SQL Editor → New Query
-- ═══════════════════════════════════════════════════════

-- 1. Fix handle_new_user search_path (Security Warning)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public'
AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, full_name, avatar_url, role, onboarding_done, created_at)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'full_name', new.email),
    new.raw_user_meta_data->>'avatar_url',
    'user',
    false,
    now()
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$;

-- 2. Drop overly permissive RLS on contributors (insert only auth)
DO $$ BEGIN
  DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON public.contributors;
  DROP POLICY IF EXISTS "Allow all" ON public.contributors;
  DROP POLICY IF EXISTS "contributors_all" ON public.contributors;
EXCEPTION WHEN OTHERS THEN NULL; END $$;

CREATE POLICY "contributors_read_all" ON public.contributors
  FOR SELECT USING (true);
CREATE POLICY "contributors_insert_auth" ON public.contributors
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- 3. Fix feedback RLS
DO $$ BEGIN
  DROP POLICY IF EXISTS "Allow all" ON public.feedback;
  DROP POLICY IF EXISTS "feedback_all" ON public.feedback;
EXCEPTION WHEN OTHERS THEN NULL; END $$;

CREATE POLICY "feedback_insert_anon" ON public.feedback
  FOR INSERT WITH CHECK (true);
CREATE POLICY "feedback_select_auth" ON public.feedback
  FOR SELECT USING (auth.role() = 'authenticated');

-- 4. Fix newsletter RLS
DO $$ BEGIN
  DROP POLICY IF EXISTS "Allow all" ON public.newsletter;
  DROP POLICY IF EXISTS "newsletter_all" ON public.newsletter;
EXCEPTION WHEN OTHERS THEN NULL; END $$;

CREATE POLICY "newsletter_insert_anon" ON public.newsletter
  FOR INSERT WITH CHECK (true);

-- 5. Add policy to plugins (RLS enabled but no policy)
DO $$ BEGIN
  CREATE POLICY "plugins_read_all" ON public.plugins
    FOR SELECT USING (true);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 6. Add policy to profiles (RLS enabled but no policy)
DO $$ BEGIN
  CREATE POLICY "profiles_read_own" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
  CREATE POLICY "profiles_update_own" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Done! Run SECURITY ADVISOR refresh setelahnya.
"""
    print(sql)

    print("\n" + "=" * 60)
    print("GOOGLE CLOUD CONSOLE — yang perlu dicek")
    print("URL: https://console.cloud.google.com/apis/credentials")
    print("=" * 60)
    print("""
Di OAuth 2.0 Client ID kamu, pastikan ada:

Authorized JavaScript origins:
  https://app.sidixlab.com
  https://fkgnmrnckcnqvjsyunla.supabase.co

Authorized redirect URIs:
  https://fkgnmrnckcnqvjsyunla.supabase.co/auth/v1/callback

Tanpa kedua ini → Google Login akan gagal.
""")


if __name__ == "__main__":
    main()
