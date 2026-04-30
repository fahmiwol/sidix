# HANDOFF — SIDIX — 2026-04-19 (Social Media + LearnAgent Sprint)

Tujuan file ini: Lanjutan sesi AI tanpa kehilangan konteks.
Baca ini dulu sebelum mulai kerja.

---

## 🎯 CURRENT FOCUS (1 baris)

Social media marketing multi-platform + LearnAgent autonomous (arXiv/Wikipedia/
MusicBrainz/GitHub/Quran) + 6 internal sub-agent architecture sudah SELESAI.
**Next**: Deploy ke server + wiring connector ke cron daily growth.

---

## 📍 STATUS

| Field | Value |
|-------|-------|
| **Project** | SIDIX / Mighan Model |
| **Phase** | Development — Growth & Autonomous Learning |
| **Blocker** | none kritis; connector belum ada di server (perlu git pull) |
| **Last action** | Buat research notes 151-153 + connectors package + learn_agent.py + 3 API endpoint |
| **Next action** | `git pull` di server → test endpoint `/learn/status` → wiring ke cron |

---

## 🧠 DECISIONS MADE (tidak boleh di-revisit)

- **LearnAgent** menggunakan `corpus_queue.jsonl` (file-based) bukan direct indexer call — hindari circular import
- **Connectors** tidak hardcode credential — semua via `os.getenv()`
- **Rate limit** per source: MIN_INTERVAL_SEC=3600 (1 jam minimum antar-fetch)
- **Sub-agent architecture** 6-layer: Learn, Promote, Develop, Monitor, Teach, Guard — fase implementasi bertahap (fase 1: connectors ✅)
- **Social media**: multi-platform tapi konten tetap via PromoteAgent (bukan manual) — "show don't tell"
- **Identity**: semua konten publik pakai `@sidixlab` / `Mighan Lab` — no owner name

---

## 📂 FILES IN PLAY

| File | Status | Note |
|------|--------|------|
| `brain/public/research_notes/151_social_media_marketing_strategy_sidix.md` | done | Strategy doc |
| `brain/public/research_notes/152_open_source_apis_learning_sources_sidix.md` | done | 50+ API sources |
| `brain/public/research_notes/153_sidix_internal_subagents_architecture.md` | done | 6 sub-agent arch |
| `apps/brain_qa/brain_qa/connectors/__init__.py` | done | Package export |
| `apps/brain_qa/brain_qa/connectors/arxiv_connector.py` | done | arXiv API |
| `apps/brain_qa/brain_qa/connectors/wikipedia_connector.py` | done | Wikipedia EN+ID |
| `apps/brain_qa/brain_qa/connectors/musicbrainz_connector.py` | done | Music metadata |
| `apps/brain_qa/brain_qa/connectors/github_connector.py` | done | GitHub trending |
| `apps/brain_qa/brain_qa/connectors/quran_connector.py` | done | Quran.com API v4 |
| `apps/brain_qa/brain_qa/learn_agent.py` | done | LearnAgent utama |
| `apps/brain_qa/brain_qa/agent_serve.py` | updated | +3 /learn/* endpoints |
| `docs/LIVING_LOG.md` | updated | Entry terbaru appended |

---

## 🔑 CONTEXT SNAPSHOT

### Environment
- Machine: Windows 11 / Mighan (lokal) + VPS Linux (production)
- Working dir: `D:\MIGHAN Model\determined-chaum-f21c81`
- Runtime: Python 3.x + FastAPI + Vite
- DB: Supabase (creds di `.env`)

### Credentials/Access
- `.env` di `apps/brain_qa/.env` (tidak di-commit)
- GITHUB_TOKEN: optional (di `.env` untuk rate limit upgrade 60→5000/hour)
- QURAN_API: tidak perlu token
- ARXIV_API: tidak perlu token
- MUSICBRAINZ_API: tidak perlu token (tapi wajib User-Agent header ✅ sudah ada)

### New Files Added
- 5 connector files (tidak perlu install package baru — semua pakai `urllib.request`)
- `learn_agent.py` — tidak ada dependency baru
- `connectors/` package — tidak ada dependency baru

---

## 🐛 KNOWN ISSUES

- `[LOW]` `corpus_queue.jsonl` belum ada proses auto-trigger indexer; perlu panggil manual `POST /learn/process_queue` atau wiring ke cron
- `[LOW]` `_next_note_number()` di learn_agent.py scan semua file di research_notes/ — OK untuk 200 file, tapi lambat kalau ribuan
- `[LOW]` `GitHubTrendingConnector` tidak ada endpoint trending resmi dari GitHub; pakai proxy (repos baru + sort star) — hasilnya agak berbeda dari github.com/trending
- `[INFO]` Connector belum ada: Spotify, Unsplash, Pexels, Papers With Code, NASA (jadwal fase 2)

---

## ✅ DONE THIS SESSION

- [x] Research note 151: Social Media Marketing Strategy (8 platform)
- [x] Research note 152: 50+ Open-source API learning sources
- [x] Research note 153: SIDIX Sub-Agent Architecture (6 agents + SAGL)
- [x] connectors/ package: ArxivConnector, WikipediaConnector, MusicBrainzConnector, GitHubTrendingConnector, QuranConnector
- [x] learn_agent.py: LearnAgent dengan state, dedup, corpus queue, auto note
- [x] agent_serve.py: +3 endpoint admin /learn/{status, run, process_queue}
- [x] LIVING_LOG.md: entry 2026-04-19 appended

---

## 🚀 NEXT SESSION CHECKLIST

1. **Deploy ke server**:
   ```bash
   cd /opt/sidix && git pull
   pm2 restart sidix-brain
   ```

2. **Test endpoint baru**:
   ```bash
   # Cek status
   curl -H "Authorization: Bearer $BRAIN_QA_ADMIN_TOKEN" https://ctrl.sidixlab.com/learn/status

   # Run fetch (arXiv 15 papers)
   curl -X POST -H "Authorization: Bearer $BRAIN_QA_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"domain":"arxiv","force":true}' \
     https://ctrl.sidixlab.com/learn/run

   # Process queue → reindex
   curl -X POST -H "Authorization: Bearer $BRAIN_QA_ADMIN_TOKEN" \
     https://ctrl.sidixlab.com/learn/process_queue
   ```

3. **Wire ke cron** (optional, append ke daily_growth cron atau buat baru):
   ```bash
   # Di /opt/sidix/scripts/threads_daily.sh atau crontab
   # Setiap hari jam 04:00 (setelah daily_growth jam 03:00)
   0 4 * * * curl -X POST -H "Authorization: Bearer $BRAIN_QA_ADMIN_TOKEN" \
     http://localhost:8765/learn/run -d '{"domain":"all"}' >> /var/log/sidix_learn.log 2>&1
   ```

4. **Tambah connector berikutnya** (fase 2, prioritas P2):
   - `connectors/papers_with_code_connector.py` (GET /api/v1/papers/)
   - `connectors/unsplash_connector.py` (GET /photos/random)
   - `connectors/spotify_connector.py` (GET /v1/audio-features, perlu Client Credentials flow)

5. **Social media**: Buat `connectors/twitter_connector.py` + `connectors/linkedin_connector.py` untuk multi-platform PromoteAgent.

---

## 💬 OPEN QUESTIONS

- [ ] Kapan wiring `LearnAgent.process_corpus_queue()` ke cron otomatis? (sekarang harus manual trigger)
- [ ] Apakah Spotify connector perlu SPOTIFY_CLIENT_ID di .env? (ya, perlu setup OAuth Client Credentials)
- [ ] Multiple platform Threads sudah ada, tapi Twitter/LinkedIn belum ada token — berapa cepat perlu diprioritaskan?
- [ ] `auto_learn/` folder di `brain/public/` akan tumbuh cepat — perlu cleanup policy (delete after N days atau archive)

---

## 🔗 RELATED DOCS

- Research notes: `brain/public/research_notes/151-153`
- Architecture: `brain/public/research_notes/153_sidix_internal_subagents_architecture.md`
- Learning sources: `brain/public/research_notes/152_open_source_apis_learning_sources_sidix.md`
- Existing social agent: `apps/brain_qa/brain_qa/social_agent.py`
- Existing threads: `apps/brain_qa/brain_qa/threads_autopost.py`, `admin_threads.py`
- LIVING_LOG: `docs/LIVING_LOG.md` (entry terbaru di bagian akhir)
- Previous handoff: `docs/HANDOFF-2026-04-17.md`

---

## 📝 NOTES UNTUK AI SESI BARU

**DO:**
- Baca docs/SIDIX_BIBLE.md + SIDIX_CHECKPOINT_2026-04-19.md dulu (anti-amnesia)
- Cek `apps/brain_qa/brain_qa/connectors/` sebelum buat connector baru (mungkin sudah ada)
- Connector baru harus: no hardcode credentials, polite rate limit, return `list[dict]` dengan field standar (`title`, `content`, `url`, `domain`, `license`)
- Semua endpoint baru di agent_serve.py → proteksi `_admin_ok(request)`
- Bahasa Indonesia di semua komunikasi user

**DON'T:**
- Jangan import `anthropic`, `openai`, `@google/genai` di inference pipeline
- Jangan expose IP server, token, atau nama owner di file/log manapun
- Jangan buat research note baru kalau topik overlap ≥0.55 dengan existing (update yang lama)
- Jangan skip LIVING_LOG update setelah setiap perubahan signifikan

**Quick audit sebelum commit:**
```bash
git diff --cached | grep -iE "fahmi|wolhuter|72\.62|password=|api_key=|secret=|gmail\.com"
```
