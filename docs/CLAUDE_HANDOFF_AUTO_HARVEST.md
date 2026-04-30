# Claude Code Handoff — Validasi Live + Sprint Auto-Harvest

> Diberikan oleh: Kimi Code CLI (partner sebelumnya)
> Tanggal: 2026-04-30
> Repo: https://github.com/fahmiwol/sidix
> Branch: `work/gallant-ellis-7cd14d`
> VPS: `72.62.125.6` (Ubuntu 22.04, 31GB RAM)

---

## Part 1: Validasi Live App (WAJIB sebelum lanjut sprint)

### 1.1 Backend Health Check

Jalankan di VPS (via Paramiko SSH):

```bash
# Health endpoint
curl -s http://localhost:8765/health | python3 -m json.tool

# Expected: model_ready: true, tools_available > 0
```

### 1.2 Endpoint `/agent/chat_holistic` Test

```bash
curl -s -X POST http://localhost:8765/agent/chat_holistic \
  -H "Content-Type: application/json" \
  -d '{"question":"siapa presiden indonesia 2024","persona":"UTZ"}' \
  --max-time 60 | python3 -m json.tool

# Expected: JSON dengan field answer, confidence, duration_ms
# Kalau return "Internal Server Error" atau "Not Found" → fix dulu
```

### 1.3 Frontend Integration Check

Cek apakah frontend `sidix-ui` (port 4000) memanggil endpoint yang benar:

```bash
# Cek file API call di frontend
grep -r "chat_holistic\|/agent/chat" /opt/sidix/SIDIX_USER_UI/src/ 2>/dev/null | head -10

# Kalau frontend masih pakai /agent/chat (bukan chat_holistic), update ke chat_holistic
```

### 1.4 Test via Nginx (Public Live)

```bash
# Test dari VPS ke public domain (via nginx)
curl -s -X POST https://app.sidixlab.com/agent/chat_holistic \
  -H "Content-Type: application/json" \
  -d '{"question":"test","persona":"UTZ"}' \
  --max-time 30 2>&1 | head -c 200

# Kalau nginx tidak proxy ke backend, perlu cek nginx config
```

### 1.5 Nginx Config Check (kalau public test gagal)

```bash
# Cek apakah nginx proxy ke backend port 8765
grep -r "8765\|chat_holistic" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null

# Kalau tidak ada, tambahkan location block:
# location /agent/chat_holistic {
#     proxy_pass http://127.0.0.1:8765/agent/chat_holistic;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
# }
```

### 1.6 Web Search Pipeline Check

```bash
cd /opt/sidix/apps/brain_qa
python3 -c "
import asyncio, logging
logging.basicConfig(level=logging.WARNING)
from brain_qa.mojeek_search import mojeek_search_async
hits = asyncio.run(mojeek_search_async('presiden indonesia 2024', max_results=3))
print(f'Hits: {len(hits)} (engine={hits[0].engine if hits else \"none\"})')
for h in hits:
    print(f'  {h.title[:60]} | {h.url[:60]}')
"

# Expected: 3+ hits, engine=duckduckgo (karena Mojeek 403 dari VPS)
```

### 1.7 Lite Browser Check

```bash
cd /opt/sidix/apps/brain_qa
python3 -c "
import asyncio
from brain_qa.lite_browser import fetch_url
result = asyncio.run(fetch_url('https://id.wikipedia.org/wiki/Presiden_Indonesia', timeout=15))
print(f'Success: {result.success}')
print(f'Title: {result.title}')
print(f'Text length: {len(result.text)}')
"

# Expected: success=True, title contains "Presiden", text length > 1000
```

---

## Part 2: Fix Checklist (kalau ada yang fail)

| Fail | Kemungkinan Cause | Fix |
|------|-------------------|-----|
| `/health` tidak respond | `sidix-brain` tidak jalan | `pm2 restart sidix-brain` |
| `chat_holistic` Not Found | File belum di-pull | `git pull origin work/gallant-ellis-7cd14d` |
| `chat_holistic` Internal Error | Import error / UnboundLocalError | Cek `pm2 logs`, fix file, restart |
| Web search 0 hits | DDG juga block | Cek log, mungkin butuh proxy rotation |
| Lite Browser fail | Chromium tidak terinstall | `playwright install chromium` |
| Nginx 404 | Location block tidak ada | Tambah nginx config, `nginx -s reload` |

---

## Part 3: Sprint Auto-Harvest Cron

### Goal
Setiap 6 jam, cron job otomatis:
1. Ambil trending topics (Google Trends RSS / news API)
2. Search via DDG → fetch page via Lite Browser → extract clean text via trafilatura
3. Generate markdown note dengan YAML frontmatter
4. Save ke `brain/public/omnyx_knowledge/YYYY-MM-DD/`
5. Auto-reindex BM25 (atau tandai untuk nightly reindex)

### Files to Create/Modify

1. `apps/brain_qa/brain_qa/auto_harvest.py` — main harvest pipeline
2. `apps/brain_qa/scripts/harvest_cron.py` — CLI entry point
3. `apps/brain_qa/crontab.example` — cron schedule
4. `docs/LIVING_LOG.md` — log progress

### Spec Detail

```python
# auto_harvest.py
class AutoHarvest:
    async def run(self, topics: list[str] = None):
        # 1. Get trending topics (default: Google Trends RSS for Indonesia)
        topics = topics or await self._fetch_trending_topics()
        
        # 2. For each topic: DDG search → top-3 URLs
        for topic in topics[:5]:
            hits = await mojeek_search_async(topic, max_results=3)
            urls = [h.url for h in hits if h.url]
            
            # 3. Lite Browser fetch each URL
            fetches = await fetch_urls(urls, max_concurrent=2)
            
            # 4. Generate markdown note
            for f in fetches:
                if f.success and len(f.text) > 500:
                    note = self._generate_note(topic, f)
                    self._save_note(note)
        
        # 5. Reindex BM25 if new notes added
        if new_notes_count > 0:
            await self._reindex_corpus()
```

### Acceptance Criteria
- [ ] Cron job jalan setiap 6 jam tanpa error
- [ ] Setiap run menghasilkan ≥3 notes baru
- [ ] Notes punya YAML frontmatter (title, date, source, tags)
- [ ] BM25 reindex berhasil setelah harvest
- [ ] Knowledge Accumulator menyimpan ke persona corpus juga

---

## Part 4: SSH Access (Paramiko)

Gunakan SSH key yang sama dengan sebelumnya:

```python
import paramiko
key = paramiko.Ed25519Key.from_private_key_file(
    r"C:\Users\ASUS\.ssh\id_ed25519",
    password="gY2UkMePh,Zvt6)6"
)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("72.62.125.6", username="root", pkey=key, timeout=30)
```

---

## Contact & Context

- **North Star:** SIDIX = self-hosted AI, no vendor LLM API for inference
- **Anti-hallucination:** Corpus passthrough primary defense
- **Knowledge flywheel:** Auto-harvest → corpus growth → more passthrough → faster answers
- **LIVING_LOG:** Append-only di `docs/LIVING_LOG.md` dengan tag `TEST:`, `FIX:`, `IMPL:`, `DECISION:`
