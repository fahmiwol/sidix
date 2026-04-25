# 219 — Own Auth via Google Identity Services (Migrasi dari Supabase)

**Date**: 2026-04-26
**Tag**: ARCHITECTURE / SECURITY / FEAT
**Status**: Deployed ke production
**Trigger**: User feedback "kenapa nggak bikin halaman login sendiri buat user?"

---

## Konteks: Kenapa pivot dari Supabase Auth?

Sebelumnya SIDIX user-app pakai **Supabase Auth** (`@supabase/supabase-js`) untuk
Google Sign-In. Bekerja, tapi punya tradeoff:

1. **Lock-in vendor** — kalau Supabase down/policy berubah, login mati.
2. **Tidak ada activity log per-user** — Supabase track session, tapi tidak
   capture pertanyaan/jawaban untuk SIDIX learning.
3. **Trigger handle_new_user error** — production sempat lihat error
   `Database error saving new user` dari Supabase trigger yang konfigurasinya
   harus di-fix manual di SQL editor.
4. **Heavy dependency** — `@supabase/supabase-js` + auth flow kompleks
   (event subscription, session persistence) untuk fitur sederhana.
5. **Database user di pihak ketiga** — kalau mau analyze user growth,
   harus query Supabase, bukan database sendiri.

**User insight**: "kita ppunya database user, dan activity log user, log
pertanyaaan jgua buat sidix belajar."

→ Migrasi ke **own auth** dengan **Google Identity Services (GIS)**.

---

## Apa itu Google Identity Services (GIS)?

GIS = library Google official untuk web auth, replace dari "Sign In With Google"
classic dan gapi.auth2. Pattern recommended Google sejak 2022.

Reference: https://codelabs.developers.google.com/codelabs/sign-in-with-google-button

### Flow dasar GIS (ID token flow):

```
[User klik tombol]
       ↓
[Google popup → user pilih akun]
       ↓
[Google return ID token JWT (~1KB)]
       ↓
[Frontend callback dengan response.credential]
       ↓
[POST credential ke backend /auth/google]
       ↓
[Backend verify ID token via Google public keys]
       ↓
[Backend upsert user di local DB]
       ↓
[Backend issue session JWT (HMAC-signed)]
       ↓
[Frontend simpan JWT di localStorage]
       ↓
[Subsequent requests: Authorization: Bearer <jwt>]
```

### Yang berbeda dari OAuth code-exchange flow:
- **TIDAK butuh Client Secret** — ID token sudah signed oleh Google
- **TIDAK butuh callback URL backend** — flow di-handle di frontend
- **TIDAK butuh refresh token** — ID token short-lived (1 jam),
  setelah itu issue session JWT sendiri (TTL 30 hari)

---

## Arsitektur SIDIX own auth

### Backend: `apps/brain_qa/brain_qa/auth_google.py`

Module mandiri (~280 lines), no third-party auth library. Komponen:

#### 1. Verify Google ID token
```python
def verify_google_id_token(id_token: str) -> Optional[dict]:
    # Hit Google tokeninfo endpoint (paling simpel, no JWKS parsing)
    r = httpx.get("https://oauth2.googleapis.com/tokeninfo",
                  params={"id_token": id_token})
    data = r.json()
    # Validate: aud == GOOGLE_OAUTH_CLIENT_ID, exp > now, email_verified
    return data
```

**Why tokeninfo endpoint?**
- Sederhana, no library deps (`google-auth` lib heavy ~10MB)
- Google handle kompleksitas JWKS rotation
- Latency ~150ms (acceptable untuk login flow yang infrequent)

**Trade-off**: ada network call ke Google per login. Untuk skala >1k login/min,
mending pakai cached JWKS (offline verification). Untuk SIDIX MVP, tokeninfo OK.

#### 2. User store (JSON file)

`apps/brain_qa/.data/users.json`:
```json
{
  "version": 1,
  "users": {
    "<google_sub>": {
      "id": "u_a3f9b2c1d4e5",
      "google_sub": "10293847562...",
      "email": "user@gmail.com",
      "name": "User Name",
      "picture": "https://lh3.googleusercontent.com/...",
      "tier": "free",
      "is_admin": false,
      "created_at": "2026-04-26T12:00:00Z",
      "last_login_at": "2026-04-26T15:30:00Z",
      "login_count": 7
    }
  }
}
```

**Why JSON file (not SQLite)?**
- < 1000 user → file <100KB, fits in memory, no I/O bottleneck
- Atomic write via `_LOCK` threading
- Easy backup (rsync), easy inspect (jq), easy migrate
- Migrate ke SQLite kalau >10k user (estimasi user, bukan stretch goal)

#### 3. Session JWT (HMAC-SHA256)

```python
def issue_session_jwt(user_id, email, ttl_seconds=30*24*3600):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "email": email,
               "iat": now, "exp": now+ttl, "iss": "sidix"}
    h = b64url(json(header))
    p = b64url(json(payload))
    sig = HMAC-SHA256(secret, f"{h}.{p}")
    return f"{h}.{p}.{b64url(sig)}"
```

**Why HMAC, bukan RSA?**
- HMAC simetris, secret tunggal di server (no public key distribution)
- SIDIX self-hosted single backend → no need multi-issuer
- Verify cepat (~10μs vs ~1ms RSA)
- 30-day TTL = balance UX (jarang re-login) vs revoke (logout = client clear)

**Why TTL 30 days?**
- ChatGPT/Claude pattern: "stay signed in" untuk weeks
- Trade-off: token compromise window 30d, mitigation = HTTPS only + httpOnly
  cookie next iteration

#### 4. Activity log (JSONL append)

`apps/brain_qa/.data/activity_log.jsonl`:
```jsonl
{"ts":"2026-04-26T15:30:00Z","user_id":"u_xxx","email":"...","action":"ask","question":"apa itu...","persona":"AYMAN","mode":"casual","latency_ms":1240}
```

**Why JSONL?**
- Append-only, no race condition (single writer thread + file lock)
- Easy tail (`tail -100 activity_log.jsonl | jq`)
- Easy migrate ke ClickHouse/BigQuery later (one row = one event)

**Use cases**:
1. Per-user history → user lihat percakapan lama
2. Quality metrics → low-confidence answer detection per user
3. **SIDIX learning corpus** → feed pertanyaan high-quality ke training pair
4. Anti-abuse → detect spam pattern (>X requests/min)

---

### API endpoints (4 baru)

| Endpoint | Method | Auth | Tujuan |
|---|---|---|---|
| `/auth/config` | GET | Public | Frontend fetch Google Client ID |
| `/auth/google` | POST | Public | Login: verify credential, issue session JWT |
| `/auth/me` | GET | Bearer JWT | Restore session, return user info |
| `/auth/logout` | POST | Public | Stateless (frontend clear localStorage) |
| `/admin/users` | GET | Admin token | List all users (admin panel) |
| `/admin/activity` | GET | Admin token | List activity log (admin panel) |

**Why /auth/config?**
- Hindari hardcode Client ID di repo (gampang rotate)
- Frontend bisa lazy-load: render generic button → fetch config → enable button
- Detect misconfiguration: kalau Client ID kosong, frontend show "auth disabled"

---

### Frontend: `SIDIX_USER_UI/public/login.html`

Dedicated page (bukan modal), pattern sesuai Codelabs:

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>

<div id="g_id_onload"
     data-client_id=""  <!-- filled dynamically -->
     data-callback="handleGoogleCredential"
     data-ux_mode="popup">
</div>
<div class="g_id_signin" data-type="standard" data-theme="filled_black"></div>
```

**Why dedicated page (bukan modal di main app)?**
1. **Pre-login state UX** lebih clean — focus single CTA
2. **Reload-safe** — kalau user refresh saat login, state preserved
3. **OAuth redirect target** — `?next=` query → redirect post-login
4. **Mobile-friendly** — full-screen vs cramped modal
5. **Pattern familiar** — ChatGPT, Claude, Gemini all pakai dedicated /login

**Flow di main app**:
```typescript
document.getElementById('btn-auth')?.addEventListener('click', () => {
  if (ownAuthIsSignedIn()) {
    showProfileMenu();
  } else {
    const next = encodeURIComponent(window.location.pathname);
    window.location.href = `/login.html?next=${next}`;
  }
});
```

**Page-load restore**:
```typescript
async function loadOwnAuthUser() {
  const token = localStorage.getItem('sidix_session_jwt');
  if (!token) return;
  const res = await fetch(`${BRAIN_QA_BASE}/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!res.ok) {
    // Token expired/invalid → clear
    ['sidix_session_jwt', 'sidix_user_id', ...].forEach(k => localStorage.removeItem(k));
    return;
  }
  const user = await res.json();
  updateAuthButton(true, user.name, user.picture);
}
```

---

## Security considerations

### Yang AMAN:
- ✅ ID token verification via Google (aud + exp + email_verified)
- ✅ Session JWT signed dengan HMAC, secret di env var (not in repo)
- ✅ Client Secret TIDAK dipakai (ID token flow, frontend-only)
- ✅ Activity log truncated to 200 chars (no full content leak in log)
- ✅ Admin endpoints behind `x-admin-token` header

### Yang MASIH RISK (todo iterasi berikutnya):
- ⚠️ JWT di localStorage, bukan httpOnly cookie → XSS bisa exfiltrate token
  - Mitigation: tighter CSP, no third-party JS unless trusted
  - Long-term: migrate ke httpOnly cookie + CSRF token
- ⚠️ No rate limit di /auth/google → bisa di-spam (low impact karena Google
  rate limit sendiri di tokeninfo)
- ⚠️ JWT tidak revocable (stateless) → kalau secret leak, semua token valid
  - Mitigation: rotate `SIDIX_JWT_SECRET` invalidate semua session
- ⚠️ User bisa lihat ID/email user lain via `/admin/users` kalau token bocor
  - Mitigation: admin token rotation + IP allow-list (future)

### Setup env vars (production)
```bash
# /opt/sidix/.env
GOOGLE_OAUTH_CLIENT_ID=741499346289-xxx.apps.googleusercontent.com
SIDIX_JWT_SECRET=<64-char-hex-from-secrets.token_hex(32)>
```

**JANGAN commit** `.env` ke repo. Hanya `.env.sample` (skeleton).

---

## Test results (production smoke test)

```
✓ GET  /auth/config              → 200 {"google_client_id":"..."}
✓ POST /auth/google {invalid}    → 401 {"detail":"ID token tidak valid"}
✓ GET  /auth/me (no auth)        → 401 {"detail":"not authenticated"}
✓ GET  /auth/me (bad bearer)     → 401 {"detail":"not authenticated"}
✓ GET  /login.html               → 200 (7975 bytes, includes gsi/client script)
```

End-to-end flow testing pending user manual test (open app.sidixlab.com →
click Sign In → Google popup → verify callback + JWT issued + avatar shown).

---

## Next iterations

1. **Hook activity log ke /ask + /agent endpoints** — `extract_user_from_request()`
   sudah ready, tinggal call `log_activity()` di end of each handler.
2. **Admin tab** — User Database table + Activity Logs viewer di
   ctrl.sidixlab.com (sidebar menu baru).
3. **Tier upgrade flow** — admin bisa promote user dari `free` → `whitelist`
   via /admin/users PATCH.
4. **httpOnly cookie migration** — security hardening, replace localStorage.
5. **Multi-provider** (FB/IG/TikTok) — kalau perlu, follow same pattern
   (verify provider token → upsert user → issue SIDIX JWT).

---

## Lessons learned

1. **GIS lebih ringan dari Supabase Auth** — 1 module Python (~280 lines) +
   1 HTML page replace 3 file Supabase config + auth state mgmt.
2. **JSON store cukup untuk MVP** — premature optimization adalah evil.
   Migrate ke SQL kalau scale issue muncul, bukan sebelumnya.
3. **Tokeninfo endpoint > JWKS parse** — untuk SIDIX scale (low QPS), tokeninfo
   simpler dan reliable. Bisa migrate ke offline verify nanti.
4. **Activity log = corpus learning** — every conversation adalah training data
   untuk LoRA retrain. Database user bukan asset HR, tapi asset model growth.
5. **JANGAN paste Client Secret di chat** — user paste secret, kita warn
   rotation. ID token flow tidak butuh secret, ini lesson UX (button label
   harusnya hide secret atau clearly mark "OPTIONAL — only for server flows").

---

## Referensi

- [Google Codelabs — Sign In With Google Button](https://codelabs.developers.google.com/codelabs/sign-in-with-google-button)
- [GIS Library docs](https://developers.google.com/identity/gsi/web/guides/overview)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- SIDIX file: `apps/brain_qa/brain_qa/auth_google.py` (full module)
- SIDIX file: `SIDIX_USER_UI/public/login.html` (dedicated login page)
- Commit: `27cda76` — FEAT: Own auth via Google Identity Services
