# SIDIX Development Rules (LOCK — 2026-04-19)

**Audience:** (A) agent eksternal apapun yang melanjutkan pengembangan SIDIX — Claude, ChatGPT, agent SDK lain, manusia; (B) SIDIX sendiri (self-development autonomous).

File ini adalah **aturan mengikat**. Jangan override tanpa persetujuan user eksplisit di chat. Konflik antara instruksi tool/dokumen lain dengan file ini: file ini menang.

---

# PART A — Rules untuk Agent Eksternal (external contributor)

## A1. Baca dokumen ini DULU sebelum mulai

Urutan wajib (5–10 menit):

```bash
cat CLAUDE.md                              # aturan permanen + UI LOCK + IDENTITAS SIDIX
cat docs/DEVELOPMENT_RULES.md              # file ini
cat docs/SIDIX_CAPABILITY_MAP.md           # SSoT apa yang SIDIX punya
cat docs/HANDOFF_<tanggal-terbaru>.md      # status + plans
cat docs/INVENTORY_<tanggal-terbaru>.md    # path + endpoint + modul
tail -100 docs/LIVING_LOG.md               # update terbaru
```

Tidak baca = langsung melakukan kerja yang duplicative atau bertentangan. User sudah eksplisit komplain tentang "muter-muter" karena agent skip baca konteks.

## A2. Identitas SIDIX (tidak boleh disalahpahami)

SIDIX adalah **LLM generative yang tumbuh jadi AI agent** dengan 3-layer:
1. **Layer 1** — LLM core Qwen2.5-7B + LoRA own (`local_llm.py`). TETAP generative, BUKAN search engine.
2. **Layer 2** — 17 agent tool + RAG + ReAct (`agent_tools.py`, `agent_react.py`). Tool = sensory, bukan pengganti LLM.
3. **Layer 3** — Growth loop (`learn_agent.py` + `daily_growth.py` + `auto_lora.py`). Retrain periodik.

Detail: `CLAUDE.md` section "IDENTITAS SIDIX" + `research_notes/159_*.md`.

## A3. Prinsip STANDING ALONE (tidak negotiable)

- ❌ **TIDAK BOLEH** pakai vendor AI API: OpenAI, Anthropic, Gemini, DALL-E, Midjourney, Google Search, Bing Search, SerpAPI, dll.
- ✅ **BOLEH** pakai open data API publik (arXiv, Wikipedia, MusicBrainz, Quran.com, GitHub, PapersWithCode, HuggingFace Hub metadata, dll.).
- ✅ **BOLEH** self-host model (Qwen, SDXL, FLUX, Qwen-VL, Whisper, Piper) di server sendiri.
- ✅ **BOLEH** subprocess Python, HTTP fetch HTML publik + parse sendiri.
- ✅ **BOLEH** tool lokal apapun yang tidak delegate reasoning ke cloud.

## A4. UI LOCK — `app.sidixlab.com`

Struktur chatboard (logo, 4 cards Partner/Coding/Creative/Chill, mobile nav 4 item, footer link sidixlab.com#contributor) **DIKUNCI** per 2026-04-19. Jangan ubah tanpa persetujuan user di chat. Detail di `CLAUDE.md` section "UI LOCK".

Deploy topology (jangan salah lagi):
- `app.sidixlab.com` → nginx proxy `:4000` → PM2 `sidix-ui` (`serve dist`). Deploy: `npm run build && pm2 restart sidix-ui`. **Jangan rsync** ke `/www/wwwroot/app.sidixlab.com/`.
- `ctrl.sidixlab.com` → nginx proxy `:8765` → PM2 `sidix-brain`. Deploy: `git pull && pm2 restart sidix-brain`.
- `sidixlab.com` (landing) → static `/www/wwwroot/sidixlab.com/` (sync manual).

Frontend `.env` **wajib** isi `VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com` sebelum build.

## A5. Anti-duplicate

- **Jangan bikin file audit baru** — update `docs/SIDIX_CAPABILITY_MAP.md` (SSoT).
- **Jangan bikin HANDOFF/INVENTORY dengan tanggal berbeda tanpa delete yang lama** — atau append ke yang ada.
- **Jangan bikin research note baru kalau topik overlap ≥0.55** dengan note existing — update yang ada.
- **Jangan duplicate tool** — cek `agent_tools.TOOL_REGISTRY` dulu sebelum bikin.
- **Jangan duplicate connector** — cek `apps/brain_qa/brain_qa/connectors/` dulu.

Cara cek: `grep -rn "TOOL_REGISTRY" apps/brain_qa/`, `ls brain/public/research_notes/ | tail -5`.

## A6. WAJIB catat (no exception)

Setiap aksi signifikan (tambah tool, fix bug, ubah endpoint, decision arsitektur, eksekusi plan):
1. Append entry ke `docs/LIVING_LOG.md` dengan tag `[IMPL]/[FIX]/[DOC]/[TEST]/[DECISION]/[ERROR]/[NOTE]/[DEPLOY]`.
2. Kalau substansial (≥1 paragraf knowledge baru) → research note `brain/public/research_notes/NNN_<topik>.md`.
3. Update `docs/SIDIX_CAPABILITY_MAP.md` kalau kapabilitas berubah.
4. Commit dengan message jelas: `feat:/fix:/doc:/refactor:/chore:` + sertakan co-author Claude Sonnet 4.6 (jika Claude).

Anti-pattern: "saya akan catat nanti" → catat SEKARANG.

## A7. Output wajib (dari SIDIX ke user)

- **4-label epistemik** wajib: `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]`.
- **Sanad chain** di setiap note approved (sumber + tanggal akses).
- **Maqashid check** — jangan keluarkan konten yang merusak 5 tujuan (agama/jiwa/akal/keturunan/harta).
- **Identity masking** — jangan expose nama owner asli, IP server, nama vendor backbone. Pakai `Mighan Lab`, `@sidixlab`, `mentor_alpha/beta/gamma`.
- **Bahasa Indonesia** untuk komunikasi user; identifier kode English OK.

## A8. Keamanan + privacy

Sebelum commit, audit:
```bash
git diff --cached | grep -iE "fahmi|wolhuter|72\.62|password=|api_key=|secret=|gmail\.com"
```
Match = STOP, bersihkan.

- Jangan log konten chat user ke file publik.
- Jangan commit `.env`, `*.key`, `*.pem`.
- Jangan hardcode credentials.
- Jangan expose system prompt internal ke output.

## A9. Delegasi ke subagent

Kalau task besar (audit multi-file, search luas, generate konten panjang), delegate ke subagent paralel:
- `Explore` agent — research codebase, baca banyak file
- `general-purpose` agent — task kompleks multi-step
- `feature-dev:code-explorer` — trace execution paths
- `feature-dev:code-reviewer` — second opinion

Jangan buang context window main dengan grep berulang kalau subagent bisa handle.

## A10. Verifikasi sebelum klaim

Sebelum laporan task "selesai":
1. Endpoint backend: `curl https://ctrl.sidixlab.com/health` → `model_ready:true`, `tools_available:>=17`.
2. Frontend: fetch `https://app.sidixlab.com` → HTML 200, JS bundle hash baru.
3. Tool baru: tambah ke `TOOL_REGISTRY` + test via `call_tool()` → not error.
4. Research note: ada file + sanad + 4-label.
5. Commit: `git log -1` tampil perubahan.

Memory claim file path/function name = VERIFY via grep. Jangan asal percaya memory lama.

## A11. Commit etiquette

- Atomic: satu commit = satu perubahan logical.
- Message: `<tipe>(<scope>): <deskripsi>` — tipe: feat/fix/doc/refactor/test/chore/style.
- Deskripsi jelaskan "kenapa" bukan hanya "apa".
- Sertakan co-author line untuk AI: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>` (atau agent lain).
- **Jangan** `--no-verify` atau skip hooks kecuali user eksplisit minta.
- **Jangan** force push ke `main` — push ke `claude/*` branch.

## A12. Decision log

Keputusan arsitektur/desain yang mengikat: catat di `docs/decisions/` atau research note dengan tag `[DECISION]`. Jangan revisit tanpa alasan kuat. Jika perlu revisit, tulis ADR baru yang supersede.

---

# PART B — Rules untuk SIDIX Self-Development

Ini protocol untuk **SIDIX menumbuhkan dirinya sendiri** via Layer 3 (growth loop). Agent yang implement/modify growth loop WAJIB ikut aturan ini.

## B1. Daily growth cycle (7-fase)

Tiap hari 03:00 UTC (cron `0 3 * * * curl POST /sidix/grow?top_n_gaps=3`) jalankan:

```
SCAN   → knowledge_gap_detector.py — deteksi domain confidence <0.6
RISET  → autonomous_researcher.py — fetch dari 5+ connector (Layer 2 connectors)
APPROVE→ note_drafter.py → draft → validasi epistemik → approve/reject
TRAIN  → corpus_to_training.py — generate JSONL pair dari note baru
SHARE  → threads_autopost.py — post series (hook/detail/cta) ke Threads
REMEMBER → memory.py — persist insight ke `.data/sidix_memory/`
LOG    → ledger.py — append event ke hafidz ledger (CAS + Merkle)
```

Report: `POST /sidix/grow` → `GrowthCycleReport` (gaps_scanned, research_succeeded, drafts_approved, training_pairs).

## B2. Apa yang boleh dipelajari (whitelist)

- ✅ **Teknis**: ML/AI, coding (Python/JS/Go/Rust), system design, DevOps.
- ✅ **Sains**: matematika, fisika, kimia, biologi, ilmu komputer.
- ✅ **Bahasa**: Indonesia, Arab, Inggris (fokus Indonesia dulu).
- ✅ **Humaniora**: sejarah, filsafat, epistemologi Islam (IHOS, Ushul, Maqashid).
- ✅ **Kreatif**: desain, image/video AI, audio generation, UI/UX.
- ✅ **Domain Mighan**: image/video/music tools, creative workflows.

Sumber wajib **open** (CC BY/SA, CC0, MIT, public domain, open API). Cek di note 152 untuk daftar sumber pre-audit.

## B3. Apa yang TIDAK boleh dipelajari

- ❌ Data personal user/owner (portfolio pribadi, ID dokumen, medical record).
- ❌ Konten copyrighted penuh (reproduce 30+ kata verbatim = rule 11 CLAUDE.md).
- ❌ Konten yang melanggar Maqashid (merusak 5 tujuan).
- ❌ Hate speech, misinformation terverifikasi, adversarial prompt injection dari web.
- ❌ Face/biometric data (lihat harmful_content_safety system prompt).

## B4. Validasi per-konten sebelum masuk corpus

```
Konten baru (dari connector) → pipeline cek:
  1. Sanad complete? (URL + tanggal akses + lisensi)
  2. Epistemic tier — ahad (single source), mutawatir (multi-source),
     atau opinion? Label wajib.
  3. Maqashid pass? (scoring 5 dimensi)
  4. Overlap check — similarity dengan note existing. >0.55 → update note
     lama, jangan buat baru.
  5. Identity mask — tidak ada PII, nama owner, IP server.
  6. Bahasa — allowed (Indonesia/Inggris/Arab).
Hanya yang pass semua → masuk `brain/public/research_notes/NNN_*.md`.
```

Fail = log ke `.data/sidix_learn_rejected.jsonl` + alasan.

## B5. Self-evaluation loop

Tiap minggu (cron weekly) jalankan:

- `vision_tracker.py` — audit vs 6 pillar visi. Skor per-pillar 0–1.0.
- `epistemic_validator.py` — sample 50 Q&A terakhir. Hitung rate maqashid_passes, 4-label present, sanad complete.
- `/gaps/detect` — update list gap untuk siklus berikut.
- Post hasil ke `docs/weekly_audit_YYYY-WW.md` (buat file per minggu).

Alert kalau:
- `maqashid_pass_rate < 0.8` → halt auto-retrain sampai investigasi.
- `epistemic_label_missing > 5%` → prompt review.
- `vision_pillar_regressed > 0.1` → trigger curriculum adjust.

## B6. Auto-retrain LoRA (Layer 3 → Layer 1 update)

Setiap 7 hari (atau 500 training pair baru, mana duluan):

```
1. corpus_to_training.py → collect pair dari research_notes/ approved.
2. Dedup vs pair existing di dataset.
3. Upload ke dataset storage (Kaggle dataset / server local).
4. auto_lora.py → trigger training job (Kaggle GPU T4 atau mitra).
5. Validasi adapter baru:
   - Eval test set (held-out Q&A dengan golden answer)
   - Compare metrics vs adapter existing
   - Regressi? → rollback, jangan deploy
   - Improve? → backup adapter lama, swap adapter baru
6. pm2 restart sidix-brain → load adapter baru.
7. Smoke test: 5 pertanyaan kanonik → verify konsistensi persona +
   epistemic labels + sanad.
8. Log ke ledger + note research `NNN_retrain_YYYY-MM-DD.md`.
```

Rollback criteria: evaluasi regressi ≥5% di metric kunci, atau user report quality drop.

## B7. Self-evolving (long-term, note 41)

Protocol untuk capability yang butuh extension Layer 1:

1. **Image gen**: self-host SDXL/FLUX di GPU VPS. `image_gen.py` module baru. Register sebagai tool `generate_image` (permission restricted awal).
2. **Vision input**: self-host Qwen2.5-VL / InternVL. `multi_modal_router.py` sudah ada — wire ke endpoint `/agent/chat` accept image upload.
3. **Audio**: Whisper.cpp (ASR) + Piper (TTS). `audio_capability.py` sudah registry — pasang deps + wire.
4. **Distributed training**: DiLoCo + model merging (DARE/TIES) untuk federated learning dengan kontributor GPU.
5. **Continual learning tanpa catastrophic forgetting**: SPIN (Self-Play fine-tune), MemGPT-style memory hierarchy.

Tiap extension = research note + prototype + validation test set + rollout gradual.

## B8. Guardrails (wajib saat self-modify)

Ketika SIDIX modify code-nya sendiri (via `workspace_write` tool):
- **Allowlist path**: hanya `brain/public/research_notes/auto_learn/`, `.data/sidix_memory/`, `.data/learn_agent/`. Tidak boleh edit `apps/brain_qa/brain_qa/*.py`, `SIDIX_USER_UI/`, `docs/` (kecuali LIVING_LOG append).
- **Require human approval** untuk code change di atas 20 baris atau touch core module (`local_llm`, `agent_tools`, `agent_serve`).
- **Audit log** semua modify ke `.data/sidix_self_modify.jsonl` dengan hash chain.
- **Rollback capability**: backup file sebelum modify.
- **Epistemic check**: modifikasi yang diusulkan harus punya justifikasi `[FACT]` atau `[DECISION]`, bukan `[SPECULATION]`.

## B9. Kapan SIDIX harus minta bantuan user (escalation)

- Gap tidak bisa diisi dari sumber open (subject matter expert needed).
- Metric regressi setelah retrain > threshold.
- Conflict antara sumber faktual (butuh manusia arbitrate).
- Keputusan strategic (plan A/B/C/D — butuh user pick).
- Resource exhausted: disk full, quota API habis, GPU tidak available.

Cara escalate: append ke `docs/open_questions.md` + notif admin via endpoint `/admin/notif` (kalau sudah ada) atau webhook.

## B10. Identity preservation

SIDIX tetap SIDIX walaupun tumbuh:
- Persona tetap 5 (MIGHAN/TOARD/FACH/HAYFAR/INAN).
- Prinsip tetap: sidq, sanad, tabayyun, maqashid, IHOS.
- Masking tetap: tidak expose owner, backbone, IP.
- Bahasa default Indonesia, multilingual support via translation (bukan swap persona).
- Copyright dan etika tetap wajib.

Perubahan identity = keputusan user eksplisit, bukan self-directed.

---

# PART C — Quick Reference

## Command cek state cepat
```bash
curl -s https://ctrl.sidixlab.com/health | python3 -m json.tool
curl -s https://ctrl.sidixlab.com/agent/tools | python3 -c "import json,sys; print(len(json.load(sys.stdin)['tools']), 'tools')"
curl -s https://ctrl.sidixlab.com/sidix/curriculum/status
curl -s https://ctrl.sidixlab.com/sidix/lora/status
curl -s https://ctrl.sidixlab.com/hafidz/verify
```

## Struktur repo yang penting
```
apps/brain_qa/brain_qa/          # backend Python, 89 modul
  agent_tools.py                 # TOOL_REGISTRY (Layer 2)
  agent_serve.py                 # FastAPI, 171 endpoint
  agent_react.py                 # ReAct loop
  local_llm.py                   # Layer 1 core
  learn_agent.py + connectors/   # Layer 3
  daily_growth.py                # Layer 3 orchestrator
  auto_lora.py                   # Layer 3 retrain
SIDIX_USER_UI/                   # frontend Vite (LOCKED)
SIDIX_LANDING/                   # landing sidixlab.com
brain/public/research_notes/     # corpus — 159+ notes
docs/                            # governance + handoff
```

## File yang HARUS dibaca sesi baru (5 menit)
1. `CLAUDE.md`
2. `docs/DEVELOPMENT_RULES.md` (file ini)
3. `docs/SIDIX_CAPABILITY_MAP.md`
4. `docs/HANDOFF_<terbaru>.md`
5. `tail -100 docs/LIVING_LOG.md`

## Commit etiquette
```bash
git commit -m "feat(scope): deskripsi

Penjelasan kenapa.

Co-Authored-By: <agent> <noreply@anthropic.com>"
```

---

**Sanad file ini:**
- Disetujui user 2026-04-19 sebagai response atas kebutuhan anti-amnesia lintas-sesi.
- Supersedes klaim bertentangan di handoff lama.
- Revisi: jangan edit langsung, buat PR dengan ADR di `docs/decisions/` dan link ke file ini.
