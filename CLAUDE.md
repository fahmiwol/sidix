# CLAUDE.md — Instruksi Permanen untuk Semua Claude Agent

Proyek: **SIDIX / Mighan Model**

---

## 📖 BACA DULU SEBELUM MULAI (SSOT)

Sebelum kerja apapun, baca 3 file ini berurutan (cegah amnesia + repeat work):

1. **`docs/SIDIX_BIBLE.md`** — konstitusi hidup (4 pilar identitas, IHOS,
   4-label epistemik, Maqashid filter, sanad-required, trajectory mandiri,
   parity target GPT/Claude/ByteDance/Gemini)
2. **`docs/SIDIX_CHECKPOINT_<latest>.md`** — snapshot state + queue
3. **`docs/LIVING_LOG.md`** (tail 50 lines) — apa yang baru dikerjakan

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

## 🧠 Cara Claude Bekerja di Proyek Ini

1. **Baca konteks** — cek LIVING_LOG, research notes terbaru, state file yang relevan
2. **Eksekusi task**
3. **Tulis research note** — dokumentasikan proses, keputusan, dan knowledge yang dipakai
4. **Update LIVING_LOG** — append entri dengan tag yang tepat
5. **Commit** — task + docs dalam satu commit atau dua commit berurutan
6. **Push** — agar server dan kontributor bisa pull terbaru

Urutan ini berlaku untuk **setiap task**, tidak peduli sekecil apapun.
