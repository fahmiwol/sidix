# Mulai di sini — pintu masuk tunggal

**Mighan-brain-1** adalah proyek open-source (MIT) untuk **brain pack** + **AI workspace** bertahap: korpus Markdown terstruktur, RAG + sitasi, memori/evaluasi, dan nanti UI/agent — tanpa janji “latih LLM dari nol” sebagai target utama.

Halaman ini untuk **siapa saja** yang baru masuk: kontributor korpus, developer tool, pengguna lokal, atau **agen AI** — supaya tidak harus membaca repo secara acak.

---

## 1) Baca dulu (urutan ±15 menit)

| Urutan | File | Isi |
|--------|------|-----|
| 1 | **[Status hari ini](STATUS_TODAY.md)** + **[Rencana eksekusi](10_execution_plan.md)** | Snapshot fokus + checklist fase & “kapan perlu kamu”. |
| 2 | [Visi & misi](01_vision_mission.md) | Kenapa repo ini ada, nilai, batasan realistis. |
| 3 | [PRD](02_prd.md) | Masalah, tujuan, persona, requirement MVP+. |
| 4 | [Roadmap](06_roadmap.md) | Fase 0–4 waktu tinggi. |
| 5 | [Spesifikasi brain pack](08_mighan_brain_1_spec.md) | Struktur `brain/`, format dataset, privasi vs publik. |

**Opsional sesuai peran:**

- Kontributor korpus → [CONTRIBUTING.md](CONTRIBUTING.md), [brain/public/README.md](../brain/public/README.md), [sources/CONTRIBUTION_POLICY.md](../brain/public/sources/CONTRIBUTION_POLICY.md).
- Arsitektur/data model → [05_architecture.md](05_architecture.md), [04_erd.md](04_erd.md).
- User stories → [03_user_stories.md](03_user_stories.md).
- Governance OSS → [07_open_source_governance.md](07_open_source_governance.md).
- Plugin/tool → [plugins_skills_connectors.md](plugins_skills_connectors.md).
- Desain UI (Google AI Studio / Gemini) → [11_prompt_google_ai_studio_mvp_ui.md](11_prompt_google_ai_studio_mvp_ui.md) — prompt + menu + ERD ringkas.
- Konteks untuk **Claude** (Code / project / chat) → [12_prompt_claude_project_context.md](12_prompt_claude_project_context.md) — apa yang dibangun + aturan + path repo + **inferensi/own-stack (bukan default Claude API)**.
- Sprint singkat **SIDIX / inference lokal** (±2 jam, scope realistis) → [SPRINT_SIDIX_2H.md](SPRINT_SIDIX_2H.md).
- Fondasi **SIDIX + IHOS** dan lapisan AI (RAG, ReAct, tool gate) → [SIDIX_FUNDAMENTALS.md](SIDIX_FUNDAMENTALS.md); latihan kurikulum coding → [SIDIX_CODING_CURRICULUM_V1.md](SIDIX_CODING_CURRICULUM_V1.md).

---

## 2) Prolog (latar ringkas)

Banyak orang ingin **satu AI** yang mengenal cara berpikir, referensi, dan konteks mereka — tanpa mengunci data di satu vendor, dan dengan jejak yang bisa diaudit. **Brain pack** di repo ini adalah jawaban tahap pertama: dokumen publik/pribadi, dataset (memory cards, QA pairs), dan prinsip pengetahuan yang bisa di-index dan dikutip.

Repo ini **tidak** menjanjikan produk jadi dalam satu file README saja. Yang ada adalah **dokumen produk** (visi, PRD, roadmap), **korpus** di `brain/public/` (dan pola untuk `brain/private/` yang tidak di-commit), serta **kode MVP lokal** di `apps/brain_qa/` untuk index, tanya, kurasi, ledger, dan eksperimen storage — semuanya dirancang agar komunitas bisa ikut **bertahap**: data dulu, tool dengan review ketat.

Identitas proyek di sisi publik disapa **Mighan**; detail identitas pribadi pemilik korpus tetap di luar git bila perlu.

---

## 3) Di mana “yang jalan” vs “yang direncanakan”

| Lapisan | Lokasi | Catatan |
|---------|--------|---------|
| Rencana & kontrak produk | `docs/01`–`08`, roadmap | Sumber kebenaran untuk *apa* yang dibangun. |
| Status operasional singkat | [STATUS_TODAY.md](STATUS_TODAY.md) | **Update manual** saat fokus berubah. |
| Riwayat perubahan fitur | [CHANGELOG.md](CHANGELOG.md) | Ringkas per tanggal/scope. |
| Log kerja agen / detail uji | [LIVING_LOG.md](LIVING_LOG.md) | Append-only, pakai tag `TEST:` `FIX:` dll. (lihat header file itu). |
| Rencana prioritas | [10_execution_plan.md](10_execution_plan.md) | Fase A–E; sinkron dengan `STATUS_TODAY`. |
| Korpus & metodologi | `brain/public/principles/`, `research_notes/` | Mis. metodologi riset: `principles/08_learning_methodology.md`. |
| MVP lokal (CLI) | `apps/brain_qa/` | Lihat README di folder itu untuk perintah. |

---

## 4) Untuk agen AI (Cursor, Claude Code, dll.)

**Inti (jangan lompat):** [STATUS_TODAY.md](STATUS_TODAY.md) → [AGENTS.md](../AGENTS.md) (preferensi + fakta workspace + aturan log) → cuplikan terbaru [LIVING_LOG.md](LIVING_LOG.md).

**Lanjutan sesuai tugas:** [CLAUDE.md](../CLAUDE.md) (SSOT Claude: North Star, MASTER_ROADMAP, DEVELOPMENT_RULES, keamanan); [NORTH_STAR.md](NORTH_STAR.md), [MASTER_ROADMAP_2026-2027.md](MASTER_ROADMAP_2026-2027.md), [SIDIX_CAPABILITY_MAP.md](SIDIX_CAPABILITY_MAP.md).

**Setelah tugas berarti:** tambah satu atau lebih baris di [LIVING_LOG.md](LIVING_LOG.md) dengan tag wajib (`TEST:` `FIX:` `IMPL:` `UPDATE:` `DOC:` `DECISION:` `ERROR:` `NOTE:` — lihat header file itu).

**Jangan** commit isi `brain/private/` atau secret; ikuti [CONTRIBUTING.md](CONTRIBUTING.md) untuk tier A vs B.

---

## 5) Lisensi

MIT — lihat `LICENSE` di root repo.
