# 78 — Threads Admin Integration di SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18
**Scope:** Backend (FastAPI) + Frontend (Vite/TS admin panel)
**Related:** 60 (VPS deployment), 62 (API keys & env vars), `social_agent.py`

---

## Apa

Integrasi satu-klik untuk menghubungkan akun **Threads (Meta)** ke SIDIX dari
admin dashboard di `ctrl.sidixlab.com`. Setelah terhubung, admin bisa
men-trigger generate + post konten otomatis dengan persona MIGHAN/INAN tanpa
perlu SSH ke VPS atau mengedit `.env` secara manual.

Deliverable:

- **Backend** — 4 endpoint baru:
  - `POST /admin/threads/connect` — validasi token ke `graph.threads.net/me`, simpan ke `.env`
  - `GET  /admin/threads/status` — status koneksi, username, posts hari ini
  - `POST /admin/threads/disconnect` — hapus kredensial dari `.env`
  - `POST /admin/threads/auto-content` — generate via Ollama + publish ke Threads
- **Frontend** — tab baru "Threads" di settings admin dengan form token,
  status badge, dan tombol "Generate & Post Sekarang".
- **Auto-content generator** — pilih topik dari research notes terbaru,
  generate lewat Ollama + persona voice, fallback ke template statis.

## Kenapa

1. **Mengurangi friction operasional.** Sebelum ini, setiap rotasi token
   Threads mengharuskan edit file `.env` manual di VPS. Sekarang admin cukup
   paste token di browser.
2. **Pisahkan concern admin dari autonomous learning.** `social_agent.py`
   sudah menangani belajar dari Reddit/Threads replies. Admin endpoint
   dipisah ke `admin_threads.py` supaya:
   - Rate limit admin (3/hari manual) tidak tabrakan dengan rate limit social agent.
   - Logging posts admin (`.data/threads/posts_log.jsonl`) terpisah dari
     `.data/social_agent/post_log.jsonl`.
3. **Validasi dini.** Token divalidasi lewat call `/me` sebelum disimpan,
   jadi kesalahan (token salah, user_id mismatch, token expired) ketangkap
   di tombol "Connect" bukan saat posting gagal.

## Bagaimana

### 1. Backend — file baru

```
apps/brain_qa/brain_qa/
├── admin_threads.py       # Router FastAPI + .env manipulator + posts log
└── threads_autopost.py    # Topic picker + Ollama generator + Threads publisher
```

**`.env` writer** (`admin_threads._write_env_updates`) preserve urutan &
komentar: scan line-by-line, update key yang match, append yang baru.
`None` berarti hapus. Refresh `os.environ` supaya proses berjalan langsung
pakai nilai baru tanpa restart.

**Token validation** (`_validate_token`): `GET /me?fields=id,username` dengan
`access_token`. Cek `id` sama dengan `user_id` yang dikirim. Kalau tidak,
reject.

**Post pipeline** (2-step Threads API):
1. `POST /{user_id}/threads` — buat media container dengan `media_type=TEXT`.
2. `POST /{user_id}/threads_publish` dengan `creation_id` dari step 1.

**Router didaftarkan** di `agent_serve.py` via `app.include_router(build_router())`
dengan try/except supaya gagal load admin_threads tidak bikin seluruh serve crash.

### 2. Generator konten (`threads_autopost.py`)

- **Topic picker**: ambil 15 research note terbaru (by `mtime`), random pick,
  extract H1 atau fallback ke nama file. Menjamin konten segar mengikuti
  fokus corpus terkini.
- **Persona voice**: system prompt berbeda untuk MIGHAN (reflektif) vs INAN
  (ringkas). User prompt memberi aturan: 200-400 char, 1-2 hashtag, max 1
  emoji, tanpa pembuka "Berikut post:".
- **Fallback**: jika Ollama tidak tersedia, pakai 3 template statis per
  persona. Admin tetap bisa posting meski LLM lokal sedang maintenance.
- **Rate limit**: dicek di layer `admin_threads.auto_content()` sebelum
  generate — hemat GPU call ketika sudah capai limit.

### 3. Frontend — tab Threads

Tambahan ke `SIDIX_USER_UI/src/main.ts`:

- `getSettingsNavItems()` — tambah entry `threads`.
- `settingsTabs.threads` — HTML: status card + connect form + autopost panel.
- `initThreadsTab()` — dipanggil dari `switchSettingsTab`. Wiring:
  - `fetchThreadsStatus()` — polling sekali saat tab dibuka.
  - Connect button → `POST /admin/threads/connect`, bersihkan input token
    setelah sukses (jangan tinggalkan di DOM).
  - Disconnect button → confirm dialog + `POST /admin/threads/disconnect`.
  - Autopost button → `POST /admin/threads/auto-content`, tampilkan output
    (id + content) di `<pre>`.

## Contoh

**Connect flow dari browser:**

```
Admin → ctrl.sidixlab.com/settings → tab "Threads"
→ paste THREADS_ACCESS_TOKEN + THREADS_USER_ID
→ klik Connect
→ backend call graph.threads.net/v1.0/me?access_token=XXX
→ return {username: "sidix_ai", id: "17841412..."}
→ .env diupdate (atomik, preserve komentar)
→ UI refresh status: "Connected — @sidix_ai — posts_today: 0"
```

**Autopost flow:**

```
Admin → klik "Generate & Post Sekarang" (persona=MIGHAN, topic_seed kosong)
→ pick_topic_seed() → baca research_notes/77_sidix_kapabilitas_lengkap_april_2026.md
→ Ollama generate (qwen2.5) dengan persona MIGHAN
→ output: "Kapabilitas SIDIX April 2026 — yang paling sering terlewat bukan
  fiturnya, tapi bahwa ia dibentuk dari sanad nyata, bukan model generic.
  Kamu pernah coba tanya hal yang sifatnya filosofis? #SIDIX #BelajarBareng"
→ POST container + publish → id=17895123...
→ log ke .data/threads/posts_log.jsonl
→ UI tampilkan preview + id
```

## Keterbatasan

1. **Single account.** Schema `.env` hanya mendukung 1 akun Threads. Kalau
   nanti butuh multi-akun (mis. `@sidix_id` + `@sidix_en`), perlu migrasi
   ke DB (Supabase) dengan table `social_accounts`.
2. **Token expiry tidak dimonitor otomatis.** Long-lived token Threads berumur
   ~60 hari. Belum ada cron yang refresh atau alert ke admin. TODO: tambah
   check `expires_in` di `/status` + reminder email 7 hari sebelum expired.
3. **Rate limit per-hari di-file, bukan DB.** Kalau `.data/threads/` hilang
   (mis. rebuild container tanpa volume), counter reset. Untuk
   production-grade perlu simpan di Postgres/Redis.
4. **Tidak ada preview sebelum post.** `dry_run=true` tersedia di body API
   tapi belum ada tombol "Preview Only" di UI. Saat ini tombol langsung
   post — konsekuensi rate limit 3/hari cukup sebagai safety net.
5. **Generator topic-agnostic soal bahasa.** Fallback template selalu
   Bahasa Indonesia; kalau akun Threads target audiens Inggris, perlu
   extend `_PERSONA_VOICES` + `_FALLBACK_TEMPLATES_*`.
6. **Belum terhubung ke feedback loop.** Post yang sukses belum ditrack
   engagement-nya (likes, replies, reach). Integrasi ke `ExperienceEngine`
   bisa dikerjakan di iterasi berikutnya — link ke social_agent's
   `learn_from_replies()`.

## Referensi

- Threads Graph API docs: https://developers.facebook.com/docs/threads
- File terkait: `apps/brain_qa/brain_qa/social_agent.py` (reuse pattern client)
- Research note 60 — VPS deployment SIDIX aaPanel
- Research note 62 — API keys & env vars security
