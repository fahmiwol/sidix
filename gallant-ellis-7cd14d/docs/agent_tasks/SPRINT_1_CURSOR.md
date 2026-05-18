# Task bundle untuk Cursor — Sprint 1 (T1.2) + Sprint 2 (T2.1–T2.4)

**Agent:** Cursor (IDE-based).
**Branch per task:** `cursor/sprint-1/t1.2-sanad-ranker`, `cursor/sprint-2/tX-name`.
**Prasyarat baca (wajib 5 menit sebelum mulai):**
- [CLAUDE.md](../../CLAUDE.md) — aturan permanen + UI LOCK + IDENTITAS SIDIX 3-layer.
- [docs/NORTH_STAR.md](../NORTH_STAR.md) — tujuan akhir + release strategy + lock apa yang tidak berubah.
- [docs/DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md) — aturan mengikat (Part A: agent eksternal).
- [docs/MULTI_AGENT_WORKFLOW.md](../MULTI_AGENT_WORKFLOW.md) — rules koordinasi antar-agent.
- [brain/public/research_notes/163_*.md](../../brain/public/research_notes/163_rekomendasi_jalur_a_baby_sprint_detail.md) — detail sprint 1–3.

**Prinsip non-negosiasi:**
- Standing alone: tidak import vendor AI API (OpenAI/Anthropic/Gemini).
- Tidak edit: CLAUDE.md, NORTH_STAR, DEVELOPMENT_RULES, SIDIX_CAPABILITY_MAP, SIDIX_ROADMAP_2026, SIDIX_USER_UI/index.html (UI LOCK struktur).
- LIVING_LOG: append-only.
- Bahasa: Indonesia untuk dokumentasi user-facing, English OK di kode.
- 4-label epistemik di research note: `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]`.

---

## 🎯 Task 1 — T1.2: Sanad-Based Ranker di `search_corpus`

### Tujuan
Modifikasi `search_corpus` supaya hasil BM25 di-rerank berdasarkan **sanad tier** sumbernya. Sumber primer (Al-Quran, hadits shahih, paper peer-review, kitab klasik) diangkat ke atas; sumber aggregator (blog, AI-generated content) di-demote.

### Kenapa ini penting
Differensiator SIDIX #1 vs GPT/Claude: **transparansi epistemologis**. Sanad ranking adalah implementasi konkret prinsip ini di lapis retrieval.

### Context file
- `apps/brain_qa/brain_qa/query.py` — query engine BM25
- `apps/brain_qa/brain_qa/indexer.py` — build index + frontmatter parse
- `brain/public/research_notes/` — contoh markdown dengan frontmatter
- `apps/brain_qa/brain_qa/agent_tools.py:88` — `_tool_search_corpus` wrapper

### Tasks terperinci

- [ ] **T1.2.1** — Tambah field `sanad_tier` di parse frontmatter markdown (`indexer.py`). Nilai allowed: `primer` | `ulama` | `peer_review` | `aggregator` | `unknown` (default).
- [ ] **T1.2.2** — Tambah helper di `query.py`: `apply_sanad_weight(doc, base_score)` → `base_score * sanad_weight`. Weight: primer=1.5, ulama=1.3, peer_review=1.2, aggregator=0.9, unknown=1.0.
- [ ] **T1.2.3** — Integrate ke `answer_query_and_citations` (atau equivalent) — rerank setelah BM25 score.
- [ ] **T1.2.4** — Update 5 research note sampel dengan `sanad_tier:` di frontmatter untuk testing. Pilih:
  - `03_rag_chunking_markdown_aware.md` → `peer_review`
  - `41_sidix_self_evolving_distributed_architecture.md` → `peer_review`
  - `157_capability_audit_standing_alone_2026_04_19.md` → `primer` (internal authoritative)
  - `161_ai_llm_generative_claude_dan_differensiasi_sidix.md` → `primer`
  - `162_framework_brain_hands_memory_peta_kemampuan_sidix.md` → `primer`
- [ ] **T1.2.5** — Unit test di `apps/brain_qa/tests/test_sanad_ranker.py` — 3 test case minimum: primer > peer_review, ranking stability, unknown default.
- [ ] **T1.2.6** — Research note `brain/public/research_notes/164_sprint1_t1_2_sanad_ranker.md` — dokumentasi implementasi + rationale + sanad tier philosophy.

### Definition of Done
- [ ] `search_corpus` return hasil dengan urutan terpengaruh sanad weight (verify via test).
- [ ] 5 note punya frontmatter `sanad_tier`.
- [ ] Unit test pass.
- [ ] Research note 164 ditulis.
- [ ] `docs/LIVING_LOG.md` di-append dengan tag `[IMPL]` + `[TEST]`.
- [ ] `docs/SIDIX_CAPABILITY_MAP.md` — tambah baris untuk sanad ranking di section kapabilitas aktif.
- [ ] PR opened, body link ke task file ini, request review `@claude`.

### File boleh edit
- `apps/brain_qa/brain_qa/query.py`
- `apps/brain_qa/brain_qa/indexer.py`
- `apps/brain_qa/brain_qa/agent_tools.py` (jika butuh wire tambahan)
- `apps/brain_qa/tests/test_sanad_ranker.py` (baru)
- `brain/public/research_notes/*.md` (tambah frontmatter saja di 5 note yang disebut)
- `brain/public/research_notes/164_*.md` (baru)
- `docs/LIVING_LOG.md` (append saja)
- `docs/SIDIX_CAPABILITY_MAP.md` (tambah 1 baris, jangan rewrite)

### File JANGAN sentuh
- `CLAUDE.md`, `docs/NORTH_STAR.md`, `docs/DEVELOPMENT_RULES.md`, `docs/SIDIX_ROADMAP_2026.md`, `docs/MULTI_AGENT_WORKFLOW.md`.
- `apps/brain_qa/brain_qa/local_llm.py`, `agent_react.py`.
- `SIDIX_USER_UI/index.html` struktur (UI LOCK).
- Research note existing (kecuali 5 note yang disebut untuk tambah frontmatter).

### Verifikasi
```bash
# Test lokal
pytest apps/brain_qa/tests/test_sanad_ranker.py -v

# Smoke test via curl
curl -s https://ctrl.sidixlab.com/agent/tool-call \
  -H "Content-Type: application/json" \
  -d '{"tool":"search_corpus","args":{"query":"IHOS maqasid","k":5}}'
# Verify: hasil teratas adalah note dengan sanad_tier=primer
```

### Report back
Setelah PR merge, tulis `docs/agent_tasks/reports/T1.2_report_cursor.md` dengan:
- Diff summary (file changed, line added/removed).
- Hasil unit test.
- Sample query + hasil ranking (before/after).
- Blocker atau edge case yang ditemukan.

---

## 🎯 Task 2 — T1.4: Frontend tampilkan sanad tier + concept_graph hasil

**Catatan:** T1.4 backend sudah dikerjakan Claude (endpoint `/concept_graph/query` live). Task frontend:

### Tujuan
Update SIDIX_USER_UI supaya kalau SIDIX panggil `concept_graph` atau `search_corpus` dengan sanad tier, hasil ditampilkan dengan badge visual (primer=emas, ulama=perak, peer_review=biru, aggregator=abu, unknown=netral).

### File boleh edit
- `SIDIX_USER_UI/src/main.ts`
- `SIDIX_USER_UI/src/api.ts` (kalau perlu tambah tipe citation)
- `SIDIX_USER_UI/src/lib/*` (kalau perlu helper baru)
- NO perubahan ke `index.html` struktur — hanya tambah CSS class kalau butuh.

### Tasks
- [ ] Tambah tipe di `api.ts`: `Citation { type: string; sanad_tier?: string; url?: string; title?: string }`.
- [ ] Di render citation (cari di main.ts), tambah badge berdasarkan `sanad_tier`.
- [ ] Style minimal pakai class Tailwind existing + kustom kalau perlu.
- [ ] Screenshot demo → masukkan ke report.

### DoD
- Build `npm run build` sukses, no TS error.
- Demo: chat query → jawaban dengan citation badge tier muncul.

---

## 🎯 Task 3 — Sprint 2 bundle (start paralel kalau Sprint 1 sudah submit PR)

Sprint 2 target (2 minggu): Python executor wrap untuk matematika + data analysis.

### T2.1 `math_solve` tool (SymPy)
- File: `apps/brain_qa/brain_qa/agent_tools.py` — tambah `_tool_math_solve`.
- Input: `expression` (str), `operation` (diff/integrate/solve/simplify), `variable` (default 'x').
- Output: LaTeX + plain text + (optional) step-by-step.
- Register di TOOL_REGISTRY permission `open`.
- Unit test: 5 case (derivative, integral, algebra equation, limit, simplify).

### T2.2 `data_analyze` tool (pandas)
- File: `apps/brain_qa/brain_qa/data_analyze.py` (baru) + wire di `agent_tools.py`.
- Input: `path` (CSV/XLSX di workspace), `question` (natural language).
- Logic: load via pandas → describe schema → user question → decide analysis (groupby, corr, trend) → execute dalam `code_sandbox` → return markdown + sample table.
- Unit test dengan fixture CSV.

### T2.3 `plot_generate` tool (matplotlib)
- File: `plot_generate.py` (baru) + tool wrapper.
- Input: `data` (list atau path CSV), `kind` (bar/line/scatter/heatmap), `title`, `xlabel`, `ylabel`.
- Save PNG ke `.data/generated_plots/` dengan hash filename.
- Return path file.

### T2.4 Frontend file upload (CSV/XLSX)
- `SIDIX_USER_UI/src/main.ts` — button "Upload file" di textarea area.
- Backend endpoint `/workspace/upload` (minta Claude tambah kalau belum ada).
- Detect mime type, save ke `.data/sidix_workspace/anon/<hash>.csv`.
- Attach info file ke chat context supaya ReAct bisa panggil `data_analyze`.

### DoD Sprint 2
- 3 tool baru live (`math_solve`, `data_analyze`, `plot_generate`). TOOL_REGISTRY: 19 → 21.
- Frontend bisa upload CSV → chat → SIDIX analyze + plot.
- Research note 165 sprint 2 review.

---

## 📞 Komunikasi

- Stuck? Tulis di `docs/open_questions.md` dengan tag `@claude` atau `@user`.
- Conflict dengan prinsip? Buka ADR di `docs/decisions/` sebelum ubah arah.
- Scope drift? Stop, tulis pertanyaan, tunggu konfirmasi.

**JANGAN tebak-tebak.** Prinsip lock dari North Star: kalau ragu standing-alone atau tidak, jangan pakai library vendor AI.

---

## Signature
Task file dibuat: 2026-04-19 oleh Claude sebagai koordinator Sprint 1–2.
Review: setelah T1.2 PR merge → lanjut T2.1.
