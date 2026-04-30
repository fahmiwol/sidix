# 149. Threads Autopost — Diagnosis Fix + Content Designer Multi-Tipe

> **Domain**: marketing / outreach / threads
> **Status validasi**: `[FACT]` (3 post real terverifikasi live di Threads)
> **Tanggal**: 2026-04-19

---

## Mukadimah

Mandate user: cek kenapa threads autopost belum jalan, bikin design skill
konten + autopost untuk cari user beta + harvest data + ajak kontributor.
Mumpung API Threads gratis.

---

## Diagnosis

### Pre-existing
| Komponen | Status |
|----------|--------|
| Token Threads OAuth | ✅ Valid (`/opt/sidix/.data/threads_token.json`) |
| Endpoint `/threads/scheduler/run` | ✅ Working (dry_run sukses) |
| Endpoint `/admin/threads/auto-content` | ✅ Working |
| Endpoint baru `/sidix/threads-queue/consume` | ✅ Working (sprint 5) |
| Cron entry | ✅ Ada (`0 1 * * *` post) |
| Script `threads_daily.sh` | ❌ **BROKEN** — escape chars rusak |
| Posts log | ❌ Belum ada (cron tidak pernah jalan benar) |
| Growth queue dari `daily_growth` | ✅ 5 post pending tapi tidak ter-consume |

### Root Cause
File `/opt/sidix/scripts/threads_daily.sh` sebelumnya:
```bash
case \ in              # ← seharusnya: case "$1" in
  post)
    curl -s -X POST " \/threads/scheduler/run\ \   # ← URL broken
      -d '{\dry_run\:false}' ...                   # ← JSON broken
```

Editor Windows kemungkinan ganti escape karakter saat save. Result:
syntax error → cron jalan tapi exit code != 0 → log kosong → tidak ada
post yang masuk Threads.

---

## Fix yang Dilakukan

### 1. Rewrite `scripts/threads_daily.sh` (clean)
8 sub-command:
- `post` — daily scheduler (auto-generate konten)
- `harvest` — mining mention/reply
- `mentions` — process new mentions
- `consume-queue` — **BARU**: pick up dari growth_queue.jsonl
- `series-hook` — series post pagi
- `series-detail` — series post siang
- `series-cta` — series post sore
- `status` — print queue + scheduler stats

### 2. Cron Schedule Baru (9 entries)
```
# 3 Series posts/hari (peak engagement Indonesia)
0 8  * * * series-hook
0 13 * * * series-detail
0 19 * * * series-cta

# 3 Consume queue/hari (post dari curriculum/content_designer)
30 11 * * * consume-queue
30 17 * * * consume-queue
30 21 * * * consume-queue

# Engagement & data mining
0 */4 * * * mentions
30 */6 * * * harvest

# Daily growth (existing)
0 3 * * * /sidix/grow?top_n_gaps=3
```

**Total post per hari**: 3 series + 3 queue × 2 posts = ~9 post/hari (jauh di
bawah Threads rate limit 250/hari untuk akun gratis).

### 3. Build `content_designer.py` — 8 Tipe Konten

| Tipe | Tujuan | Variasi/Week |
|------|--------|--------------|
| `hook` | Engagement (pertanyaan provokatif) | 4 |
| `education` | Value (insight teknis dari corpus) | — (on-demand) |
| `case_study` | Proof (penerapan nyata) | — (on-demand) |
| `behind_scene` | Build-in-public, transparency | 3 |
| `invitation` | Acquisition (ajak coba SIDIX/kontributor) | 3 |
| `question` | Data mining (harvest opinion) | 4 |
| `quote` | Identitas (filosofi IHOS/SIDIX) | 2 |
| `announcement` | FOMO (fitur baru, milestone) | 2 |

`fill_queue_for_week()` generate 18-21 post sekaligus → append ke queue.

### 4. Endpoint Baru `/sidix/content/*`
- `POST /sidix/content/fill-week` — generate batch 1 minggu
- `GET /sidix/content/queue-distribution` — stats by type/status
- `POST /sidix/content/design-quote` — single quote
- `POST /sidix/content/design-invitation?variant=` — single invitation

---

## Verifikasi LIVE (Production)

### Test #1 — Real Post via Scheduler
```
POST /threads/scheduler/run {"dry_run":false}
→ post_id: 18097823213014190
→ permalink: https://www.threads.net/@sidixlab/post/18097823213014190
✅ Token valid, scheduler engine works
```

### Test #2 — Real Post via Consume Queue
```
bash /opt/sidix/scripts/threads_daily.sh consume-queue
→ executed: 2 posts
→ thread_id: 17959487556076518 + 17849949888676738
→ Queue: 5 → 2 published, 3 queued
✅ Growth queue consumer works
```

### Test #3 — Fill Queue Week
```
POST /sidix/content/fill-week
→ appended: 18 posts
  - question: 4
  - hook: 4
  - invitation: 3
  - behind_scene: 3
  - quote: 2
  - announcement: 2
✅ Variasi konten ter-generate
```

### Status Queue Final
- Total: 23 post
- Published: 2
- Queued: 21
- Stock: ~3.5 hari pada rate 6 post/hari

---

## Strategi Beta Acquisition + Harvest (Compound)

Cron ini mengakselerasi 3 funnel sekaligus:

### Funnel 1: User Acquisition
- 3 invitation post/week → drive ke `app.sidixlab.com`
- 3 series post/hari (8/13/19 jam) — peak Indonesia engagement
- Total: ~30 acquisition touchpoint/week

### Funnel 2: Contributor Acquisition
- 1 invitation specific contributor/week
- Behind-scene posts (3/week) → builder narrative → atrak dev/researcher
- Quote posts (2/week) → showcase identitas + filosofi unik

### Funnel 3: Data Harvest
- 4 question posts/week → harvest opinion komunitas
- `harvest` cron (4×/day) → mining mention + reply baru
- Setiap mention/reply → potential research note draft

### Compound Effect
```
Daily (auto):
  3 series post + 6 consume post + harvest 4× + mentions 6×
       ↓
  Weekly: ~63 post + ~28 harvest cycle
       ↓
  Monthly: ~270 post outreach + harvest data
       ↓
  Quarterly: ~810 post = sustained brand awareness Threads ID
```

---

## Compliance dengan SIDIX_BIBLE

- Pasal "Mandiri": growth_queue diisi via `daily_growth` (curriculum lesson) +
  `content_designer` (tidak butuh manual writing per post)
- Pasal "Identity Shield": semua post pakai brand "Mighan Lab" / `@sidixlab`
- Pasal "Tumbuh": setiap question post = harvest data → masuk corpus
- Pasal "Catat": setiap post tersimpan di `posts_log.jsonl` + `audit_log`

---

## Keterbatasan Jujur

1. **Token Threads bisa expire**: 60 hari, perlu refresh manual via
   `/threads/auth` flow. Belum ada auto-refresh.
2. **Konten masih template-based**: belum LLM-generated kontekstual.
   Variasi terbatas pada template pool (8 tipe × 2-5 template each).
3. **Belum tracking conversion**: post → click → signup belum ter-correlate.
   TODO: UTM parameter di link + analytics_pipeline.
4. **Manual fill queue**: `/sidix/content/fill-week` perlu trigger manual
   tiap 3 hari. TODO: cron auto-fill kalau queue < 10.
5. **Belum multi-channel**: hanya Threads. TODO: integrasi X/LinkedIn.
6. **Series posts hardcoded**: dari `threads_series.py` existing, belum
   sync dengan note baru harian. TODO: dynamic series dari curriculum lesson.
7. **Quality gate konten**: belum ada filter spam/duplikasi sebelum post.

---

## Roadmap Lanjutan

- [ ] Auto-refresh Threads token (sebelum expire 60 hari)
- [ ] LLM-generated content (bukan template) untuk variasi tinggi
- [ ] UTM tracking + analytics conversion
- [ ] Auto-fill queue cron (kalau < 10, generate 21 lagi)
- [ ] Multi-channel: X/Twitter + LinkedIn integration
- [ ] Dynamic series dari curriculum lesson (sync daily)
- [ ] Quality gate konten (anti-duplikasi, spam filter)
- [ ] A/B test post type performance (engagement metric per type)
- [ ] Reply automation untuk mention (positive engagement)
- [ ] Hashtag optimizer (trending tag Indonesia)

---

## Sumber

- `apps/brain_qa/brain_qa/threads_*.py` (existing, sudah lengkap)
- `apps/brain_qa/brain_qa/content_designer.py` (BARU, ~290 baris)
- `scripts/threads_daily.sh` (rewrite clean)
- `scripts/install_threads_cron.sh` (BARU, install 9 cron)
- `apps/brain_qa/scripts/check_threads_status.sh` + `check_threads_auth.sh`
  (diagnostic tools)
- Commit: `0d39682`

## Status Final

| Metric | Value |
|--------|-------|
| Token Threads | ✅ Valid |
| Cron entries | 9 (vs 4 sebelumnya) |
| Post types tersedia | 8 |
| Queue stock | 21 post (~3.5 hari) |
| Real posts terverifikasi | 3 (1 series + 2 consume) |
| Auto-post per hari | ~6-9 |
| Estimated Quarterly post | ~540-810 |
