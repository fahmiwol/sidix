# 104 — Projects Folder Archetypes: Pemetaan Proyek Nyata di D:\Projects

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Task:** Track L — scan D:\Projects, identifikasi pola berulang  
**Dibuat oleh:** Claude (Sonnet 4.6) bersama Fahmi  

---

## Apa Ini?

Research note ini mendokumentasikan hasil scan folder `D:\Projects` milik Fahmi (ekosistem Tiranyx). Tujuannya adalah mengidentifikasi **pola archetype proyek** yang bisa dijadikan template SIDIX untuk membantu user memulai proyek baru.

---

## Proyek yang Ditemukan

| Folder | Jenis | Tech Stack | Status |
|--------|-------|-----------|--------|
| `tiranyx/tiranyx-web` | Web fullstack CMS + admin | Next.js 14, TypeScript, Prisma, SQLite | Partial (source hilang) |
| `Galantara` | Game sosial 3D + landing | Three.js, Socket.io, Express, HTML/CSS | Aktif (galantara.io) |
| `bank-tiranyx` | Ledger/wallet service | Fastify, TypeScript, Prisma, PostgreSQL | Partial |
| `Shopee-API-Gateway` | OAuth proxy / API gateway | Hono, TypeScript, Prisma, PostgreSQL | Context only |
| `Mighan-Building-Dashboard` | Dashboard pipeline visual | Python Flask, Pillow, HTML5 Canvas | Partial (app.py ada) |
| `Omnyx` | Chatbot omnichannel SaaS | NestJS, Next.js, PostgreSQL, Prisma | Context only |
| `Dompet-tiranyx` | Wallet frontend | Next.js | Partial |
| `AGENT-HUB` | AI governance hub | Markdown docs | Lengkap (docs only) |
| `AgentSkills-Library` | Skills library | Markdown | README only |
| `raddict` | UI design mockup | PDF only | Concept stage |
| `Mighan` | Workspace templates | Context only | Context only |
| `ABRA` | Web app (belum terpetakan) | TBD | Unknown |
| `Raumah-tiranyx` | Web app (Next.js) | Next.js, TypeScript | Partial |
| `Uhud-tiranyx` | Web app (Next.js) | Next.js, TypeScript | Partial |

---

## Pattern yang Berulang

### 1. Next.js + Prisma (Paling dominan)
Hampir semua web app Tiranyx memakai Next.js (App Router) + TypeScript + Prisma. Ini mencerminkan preferensi stack yang konsisten.

**Proyek:** tiranyx-web, Dompet-tiranyx, Raumah-tiranyx, Uhud-tiranyx, Omnyx (frontend).

### 2. TypeScript Everywhere
Semua proyek JavaScript/TypeScript. Tidak ada JavaScript vanilla kecuali game Galantara (ES modules tanpa bundler untuk performa browser).

### 3. PostgreSQL via Prisma
Database pilihan untuk semua backend produksi. SQLite hanya untuk development/lokal ringan.

### 4. Monorepo partial
Beberapa proyek punya `apps/`, `src/`, `packages/` — tapi belum monorepo penuh. Galantara punya `apps/web/` + `galantara-server/` tapi masih dikelola manual.

### 5. Python untuk AI/pipeline
Flask (Mighan-Building-Dashboard), FastAPI (brain_qa SIDIX). Python dipakai untuk semuanya yang berhubungan AI atau pipeline data.

### 6. Docs-first ketika source hilang
Banyak proyek hanya tersisa CONTEXT.md setelah source code hilang. Ini bukti pentingnya dokumentasi sebagai "code backup terakhir".

---

## Archetype yang Diekstrak

Berdasarkan scan ini, 8 archetype didefinisikan di `apps/brain_qa/brain_qa/project_archetypes.py`:

1. `nextjs_fullstack` — Next.js 14 + Prisma + SQLite/PostgreSQL
2. `threejs_game_multiplayer` — Three.js + Socket.io + Express
3. `fastify_prisma_api` — Fastify + Prisma + PostgreSQL
4. `hono_edge_api` — Hono + Prisma (OAuth/gateway)
5. `flask_canvas_dashboard` — Flask + HTML5 Canvas
6. `nestjs_nextjs_saas` — NestJS + Next.js (SaaS platform)
7. `fastapi_rag_ai` — FastAPI + BM25 + Ollama (AI backend)
8. `vite_react_ts` — Vite + React + TypeScript (SPA)

---

## Keterbatasan

- Banyak source code hilang — analisis stack hanya dari CONTEXT.md dan file yang masih ada
- `ABRA`, `raddict` belum terpetakan dengan jelas
- Stack `Raumah-tiranyx` dan `Uhud-tiranyx` diasumsikan dari pola `.next/` folder

---

## Implikasi untuk SIDIX

SIDIX bisa menggunakan `project_archetypes.py` untuk:
1. Merekomendasikan stack ketika user bertanya "mau buat [jenis proyek]"
2. Generate project plan otomatis (sprint, env vars, deploy steps)
3. Menjadi "template mesin" agar user tidak mulai dari nol setiap kali
