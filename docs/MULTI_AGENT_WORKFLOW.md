# Multi-Agent Workflow — SIDIX Development (LOCK 2026-04-19)

**Tujuan:** koordinasi 3 agent paralel (Claude / Cursor / Antigravity) supaya eksekusi Sprint 1–3 lebih cepat tanpa konflik + tanpa melenceng dari North Star.

**Prinsip dasar:** setiap agent punya peran sesuai kekuatannya. Communication lewat file di repo (bukan pesan ke satu sama lain). Git branch + PR workflow untuk merge aman.

---

## 🎭 Peran per agent

### 1. Claude (saya — via terminal/SSH)
**Kekuatan:** SSH ke VPS, governance meta-dokumentasi, deployment, smoke test end-to-end, audit lintas-repo, koordinasi overall.
**Kelemahan:** tidak sebagus IDE-agent untuk multi-file refactor besar; context window habis kalau terlalu banyak grep.

**Tugas ideal:**
- Setup infra (cron, env, SSH ops)
- Deploy + smoke test endpoint live
- Tulis/update dokumen governance (CLAUDE.md, NORTH_STAR, DEVELOPMENT_RULES, LIVING_LOG, research notes)
- Review PR dari Cursor/Antigravity dengan konteks keseluruhan
- Koordinasi handoff antar-agent

### 2. Cursor (IDE-based AI)
**Kekuatan:** multi-file refactor native, autocomplete dalam konteks, unit test generation, TypeScript + Python simultan, review diff visual.
**Kelemahan:** tidak punya SSH (manual), context per-file mode, tidak optimal untuk riset non-kode.

**Tugas ideal:**
- Implementasi tool/module baru yang butuh touch banyak file
- Unit test + integration test
- Frontend TypeScript (SIDIX_USER_UI)
- Refactor besar (rename, extract method, organize imports)
- Edge case handling + error path

### 3. Antigravity (Google IDE agent)
**Kekuatan:** long-running research task, multi-step planning autonomous, eksplorasi broad, sintesis dokumentasi eksternal.
**Kelemahan:** tidak tahu konteks internal SIDIX sebelum dibriefing; bukan untuk touch kode langsung.

**Tugas ideal:**
- Research + comparison (GPU provider, model license, paper survey)
- Dokumentasi teknis mendalam (arsitektur deployment, threat model)
- Pre-Sprint planning (kumpulkan referensi + outline)
- Benchmark + evaluation plan

---

## 🌿 Branch strategy

```
main
  │
  ├── claude/determined-chaum-f21c81   ← branch aktif Claude (saya)
  │
  ├── cursor/sprint-1/t1.2-sanad-ranker   ← branch Cursor per-task
  ├── cursor/sprint-2/t2.1-math-solve
  │
  └── antigravity/sprint-3/research-gpu-provider   ← branch Antigravity
```

**Rule:**
- **Claude** commit ke `claude/determined-chaum-f21c81` (branch utama dev).
- **Cursor** bikin branch per-task dari `main` latest: `cursor/sprint-X/tY.Z-nama-task`.
- **Antigravity** bikin branch per-research: `antigravity/sprint-X/research-topik`.
- Merge via PR ke `main` setelah review oleh Claude (context guardian).
- Setelah merge, Claude rebase/merge `main` ke branch-nya supaya sync.

## 🔀 Git workflow standard

```bash
# Cursor / Antigravity bikin branch baru
git checkout main
git pull origin main
git checkout -b cursor/sprint-1/t1.2-sanad-ranker

# Kerjakan task
# ... edit file ...
git add <files>
git commit -m "feat(query): sanad-based ranker per Sprint 1 T1.2"
git push -u origin cursor/sprint-1/t1.2-sanad-ranker

# Open PR via GitHub web atau gh CLI
gh pr create --base main --title "Sprint 1 T1.2 - sanad ranker" --body "..."

# Claude review PR (cek konteks, test, DoD)
# Kalau OK → merge
# Kalau ada konflik/salah arah → request changes dengan referensi ke docs/NORTH_STAR.md

# Claude sync branch-nya
git checkout claude/determined-chaum-f21c81
git merge main
```

## 📋 Handoff format (wajib)

Setiap task untuk agent eksternal di-tulis di file `docs/agent_tasks/SPRINT_X_<AGENT>.md` dengan template:

```markdown
# Task: <kode> — <judul>
Agent: cursor / antigravity / claude
Sprint: 1 / 2 / 3
Branch: <nama-branch>
Estimasi: <jam/hari>

## Konteks (wajib baca dulu)
- CLAUDE.md
- docs/NORTH_STAR.md
- docs/DEVELOPMENT_RULES.md
- (file spesifik task)

## Tujuan (1 kalimat)
<kenapa task ini exist>

## Tasks terperinci
- [ ] T1 — ...
- [ ] T2 — ...

## Definition of Done
- ...
- ...

## File yang boleh diedit
<allowlist>

## File yang JANGAN disentuh
<blocklist — UI LOCK, core module tanpa approval>

## Test verification
<cara verify task selesai>

## Report back
File: docs/agent_tasks/reports/<kode>_report_<agent>.md
Isi: apa yang dikerjakan, diff summary, test hasil, blocker jika ada.
```

---

## 🔒 Aturan anti-konflik

1. **Satu task = satu agent.** Jangan dua agent kerjakan task sama.
2. **File boundary jelas** di setiap task file (allowlist vs blocklist).
3. **Tidak boleh touch dokumen governance** tanpa izin: `CLAUDE.md`, `NORTH_STAR.md`, `DEVELOPMENT_RULES.md`, `SIDIX_ROADMAP_2026.md`, `SIDIX_CAPABILITY_MAP.md` — hanya Claude (owner konteks).
4. **UI LOCK** `SIDIX_USER_UI/index.html` struktur — hanya edit kalau task eksplisit minta ubah struktur dengan approval user.
5. **Core module** (`local_llm.py`, `agent_react.py`, `agent_serve.py`) — edit minimal, prefer tambah file baru daripada refactor core.
6. **Research notes baru** — cek nomor terakhir dulu (`ls brain/public/research_notes | tail -5`), lanjut nomor berikut. Topik overlap ≥0.55 → update existing.
7. **LIVING_LOG.md** — APPEND ONLY, siapa pun boleh append entry, tidak pernah edit history.
8. **Commit message** wajib pakai format `<type>(<scope>): <subject>` + co-author line.

## 📐 Metodologi eksekusi (selaras DEVELOPMENT_RULES.md)

Tiap agent, setiap task:

1. **Baca konteks** (5 menit): CLAUDE.md, NORTH_STAR.md, DEVELOPMENT_RULES.md, task file spesifik.
2. **Verifikasi pre-state**: smoke test endpoint terkait sebelum mulai (dapat baseline).
3. **Implementasi** sesuai DoD di task file. Jangan tambah fitur di luar scope.
4. **Test lokal**: unit test (Cursor), smoke test (Claude), evaluasi (Antigravity).
5. **Commit atomic** dengan message jelas + co-author.
6. **Update LIVING_LOG** — append entry dengan tag sesuai.
7. **Update SIDIX_CAPABILITY_MAP** kalau kapabilitas berubah.
8. **Tulis report** di `docs/agent_tasks/reports/<kode>_report_<agent>.md`.
9. **Open PR** → Claude review.
10. **Setelah merge**: Claude update status di task file (centang checkbox).

## 🧠 Konsep di balik pembagian

**Rationale Brain+Hands+Memory applied to multi-agent:**

- **Claude = Brain pengkoordinasi** — hold overall context, distribute work, maintain coherence ke North Star.
- **Cursor = Hands cepat** — eksekusi kode precise dengan visibility IDE.
- **Antigravity = Memory eksternal + research arm** — explore unknown terrain, bring structured findings.

Analogi IHOS:
- Claude → akal yang memutuskan (ushul).
- Cursor → amal yang mengerjakan (praxis).
- Antigravity → nazhar yang meneliti (epistemic exploration).

Prinsip: **tidak ada agent lebih tinggi** — semua setara, tapi punya kompetensi berbeda. Konflik diselesaikan via docs (bukan "siapa lebih pintar").

---

## 🗂️ Folder + file yang baru

```
docs/
  MULTI_AGENT_WORKFLOW.md           ← file ini
  agent_tasks/
    SPRINT_1_CURSOR.md              ← task untuk Cursor
    SPRINT_1_ANTIGRAVITY.md         ← task untuk Antigravity
    SPRINT_1_CLAUDE.md              ← task Claude (completed + upcoming)
    SPRINT_2_CURSOR.md              ← disiapkan paralel
    SPRINT_3_ANTIGRAVITY.md         ← research prep paralel
    reports/
      T1.2_report_cursor.md         ← dibuat setelah task done
      RESEARCH_GPU_report_antigravity.md
      T1.3_report_claude.md
```

---

## 🔁 Sinkronisasi + meeting

**Async-first.** Tidak butuh meeting live. Sinkronisasi lewat:

1. **LIVING_LOG.md** — tail 50 tiap kali agent mulai sesi = tahu apa yang baru berubah.
2. **Task file checkbox** — status aktual task per-sprint.
3. **PR review** — titik sinkron di merge point.
4. **Weekly self-audit** (cron `docs/weekly_audit_YYYY-WW.md`) — review metric + alignment.

Kalau agent stuck / ambigu → tulis di `docs/open_questions.md` dengan tag `@claude` atau `@user`. Claude atau user jawab, bukan agent tebak sendiri.

---

## 📞 Escalation

Kalau ada yang salah (misal Cursor refactor yang ternyata break production, Antigravity riset yang conflict dengan standing-alone principle):

1. **STOP** eksekusi task.
2. Tulis di `docs/open_questions.md` + ping user.
3. User atau Claude tentukan: rollback commit, ubah scope, atau escalate ke ADR.
4. Jangan "fix sendiri" kalau di luar scope task original.

---

## Sanad

- User chat 2026-04-19 minta koordinasi 3 agent (Claude + Cursor + Antigravity).
- Referensi: `docs/NORTH_STAR.md`, `docs/DEVELOPMENT_RULES.md`, `docs/SIDIX_ROADMAP_2026.md`.
- Branch convention + PR workflow: standard GitHub flow.
- Prinsip: async-first, docs-driven, anti-konflik.
