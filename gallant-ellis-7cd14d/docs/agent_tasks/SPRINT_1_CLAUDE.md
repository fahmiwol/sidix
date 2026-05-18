# Task bundle untuk Claude — Sprint 1 progress + upcoming

**Agent:** Claude (terminal/SSH, governance guardian).
**Branch:** `claude/determined-chaum-f21c81`.

---

## ✅ Completed (Sprint 1, 2026-04-19)

### T1.1 — Wire `concept_graph` tool
- Commit `6b38731`.
- Reuse `brain_synthesizer.build_knowledge_graph()`.
- Mode A (summary graph) + Mode B (BFS 1–2 hop by concept).
- Live: `tools_available: 18`.

### T1.3 — Fix cron LearnAgent + corpus index
- Generate `BRAIN_QA_ADMIN_TOKEN` di `/opt/sidix/apps/brain_qa/.env` (48 hex chars).
- Install cron: daily 04:00 UTC `POST /learn/run`, 04:30 UTC `POST /learn/process_queue`.
- Restart PM2 sidix-brain.
- Verify: corpus_doc_count 0 → **1149**.

### T1.4 — Endpoint `/concept_graph/query`
- Tambah route `GET /concept_graph/query?concept=&depth=&max_related=` di `agent_serve.py`.
- Public read-only (tidak butuh admin token — endpoint deskriptif bukan destruktif).
- Delegate ke `call_tool("concept_graph", ...)`.

### Governance docs (hari ini)
- `docs/NORTH_STAR.md` — tujuan akhir + release strategy v0.1→v3.0.
- `docs/SIDIX_ROADMAP_2026.md` — 4 stage × sprint 2 minggu + framework Brain+Hands+Memory.
- `docs/DEVELOPMENT_RULES.md` — 22 rules (Part A agent eksternal + Part B self-dev SIDIX).
- `docs/SIDIX_CAPABILITY_MAP.md` — SSoT kapabilitas (17 → 18 tool).
- `docs/MULTI_AGENT_WORKFLOW.md` — koordinasi Claude/Cursor/Antigravity.
- `brain/public/research_notes/161` konsep AI/LLM + 8 differentiator.
- `brain/public/research_notes/162` framework Brain+Hands+Memory.
- `brain/public/research_notes/163` rekomendasi Jalur A + sprint detail.

---

## 🚀 Upcoming — Claude ownership

### Pre-Sprint 2 / selama Cursor kerjain T1.2

**C-01 Review PR Cursor T1.2** (sanad ranker)
- Baca diff end-to-end.
- Smoke test endpoint di VPS (`curl /agent/tool-call search_corpus`).
- Validasi DoD checklist.
- Kalau OK → merge ke main; kalau tidak → request changes via PR comment.

**C-02 Review PR Antigravity research notes**
- Cek format: 4-label epistemik + sanad chain present?
- Cek alignment dengan standing-alone (tidak ada rekomendasi vendor AI API).
- Cek rekomendasi konkret (bukan "tergantung").
- Merge atau request revision.

**C-03 Setup endpoint `/workspace/upload`** (untuk Cursor T2.4 frontend upload CSV)
- Endpoint `POST /workspace/upload` dengan multipart.
- Validasi: mime type (csv/xlsx/pdf/txt/md), max 10 MB.
- Save ke `.data/sidix_workspace/<session_id>/<hash>.<ext>`.
- Return path + metadata (size, mime, rows jika CSV).
- Quota per session.

**C-04 Weekly audit setup (DEVELOPMENT_RULES Part B-5)**
- Endpoint `/research/weekly-audit` — generate `docs/weekly_audit_YYYY-WW.md`.
- Cron `0 4 * * 0` (Minggu 04:00 UTC).
- Content: vision_tracker score, epistemic validator sample, maqashid pass rate.

**C-05 Sync branch dengan PR merges**
- Tiap PR Cursor/Antigravity merge → Claude sync `main` ke branch-nya:
  ```
  git checkout claude/determined-chaum-f21c81
  git merge main
  ```
- Resolve conflict kalau ada.

### Sprint 1 closure

**C-06 Research note 164 sprint 1 review**
- File: `brain/public/research_notes/164_sprint1_review.md` (atau 167 jika Cursor ambil 164-166).
- Content: apa yang berhasil, blocker, lesson learned, DoD checklist.

**C-07 Update SIDIX_CAPABILITY_MAP + LIVING_LOG**
- Capability baru: concept_graph, sanad ranking (setelah merge Cursor PR).
- LIVING_LOG: entry closure sprint 1.

**C-08 Launch v0.2 preparation** (setelah Sprint 3 done)
- Demo video 60 detik
- Blog post draft
- Threads series (hook/detail/cta)
- Changelog + GitHub release

---

## 🎯 Sprint 2 (setelah Sprint 1 done)

Claude kerjain yang butuh SSH atau backend integration heavy:

- **C-S2-01** Endpoint `/workspace/upload` (sudah list di C-03)
- **C-S2-02** Integration test end-to-end sprint 2 tools (setelah Cursor submit)
- **C-S2-03** Deploy + smoke test pasca Cursor merge

Cursor kerjain tool-nya, Claude wire + test + deploy.

## 🎯 Sprint 3 (butuh output research Antigravity dulu)

**Decision gate:** setelah 4 research note Antigravity merge, Claude bikin ADR pick GPU provider + model + deployment pattern.

Execution Sprint 3 bagi ulang antara Claude (infra + deploy) dan Cursor (image_gen.py + prompt_enhancer_nusantara.py code).

---

## 📞 Komunikasi Claude ke user

Setiap sprint selesai:
1. Update user via chat dengan ringkasan + link commit.
2. Tulis summary di `docs/agent_tasks/reports/`.
3. Tanya user: lanjut sprint berikut? atau ada feedback?

Setiap ambigu / blocker:
- Flag di `docs/open_questions.md`.
- Pause eksekusi.
- Tunggu user response.

---

## Signature
Task file dibuat + di-update: 2026-04-19.
Branch aktif: `claude/determined-chaum-f21c81`.
Owner konteks: Claude (pastikan tidak melenceng dari North Star).
