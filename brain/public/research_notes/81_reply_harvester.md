---
title: Reply Harvester — Auto-baca komentar Threads & Reddit jadi corpus + Q&A
number: 81
date: 2026-04-18
tags: [harvester, social, threads, reddit, rag, training-data, corpus]
status: implemented
---

# 81. Reply Harvester — Belajar Dari Komentar Publik

## Apa
`apps/brain_qa/brain_qa/reply_harvester.py` adalah modul untuk:

1. Mengambil **reply/komentar publik** pada post SIDIX di Threads & Reddit.
2. Menyaring kualitas (min 20 char, bukan pure-URL, bukan spam/ad/judi/bot).
3. Menyimpan tiap reply sebagai **markdown + frontmatter** ke `brain/public/sources/social_replies/{platform}_{id}.md` sehingga otomatis terindex BM25.
4. Mengkonversi reply jadi **Q&A pair format Alpaca** (`instruction/input/output`) untuk fine-tuning.
5. **Idempoten** — tidak pernah harvest ulang reply yang sama (tracked di `.data/harvest/replies_seen.json`).

## Mengapa
SIDIX perlu **belajar dari orang nyata**, bukan hanya corpus statis:
- Reply adalah data **dialogis** (ada pertanyaan → ada jawaban) → langsung pas untuk instruction tuning.
- Setiap reply publik adalah signal tentang gaya bahasa, kekhawatiran nyata, istilah lokal Indonesia yang tidak muncul di buku.
- Biaya nol (tidak panggil vendor API untuk fetch), karena Reddit `.json` endpoint dan Threads Graph API sudah cukup.
- Menutup **feedback loop Growth Manifesto (Note 42)**: Data → Information → Knowledge → Wisdom, dengan data baru masuk tiap kali SIDIX memposting.

## Bagaimana

### Arsitektur
```
post_log.jsonl (dari social_agent.py)
       │
       ▼
iter_posts_recent(hours=24)
       │
       ├── platform=="threads"  ──► fetch_threads_replies(post_id, token)
       │                              GET graph.threads.net/v1.0/{post_id}/replies
       │
       └── platform=="reddit"   ──► fetch_reddit_comments(post_url)
                                      GET {post_url}.json    (walk tree)
       │
       ▼
quality_filter(min_length=20, blacklist=[...])
       │
       ▼
┌── convert_reply_to_corpus(reply) ─► brain/public/sources/social_replies/{plat}_{id}.md
│
└── convert_to_qa_pair(reply, parent_post) ─► .data/harvest/training_pairs/reply_alpaca_YYYYMMDD.jsonl
       │
       ▼
_save_seen(new_seen)   .data/harvest/replies_seen.json
```

### API publik
```python
from brain_qa.reply_harvester import (
    fetch_threads_replies, fetch_reddit_comments,
    quality_filter, convert_reply_to_corpus,
    convert_to_qa_pair, harvest_all_recent, reply_stats,
)

# Manual single run
report = harvest_all_recent(
    hours=24,
    threads_token=os.getenv("THREADS_ACCESS_TOKEN", ""),
    extra_reddit_urls=["https://reddit.com/r/indonesia/comments/xxxx/abc/"],
)
print(report)

# Stats
print(reply_stats())
```

### HTTP Endpoint
Terdaftar di `apps/brain_qa/brain_qa/serve.py`:
- `POST /harvest/replies/run` — body `{hours, threads_token, extra_reddit_urls, min_length, write_qa}`
- `GET /harvest/replies/stats` — total, by_platform, qa_pairs, seen_ids

### Rate-limit & User-Agent
- `User-Agent: SIDIX-Harvester/1.0 (+https://sidixlab.com; belajar-dari-publik)`
- `time.sleep(1.0)` setelah request Threads (Graph API limit ~200 req/hour/user).
- `time.sleep(2.0)` setelah request Reddit (`.json` publik, aturan komunitas: 1 req/2s).
- Timeout 15 detik per request.

### Kualitas filter (default)
```python
DEFAULT_BLACKLIST = ["spam","buy now","click here","promo","iklan",
                     "judi","slot","bot reply","bit.ly","onlyfans","porn"]
```
- Panjang teks ≥ 20 char.
- Setelah strip URL, sisa teks ≥ 10 char (buang pure-URL).
- Case-insensitive substring match untuk blacklist.

### Idempotensi
`.data/harvest/replies_seen.json`:
```json
{"seen_ids": ["threads_123...", "reddit_t1abc..."], "updated_at": "..."}
```
Sebelum menulis ke corpus atau Q&A, cek `reply.id in seen`. ID diberi prefix platform.

## Contoh nyata

### Threads reply → corpus markdown
Input dari `GET graph.threads.net/v1.0/POSTID/replies`:
```json
{"data":[{"id":"999","text":"Menurut saya tabayyun itu bukan cuma cek fakta...",
          "username":"@fulan","timestamp":"2026-04-18T10:00:00Z",
          "permalink":"https://threads.net/..."}]}
```
Output `brain/public/sources/social_replies/threads_threads_999.md`:
```markdown
---
source: social_reply
platform: threads
reply_id: threads_999
post_id: POSTID
author: "@fulan"
created_at: 2026-04-18T10:00:00Z
score: 0
url: https://threads.net/...
harvested_at: 2026-04-18T...
tags: [social_reply, community, threads]
---

# Reply dari @@fulan (threads)

## Isi Reply
Menurut saya tabayyun itu bukan cuma cek fakta...
```

### Reddit comment → Q&A pair
`reply_alpaca_20260418.jsonl`:
```json
{"instruction":"Apa perbedaan belajar teknis vs memahami filosofi?",
 "input":"",
 "output":"Teknis itu know-how, filosofi itu know-why. Keduanya saling mengikat.",
 "source":"reddit","author":"mighty_redditor","score":12,
 "url":"https://reddit.com/r/.../abc/","reply_id":"reddit_t1_xyz","post_id":"abc",
 "harvested_at":"2026-04-18T..."}
```

## Cara trigger
1. **Manual HTTP**
   ```bash
   curl -X POST http://localhost:8765/harvest/replies/run \
        -H "Content-Type: application/json" \
        -d '{"hours":24,"threads_token":"<TOKEN>"}'
   ```
2. **Cron VPS** (`crontab -e` pada user yang jalankan backend):
   ```
   0 */6 * * * curl -s -X POST http://127.0.0.1:8765/harvest/replies/run \
                  -H "Content-Type: application/json" \
                  -d '{"hours":6,"threads_token":"'"$THREADS_TOKEN"'"}' \
                  >> /var/log/sidix/reply_harvest.log 2>&1
   ```
3. **Python** dari REPL:
   ```python
   from brain_qa.reply_harvester import harvest_all_recent
   harvest_all_recent(hours=48)
   ```

Setelah harvest: panggil `POST /corpus/reindex` agar markdown baru masuk ke BM25.

## Keterbatasan
- **Threads API** butuh access token user Meta (butuh app review untuk fitur tertentu). Tanpa token → skip otomatis.
- **Reddit .json** endpoint public cukup untuk subreddit terbuka, tapi:
  - Tree comment dibatasi default ~200 top replies (Reddit `limit` parameter belum diset; perlu tambahan untuk `more` children).
  - Beberapa subreddit NSFW/private tidak bisa diakses tanpa OAuth.
- **Tidak ada deduplikasi konten** (hanya dedupe by `reply_id`). Dua user menulis teks identik tetap tersimpan dua kali.
- **Quality filter sederhana**: substring match. Belum ada deteksi bahasa, sentiment, atau toxicity.
- **Q&A pair instruction** = text post asli SIDIX. Kalau post asli adalah pernyataan (bukan pertanyaan), hasil instruction tuning bisa kurang ideal. Mitigasi: kelak preprocess instruction via SIDIX sendiri.
- **Idempotensi global**: `replies_seen.json` bisa membengkak. Belum ada rotasi/arsip. Saat mendekati 1 juta entries, pertimbangkan SQLite.

## Ke depan
- Tambah fetcher YouTube comments (via YouTube Data API v3) dan Twitter/X (jika v2 API dapat).
- Auto-language detect → hanya ingest reply Bahasa Indonesia + Inggris.
- Integrasi dengan `curation.py` agar reply auto-tagged domain (islamic, coding, ai, dll).
- Scheduler built-in (APScheduler) daripada cron eksternal.
- Tambah harvest dari **quote-replies / stitches** Threads v2 ketika tersedia.

## File yang diubah/dibuat
- `apps/brain_qa/brain_qa/reply_harvester.py` — modul baru (~470 LOC).
- `apps/brain_qa/brain_qa/serve.py` — tambah endpoint `/harvest/replies/run` + `/harvest/replies/stats`.
- `brain/public/research_notes/81_reply_harvester.md` — dokumen ini.

## Terkait
- `harvest.py` (Note: existing) — harvest sesi Q&A internal SIDIX; reply_harvester adalah pelengkap untuk data eksternal.
- `social_agent.py` — modul posting & tracking post_id_remote; reply_harvester membaca output-nya.
- Note 42 Growth Manifesto, Note 69 feedback loop, Note 75 Kaggle QLoRA.
