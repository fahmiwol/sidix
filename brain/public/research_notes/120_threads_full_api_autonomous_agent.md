# 120 — Threads Full API Integration: SIDIX sebagai Autonomous Social Agent

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Sumber:** Meta Threads Graph API v1.0 Docs + implementasi SIDIX  
**Relevansi SIDIX:** Social presence, learning harvest, community building, brand awareness

---

## Apa

SIDIX kini menggunakan **semua permissions Threads API** yang tersedia untuk:
1. **Auto-posting** konten harian (bilingual ID+EN)
2. **Harvesting** diskusi komunitas untuk learning data
3. **Monitoring** mentions @sidixlab
4. **Insights** analytics per-post dan account-level
5. **Search** keyword & hashtag discovery

---

## Semua Permissions yang Digunakan

| Permission | Fungsi | Endpoint SIDIX |
|-----------|--------|----------------|
| `threads_basic` | Read posts, profil | `GET /threads/profile`, `/threads/recent` |
| `threads_content_publish` | Post & reply | `POST /threads/post`, `/threads/reply` |
| `threads_read_replies` | Baca replies ke post | `GET /threads/replies/{post_id}` |
| `threads_manage_replies` | Hide/unhide reply, auto-reply | `POST /threads/replies/{id}/hide` |
| `threads_manage_insights` | Metrics views/likes/reach | `GET /threads/insights`, `/threads/insights/{post_id}` |
| `threads_manage_mentions` | Monitor @sidixlab mentions | `GET /threads/mentions` |
| `threads_keyword_search` | Search teks + hashtag | `GET /threads/search?q=`, `/threads/hashtag/{tag}` |
| `threads_profile_discovery` | Discover profil | `GET /threads/profile` |

---

## Arsitektur: SIDIX Threads Autonomous Agent

```
threads_scheduler.py          — Orchestrator harian
   ├── run_daily_post()       — 1x/hari, rotasi bilingual
   ├── run_harvest_cycle()    — 4x/hari, keyword search → corpus
   ├── run_mention_monitor()  — 3x/hari, cek @mention
   └── run_daily_cycle()      — semua sekaligus

threads_oauth.py              — Semua API calls
   ├── create_text_post()     — publish post atau reply
   ├── get_account_insights() — account-level metrics
   ├── get_post_insights()    — per-post metrics
   ├── get_mentions()         — monitor mentions
   ├── keyword_search()       — search teks
   ├── hashtag_search()       — search #hashtag
   ├── discover_trending()    — multi-keyword discovery
   ├── harvest_for_learning() — scrape + save ke corpus
   └── generate_daily_post()  — bilingual content generator

agent_serve.py                — API endpoints
   ├── GET  /threads/status
   ├── GET  /threads/token-alert
   ├── GET  /threads/profile
   ├── GET  /threads/recent
   ├── GET  /threads/mentions
   ├── GET  /threads/insights
   ├── GET  /threads/insights/{post_id}
   ├── GET  /threads/replies/{post_id}
   ├── GET  /threads/search?q=
   ├── GET  /threads/hashtag/{tag}
   ├── GET  /threads/discover
   ├── POST /threads/post
   ├── POST /threads/reply
   ├── POST /threads/replies/{id}/hide
   ├── POST /threads/harvest-learning
   ├── GET  /threads/scheduler/stats
   ├── POST /threads/scheduler/run
   ├── POST /threads/scheduler/post-now
   ├── POST /threads/scheduler/config
   ├── POST /threads/scheduler/harvest
   └── POST /threads/scheduler/mentions
```

---

## Content Strategy: Bilingual, Autentik, Mengundang

### Template Categories (12 total)
- **6 Indonesia** (template index genap): untuk komunitas lokal
- **6 English** (template index ganjil): untuk target internasional

### Mandatory Keywords (setiap post)
- `#FreeAIAgent` — gratis, tidak perlu langganan
- `#AIOpenSource` — open source sepenuhnya
- `#FreeAIGenerative` — generative AI tanpa API cost
- `#LearningAI` — terus belajar, tumbuh bersama
- `#AIIndonesia` / `#OpenSourceAI` — identitas komunitas
- `@sidixlab` — always mentioned, selalu ada CTA follow
- `sidixlab.com` — link wajib di setiap post

### Call-to-Action Pattern
Setiap post menyertakan minimal satu dari:
- "Follow @sidixlab untuk update harian!"
- "Follow @sidixlab for daily AI insights!"
- "Bergabung? sidixlab.com"
- "Try it free: sidixlab.com"

---

## Token Expiry Alert System

Token Threads berlaku 60 hari. SIDIX memantau dan alert:

```python
# di get_token_info():
if remaining_days < 7:  alert = "warning"  # ⚠️ kuning
if has_expired:         alert = "expired"  # ❌ merah

# di /health endpoint:
"threads_alert": "⚠️ Token Threads akan expire dalam 5 hari. Segera reconnect!"
```

Cara reconnect: `GET /threads/auth` → redirect ke Meta OAuth → token baru 60 hari.

---

## Jadwal Aman (Rate Limit Safe)

```
Jam 08:00 WIB (01:00 UTC) — run_daily_post()
Jam 09:00 WIB (02:00 UTC) — run_harvest_cycle() [pertama]
Jam 15:00 WIB (08:00 UTC) — run_harvest_cycle() [kedua]
Jam 18:00 WIB (11:00 UTC) — run_mention_monitor()
Jam 21:00 WIB (14:00 UTC) — run_harvest_cycle() [ketiga]
```

Total API calls per hari: ~40-60 (jauh di bawah limit Meta: 200/jam per user).

---

## Learning Pipeline dari Threads

```
Threads keyword search
    ↓ harvest_for_learning()
    ↓ .data/threads_harvest/threads_harvest_YYYYMMDD.jsonl
    ↓ [manual review]
    ↓ brain/public/research_notes/ atau training data
    ↓ SIDIX corpus → better answers
```

Data yang dikumpulkan: teks post, username, timestamp, permalink.  
Data yang **tidak** dikumpulkan: private profile, messages, password.

---

## Keterbatasan

1. **Image generation**: Belum tersedia — SIDIX belum punya image gen capability
2. **Auto-reply**: Default `dry_run=True` — harus diaktifkan manual
3. **Rate limit**: Threads Graph API masih dalam "Development Mode" → hanya token yang terdaftar sebagai Tester bisa dipakai
4. **Redirect Callback URL**: Masih belum bisa disave di Meta dashboard (bug Meta UI) — OAuth manual untuk sekarang
5. **threads_share_to_instagram**: Belum diimplementasi (butuh setup IG Business)

---

## Contoh Output Post (bilingual)

**Indonesia:**
```
⚡ Update SIDIX:

Cara kerja RAG (Retrieval-Augmented Generation) dalam konteks bahasa Indonesia

Visi kami: AI yang memahami konteks Indonesia & Islam — bukan sekadar asisten generik.

Gratis dipakai. Open source sepenuhnya.
Follow untuk terus update 👉 @sidixlab
🔗 sidixlab.com

#FreeAIAgent #AIOpenSource #AIIndonesia
```

**English:**
```
🔬 How SIDIX works:

How we built a free AI agent without using any cloud AI APIs

ReAct agent loop → BM25 RAG → local Qwen2.5 inference → Islamic epistemology filter
Zero third-party AI APIs. Your data stays on our servers.

Free open-source AI agent for Indonesian & global communities.
🔗 sidixlab.com | Follow @sidixlab

#FreeAIAgent #AIOpenSource #OpenSourceAI #LearningAI
```

---

## Referensi

- Meta Threads Graph API: https://developers.facebook.com/docs/threads
- Token file: `/opt/sidix/apps/.data/threads_token.json`
- Scheduler state: `/opt/sidix/apps/.data/threads_scheduler_state.json`
- Code: `apps/brain_qa/brain_qa/threads_oauth.py`, `threads_scheduler.py`
