# 101 — Inventori Folder D:\skills

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** DOC  
**Tanggal:** 2026-04-18  
**Author:** Claude Sonnet 4.6 (agen SIDIX)

---

## Apa

Dokumen ini adalah inventori lengkap dari folder `D:\skills` yang berisi koleksi skill dan plugin resmi Anthropic, plugin knowledge-work, serta plugin komunitas yang tersedia di mesin lokal.

---

## Struktur Tingkat Atas

```
D:\skills\
├── anthropics-skills/          ← Skill resmi Anthropic
├── claude-plugins-official/    ← Plugin resmi Claude (code-review, feature-dev, dll)
├── knowledge-work-plugins/     ← Plugin domain kerja (engineering, data, marketing, dll)
├── claude-code/                ← Plugin khusus Claude Code
├── claude-plugins-cursor-parity.json
├── link_cursor_skills.py
└── link_skill_aliases.py
```

---

## Detail Per Sub-folder

### 1. `anthropics-skills/skills/` — 17 skill

| Skill | Deskripsi Singkat |
|-------|------------------|
| algorithmic-art | Membuat seni generatif dengan kode |
| brand-guidelines | Panduan brand dan identitas visual |
| canvas-design | Desain canvas interaktif |
| claude-api | Bangun aplikasi dengan Claude API (termasuk prompt caching) |
| doc-coauthoring | Ko-penulisan dokumen kolaboratif |
| docx | Buat dan edit file Word (.docx) |
| frontend-design | Desain dan implementasi UI frontend |
| internal-comms | Komunikasi internal perusahaan |
| mcp-builder | Bangun MCP server baru |
| pdf | Operasi PDF (merge, split, extract, OCR) |
| pptx | Buat presentasi PowerPoint |
| skill-creator | Buat skill Claude baru |
| slack-gif-creator | Buat GIF untuk Slack |
| theme-factory | Buat tema visual |
| web-artifacts-builder | Bangun web artifact interaktif |
| webapp-testing | Testing aplikasi web |
| xlsx | Manipulasi spreadsheet Excel |

**Format skill:** setiap skill berisi `skill.md` (instruksi + contoh) dan kadang file referensi tambahan (`REFERENCE.md`, `FORMS.md`, dll).

---

### 2. `claude-plugins-official/plugins/` — 31 plugin

Plugin resmi untuk Claude Code. Beberapa yang paling relevan:

| Plugin | Jenis | Isi |
|--------|-------|-----|
| code-review | command | `/code-review` — structured review |
| feature-dev | command + agents | `/feature-dev` + 3 agent spesialis (architect, explorer, reviewer) |
| hookify | skill | Buat hook otomatisasi |
| agent-sdk-dev | skill | Develop Claude Agent SDK |
| playground | skill | Eksperimen cepat |
| security-guidance | skill | Review keamanan kode |
| math-olympiad | skill | Selesaikan soal matematika olimpiade |
| mcp-server-dev | skill | Buat MCP server |
| session-report | skill | Buat laporan sesi kerja |
| skill-creator | skill | Buat skill baru |
| plugin-dev | skill | Develop plugin Claude |
| frontend-design | skill | Desain UI |

Plugin lain: clangd-lsp, gopls-lsp, pyright-lsp, ruby-lsp, rust-analyzer-lsp, typescript-lsp, kotlin-lsp, swift-lsp, lua-lsp, jdtls-lsp, csharp-lsp, php-lsp (semua adalah Language Server Protocol wrappers).

---

### 3. `knowledge-work-plugins/` — 18 domain

Plugin untuk knowledge work profesional:

| Domain | Skill Tersedia |
|--------|---------------|
| engineering | architecture, code-review, debug, deploy-checklist, documentation, incident-response, standup, system-design, tech-debt, testing-strategy |
| data | analyze, build-dashboard, create-viz, data-context-extractor, data-visualization, explore-data, sql-queries, statistical-analysis, validate-data, write-query |
| marketing | brand-review, campaign-plan, competitive-brief, content-creation, email-sequence, performance-report, seo-audit |
| design | accessibility-review, design-critique, design-handoff, design-system, research-synthesis, user-research, ux-copy |
| sales | call-prep, call-summary, competitive-intelligence, create-an-asset, daily-briefing, draft-outreach, forecast, pipeline-review |
| legal | brief, compliance-check, legal-response, legal-risk-assessment, meeting-briefing, signature-request, triage-nda, vendor-check |
| finance | audit-support, close-management, financial-statements, journal-entry, reconciliation, sox-testing, variance-analysis |
| human-resources | comp-analysis, draft-offer, interview-prep, onboarding, org-planning, people-report, performance-review, policy-lookup, recruiting-pipeline |
| operations | capacity-plan, change-request, compliance-tracking, process-doc, process-optimization, risk-assessment, runbook, status-report, vendor-review |
| product-management | brainstorm, competitive-brief, metrics-review, roadmap-update, sprint-planning, stakeholder-update, write-spec |
| customer-support | customer-escalation, customer-research, draft-response, kb-article, ticket-triage |
| enterprise-search | digest, knowledge-synthesis, search, search-strategy, source-management |
| bio-research | instrument-data-to-allotrope, nextflow-development, scvi-tools, single-cell-rna-qc, scientific-problem-selection |
| productivity | memory-management, start, task-management, update |
| pdf-viewer | annotate, fill-form, open, sign, view-pdf |
| partner-built | apollo (enrich-lead, prospect, sequence-load), brand-voice, common-room, slack, zoom-plugin |
| cowork-plugin-management | create-cowork-plugin, cowork-plugin-customizer |

---

## File Pendukung

- **`claude-plugins-cursor-parity.json`** — Mapping skill Claude ↔ Cursor IDE
- **`link_cursor_skills.py`** — Script untuk menautkan skill ke Cursor
- **`link_skill_aliases.py`** — Script alias skill

---

## Pattern Umum Skill

Setiap skill memiliki format YAML frontmatter + instruksi Markdown:

```markdown
---
name: nama-skill
description: Kapan skill ini dipanggil
argument-hint: "<argumen>"
---

# Instruksi utama skill

## Cara Kerja
...
```

---

## Relevansi untuk SIDIX

Dari inventori ini, tools yang langsung relevan dan diimplementasikan ke `builtin_apps.py`:

1. **Math tools** → dari pola calculator/statistics di skill math-olympiad
2. **Text tools** → dari pola text manipulation di berbagai skill
3. **Data tools** → dari skill sql-queries, data-context-extractor
4. **Islamic tools** → SIDIX-native (tidak ada di folder, tapi kebutuhan utama Mighan)
5. **Web tools** → stub berdasarkan pola web-search di berbagai knowledge-work skill

---

## Keterbatasan

- Folder `D:\claude skill and plugin` **kosong** saat di-scan (kemungkinan folder placeholder)
- Skill tidak bisa dipanggil langsung sebagai fungsi Python — mereka adalah instruksi Markdown untuk Claude
- Library Python spesifik (pypdf, reportlab, dll) perlu di-install terpisah
