# Opener Prompt — Sesi Baru SIDIX (2026-04-29 onward)

> Salin **seluruh isi prompt** di section "PROMPT UNTUK COPY-PASTE" ke chat sesi baru.

---

## PROMPT UNTUK COPY-PASTE

```
Halo Claude. Saya Fahmi, founder SIDIX. Saya melanjutkan sesi sebelumnya
yang berakhir 2026-04-28 late evening setelah marathon 14 sprint
(Sprint 25 → 38) dengan commit terakhir `1c27100`.

Sebelum aksi apapun, BACA URUT dokumen ini (sanad continuity, jangan
skip):

1. CLAUDE.md — instruksi permanen, 4 OPERATING PRINCIPLES, 10 hard rules
2. docs/FOUNDER_JOURNAL.md — META-RULE: bahasa saya METAFORA & ANALOGI
   (jurus 1000 bayangan, hafidz, sanad validator, otak manusia, dst —
   spirit > literal mechanic)
3. docs/SESSION_STATE_2026-04-28_late_evening.md —
   state snapshot lengkap sesi sebelumnya
4. docs/SIDIX_NORTH_STAR.md — SIDIX = Penemu Inovatif Kreatif Digital
   (BUKAN chatbot, BUKAN ChatGPT alternative, BUKAN auto-complete besar)
5. docs/SIDIX_DEFINITION_20260426.md — formal definition LOCKED 2026-04-26
6. docs/SIDIX_CANONICAL_V1.md — single SOT consolidate notes 224+228+248+
   277+278+279+280
7. docs/SIDIX_CONTINUITY_MANIFEST.md — 19 distinctive concepts dengan status
8. docs/ROADMAP_SPRINT_36_PLUS.md — innovation-scored roadmap Sprint 36-46+
9. brain/public/research_notes/248_pivot_canonical_self_evolving_creative_agent.md
   — canonical pivot LOCKED
10. brain/public/research_notes/282_synthesis_fs_study_optimization_analysis.md
    — synthesis dokumen riset founder dengan adoption matrix
11. tail -100 docs/LIVING_LOG.md — recent actions

Setelah itu, verifikasi state production VPS via SSH:

```
ssh sidix-vps "pm2 status sidix-brain && \
  curl -s http://localhost:8765/audit/stats | jq && \
  crontab -l | grep -E 'sidix_|reflect' | wc -l"
```

Expected:
- sidix-brain ONLINE pid 21
- /audit/stats returns 1 entry (lesson-2026-04-27, hash 70c1ead4a5e4)
- 9 cron entries staggered LIVE

----------------------------------------------------------------------

## STATE SAYA SEKARANG

SIDIX state per commit `1c27100`:

✅ LIVE production:
- 6-layer anti-halusinasi defense (Sprint 28b → 34J), Q3 "Presiden
  Indonesia" → Prabowo verified (bukan Jokowi halusinasi)
- Hybrid retrieval BM25+Dense+RRF +6% Hit@5 measured (Sprint 25-27c)
- Reflection Cycle cron 02:30 UTC daily (Sprint 36) — Pillar 3
  Self-Improvement HIDUP eksplisit
- Hafidz Ledger MVP (Sprint 37) — endpoint /audit/stats + /audit/{id} LIVE
- Tool Synthesis MVP module + CLI deployed (Sprint 38) — detector source
  adapt pending Sprint 38b
- 9 cron jobs staggered (always_on, radar, classroom, worker,
  aku_ingestor, visioner, ODOA, warmup_runpod, reflect_day)
- post_deploy_chmod hook auto-preserve permissions
- Ollama systemd tune (NUM_PARALLEL=1, KEEP_ALIVE=10m)
- fact_extractor.py 9 entity types coverage

⚠ Pending:
- Sprint 38b: detector source adapt (VPS observation log format `kind` ≠
  `action` field. Solusi recommend: parse Sprint 36 reflect_day output
  yang sudah ekstrak "Repeated Tool Sequences" di lesson template)
- Sprint 39: Quarantine 7-day sandbox + auto-test
- Sprint 40: Owner Telegram (@migharabot verify) atau email summary
- Sprint 13: DoRA persona stylometry (note 248 mandate, parallel feasible)

----------------------------------------------------------------------

## 4 OPERATING PRINCIPLES (LOCKED — internalize sebelum action)

1. **ANTI-HALUSINASI** — claim grounded di basis konkret (cite line, file
   path, command output, test result). "Saya tidak yakin" > tebak.
2. **JAWABAN HARUS BENER** — correctness > speed untuk topik sensitif.
   Multi-source validation untuk fakta/data. Web_search untuk current events.
3. **IDE SAYA DIOLAH SAMPAI SEMPURNA** — multi-dimensi (5 persona × wisdom
   × KITABAH iterasi). BUKAN reduce-to-simpler. Iterasi sampai sesuai spirit.
4. **RESPOND CEPAT · TEPAT · RELEVAN** — tier-aware latency, no off-topic
   verbose, konteks user-specific.

## META-RULE PALING PENTING

Bahasa saya = **METAFORA dan ANALOGI**, BUKAN spec literal:
- "Jurus 1000 bayangan" = paralel multi-perspective fan-out (count fleksibel)
- "Hafidz mengingat" = memory recall pattern (BUKAN religious memorization)
- "Sanad validator" = multi-dimensi validation gate (BUKAN hadith chain harfiah)
- "Otak manusia" = arsitektur inspiration (BUKAN literal neural mapping)
- "Quran statis-generative" = pola arsitektur (BUKAN religious adoption)
- "Penemu Inovatif Kreatif" = spirit cipta keluar template (BUKAN literal "Tesla")

Spirit > mechanic. Multiple implementasi valid asalkan spirit terjaga.

----------------------------------------------------------------------

## LOOP MANDATORY CLAUDE.md 6.5 (setiap sprint)

CATAT (memulai) → PUSH PULL DEPLOY → TESTING → ITERASI → CATAT →
REVIEW QA → VALIDASI → OPTIMASI → CATAT FINAL.

Setiap step di-record di docs/LIVING_LOG.md dengan tag yang jelas.

----------------------------------------------------------------------

## TUGAS HARI INI

Pilih SATU dari 4 opsi (innovation-scored di ROADMAP_SPRINT_36_PLUS.md):

A) **Sprint 38b** — Detector Source Adapt (compound dengan Sprint 36)
   - Effort: 1-2 hari
   - Logic: parse Sprint 36 reflect_day output (lesson_drafts) yang sudah
     extract "Repeated Tool Sequences" section, atau hook ke run_react
     untuk write tool sequence ke dedicated track file
   - Compound: tool_synthesis.py existing + reflect_day output
   - Outcome: detector match real VPS data → propose_skill bisa generate
     proposals nyata

B) **Sprint 39** — Quarantine + Sandbox Promote Flow
   - Effort: 1-2 minggu
   - Logic: skills/quarantine/ structure, auto-test pada 3 supporting
     episodes, 7-day timer, owner approve hook
   - Compound: Sprint 38 proposals input
   - Outcome: skill pertama bisa di-test sandbox sebelum production

C) **Sprint 40** — Owner Daily Summary (Telegram atau Email)
   - Effort: 1-2 minggu
   - Logic: cron daily 08:00 WIB kirim ringkasan: 3 lesson drafts +
     N skill proposals + anomaly. Inline approve/edit/reject.
   - Compound: Sprint 36 + 37 + 38 produce drafts ready
   - Outcome: governance manual VPS edit → 5 menit di HP pagi hari

D) **Sprint 13** — DoRA Persona Stylometry (note 248 mandate)
   - Effort: 3-5 hari (Kaggle T4 training)
   - Logic: synthetic 1500 Q&A per persona via classroom_pairs +
     external teachers, fine-tune LoRA rank-16 untuk UTZ + ABOO duluan,
     deploy ke RunPod, A/B blind test
   - Compound: parallel ke Sprint 38b/39, tidak block satu sama lain
   - Outcome: 5 persona distinct di WEIGHT level (bukan akting prompt) —
     differentiator brand level

Saya rekomendasi untuk pickup pertama: **A (Sprint 38b)**, karena:
- Effort kecil (1-2 hari)
- Compound natural dengan Sprint 36 yang sudah deployed
- Unblocks Sprint 39 + 40 downstream
- Realisasi konkret Pillar Pencipta (note 278)

Tapi keputusan akhir di tangan saya. Kalau saya bilang "lanjut C" atau
"D dulu", agent jalan sesuai pilihan.

----------------------------------------------------------------------

## ANTI-DRIFT CHECKLIST (sebelum eksekusi)

Sebelum mulai sprint baru, verifikasi:
- [ ] Sudah baca CLAUDE.md + note 248 + handoff + canonical V1
- [ ] Internalize META-RULE metafora-analogi
- [ ] Pre-Exec Alignment Check (CLAUDE.md 6.4) — cite pivot terbaru
- [ ] Tidak melanggar 10 hard rules (no vendor LLM API, 5 persona LOCKED,
      sanad chain kept, MIT, self-hosted, dll)
- [ ] Compound dengan existing sprint, jangan bikin baru kalau sudah ada
- [ ] Spirit dari konsep saya dijaga (bukan literal interpretation)

----------------------------------------------------------------------

## KOMUNIKASI SETUP

- Bahasa: **Bahasa Indonesia** (kode/komentar boleh English)
- Tone: terus terang, jangan basa-basi, "respond cepat tepat relevan"
- Format: short responses, gunakan headers + tables kalau perlu, citation
  file:line pakai markdown link
- Setiap directive saya yang substansial → append ke FOUNDER_JOURNAL.md
  SEKARANG (jangan tunda) dengan quote verbatim
- Setiap output kerja → catat di LIVING_LOG.md tagged

Setelah baca semua + verifikasi state, kamu confirm dengan 3-line
ringkasan:
1. Status SIDIX sekarang (apa yang LIVE)
2. Sprint mana yang dipilih + alasan singkat
3. Step pertama eksekusi

Lalu tunggu konfirmasi saya untuk gas. Jangan langsung jalan tanpa
pre-exec alignment check.

GAS!
```

---

## CARA PAKAI

1. **Buka tab/window Claude baru** (clean context)
2. **Salin semua isi** di section "PROMPT UNTUK COPY-PASTE" (mulai dari
   "Halo Claude. Saya Fahmi..." sampai "GAS!")
3. **Paste** ke chat sesi baru sebagai message pertama
4. Agent akan:
   - Baca semua dokumen wajib (~15-20 menit reading)
   - Verifikasi state VPS via SSH
   - Confirm 3-line ringkasan + pilih sprint
   - Tunggu konfirmasi
5. Setelah confirm, agent jalan loop CLAUDE.md 6.5 untuk sprint pilihan

---

## YANG DIHIDUPI OLEH PROMPT INI

✅ **Continuity** — agent baca semua canonical doc dulu, tidak start dari blank  
✅ **Vision discipline** — META-RULE metafora + 10 hard rules + 4 OPERATING PRINCIPLES locked  
✅ **State awareness** — state production sekarang explicit (LIVE vs pending)  
✅ **Sprint clarity** — 4 opsi pilihan dengan rekomendasi + justifikasi  
✅ **Anti-drift checklist** — pre-exec alignment check before action  
✅ **Communication contract** — bahasa, tone, format, journal append discipline  
✅ **Confirmation gate** — agent tidak gas duluan tanpa user konfirm pilihan

---

## PERINGATAN

- **Jangan modifikasi** "META-RULE" section (locked founder mandate)
- **Jangan skip** baca canonical V1 + handoff (akan drift kalau skip)
- Kalau context sesi baru hampir penuh lagi (>85%), bikin handoff lagi
  + sesi baru — pattern compound continuity

---

## OUTPUT TARGET SESI BARU

Sebelum context terisi 50%, hasil yang diharapkan:
- 1 sprint baru deployed (Sprint 38b atau 39 atau 40 atau 13)
- Loop CLAUDE.md 6.5 lengkap (catat-test-iterasi-validasi-catat)
- Local + git + VPS seamless commit
- LIVING_LOG entry comprehensive
- Status: 38 sprint → 39 sprint cumulative

Jangan ngebut 14 sprint dalam satu sesi seperti hari ini — itu anomalous.
Realistic 1-3 sprint per sesi (kalau sprint kecil) atau 1 sprint dalam
multiple sesi (kalau sprint besar seperti DoRA).

---

**End of opener prompt template.** Lock 2026-04-28 late evening.
