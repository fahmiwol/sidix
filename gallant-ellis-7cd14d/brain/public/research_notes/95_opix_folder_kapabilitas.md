# 95 — D:\OPIX (SocioStudio): Kapabilitas & Sinergi dengan SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Task:** Scan, ekstrak, dan konversi D:\OPIX ke training pairs + corpus SIDIX  
**Nomor:** 95  

---

## Apa Itu D:\OPIX?

`D:\OPIX` adalah project **SocioStudio** — platform manajemen konten social media berbasis AI untuk agensi dan freelancer yang mengelola banyak client sekaligus. Tagline: *"Multi-Client Social Media Management Platform with AI-Powered Content Creation"*.

**Stack:** Next.js 14 + TypeScript, PostgreSQL (Supabase), Redis (Upstash), BullMQ, Playwright, Stripe.

**Status:** Dalam fase desain/awal development (April 2026). Dokumentasi lengkap (PRD, ERD, API Spec, Backend Arch, Roadmap) sudah ada.

---

## Struktur Folder

| File/Folder | Isi |
|-------------|-----|
| `01_PRD.md` (14KB) | Product Requirements Document lengkap |
| `02_ERD.md` (26KB) | Entity Relationship Diagram + SQL schema |
| `03_USER_STORIES.md` (25KB) | User stories semua role |
| `04_API_SPEC.md` (27KB) | REST API specification |
| `05_BACKEND_ARCH.md` (29KB) | Backend architecture, deployment, monitoring |
| `06_ROADMAP.md` (17KB) | Product roadmap Q1-Q4 2026 |
| `sociostudio/` | Next.js app (frontend + API routes) |
| `sociostudio/lib/publisher/` | Multi-strategy social media publisher |
| `sociostudio/app/api/ai/caption/` | AI caption generation (SSE streaming) |

**Total file (tanpa node_modules):** 40 file, semua relevan.

---

## Skill / Logic Yang Bisa Diekstrak

### 1. AI Caption Generation dengan Brand Context
File `sociostudio/app/api/ai/caption/route.ts` mengimplementasikan:

```typescript
function buildBrandContext(clientProfile): string
// Membangun system prompt dengan: nama brand, industri, tone, warna, bahasa,
// target audience, content pillars, blacklist words

function getPlatformInstructions(platform: string): string
// Platform-specific instructions: Instagram, Twitter/X, Threads, TikTok,
// YouTube, Facebook, LinkedIn
```

Pattern ini sangat relevan untuk SIDIX: cara inject brand context ke LLM prompt.

### 2. Multi-Strategy Social Media Publisher
`sociostudio/lib/publisher/` memiliki 5 strategi publisher:

| File | Strategi |
|------|----------|
| `playwright-publisher.ts` | Browser automation (Playwright) |
| `http-publisher.ts` | Direct HTTP API ke platform |
| `ayrshare-publisher.ts` | Via Ayrshare aggregator service |
| `direct-publisher.ts` | Direct official API |
| `browser-publisher.ts` | Headless browser fallback |

Pattern Strategy Pattern ini bisa diadopsi SIDIX untuk publisher module.

### 3. Database Schema Multi-Tenant
ERD mencakup 17 entitas dengan Row Level Security (RLS):
- `organizations` → `users` → `clients`
- `client_brand_guidelines`, `client_objectives`, `client_strategy`
- `social_accounts`, `client_credentials`
- `posts`, `post_platforms`, `media_assets`
- `research_sessions`, `caption_templates`
- `usage_logs`, `billing_subscriptions`, `audit_logs`

Schema ini adalah referensi bagaimana membangun multi-tenant SaaS dengan isolasi data yang ketat.

### 4. Background Job Architecture (BullMQ)
`05_BACKEND_ARCH.md` mendokumentasikan:
- `publish-queue` → job publish konten ke semua platform
- `ai-generate-queue` → async AI generation (image, video)
- `analytics-sync-queue` → pull analytics dari platform
- `notification-queue` → email + in-app notifications

Pattern queue-based architecture untuk operasi async yang lama.

### 5. OAuth Multi-Platform
`sociostudio/lib/oauth/platform-config.ts` (13KB) — konfigurasi OAuth untuk Instagram, TikTok, Facebook, X, Threads, YouTube, LinkedIn. Termasuk scope, endpoints, token refresh logic.

### 6. Product Documentation Komprehensif
6 dokumen dengan total ~140KB yang mencakup:
- Business goals (target 50 org, MRR Rp 50 juta dalam 6 bulan)
- User personas (Agency Owner, Social Media Manager, Content Creator)
- API endpoints 30+
- Monitoring dengan Prometheus + Grafana
- Error handling strategy
- Rate limiting per tier

---

## Kapabilitas Yang Diekstrak

| Tipe | Jumlah |
|------|--------|
| knowledge (dari docs MD) | 102 |
| logic (dari TypeScript code) | 26 |
| pattern (dari configs/schemas) | 11 |
| **Total** | **139** |

---

## Perbedaan OPIX vs SIDIX

| Dimensi | OPIX (SocioStudio) | SIDIX |
|---------|-------------------|-------|
| **Domain** | Social media management SaaS | General AI platform / brain |
| **User** | Agensi, freelancer, marketing team | Developer, knowledge worker, researcher |
| **AI Role** | AI sebagai *tools* (caption gen, scheduling) | AI sebagai *inference engine* (RAG, reasoning) |
| **Stack** | Next.js + TypeScript + Supabase | Python FastAPI + BM25 RAG |
| **Deployment** | Cloud SaaS (multi-tenant) | Self-hosted + VPS |
| **Monetization** | Subscription (Starter/Pro/Agency) | API usage / internal tool |
| **Agent** | Tidak ada multi-agent (monolithic API) | ReAct agent dengan tool calling |

---

## Bagaimana OPIX dan SIDIX Bisa Saling Melengkapi?

### 1. SIDIX sebagai "Brain" untuk SocioStudio
SocioStudio saat ini menggunakan Anthropic API langsung (dengan `apiKey: process.env.ANTHROPIC_API_KEY`). SIDIX bisa menggantikan peran ini dengan:
- Inference lokal melalui `brain_qa` (tanpa vendor API cost)
- Brand context disimpan di corpus SIDIX (bukan di clientProfile JSON sementara)
- Multi-agent research untuk konten (Iris-style research pipeline)

### 2. Social Publishing Skill di SIDIX
Publisher strategies dari OPIX bisa dijadikan **tool/skill SIDIX**:
```python
# SIDIX skill: publish ke social media
def sidix_publish_social(platform, content, client_credentials) -> dict
```

### 3. Caption Generation Training Data
Caption generation logic dari OPIX (brand context builder + platform instructions) adalah training data berkualitas tinggi untuk SIDIX. Format instruction-tuning:
```
Instruction: Buat caption Instagram untuk brand [X] dengan tone [Y]
Output: [caption dengan hashtag]
```

### 4. ERD sebagai Knowledge Base SIDIX
17-entitas schema SocioStudio adalah pengetahuan tentang arsitektur SaaS multi-tenant yang bisa diakses user SIDIX via RAG ("Bagaimana cara merancang tabel untuk multi-tenant dengan RLS?").

### 5. Product Strategy Knowledge
PRD, roadmap, dan user stories adalah knowledge tentang cara membangun product SaaS Indonesia yang bisa digunakan SIDIX untuk membantu product manager atau founder lain.

---

## Keterbatasan

- OPIX menggunakan Anthropic API langsung (`@anthropic-ai/sdk`) — tidak kompatibel dengan aturan SIDIX "no vendor AI API in inference pipeline". Perlu adapter jika ingin diintegrasikan.
- SocioStudio masih tahap awal, belum ada production data nyata
- Publisher strategies membutuhkan browser/Playwright yang berat — perlu pertimbangan resource

---

## File Output
- Corpus: `brain/public/sources/mighan_opix/opix_NNNN_*.txt` (139 items)
- Training pairs: sudah masuk `.data/harvest/mighan_opix_pairs.jsonl`
- Processor: `apps/brain_qa/brain_qa/multi_folder_processor.py`
