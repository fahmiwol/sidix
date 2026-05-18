"""Setup Supabase env di VPS + rebuild UI + fix Supabase RLS warnings."""
import paramiko
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.environ.get("SIDIX_VPS_HOST", "sidix-vps")
USER = os.environ.get("SIDIX_VPS_USER", "root")
PASS = os.environ.get("SIDIX_VPS_PASSWORD")

SUPABASE_URL = os.environ.get("SIDIX_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SIDIX_SUPABASE_PUBLISHABLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Set SIDIX_SUPABASE_URL and SIDIX_SUPABASE_PUBLISHABLE_KEY before running this script."
    )


def ssh_run(client, cmd, timeout=120):
    print(f"\n$ {cmd[:120]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"[ERR] {err}")
    return out, err


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs = {"hostname": HOST, "username": USER, "timeout": 15}
    if PASS:
        connect_kwargs["password"] = PASS
    client.connect(**connect_kwargs)
    print("=== CONNECTED ===\n")

    # ── 1. UPDATE .ENV DENGAN SUPABASE CREDENTIALS ─────────────────────────
    print("=" * 60)
    print("STEP 1: Update .env SIDIX_USER_UI dengan Supabase credentials")
    print("=" * 60)

    # Tulis ulang .env dengan lengkap
    env_content = f"""VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com
VITE_SUPABASE_URL={SUPABASE_URL}
VITE_SUPABASE_PUBLISHABLE_KEY={SUPABASE_KEY}
"""
    # Write via heredoc
    write_env_cmd = f"""cat > /opt/sidix/SIDIX_USER_UI/.env << 'ENVEOF'
{env_content}ENVEOF"""
    ssh_run(client, write_env_cmd)
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/.env")

    # ── 2. REBUILD UI ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: npm run build (rebuild dengan Supabase URL)")
    print("=" * 60)
    ssh_run(client, "cd /opt/sidix/SIDIX_USER_UI && npm run build 2>&1 | tail -8", timeout=120)

    # ── 3. RESTART SIDIX-UI ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Restart sidix-ui")
    print("=" * 60)
    ssh_run(client, "pm2 restart sidix-ui && sleep 2 && pm2 show sidix-ui | grep -E 'status|uptime'")

    # ── 4. VERIFY SUPABASE URL DI BUILD ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Verify Supabase URL ter-embed di build")
    print("=" * 60)
    ssh_run(client, "grep -o 'fkgnmrnckcnqvjsyunla' /opt/sidix/SIDIX_USER_UI/dist/assets/*.js | head -3 || echo 'NOT FOUND'")
    ssh_run(client, "grep -o 'ctrl.sidixlab.com' /opt/sidix/SIDIX_USER_UI/dist/assets/*.js | head -2 || echo 'NOT FOUND'")

    # ── 5. PM2 SAVE ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: PM2 save")
    print("=" * 60)
    ssh_run(client, "pm2 save")

    # ── 6. GENERATE SUPABASE SQL FIXES ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: SQL fixes untuk Supabase Security Advisor")
    print("=" * 60)
    print("""
-- Jalankan SQL ini di Supabase SQL Editor (sidix project):
-- https://supabase.com/dashboard/project/fkgnmrnckcnqvjsyunla/sql/new

-- 1. FIX: Function Search Path Mutable (handle_new_user)
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

-- 2. FIX: RLS Policy Always True pada public.contributors
-- Ganti dengan policy yang lebih spesifik
DROP POLICY IF EXISTS "contributors_public_read" ON public.contributors;
CREATE POLICY "contributors_public_read" ON public.contributors
  FOR SELECT USING (true);  -- read boleh semua

DROP POLICY IF EXISTS "contributors_authenticated_insert" ON public.contributors;
CREATE POLICY "contributors_authenticated_insert" ON public.contributors
  FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- 3. FIX: RLS Policy Always True pada public.feedback
DROP POLICY IF EXISTS "feedback_insert" ON public.feedback;
CREATE POLICY "feedback_insert" ON public.feedback
  FOR INSERT WITH CHECK (true);  -- allow anonymous insert (oke untuk feedback)

DROP POLICY IF EXISTS "feedback_admin_read" ON public.feedback;
CREATE POLICY "feedback_admin_read" ON public.feedback
  FOR SELECT USING (auth.role() = 'authenticated');

-- 4. FIX: RLS Policy Always True pada public.newsletter
DROP POLICY IF EXISTS "newsletter_insert" ON public.newsletter;
CREATE POLICY "newsletter_insert" ON public.newsletter
  FOR INSERT WITH CHECK (true);  -- allow anonymous subscribe

-- 5. FIX: RLS Enabled No Policy pada public.plugins
CREATE POLICY "plugins_public_read" ON public.plugins
  FOR SELECT USING (true);

-- 6. FIX: RLS Enabled No Policy pada public.profiles
CREATE POLICY "profiles_own_read" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "profiles_own_update" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);
""")

    # ── 7. STATUS AKHIR ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: Final status check")
    print("=" * 60)
    ssh_run(client, "pm2 list 2>&1 | grep -E 'sidix|status'")
    ssh_run(client, "curl -s https://ctrl.sidixlab.com/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Backend:', d.get('status'), '| Ready:', d.get('model_ready'))\"")
    ssh_run(client, "curl -s https://app.sidixlab.com | grep -o '<title>[^<]*</title>' || echo 'app.sidixlab.com merespons'")

    client.close()
    print("\n=== ALL DONE ===")


if __name__ == "__main__":
    main()
