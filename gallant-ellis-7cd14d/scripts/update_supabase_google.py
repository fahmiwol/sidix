"""Update Supabase Google OAuth config + Site URL via Management API."""
import urllib.request
import urllib.error
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_REF = "fkgnmrnckcnqvjsyunla"

# New Google OAuth credentials (from JSON file downloaded)
GOOGLE_CLIENT_ID = "REDACTED_GOOGLE_CLIENT_ID"
GOOGLE_CLIENT_SECRET = "REDACTED_GOOGLE_CLIENT_SECRET"
SITE_URL = "https://app.sidixlab.com"

# Anon key (publishable) — for read access
ANON_KEY = "REDACTED_ANON_KEY"

BASE = f"https://{PROJECT_REF}.supabase.co"


def req(method, path, data=None, key=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    headers = {
        "apikey": key or ANON_KEY,
        "Authorization": f"Bearer {key or ANON_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        return e.code, {"error": body_err}


def check_auth_settings():
    print("\n[1] CEK AUTH SETTINGS SAAT INI")
    status, data = req("GET", "/auth/v1/settings")
    if status == 200:
        ext = data.get("external", {})
        print(f"  Google enabled: {ext.get('google', False)}")
        print(f"  Site URL: {data.get('site_url', 'NOT SET')}")
        print(f"  Redirect URLs: {data.get('uri_allow_list', 'NOT SET')}")
    else:
        print(f"  Status {status}: {data}")
    return status, data


def test_newsletter_insert():
    """Test apakah bisa subscribe ke newsletter (test RLS)."""
    print("\n[2] TEST NEWSLETTER INSERT (RLS check)")
    status, data = req("POST", "/rest/v1/newsletter", {"email": "test-rls@sidixlab.com"})
    if status in (200, 201):
        print(f"  Insert OK: {data}")
    elif status == 409:
        print(f"  Duplicate (sudah ada) — RLS allow insert: OK")
    else:
        print(f"  Status {status}: {data}")


def check_dns():
    """Check apakah ctrl.sidixlab.com resolve."""
    import socket
    print("\n[3] DNS CHECK ctrl.sidixlab.com")
    try:
        ip = socket.gethostbyname("ctrl.sidixlab.com")
        print(f"  ctrl.sidixlab.com → {ip} ({'OK VPS' if '72.62' in ip else 'CEK'})")
    except Exception as e:
        print(f"  GAGAL resolve ctrl.sidixlab.com: {e}")

    print("\n[4] DNS CHECK mail.sidixlab.com")
    try:
        ip = socket.gethostbyname("mail.sidixlab.com")
        print(f"  mail.sidixlab.com → {ip}")
    except Exception as e:
        print(f"  GAGAL: {e}")


def main():
    print("=" * 60)
    print("SUPABASE GOOGLE OAUTH UPDATE")
    print("=" * 60)

    check_auth_settings()
    test_newsletter_insert()
    check_dns()

    print("\n" + "=" * 60)
    print("INSTRUKSI MANUAL YANG HARUS DILAKUKAN")
    print("=" * 60)
    print(f"""
A. Update Supabase Google OAuth credentials:
   URL: https://supabase.com/dashboard/project/{PROJECT_REF}/auth/providers

   Klik "Google" → Update:
   Client ID:     {GOOGLE_CLIENT_ID}
   Client Secret: {GOOGLE_CLIENT_SECRET}
   Klik Save

B. Set Site URL + Redirect URLs:
   URL: https://supabase.com/dashboard/project/{PROJECT_REF}/auth/url-configuration

   Site URL:    {SITE_URL}
   Redirect URL (tambah): {SITE_URL}/**

C. Google OAuth Consent Screen — PENTING:
   URL: https://console.cloud.google.com/auth/clients

   Status kamu: TESTING (hanya test users yang bisa login!)

   Untuk development: Tambah email kamu sebagai Test User
   URL: https://console.cloud.google.com/auth/audience
   → Add Users → masukkan email yang ingin bisa login

   Untuk production: Publish app (perlu verifikasi Google)

D. DNS yang sudah OK:
   ✅ MX @  → mail.sidixlab.com (Priority 10)
   ✅ A  @  → 72.62.125.6
   ✅ A  app → 72.62.125.6

   Cek apakah ctrl subdomain sudah ada:
   Tambahkan jika belum: A ctrl → 72.62.125.6
""")

    print("=" * 60)
    print("TEST CONNECTIVITY BACKEND VIA HTTPS")
    print("=" * 60)
    # Test ctrl.sidixlab.com health
    health_req = urllib.request.Request(
        "https://ctrl.sidixlab.com/health",
        headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(health_req, timeout=10) as resp:
            data = json.loads(resp.read())
            print(f"  ctrl.sidixlab.com/health: {data.get('status')} | Model: {data.get('model_ready')}")
    except Exception as e:
        print(f"  ctrl.sidixlab.com/health ERROR: {e}")


if __name__ == "__main__":
    main()
