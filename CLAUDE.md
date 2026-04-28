# CLAUDE.md — Instruksi Permanen untuk Semua Claude Agent

Proyek: **SIDIX / Mighan Model**

---

## 🔒 DEFINITION + DIRECTION LOCK 2026-04-26 (BACA PERTAMA — IMMUTABLE)

User directive eksplisit: *"gaaaaaaasssssssssssss!!!! catat!! jangan berubah-ubah lagi arah sidix"* + *"tulis dengan besar supaya nggak berubah lagi. cataaaattt!!! aligment semuanya"*

**WAJIB BACA URUTAN INI**:
1. 📜 **[`docs/SIDIX_DEFINITION_20260426.md`](docs/SIDIX_DEFINITION_20260426.md)** ← **SOURCE OF TRUTH #1** (definisi formal lengkap karakter + kemampuan + arsitektur)
2. 🔒 [`docs/DIRECTION_LOCK_20260426.md`](docs/DIRECTION_LOCK_20260426.md) ← tactical lock (8 ❌ rules + Q3 roadmap)

### Quick reference:
- **Tagline**: *"Autonomous AI Agent — Thinks, Learns & Creates"*
- **Karakter**: **GENIUS · KREATIF · INOVATIF**
- **Direction**: AI Agent yang **BEBAS dan TUMBUH**
- **Inti**: *"Entitas kecerdasan komprehensif yang tidak hanya mengeksekusi perintah multi-modal, tetapi secara PROAKTIF mengevaluasi, memori-optimasi, dan mengorkestrasi ekosistem tools untuk menciptakan nilai komersial dan inovasi TANPA PENGAWASAN TERUS-MENERUS"*
- **3 Fondasi**: The Mind (Self-Correction + RAG + ToT) · The Hands (Tool Orchestration + Aesthetic + Resource Mgmt) · The Drive (Proactivity + Boundary)
- **4-Pilar**: Memory + Multi-Agent + Continuous Learning + Proactive
- **5 Persona LOCKED**: UTZ · ABOO · OOMAR · ALEY · AYMAN
- **License**: MIT, self-hosted, no vendor LLM API

### Yang TIDAK BOLEH BERUBAH (10 ❌ hard rules):
Lihat `SIDIX_DEFINITION_20260426.md` section "Yang TIDAK BOLEH BERUBAH". Highlight:
- ❌ Tagline · ❌ klaim spiritual entity · ❌ vendor API · ❌ filter strict
- ❌ Drop 5 persona · ❌ MIT license · ❌ self-hosted core
- ❌ Drop sanad chain · ❌ Drop epistemic 4-label · ❌ Trivialize spiritual

### Yang BOLEH (Build On Top):
✅ Add fitur baru, tools baru, optimize, improve · ✅ Build di atas vol 1-13 NO replace · ✅ Sensorial multimodal (Q3-Q1 2027) · ✅ Q3 roadmap (Nightly LoRA, Trend RSS, MCP wrap, CodeAct)

**Vol 14+ = BUILD ON TOP, NO PIVOT**. Setiap pivot yang akan datang harus eksplisit user minta + buat file BARU `SIDIX_DEFINITION_<new_date>.md`.

---

## 🚦 ANTI-BENTROK: CLAUDE × KIMI (WAJIB BACA SEBELUM EDIT FILE APAPUN)

Proyek ini dikerjakan oleh DUA agent AI secara bersamaan: **Claude** (otak/deploy) dan **Kimi** (jiwa/kreatif).

### Sebelum edit file apapun, cek `docs/AGENT_WORK_LOCK.md`:
- **File milik KIMI** → JANGAN SENTUH: `parallel_executor.py`, `jiwa/*`, `emotional_tone_engine.py`, `sensor_fusion.py`, `parallel_planner.py`, dll.
- **File milik CLAUDE** → aman diedit: `agent_serve.py`, deploy scripts, tests, LIVING_LOG
- **File SHARED** (agent_react.py, cot_system_prompts.py) → edit di section yang ditandai, JANGAN hapus kode agent lain
- **Setelah Kimi commit** → run `git pull` + resolve conflict + full pytest SEBELUM commit apapun

### Quick rule:
```
Kalau file menyentuh Jiwa/Emosi/Kreativitas → Kimi
Kalau file menyentuh endpoint/deploy/orchestration → Claude
Kalau ragu → tulis di LIVING_LOG, tanya user
```

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

### 6.4. ⚠️ PRE-EXECUTION ALIGNMENT CHECK — Mandatory (2026-04-27 evening LOCK)

User directive eksplisit setelah catch alignment gap di Sprint 14c:
*"analisa dulu sebelum analisa, jangan sampe kontradiksi. kalau usha expired
dan bentrok dengan rencana akhir, ya jangan di eksekusi, kasih remark atau
apa lah."*

**SEBELUM edit file yang touch persona / prompt / agent behavior, WAJIB**:

```
1. RE-READ NORTH STAR — research_notes/248 first 50 lines
   (latest direction lock — Self-Evolving AI Creative Agent)

2. CHECK LATEST PIVOT — grep "PIVOT YYYY-MM-DD" sections di CLAUDE.md,
   identify yang paling baru. Per 2026-04-27:
   - 2026-04-26: DEFINITION + DIRECTION LOCK (note 248) ← latest
   - 2026-04-25: LIBERATION SPRINT (epistemik kontekstual, tool-aggressive)
   - 2026-04-19: IDENTITAS LOCK 3-layer

3. SELF-AUDIT — apa yang akan saya tulis ada di list anti-pattern
   pivot terbaru? Misalnya:
   - ❌ "Pakai [SPEKULASI]/[FAKTA]/[OPINI]/[TIDAK TAHU] tag bila..."
     instruction di prompt creative/casual (anti pivot 2026-04-25)
   - ❌ Blanket epistemik label per-paragraf (anti pivot 2026-04-25)
   - ❌ "Saya adalah X dengan pendekatan Y" boilerplate persona
     (anti pivot 2026-04-25)
   - ❌ Prioritize corpus untuk current events (anti pivot 2026-04-25)
   - ❌ Klaim spiritual entity / religious AI (anti note 248)
   - ❌ Drop 5 persona / drop sanad / drop epistemic 4-label sebagai
     option (anti note 248 hard rules)

4. IF CONFLICT — STOP execute. Tulis remark eksplisit ke user:
   "Instruction ini bentrok dengan pivot YYYY-MM-DD. Lanjut atau
   redirect?"
   JANGAN execute blindly walaupun copy dari research note lama.

5. IF ALIGNED — proceed dengan loop mandatory (CATAT TESTING ITERASI
   REVIEW VALIDASI QA CATAT)
```

**Familiarity bias trap** (root cause Sprint 14c gap):

Agent yang familiar dengan framing lama (pre-pivot) akan otomatis copy
pattern ke prompt baru tanpa cek pivot terbaru. SELALU verify against
source-of-truth dokumen, BUKAN mental model lama.

**Anti-pattern yang HARUS dihindari**:
- ❌ "Saya tau ini benar dari memory/research note" → research note lama
  bisa pre-pivot, WAJIB cek pivot terbaru
- ❌ Copy template prompt dari file existing tanpa audit alignment
- ❌ Skip audit karena "ini cuma minor edit"
- ❌ Self-justify alignment tanpa cite spesifik baris pivot doc

**Lesson dari Sprint 14c (2026-04-27)**: ALEY system prompt tertulis
*"Pakai [SPEKULASI] tag bila claim tidak bisa di-back hard data"* —
copy bias dari epistemic-as-differentiator framing pre-pivot 2026-04-25.
Detail full audit di research_notes/254. User catch saved compound integrity.

**ANTI-HALUSINASI rule** (user directive 2026-04-27 evening):
*"jangan sampai masuk ke dalam hallucinate lagi, nggak ada arah yang jelas."*

Setiap claim atau eksekusi WAJIB punya **basis konkret** dari salah satu:
- Cite line di CLAUDE.md / note 248 / pivot dokumen tertentu (line N)
- Cite output `git log` / `grep` / `read file` yang barusan di-run
- Cite test result actual (TIDAK boleh "saya yakin" tanpa output verifikasi)

Kalau tidak punya basis konkret → **STOP**, ambil basis dulu (read file, run grep,
verify), atau **kasih remark eksplisit**: *"Saya tidak yakin — perlu verifikasi
dulu. Lanjut cek file X / run command Y?"*

JANGAN gabungkan asumsi + memory + framing lama → **itu jalan ke halusinasi**.
Setiap output harus traceable ke source-of-truth, bukan compound dari mental
model yang mungkin sudah expired.

### 6.5. ⚠️ POST-TASK PROTOCOL — Loop Mandatory (2026-04-27 LOCK)

User directive eksplisit: *"Catat, testing, iterasi, training, Review, Catat,
Validasi, QA, Catat! Jadiin itu Mandatory kerja deh dari setiap habis done
task, push, pull and deploy."*

**SETIAP kali task selesai (sebelum push/pull/deploy/move-on)**, jalankan
loop ini SECARA URUT:

```
1. CATAT  (initial post-implement)
   └─ append progress ke LIVING_LOG (tag IMPL)
   └─ note keputusan kunci kalau ada

2. TESTING
   └─ syntax check (ast.parse / tsc --noEmit / equivalent)
   └─ smoke test: import + happy path + edge cases
   └─ integration test kalau touch flow lain

3. ITERASI
   └─ kalau test fail → fix → re-test
   └─ kalau test edge case kurang → tambah → re-test
   └─ ulang sampai green

4. TRAINING (optional, kalau task touch model behavior)
   └─ collect baseline metric (pre-change)
   └─ run new behavior → compare metric
   └─ kalau regress → rollback atau iterasi
   └─ kalau task tidak touch model: skip step ini

5. REVIEW (manual self-audit)
   └─ baca diff sendiri sebelum commit
   └─ check anti-pattern (over-engineering, secret leak, scope creep)
   └─ verify direction lock (10 ❌ rules belum dilanggar)
   └─ verify Kimi territory belum disentuh

6. CATAT (validasi findings)
   └─ append hasil testing ke LIVING_LOG (tag TEST + angka konkret)
   └─ append iterasi/regression notes

7. VALIDASI (functional verification)
   └─ kalau wired ke flow production: test dengan input nyata (atau mock representatif)
   └─ verify behavior match expectation
   └─ cek tidak break existing feature

8. QA (final check before commit)
   └─ git diff --cached | grep secret pattern (security audit)
   └─ verify all tests pass
   └─ verify dokumen ter-update (CHANGELOG kalau versi naik, HANDOFF kalau state berubah)

9. CATAT (final, before push)
   └─ commit message lengkap dengan WHY
   └─ push ke remote
   └─ kalau deploy: append entry deploy log
   └─ kalau ada DEFER: list eksplisit di HANDOFF
```

**Kenapa**: Tesla 100x percobaan compound. Setiap task tanpa catat = waste
energy karena context hilang. Setiap task tanpa testing = produksi bug.
Setiap task tanpa review = silent regression. Loop ini = compound integrity.

**Anti-pattern yang HARUS dihindari**:
- ❌ Skip testing karena "ini cuma small change" → semua change perlu test
- ❌ Skip catat di tengah loop → catat SETIAP step, bukan cuma akhir
- ❌ Push tanpa security audit → wajib `git diff | grep` pattern
- ❌ Iterasi tanpa baseline → harus ada metric/test yang jelas pass/fail
- ❌ Move ke task berikutnya tanpa selesaikan loop → finish loop dulu, baru next

**Lokasi dokumentasi yang ter-update tiap loop iteration**:
- `docs/LIVING_LOG.md` — semua step (catat steps 1, 6, 9 minimal)
- `CHANGELOG.md` — kalau versi minor/major naik
- `docs/HANDOFF_CLAUDE_<latest>.md` — kalau state berubah signifikan
- `brain/public/research_notes/<n>_*.md` — kalau ≥1 paragraf knowledge baru

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

## 🤖 MODEL POLICY — Claude Agent Model Selection (2026-04-28)

User directive: *"untuk development yang common use, riset, sintesis dll pake sonnet. kasih tau saya kalo ada yang kompleks, saya akan ganti ke opus. untuk cari data, kumpulin data, screening pake haiku biar irit usage dan token tapi efektif."*

### Default per task type

| Model | Task | Alasan |
|---|---|---|
| **Haiku 4.5** (`claude-haiku-4-5-20251001`) | Fetch URL, web search, screen data, bulk QA scan, format convert, grep/count corpus, simple parse | 10-50x lebih hemat token vs Sonnet. Output tidak perlu reasoning dalam. |
| **Sonnet 4.6** (`claude-sonnet-4-6`) | **DEFAULT** — semua coding, debug, research synthesis, sprint planning, refactor, test, dokumentasi, review | Balanced quality/cost. 90%+ task SIDIX dev masuk sini. |
| **Opus 4.7** (`claude-opus-4-7`) | Arsitektur multi-system besar, security audit serius, novel algorithm, ketika Sonnet stuck 2x iter | 5x lebih mahal dari Sonnet. Pakai hanya kalau Sonnet jelas tidak cukup. |

### Kapan Agent HARUS kasih tau bos untuk switch ke Opus

Agent wajib bilang *"Task ini sebaiknya pakai Opus — mau switch dulu?"* sebelum eksekusi kalau:
- Task touch >5 file dengan architectural decision besar (bukan cuma wire/glue)
- Security vulnerability deep analysis (bukan cuma grep scan)
- Novel algorithm yang butuh multi-hop reasoning chain
- Sonnet sudah 2x iterasi tapi output masih ngaco / stuck
- Trade-off besar yang compound (infra + model + product design sekaligus)

Agent **TIDAK** boleh switch model sendiri — selalu minta konfirmasi bos.

### Kapan pakai Haiku (hemat token)

Gunakan Haiku untuk pipeline yang bisa di-batch atau tidak butuh reasoning:
- `web_search` → screen 20 hasil → filter relevan
- Fetch URL → extract key fields
- Bulk corpus scan → count / tag / deduplicate
- Simple regex / format validation
- Data QA pass sebelum LLM processing

### Anti-pattern yang HARUS dihindari
- ❌ Pakai Sonnet untuk task yang Haiku bisa handle (buang token)
- ❌ Pakai Sonnet untuk task yang jelas butuh Opus tapi tidak kasih tau bos (output kualitas rendah + waste iter)
- ❌ Switch ke Opus tanpa bilang dulu (keputusan bos, bukan agent)
- ❌ Stuck di Sonnet >2 iter tanpa eskalasi ke Opus

---

## 🔧 Konteks Deployment

### Arsitektur Hardware (LOCK 2026-04-27 — PENTING, sebelumnya tidak tercatat)

SIDIX **2-tier hardware**:

```
┌──────────────────────────────────────────────────────────┐
│  VPS Linux (no GPU, 4 vCPU AMD EPYC, 15GB RAM)           │
│  ─ /opt/sidix path                                        │
│  ─ brain_qa FastAPI (PM2: sidix-brain, port 8765)        │
│  ─ Frontend serve (PM2: sidix-ui, port 4000)             │
│  ─ Local sentence-transformers (BGE-M3 / MiniLM CPU)     │
│  ─ RAG corpus + semantic cache + domain detector         │
│  ─ Tools execution sandbox + cognitive modules            │
└──────────────────────────────────────────────────────────┘
                          ↓ HTTP API
┌──────────────────────────────────────────────────────────┐
│  RunPod Serverless (GPU, vLLM v2.14.0)                   │
│  ─ Endpoint: ws3p5ryxtlambj                              │
│  ─ Model: Qwen2.5-7B-Instruct + LoRA SIDIX adapter       │
│  ─ HF: huggingface.co/Tiranyx/sidix-lora                 │
│  ─ GPU: 24GB Pro × 1 worker, queue-based, auto-scale     │
│  ─ Warmup script: deploy-scripts/warmup_runpod.sh        │
└──────────────────────────────────────────────────────────┘
```

**Implikasi**:
- Embedding (BGE-M3) bisa run di VPS CPU, tidak butuh GPU
- LLM inference (Qwen+LoRA) WAJIB via RunPod, jangan coba load di VPS
- Mamba2-7B embedding (~14GB inference) ⚠️ TOO SLOW di VPS CPU; pilih Mamba2-1.3B atau BGE-M3 untuk VPS
- Cold-start RunPod: 60-120s (warmup_runpod.sh run sebelum traffic)

### PM2 Apps (production VPS)

```
sidix-brain   pid varies   port 8765   /opt/sidix/start_brain.sh (bash → python3 -m brain_qa serve)
sidix-ui      pid varies   port 4000   serve dist -p 4000 dari /opt/sidix/SIDIX_USER_UI/
sidix-mcp-prod stopped (manual enable via SIDIX_MCP_ENABLED=true)
sidix-health-prod cron */15 min health check
```

### URLs

- VPS: Linux server (private — IP & specs di env file lokal, jangan log)
- Domain publik: `sidixlab.com`, `app.sidixlab.com`, `ctrl.sidixlab.com`
  - `app.sidixlab.com` → nginx proxy_pass localhost:4000 (sidix-ui)
  - `ctrl.sidixlab.com` → nginx proxy_pass localhost:8765 (sidix-brain)
  - `sidixlab.com` (landing) → static `/www/wwwroot/sidixlab.com/`
- Aapanel manages nginx config di `/www/server/panel/vhost/nginx/`
- Sync landing manual setelah git pull (TODO: auto via post-merge hook)

### ENV Vars Penting (di `/opt/sidix/.env`)

```
BRAIN_QA_ADMIN_TOKEN     # untuk akses /admin/* endpoints (header X-Admin-Token)
SIDIX_EMBED_MODEL        # bge-m3 (default safe) | minilm | mamba2-1.3b | mamba2-7b
RUNPOD_API_KEY           # untuk call vLLM endpoint
                         # endpoint URL: https://api.runpod.ai/v2/ws3p5ryxtlambj/run
SIDIX_TYPO_PIPELINE      # =1 (di ecosystem.config.js)
```

⚠️ **PM2 tidak auto-load `/opt/sidix/.env`** — env var perlu di-set via ecosystem.config.js atau export sebelum `pm2 start`. Kalau env var hilang setelah `pm2 restart --update-env`, cek shell env saat command dijalankan.

### Database
- Supabase (URL & key di `.env`, jangan commit)
- HF organization: `Tiranyx` (account user)

---

## 🔄 PIVOT 2026-04-25 — LIBERATION SPRINT (BACA SEBELUM EDIT PROMPT/PERSONA)

Setelah LOCK 2026-04-19 (IDENTITAS 3-layer), SIDIX melakukan pivot **behavior**
berdasarkan feedback user. Arsitektur tidak berubah — 3-layer tetap (generative
+ RAG/tools + growth loop). Yang berubah adalah **cara SIDIX ngomong**.

### 3 perubahan behavior (detail: `research_notes/208_pivot_liberation_sprint.md`)

**1. Tool-use AGGRESSIVE (default)** — pertanyaan current events (berita, harga,
tanggal, tokoh saat ini) langsung `web_search` sebelum corpus. Jangan pernah
bilang "saya tidak punya data terkini" — ada DuckDuckGo. Regex: `_CURRENT_EVENTS_RE`
di `agent_react.py`. Policy: `SIDIX_SYSTEM` di `ollama_llm.py`.

**2. Persona LIBERATION** — 5 persona punya voice DISTINCT (aku/gue/saya/halo),
bukan boilerplate. Lihat `PERSONA_DESCRIPTIONS` di `cot_system_prompts.py`:
- UTZ = creative/visual (bukan "engineer" seperti mental model lama yang salah)
- ABOO = engineer/technical
- OOMAR = strategist/bisnis
- ALEY = researcher/akademik
- AYMAN = general/chat hangat

**3. Epistemik labels KONTEKSTUAL** — `[FAKTA]/[OPINI]/[SPEKULASI]/[TIDAK TAHU]`
WAJIB di pembuka HANYA untuk topik sensitif (fiqh/medis/data/berita/statistik),
SKIP untuk casual chat/coding/brainstorm. Satu label di pembuka cukup — JANGAN
ulang label setiap paragraf. Lihat `EPISTEMIK_REQUIREMENT` di `cot_system_prompts.py`.

### Yang TIDAK berubah (tetap LOCK)

- Sanad chain untuk klaim fiqh/medis → tetap wajib
- Epistemic honesty sebagai differentiator → tetap inti, bentuknya subtle
- 3-layer arsitektur (LLM generative + RAG/tools + growth loop) → LOCK 2026-04-19

### Aturan untuk Agent Lain

❌ JANGAN kembalikan epistemik label ke blanket-per-kalimat
❌ JANGAN ubah persona kembali ke format "Saya adalah X dengan pendekatan Y"
❌ JANGAN prioritaskan corpus untuk pertanyaan current events
✅ Ikuti pivot ini saat editing prompt/persona/agent logic
✅ Kalau ragu, baca note 208 dulu

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
