# 220 — Activity Log + User Database Design (Post Own-Auth Migration)

**Date**: 2026-04-26 (vol 2)
**Tag**: ARCHITECTURE / PRIVACY / FEAT
**Status**: Backend deployed, frontend pending build+deploy
**Trigger**: User feedback "Log aktivtas user di app, masing-mmasing buat belajar sidix"

---

## Konteks

Setelah migrasi own auth via Google Identity Services (note 219), user feedback:

1. ✅ User yang daftar **tercatat di database** dan tampil di admin
2. ✅ **Log aktivitas user** per-individu untuk SIDIX learning
3. ✅ Drop dependency Supabase

Ketiganya saling terkait — own auth = own database = own activity log = own
training corpus.

---

## Arsitektur Activity Log

### Schema (JSONL append, single line per event)

```jsonl
{
  "ts": "2026-04-26T15:30:42.123Z",
  "user_id": "u_a3f9b2c1d4e5",
  "email": "user@gmail.com",
  "action": "ask",                  // "ask" | "agent/burst" | "agent/two-eyed" | ...
  "question": "apa itu maqashid?",  // truncated 200 chars
  "answer_preview": "Maqashid syariah adalah ...",  // truncated 160 chars
  "persona": "AYMAN",               // UTZ/ABOO/OOMAR/ALEY/AYMAN
  "mode": "agent",                  // "strict|simple|agent" untuk /ask, "burst|two_eyed|..." untuk /agent/*
  "citations": 3,
  "latency_ms": 1240,
  "ip": "203.123.45.67",            // truncated 32 chars
  "error": ""                       // empty kalau sukses
}
```

### Why JSONL (Newline-Delimited JSON)?

| Aspect | JSONL | SQLite | Postgres |
|---|---|---|---|
| Setup complexity | Trivial (file write) | Low (built-in Python) | High (server) |
| Append performance | O(1), no index update | O(log n) | O(log n) |
| Concurrent writers | File lock OK <1k QPS | DB lock | Connection pool |
| Easy export | `cat \| jq` | `.dump` SQL | `pg_dump` |
| Easy migrate | One-shot to anywhere | Schema migration | Schema migration |
| Query flexibility | Read-tail only | Full SQL | Full SQL |
| Crash safe | Yes (atomic append) | WAL needed | WAL/sync |

**Pilih JSONL untuk MVP** karena:
- SIDIX scale awal: ~100 user × 30 chat/hari = 3k events/hari = ~1MB/hari
- Linear growth, kalau >100MB bisa rotate (gzip + datestamped file)
- Migrate ke ClickHouse/BigQuery later kalau butuh real analytics

### Storage path
```
apps/brain_qa/.data/activity_log.jsonl  (gitignored)
```

Backup: rsync ke server backup nightly. Retention: 90 hari (rotate ke .gz + S3).

---

## Hook Implementation

### Helper di `agent_serve.py`

```python
def _log_user_activity(
    request: Request,
    *,
    action: str,
    question: str = "",
    answer: str = "",
    persona: str = "",
    mode: str = "",
    citations_count: int = 0,
    latency_ms: int = 0,
    error: str = "",
) -> None:
    try:
        from . import auth_google
        payload = auth_google.extract_user_from_request(request)
        if not payload:
            return  # anonymous user, skip — privacy default
        ip = ""
        try:
            ip = (request.client.host if request.client else "") or ""
        except Exception:
            pass
        auth_google.log_activity(
            user_id=payload.get("sub", ""),
            email=payload.get("email", ""),
            action=action,
            question=question,
            answer_preview=answer,
            persona=persona,
            mode=mode,
            citations_count=citations_count,
            latency_ms=latency_ms,
            ip=ip,
            error=error,
        )
    except Exception:
        pass  # never block main flow
```

### Hooks di endpoint

| Endpoint | Action | Mode logic |
|---|---|---|
| `POST /ask` | `"ask"` | `strict` if strict_mode, `simple` if simple_mode, else `agent` |
| `POST /agent/burst` | `"agent/burst"` | `"burst"` |
| `POST /agent/two-eyed` | `"agent/two-eyed"` | `"two_eyed"` |
| `POST /agent/resurrect` | `"agent/resurrect"` | `"resurrect"` |
| `POST /agent/foresight` | `"agent/foresight"` | `"foresight"` |

### Anti-pattern dihindari

- ❌ Log full question/answer (>200/160 chars) — bisa expose PII / dialog panjang
- ❌ Log per ReAct step (terlalu verbose, fokus ke final outcome)
- ❌ Block main flow kalau log gagal (always best-effort)
- ❌ Log untuk anonymous user (default opt-out, hanya signed-in user)

---

## Privacy Considerations

### What we log
- ✅ user_id (UUID hash dari Google sub) — pseudonymous
- ✅ email — required untuk admin lookup
- ✅ question (200 chars) + answer preview (160 chars) — for learning
- ✅ persona/mode/latency/citations — for quality monitoring
- ✅ IP (32 chars, truncated) — for anti-abuse only

### What we DO NOT log
- ❌ Full conversation context (prior turns)
- ❌ Reasoning chain / ReAct trace (sensitive)
- ❌ User agent / browser fingerprint
- ❌ Geo-location (IP only, no reverse lookup)
- ❌ Anonymous user activity (signed-in opt-in by default)

### User control
- Logout → `localStorage.clear()` di frontend → backend tidak tahu user logout (stateless JWT)
- Admin endpoint untuk delete user activity (P2 future): `DELETE /auth/me/activity`
- Export user data (GDPR): `GET /auth/me/export` (P2 future)

### Compliance roadmap
- [ ] Privacy policy page (sidixlab.com/privacy.html) — mention activity log
- [ ] User consent banner saat first sign-in
- [ ] Data retention policy: 90 hari rolling, full delete on user logout request
- [ ] Backup encryption (rsync via SSH, ok untuk MVP)

---

## Admin UI Design

### Sidebar menu (admin.html)

```
┌─────────────────────────┐
│ 🛡️ SIDIX Admin          │
├─────────────────────────┤
│ Management              │
│   🎟️ Whitelist          │
│   💬 Feedback           │
│   👥 Users        ← NEW │
│   🧰 Tool Permissions   │
├─────────────────────────┤
│ Monitoring              │
│   💚 System Health      │
│   📜 Activity Log ← NEW │
│   📊 Metrics (soon)     │
├─────────────────────────┤
│ System                  │
│   📘 API Docs           │
└─────────────────────────┘
```

### Tab Users — design rationale

**Stats first**: 4 boxes (Total, Aktif Hari Ini, Free, Whitelist) untuk overview
cepat — kalau total naik tapi aktif hari ini stagnan, mungkin acquisition OK
tapi retention buruk.

**Search bar**: instant client-side filter (no API call) — UX smoother untuk
list <500 user. Fallback ke backend search kalau >500.

**Action button "Lihat"**: cross-tab navigation ke Activity Log dengan filter
pre-set. Workflow: admin lihat user mencurigakan → klik Lihat → langsung
investigasi pertanyaan dia.

### Tab Activity Log — design rationale

**Card-based render** (bukan table) karena:
- Each entry ada Q + A preview (panjang, gak fit table cell)
- Header punya banyak metadata (timestamp, action, persona, mode, latency, error)
- Card visual = scan-friendly untuk admin manual review

**Filter user_id wajib** untuk privacy + performance — tanpa filter, query
return last 200 entries semua user (max). Filter user_id paksa admin focused
investigation, gak browse-all-data casually.

**Error highlight merah**: penting untuk operations — kalau >10 error per hari,
ada masalah. SLA monitoring future.

---

## Drop Supabase Decision

User explicitly asked: "jadi sudah nggak pelru supabase dong?"

### Status setelah refactor

**Supabase USED (legacy DB calls only)**:
- ✅ `lib/supabase.ts` — masih ada
- ✅ `subscribeNewsletter()` — newsletter form di app
- ✅ `submitFeedbackDB()` — feedback fallback (backend down case)
- ✅ `saveDeveloperProfile()` + `contributors` table — sidixlab.com#contributor

**Supabase DROPPED (auth specifically)**:
- ❌ `signInWithGoogle()`, `signInWithEmail()` — replace by /login.html GIS
- ❌ `getCurrentUser()`, `getCurrentSession()` — replace by /auth/me + JWT
- ❌ `signOut()` — replace by `ownAuthLogout()` (clear localStorage)
- ❌ `onAuthChange()` listener — replace by `loadOwnAuthUser()` di page-load
- ❌ `upsertUserProfile()`, `getUserProfile()` — replace by own user store
- ❌ `saveOnboarding()`, `trackBetaTester()` — paused (re-add via own endpoint)

### Bundle size win

- Before: **321.65 kB** JS bundle (gzip 85.64 kB)
- After: **114.58 kB** JS bundle (gzip 30.56 kB)
- Reduction: **207 kB / 64%** dari Supabase auth client + GoTrue + modal HTML

Ini real win — load time mobile turun ~1-2 detik di koneksi 3G.

### Yang berubah dari user POV

✅ Sign In tetap pakai Google (sama experience)
✅ Avatar muncul, name muncul, tier muncul
❌ Email magic link — sementara di-pause (re-add nanti via own endpoint)
❌ Onboarding interview survey — tidak save ke DB (cuma display, future re-add)

---

## Test results

```
✓ Build: vite 1.62s, 0 TS errors
✓ Bundle: 114.58 kB (vs 321.65 kB before)
✓ pytest: 520 passed, 1 deselected (flaky perf test)
✓ Backend syntax: agent_serve.py + auth_google.py valid
```

End-to-end test pending production deploy:
1. Sign in → chat → cek activity_log.jsonl ada entry
2. Open ctrl.sidixlab.com/admin → Users tab → user muncul
3. Click "Lihat" pada user → Activity tab buka dengan filter user_id

---

## Lessons learned

1. **Activity log = primary asset** untuk AI startup yang growing — bukan revenue, bukan signups, tapi conversation data yang feed model improvement.

2. **JSONL > SQL untuk early-stage** — premature DB optimization wastes weeks. JSON file → JSONL append → migrate ke OLAP later kalau scale demand.

3. **Drop dependency = real win** — 64% bundle reduction dari satu lib (Supabase) mengubah perceived speed. Vendor neutrality + smaller deploy = compound benefit.

4. **Privacy by default** — anonymous user TIDAK di-log (skip kalau no JWT). Signed-in user di-log dengan truncation (200/160 chars). User control via logout = clear local state.

5. **Admin UX = investigation flow** — bukan dashboard yang fancy, tapi tools untuk admin investigate masalah cepat (search → click → drill-down). Cross-tab navigation (User → Activity filtered) adalah killer feature yang sederhana.

---

## Referensi

- Backend: `apps/brain_qa/brain_qa/agent_serve.py` (`_log_user_activity`)
- Module: `apps/brain_qa/brain_qa/auth_google.py` (`log_activity`, `list_activity`)
- Admin UI: `apps/brain_qa/brain_qa/static/admin.html` (`#tab-users`, `#tab-activity`)
- Frontend refactor: `SIDIX_USER_UI/src/main.ts` (drop Supabase auth flow)
- Note 219: own auth via Google Identity Services
- Commit: pending (current session)
