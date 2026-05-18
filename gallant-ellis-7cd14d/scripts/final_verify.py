"""Final verification — test semua komponen SIDIX."""
import urllib.request
import urllib.error
import json
import socket
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PROJECT_REF = "fkgnmrnckcnqvjsyunla"
ANON_KEY = "sb_publishable_ZGcdlsaf-ghUqKvkZn3HQg_GE1CFUWM"
BASE_SUPABASE = f"https://{PROJECT_REF}.supabase.co"
BASE_APP = "https://app.sidixlab.com"
BASE_CTRL = "https://ctrl.sidixlab.com"

OK = "OK"
FAIL = "FAIL"


def check(label, ok, detail=""):
    icon = "✓" if ok else "✗"
    status = OK if ok else FAIL
    print(f"  [{icon}] {label}: {status}  {detail}")
    return ok


def http_get(url, headers=None, timeout=10):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)


def http_post(url, data, headers=None, timeout=10):
    body = json.dumps(data).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body_err = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body_err)
        except Exception:
            return e.code, {"raw": body_err}
    except Exception as ex:
        return 0, {"error": str(ex)}


def main():
    results = []

    print("\n" + "=" * 60)
    print("1. DNS RESOLUTION")
    print("=" * 60)
    for host in ["app.sidixlab.com", "ctrl.sidixlab.com", "mail.sidixlab.com", "sidixlab.com"]:
        try:
            ip = socket.gethostbyname(host)
            ok = "72.62.125.6" in ip
            results.append(check(host, ok, f"→ {ip}"))
        except Exception as e:
            results.append(check(host, False, str(e)))

    print("\n" + "=" * 60)
    print("2. BACKEND HEALTH (ctrl.sidixlab.com)")
    print("=" * 60)
    status, raw = http_get(f"{BASE_CTRL}/health")
    if status == 200:
        d = json.loads(raw)
        results.append(check("Backend status", d.get("status") == "ok", f"model_ready={d.get('model_ready')} tools={d.get('tools_available')}"))
        results.append(check("Corpus", d.get("corpus_doc_count", 0) > 0, f"{d.get('corpus_doc_count')} docs"))
        results.append(check("LLM ready", d.get("model_ready") is True))
    else:
        results.append(check("Backend health", False, f"HTTP {status}"))

    print("\n" + "=" * 60)
    print("3. FRONTEND (app.sidixlab.com)")
    print("=" * 60)
    status, raw = http_get(BASE_APP)
    results.append(check("app.sidixlab.com loads", status == 200, f"HTTP {status}"))
    results.append(check("Title SIDIX", "SIDIX" in raw))
    results.append(check("Supabase URL embedded", "fkgnmrnckcnqvjsyunla" in raw))
    results.append(check("ctrl.sidixlab.com embedded", "ctrl.sidixlab.com" in raw))

    print("\n" + "=" * 60)
    print("4. SUPABASE AUTH CONFIG")
    print("=" * 60)
    status, raw = http_get(f"{BASE_SUPABASE}/auth/v1/settings", headers={"apikey": ANON_KEY})
    if status == 200:
        d = json.loads(raw)
        ext = d.get("external", {})
        site_url = d.get("site_url", "")
        google_ok = ext.get("google", False)
        site_ok = "app.sidixlab.com" in (site_url or "")
        results.append(check("Google OAuth enabled", google_ok))
        results.append(check("Site URL set", site_ok, f"→ {site_url or 'NOT SET'}"))
    else:
        results.append(check("Supabase auth settings", False, f"HTTP {status}"))

    print("\n" + "=" * 60)
    print("5. SUPABASE DATABASE (tabel accessibility)")
    print("=" * 60)
    tables = ["user_profiles", "contributors", "feedback", "newsletter"]
    for table in tables:
        status, raw = http_get(
            f"{BASE_SUPABASE}/rest/v1/{table}?limit=1",
            headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"}
        )
        ok = status in (200, 206)
        results.append(check(f"Table {table}", ok, f"HTTP {status}"))

    print("\n" + "=" * 60)
    print("6. QUOTA ENDPOINT")
    print("=" * 60)
    status, d = http_post(f"{BASE_CTRL}/quota/status", {})
    if status in (200, 405):
        # quota/status is GET
        status2, raw2 = http_get(f"{BASE_CTRL}/quota/status")
        if status2 == 200:
            d2 = json.loads(raw2)
            ok = d2.get("ok") is True
            results.append(check("Quota guest", ok, f"limit={d2.get('limit')} remaining={d2.get('remaining')}"))
        else:
            results.append(check("Quota endpoint", False, f"HTTP {status2}"))
    else:
        results.append(check("Quota endpoint", status == 200, f"HTTP {status}"))

    print("\n" + "=" * 60)
    print("RINGKASAN")
    print("=" * 60)
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    print(f"\n  Total: {total} | Pass: {passed} | Fail: {failed}")
    if failed == 0:
        print("\n  SEMUA SISTEM GO. SIDIX siap dipakai!")
    else:
        print(f"\n  {failed} item perlu perhatian (lihat tanda [x] di atas)")


if __name__ == "__main__":
    main()
