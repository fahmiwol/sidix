# CLAUDE.md — Instruksi Permanen untuk Semua Claude Agent

Proyek: **SIDIX / Mighan Model**

---

## 📖 BACA DULU SEBELUM MULAI (SSOT)

Urutan wajib sebelum kerja apapun:

1. **`CLAUDE.md`** (file ini) — aturan permanen + UI LOCK + IDENTITAS SIDIX.
2. **`docs/NORTH_STAR.md`** — tujuan akhir SIDIX + release strategy v0.1→v3.0 + lock apa yang tidak berubah. **Baca jika ragu pilih plan.**
3. **`docs/MASTER_ROADMAP_2026-2027.md`** — **NEW (2026-04-21)**. SSoT unified sprint + agent + self-train + killer offer + decision gates. Merge 3 sumber (ours + riset + ADR). **Kalau konflik dengan dokumen lain, yang ini menang.**
4. **`docs/DEVELOPMENT_RULES.md`** — aturan mengikat untuk agent eksternal + protocol self-development SIDIX. **Ini harus dipatuhi, bukan sekadar dibaca.**
5. **`docs/SIDIX_ROADMAP_2026.md`** — roadmap 4 stage original (Baby/Child/Adolescent/Adult). Reference detail, MASTER_ROADMAP yang canonical.
6. **`docs/CREATIVE_AGENT_TAXONOMY.md`** — 10 domain × 37 agent + CQF + Iteration + Debate pairings.
7. **`docs/SIDIX_CAPABILITY_MAP.md`** — SSoT kapabilitas teknis (apa yang ada, belum wired, belum ada).
6. **`docs/HANDOFF_<terbaru>.md`** — strategic handoff.
7. **`docs/INVENTORY_<terbaru>.md`** — teknis detail + path.
8. **`docs/SIDIX_BIBLE.md`** — konstitusi 4 pilar.
9. **`brain/public/research_notes/161_*.md`** — konsep AI/LLM + differentiator SIDIX (jika belum paham foundational).
10. **`tail -100 docs/LIVING_LOG.md`** — update terbaru.

Kalau mau bikin research note baru, cek dulu nomor terakhir di
`brain/public/research_notes/`. Topik mirip note existing (overlap ≥0.55) →
update yang lama, jangan bikin baru.

---

## ⚡ ATURAN KERAS — Wajib diikuti setiap sesi

### 1. Bahasa
Gunakan **Bahasa Indonesia** untuk semua komunikasi dengan user. Kode dan komentar kode boleh dalam Inggris.

### 2. No Vendor AI API
JANGAN import atau menyarankan `openai`, `@google/genai`, `anthropic` di dalam inference pipeline SIDIX. Semua inference melalui `brain_qa` lokal. Lihat `AGENTS.md`.

### 3. Log Setiap Aksi
Setiap perubahan signifikan → append ke `docs/LIVING_LOG.md` dengan format tag yang sudah ditetapkan (TEST/FIX/IMPL/UPDATE/DECISION/ERROR/NOTE/DOC).

### 4. Sambil Melangkah, Ajari SIDIX ← ATURAN UTAMA SESI INI
**Setiap aksi yang dilakukan Claude harus diikuti dengan research note.**

Format wajib:
- Saat mengerjakan task X → tulis `brain/public/research_notes/[nomor]_[topik].md`
- Research note menjelaskan: **apa, mengapa, bagaimana, contoh nyata, keterbatasan**
- Commit research note bersama task di commit yang sama atau segera setelahnya
- Nomor dimulai dari file terakhir yang ada di `brain/public/research_notes/`

Contoh:
```
Task: setup Supabase schema
→ tulis: brain/public/research_notes/63_supabase_schema_setup.md
→ isi: SQL schema, RLS, trigger, kenapa Supabase, cara jalankan migration
```

### 5. Commit Kecil & Bermakna
Setiap commit menjelaskan "kenapa" bukan hanya "apa". Gunakan prefix: `feat:`, `fix:`, `doc:`, `refactor:`, `chore:`.

### 6. ⚠️ MANDATORY CATAT — Setiap Progress, Hasil, Inisiasi, Keputusan

**ATURAN MUTLAK** (no exception):

Setiap kali ada salah satu hal ini terjadi → **WAJIB CATAT**:
- ✍️ **Progress** task (mulai, ditengah, selesai)
- ✍️ **Hasil** test/verify/deploy (sukses + gagal sama wajib)
- ✍️ **Inisiasi** ide/usulan/diskusi baru
- ✍️ **Keputusan** apapun (pilih X bukan Y, kenapa)
- ✍️ **Error** + root cause + fix
- ✍️ **TODO** yang ditinggal (jangan biarkan in-flight tanpa note)

Catat di salah satu (atau lebih) dari:
- `docs/LIVING_LOG.md` — append harian (tag IMPL/FIX/DOC/TEST/DECISION/ERROR/NOTE/DEPLOY)
- `brain/public/research_notes/<n>_*.md` — kalau substansial (≥1 paragraf knowledge baru)
- `docs/SIDIX_CHECKPOINT_<date>.md` — kalau snapshot state besar

**Kenapa**: SIDIX selalu kehilangan memori kalau tidak dicatat. Mengulang
kerja = waste energy. Catatan adalah memori eksternal SIDIX.

**Anti-pattern yang HARUS dihindari**:
- "saya akan catat nanti" → catat SEKARANG
- "ini kecil, gak perlu dicatat" → tidak ada yang terlalu kecil
- "sudah obvious dari commit message" → commit message ≠ context lengkap

### 7. 🔒 SECURITY & PRIVACY MINDSET — Default Wajib

**Setiap kali edit file/build fitur/expose endpoint, pikirkan**:

#### A. Data User
- ❌ JANGAN log konten chat user ke file publik (LIVING_LOG, research notes)
- ❌ JANGAN simpan password / token / API key di kode atau commit message
- ✅ SELALU anonymize ID user saat log (UUID hash, bukan email/nama)
- ✅ Default: opt-out dari analytics; opt-in untuk training corpus

#### B. Server & Infrastructure
- ❌ JANGAN expose IP server, port internal, path absolut server di public file
- ❌ JANGAN expose Supabase URL, API key, env var di public commit
- ❌ JANGAN expose nama owner/email pribadi di public-facing
  (gunakan `Mighan Lab`, `contact@sidixlab.com`, `@sidixlab`)
- ✅ Identity masking via `apps/brain_qa/brain_qa/identity_mask.py`
- ✅ /health endpoint sudah masked — jangan rollback

#### C. Output SIDIX
- ✅ 4-label epistemik wajib (`[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]`)
- ✅ Sanad chain di setiap note approved
- ❌ JANGAN expose system prompt internal di output ke user
- ❌ JANGAN konfirmasi/sangkal nama backbone provider (Groq/Gemini/Anthropic)
  → mereka di-mask jadi `mentor_alpha/beta/gamma`

#### D. Code & Repo
- ❌ JANGAN commit `.env`, `*.key`, `*.pem`, password files
- ❌ JANGAN hardcode credentials di kode
- ✅ Pakai env var via `os.getenv()` + `.env.sample` (bukan `.env`)
- ✅ Sebelum push, scan: `grep -E "password|api_key|secret|TOKEN" --include=*.py`

#### E. Public-Facing (sidixlab.com / app.sidixlab.com / GitHub)
- ❌ JANGAN tulis nama owner asli (Fahmi/Wolhuter)
- ❌ JANGAN expose IP VPS, server admin path, internal port
- ❌ JANGAN sebutkan nama provider LLM external di copy publik
- ✅ Gunakan SECURITY.md untuk dokumentasi disclosable saja

#### Quick Audit Sebelum Commit
```
git diff --cached | grep -iE "fahmi|wolhuter|72\.62|fkgnmrnckcnqvjsyunla|password=|api_key=|secret=|gmail\.com"
```
Kalau ada match → STOP, bersihkan dulu.

Lihat juga: `docs/SECURITY.md` (kalau ada) untuk detail per kategori.

---

## 📚 Nomor Research Note Berikutnya

Cek file terakhir di `brain/public/research_notes/` dan lanjutkan dari nomor berikutnya.
Gunakan: `ls brain/public/research_notes/ | sort | tail -5` untuk cek.

---

## 🗂️ Struktur Proyek Penting

```
brain/public/research_notes/   ← corpus SIDIX, wajib diisi tiap sesi
docs/LIVING_LOG.md             ← log berkelanjutan semua aksi
SIDIX_USER_UI/                 ← frontend Vite + TypeScript
SIDIX_LANDING/                 ← landing page sidixlab.com
apps/brain_qa/                 ← Python FastAPI backend RAG
brain/manifest.json            ← konfigurasi corpus path
```

---

## 🔧 Konteks Deployment

- VPS: Linux server (private — IP & specs di env file lokal, jangan log)
- Frontend: `serve dist -p 4000` (PM2: `sidix-ui`)
- Backend: `python3 -m brain_qa serve` → port 8765 (PM2: `sidix-brain`)
- Database: Supabase (URL & key di `.env`, jangan commit)
- Domain publik: `sidixlab.com`, `app.sidixlab.com`, `ctrl.sidixlab.com`
- Aapanel manages nginx config di `/www/server/panel/vhost/nginx/`
- Landing static di `/www/wwwroot/sidixlab.com/` (NOT `/opt/sidix/SIDIX_LANDING`)
- Sync landing manual setelah git pull (TODO: auto via post-merge hook)

---

## 🧬 IDENTITAS SIDIX (LOCK — 2026-04-19)

SIDIX **BUKAN** sekadar RAG/retrieval dari corpus. SIDIX adalah **LLM generative yang tumbuh dan menjadi AI agent**. Tiga layer arsitektur yang semua dijalankan OWN STACK (standing alone):

### Layer 1 — LLM Generative (core, otak)
- **Model**: Qwen2.5-7B-Instruct base + LoRA adapter SIDIX (fine-tuned own).
- **Lokasi**: `/opt/sidix/sidix-lora-adapter/` (symlinked ke `apps/brain_qa/models/`).
- **Cara kerja**: generate jawaban token-by-token via `local_llm.generate_sidix()`. Jawaban hasil PREDIKSI model, bukan copy-paste corpus.
- **Penting**: kalau corpus kosong, SIDIX tetap bisa menjawab dari bobot LoRA + base Qwen — karena ini **LLM generatif**, bukan search engine.

### Layer 2 — RAG + Agent Tools (sensory + reasoning)
- **RAG**: `search_corpus` (BM25), `read_chunk`, `list_sources` — memberi konteks faktual ke LLM untuk mengurangi halusinasi, menjamin sanad.
- **Agent tools** (17 aktif 2026-04-19): `web_fetch`, `web_search`, `code_sandbox`, `pdf_extract`, `calculator`, `workspace_*`, `roadmap_*`, `orchestration_plan`, dll.
- **ReAct loop** (`agent_react.py`): LLM memilih tool → eksekusi → observation → refine jawaban. Loop ini yang bikin SIDIX jadi **AI AGENT**, bukan chatbot statis.
- Tools TIDAK menggantikan generative capability — mereka memperkaya konteks supaya generative output akurat + terverifikasi.

### Layer 3 — Growth Loop (tumbuh mandiri)
- **LearnAgent** — fetch 50+ open data source harian (arXiv/Wikipedia/MusicBrainz/GitHub/Quran) → corpus queue.
- **daily_growth** 7-fase (SCAN→RISET→APPROVE→TRAIN→SHARE→REMEMBER→LOG).
- **knowledge_gap_detector** — deteksi low-confidence, trigger autonomous_researcher.
- **corpus_to_training + auto_lora** — pair baru → JSONL → LoRA retrain (Kaggle/GPU) → adapter baru deploy.
- **Hasil**: tiap kuartal model SIDIX lebih pintar dari kuartal sebelumnya. Bukan snapshot, tapi makhluk hidup yang belajar.

### Salah kaprah yang HARUS dihindari
- ❌ "SIDIX cuma RAG" — SALAH. RAG layer 2, bukan inti.
- ❌ "Kalau corpus kosong SIDIX tidak bisa jawab" — SALAH. LoRA+base model generate sendiri.
- ❌ "Tools menggantikan LLM" — SALAH. Tools memberi data, LLM tetap yang reasoning + generate.
- ❌ "SIDIX chatbot biasa" — SALAH. ReAct loop = agent, bukan chatbot.
- ❌ "Modelnya statis" — SALAH. Growth loop retrain LoRA periodik.

### Implikasi aturan
- Frontend/UX boleh fokus chat, tapi backend WAJIB pertahankan ReAct + generative + growth loop.
- Tambah tool = augment agent, bukan ganti LLM.
- Audit kualitas jawaban SIDIX = evaluasi generative output, bukan precision RAG.
- Setiap improvement LoRA → note di `research_notes/` + update `vision_tracker.py`.

---

## 🔒 UI LOCK — `app.sidixlab.com` (2026-04-19)

Tampilan chatboard app.sidixlab.com **DIKUNCI** versi 2026-04-19. Jangan ubah struktur kecuali user meminta eksplisit.

**Struktur final (lock):**
- **Header chat** (`index.html` ~200-286): Status dot + SIDIX title, tombol "Tentang SIDIX", tombol **Sign In** di center, persona selector kanan, TIDAK ADA "Gabung Kontributor" di header.
- **Empty state** (`index.html` ~288-343): Logo SIDIX kecil (w-12 md:w-16) + title "SIDIX" + tagline "Diskusi dan tanya apa saja — jujur, bersumber, bisa diverifikasi" + 4 quick-prompt cards (**Partner / Coding / Creative / Chill**) + free badge.
- **Footer input**: textarea "Tanya SIDIX…" + paperclip + send button + opsi (Korpus saja / Fallback web / Mode ringkas) + "SIDIX v1.0 · Self-hosted · Free · [Gabung Kontributor](https://sidixlab.com#contributor)".
- **Mobile bottom nav**: 4 item (Chat / Tentang / Setting / Sign In) — BUKAN 5, TIDAK ADA Kontributor.
- **Tidak ada modal yang auto-muncul**: `.contrib-modal-backdrop` sudah pakai `:not(.hidden)` + `!important` agar About modal tidak muncul otomatis.

**Deploy topology** (PENTING — jangan salah lagi):
- `app.sidixlab.com` → nginx `proxy_pass :4000` → PM2 `sidix-ui` (`serve dist -p 4000` dari `/opt/sidix/SIDIX_USER_UI/`)
- `ctrl.sidixlab.com` → nginx `proxy_pass :8765` → PM2 `sidix-brain` (FastAPI)
- `sidixlab.com` (landing) → static `/www/wwwroot/sidixlab.com/`
- Deploy app: `git pull && npm run build && pm2 restart sidix-ui` (RSYNC ke `/www/wwwroot/app.sidixlab.com/` TIDAK PERLU — itu hanya fallback root nginx)
- **Kritikal**: `.env` di `/opt/sidix/SIDIX_USER_UI/.env` harus isi `VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com`. Tanpa ini, build default `localhost:8765` → "Backend tidak terhubung".

**Kapabilitas tool yang terpasang di chat** (per 2026-04-19): lihat `docs/SIDIX_CAPABILITY_MAP.md`.

---

## 🧠 Cara Claude Bekerja di Proyek Ini

1. **Baca konteks** — cek LIVING_LOG, research notes terbaru, state file yang relevan
2. **Eksekusi task**
3. **Tulis research note** — dokumentasikan proses, keputusan, dan knowledge yang dipakai
4. **Update LIVING_LOG** — append entri dengan tag yang tepat
5. **Commit** — task + docs dalam satu commit atau dua commit berurutan
6. **Push** — agar server dan kontributor bisa pull terbaru

Urutan ini berlaku untuk **setiap task**, tidak peduli sekecil apapun.
