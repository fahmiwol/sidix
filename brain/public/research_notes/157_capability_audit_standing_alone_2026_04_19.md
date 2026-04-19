# 157 — SIDIX Capability Audit & Standing-Alone Roadmap

Tanggal: 2026-04-19
Tag: [FACT] audit code + repo state; [DECISION] prioritas implementasi; [IMPL] web_fetch + code_sandbox

## Konteks

User frustrasi karena beberapa sesi muter-muter di UX fix, sementara hasil sprint
panjang (LearnAgent, connectors, dll.) belum terpakai di chat. User menegaskan
prinsip: **SIDIX harus standing alone — own modules, framework, tools sendiri,
bukan API orang.** Catatan ini mendokumentasikan state aktual SIDIX, gap, dan
implementasi awal untuk mengisi gap yang bisa diisi tanpa GPU.

## Audit ringkas

### Yang sudah aktif di backend (per audit 2026-04-19)
- Own inference stack: `local_llm.py` (Qwen2.5-7B base + LoRA adapter) + mock
  fallback. Setelah symlink adapter, `model_ready=true, models_loaded=3`.
- ReAct loop (`agent_react.py`) + persona routing (MIGHAN/TOARD/FACH/HAYFAR/INAN).
- Epistemic labels wajib, orchestration_digest per-answer, maqashid scoring.
- 13 tools lama di TOOL_REGISTRY (search_corpus, read_chunk, list_sources,
  calculator, search_web_wikipedia, orchestration_plan, workspace_*, roadmap_*).
- LearnAgent + 5 connectors (arXiv, Wikipedia, MusicBrainz, GitHub, Quran).
- Social agent penuh untuk Threads (40 endpoint).
- Daily growth loop 7-fase, curriculum engine, brain synthesizer, vision tracker.

### Yang SUDAH ADA kodenya tapi TIDAK wired ke chat
- `webfetch.py` — lengkap (httpx + BeautifulSoup → markdown). Tool `web_fetch`
  masih pointing ke `_tool_disabled` stub. → **diaktifkan di note ini.**
- `audio_capability.py` — registry TTS/ASR/voice-clone/music-gen. Butuh deps
  (whisper, librosa). Belum wired sebagai tool. → roadmap P2.
- `brain_synthesizer.py` — knowledge graph + CONCEPT_LEXICON (IHOS, Sanad,
  Maqasid, …). Belum exposed sebagai tool. → roadmap P2.

### Yang BELUM ADA
- Code execution sandbox → **diimplementasi di note ini.**
- Image generation (butuh GPU self-host SDXL/FLUX).
- Vision/multimodal input (butuh GPU self-host Qwen2.5-VL/InternVL).
- OCR/PDF analysis (tinggal tambah `pdfplumber`+`pytesseract`).
- Generic web search (ekstensi atas `web_fetch` pakai DuckDuckGo HTML).
- ASR/TTS self-host (Whisper/Piper, P2).

## Implementasi hari ini (P1, tanpa GPU, 100% own stack)

### 1. `web_fetch` tool — enabled
Lokasi: `apps/brain_qa/brain_qa/agent_tools.py`.

Pendekatan: `httpx.Client` (follow_redirects, timeout 20s, custom User-Agent
"SIDIX-Agent/1.0") → BeautifulSoup `html.parser` (tidak butuh `lxml` native).
Strip `script/style/noscript/nav/footer/aside`, ambil `soup.get_text`, normalisasi
whitespace, cap 6000 karakter default (max 20000). Output format:
`# {title}\nURL: {url}\n\n{body}`.

Citations diisi `{type: "web_fetch", url, title}` untuk dilacak di sanad chain.

**Kenapa standing alone?** Tidak pakai Google Search API, Bing API, atau scraper
SaaS. Hanya HTTP GET ke URL publik + parsing lokal. Sama prinsipnya dengan
browser membuka halaman.

### 2. `code_sandbox` tool — baru
Lokasi: `apps/brain_qa/brain_qa/agent_tools.py`.

Pendekatan: `subprocess.run([sys.executable, "-I", "-B", script_path])` di
`tempfile.TemporaryDirectory`. Flag `-I` = isolated mode (abaikan PYTHONPATH &
user site), `-B` = tidak tulis `.pyc`. Timeout 10s (TimeoutExpired → error
message). `env` dikurangi ke PATH + LANG saja. `input=""` agar stdin tertutup.
Output dicap 4000 karakter stdout + 2000 karakter stderr.

Pattern blacklist ringan: `os.system`, `subprocess.`, `socket.`,
`__import__('os')` — untuk mencegah penyalahgunaan sebagai RCE walaupun ini
sekarang open permission. Catatan: ini bukan sandbox penuh; untuk keamanan
produksi perlu `bubblewrap`/`firejail`/container isolated network.

**Kenapa standing alone?** Python subprocess di host SIDIX sendiri. Tidak ada
kode user dikirim ke cloud execution service (Judge0/Riza/e2b).

## Deploy

1. Commit `feat(agent-tools): enable web_fetch + add code_sandbox` (952a586).
2. `git pull` di VPS, `pm2 restart sidix-brain`.
3. Verifikasi: `GET /health` → `tools_available: 15` (sebelumnya 13).
4. Verifikasi tools terdaftar: `GET /agent/tools` → `web_fetch` + `code_sandbox`
   keduanya permission `open` dengan deskripsi lengkap.

## Fix kritikal: symlink adapter LoRA

Masalah ketika chat kirim "test" respons `SIDIX sedang offline`. Penyebab:
`find_adapter_dir()` di `local_llm.py` hanya cek `apps/brain_qa/models/sidix-lora-adapter/`.
Adapter di VPS ada di `/opt/sidix/sidix-lora-adapter/` (level root repo), bukan
di lokasi yang dicek.

Fix: `ln -sfn /opt/sidix/sidix-lora-adapter /opt/sidix/apps/brain_qa/models/sidix-lora-adapter`
→ `pm2 restart sidix-brain` → `model_ready: true`, `models_loaded: 3`.

Smoke test `POST /agent/chat` dengan persona INAN → SIDIX menjawab dengan
struktur sidq/sanad/tabayyun + epistemic_tier=`ahad_dhaif`,
yaqin_level=`ilm`, maqashid_passes=true.

## Batasan & keterbatasan

- `code_sandbox` blacklist patern = bukan sandbox penuh. Pada deploy produksi
  yang terbuka ke user publik, upgrade ke `bwrap --unshare-net` atau container.
- `web_fetch` tidak rendering JS (no headless browser). Halaman SPA hasil
  dinamis mungkin kosong. Untuk SPA-heavy butuh Playwright/Puppeteer self-host
  (P2).
- Model Qwen2.5-7B + 4-bit butuh lumayan RAM VRAM. Kalau VPS CPU-only, loading
  bisa lambat/OOM. Perlu monitor. (Per now di server sudah loaded 3 models.)

## Yang belum diselesaikan (next)

- Wire `audio_capability` sebagai tool chat (butuh whisper/piper/librosa install).
- Tambah `pdf_extract` tool (pdfplumber — CPU only, bisa sekarang).
- Tambah `web_search` tool (DuckDuckGo HTML via `web_fetch` → extract results).
- Self-host SDXL/FLUX di GPU (P2, butuh alokasi GPU VPS/Kaggle/mitra).
- Self-host Qwen2.5-VL untuk vision input (P2, butuh GPU).
- Cron harian LearnAgent (blocker: nama env var token di server `.env`).

## Sanad

- Kode sumber: `apps/brain_qa/brain_qa/agent_tools.py` (commit 952a586),
  `apps/brain_qa/brain_qa/webfetch.py`, `apps/brain_qa/brain_qa/local_llm.py`.
- Dokumen pedoman: `CLAUDE.md` (UI LOCK), `docs/SIDIX_CAPABILITY_MAP.md` (SSoT),
  `docs/SIDIX_BIBLE.md` (prinsip standing alone).
- Audit ringkas oleh 3 sub-agen paralel: backend code, research notes,
  konstitusi — disimpan di `docs/LIVING_LOG.md` entry 2026-04-19.

## Keputusan (anti-revisit)

- **Standing alone** = own modules di host SIDIX. Open data APIs publik boleh.
  Vendor AI API tidak.
- **Code sandbox** memakai `subprocess` + flag isolasi, bukan Docker per-call
  (overhead + kompleksitas). Upgrade ke container hanya jika dibuka untuk
  user publik.
- **Web fetch** pakai `html.parser` stdlib (bukan `lxml`) supaya tidak butuh
  build native di Windows.
- **Tool permission** `open` untuk keduanya → ReAct bisa pilih sendiri tanpa
  flag `allow_restricted`.
