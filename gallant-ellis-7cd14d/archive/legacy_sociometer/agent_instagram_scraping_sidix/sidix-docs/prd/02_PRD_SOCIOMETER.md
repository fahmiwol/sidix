# PRD: SIDIX-SocioMeter — Product Requirements Document

**Versi:** 1.0  
**Status:** FINAL  
**Klasifikasi:** Product Requirements — Arsitektur Ekosistem

---

## 1. RINGKASAN PRODUK

### 1.1 Definisi Produk

SIDIX-SocioMeter adalah **sistem ekspansi terdistribusi** yang memungkinkan SIDIX (AI agent self-hosted berbasis IHOS) untuk:

1. **Menjadi tool/plugin** yang dapat di-install di AI platforms lain (ChatGPT, Claude, Cursor, dll) via MCP (Model Context Protocol)
2. **Mengumpulkan data** dari jutaan interaksi melalui Chrome Extension (`sociometer-browser`)
3. **Berkembang secara mandiri** melalui sistem self-training (Jariyah harvesting loop)
4. **Mencapai kemampuan generatif** yang komprehensif: creative, branding, marketing, SEO, SEM, advertising, social media, monetize, design, content creation, video, 3D, coding

### 1.2 Tagline

> *"SIDIX di mana-mana. Ilmu yang mengalir. Standing alone, tapi tidak sendirian."*

### 1.3 Target User

| Segment | Karakteristik | Kebutuhan |
|---------|--------------|-----------|
| **UMKM Creator** | 1-5 orang, budget terbatas, aktif di social media | Competitor analysis, content creation, branding |
| **Digital Marketer** | Freelance/agency, mengelola multiple clients | Campaign automation, reporting, multi-platform |
| **Developer** | Solo/team, butuh AI coding assistant | Code generation, review, debugging |
| **AI Enthusiast** | Early adopter, self-hosted advocate | Plugin untuk AI agent mereka, data privacy |
| **Enterprise** | Tim marketing besar, compliance-sensitive | White-label, on-premise, custom integration |

### 1.4 User Stories

#### UMKM Creator
- Sebagai pemilik UMKM fashion, saya ingin melihat analisis kompetitor Instagram saya, supaya saya tahu strategi konten yang works
- Sebagai content creator, saya ingin generate caption + visual untuk posting harian, supaya saya konsisten tanpa burnout

#### Digital Marketer
- Sebagai digital marketer, saya ingin monitoring 10 kompetitor di multi-platform, supaya saya tidak ketinggalan tren
- Sebagai agency owner, saya ingin white-label report untuk client saya, supaya terlihat profesional

#### Developer
- Sebagai developer, saya ingin SIDIX sebagai MCP tool di Cursor, supaya saya bisa generate code dengan sanad chain
- Sebagai indie hacker, saya ingin auto-generate landing page dari brief, supaya saya cepat launch

#### AI Enthusiast
- Sebagai AI enthusiast, saya ingin install SIDIX di ChatGPT via GPT Actions, supaya saya bisa pakai Maqashid filter di conversational AI
- Sebagai privacy advocate, saya ingin data saya tetap di local, supaya tidak training model orang lain

---

## 2. FITUR PRODUK

### 2.1 Fitur Core

#### F-001: SIDIX-SocioMeter MCP Server
**Prioritas:** P0  
**Deskripsi:** MCP server yang mengekspos 35+ tools SIDIX sebagai callable functions untuk AI agents lain  
**Acceptance Criteria:**
- [ ] 6 core tools tersedia via MCP: `nasihah_creative`, `nasihah_analyze`, `nasihah_design`, `nasihah_code`, `nasihah_raudah`, `nasihah_learn`
- [ ] Support transport: stdio, streamable-http, SSE
- [ ] Auto-discovery: AI agent bisa lihat daftar tools + deskripsi
- [ ] Maqashid filter otomatis pada setiap output
- [ ] Sanad chain tersedia di metadata response

#### F-002: SIDIX-SocioMeter Browser (Chrome Extension)
**Prioritas:** P0  
**Deskripsi:** Chrome Extension untuk universal data collection + SIDIX assistant injection  
**Acceptance Criteria:**
- [ ] Network interception untuk Instagram, TikTok, YouTube, LinkedIn
- [ ] Sidebar panel dengan persona selector (AYMAN/ABOO/OOMAR/ALEY/UTZ)
- [ ] Auto-suggest saat mengetik di Gmail, WhatsApp Web, Twitter
- [ ] One-click generate: reply, caption, ad copy, image
- [ ] Offline buffer dengan sync ke backend
- [ ] Privacy: local-first, opt-in per platform, anonymization

#### F-003: Jariyah Harvesting Loop
**Prioritas:** P1  
**Deskripsi:** Sistem self-training yang mengubah setiap interaksi menjadi training pair  
**Acceptance Criteria:**
- [ ] Auto-capture: input → output → feedback → context
- [ ] Sanad Pipeline: dedup (MinHash) → CQF scoring → validation → storage
- [ ] Mizan Repository: unified storage (PostgreSQL + MinIO)
- [ ] Tafsir Engine: auto-trigger QLoRA retrain saat corpus > 5,000 pairs
- [ ] Naskh Handler: conflict resolution corpus baru vs lama

#### F-004: Raudah Multi-Agent (v0.2)
**Prioritas:** P1  
**Deskripsi:** Multi-agent orchestration dengan TaskGraph DAG  
**Acceptance Criteria:**
- [ ] TaskGraph dengan dependency tracking
- [ ] POST `/raudah/run` endpoint
- [ ] GET `/raudah/status/{session_id}` progress tracking
- [ ] SSE stream untuk real-time progress
- [ ] Auto-select specialists berdasarkan task type

#### F-005: Maqashid Filter (v2.1)
**Prioritas:** P0  
**Deskripsi:** Mode-based output filter yang sudah di-wire ke pipeline  
**Acceptance Criteria:**
- [ ] Wire ke `run_react()` sebagai middleware layer
- [ ] 4 mode: CREATIVE, ACADEMIC, IJTIHAD, GENERAL
- [ ] Auto-select mode berdasarkan persona + task type
- [ ] Block harmful content dengan 0% false negative
- [ ] Tag output dengan Maqashid score

#### F-006: Naskh Handler (v1.1)
**Prioritas:** P1  
**Deskripsi:** Conflict resolution corpus dengan `is_frozen` flag  
**Acceptance Criteria:**
- [ ] Wire ke `learn_agent.py` corpus pipeline
- [ ] Sanad-tier: primer > ulama > peer-reviewed > aggregator
- [ ] Auto-merge untuk non-conflicting updates
- [ ] Manual review flag untuk conflicts kompleks
- [ ] Preserve `is_frozen` items dari overwrite

### 2.2 Fitur Generative (Roadmap)

| Kode | Fitur | Fase | Status |
|------|-------|------|--------|
| G-001 | Vision understanding (Qwen2.5-VL) | Fase 1 | Planned |
| G-002 | FLUX image generation | Fase 2 | Planned |
| G-003 | Brand visual style transfer | Fase 2 | Planned |
| G-004 | Layout auto-generation | Fase 2 | Planned |
| G-005 | Infographic generation | Fase 2 | Planned |
| G-006 | Text-to-video (CogVideo) | Fase 3 | Planned |
| G-007 | Image-to-video animation | Fase 3 | Planned |
| G-008 | Reel/TikTok auto-generator | Fase 3 | Planned |
| G-009 | Video editing AI | Fase 3 | Planned |
| G-010 | Text-to-3D (Hunyuan3D) | Fase 4 | Planned |
| G-011 | Image-to-3D conversion | Fase 4 | Planned |
| G-012 | AR preview generation | Fase 4 | Planned |
| G-013 | Full-stack code generation | Fase 5 | Planned |
| G-014 | Website builder (prompt → deploy) | Fase 5 | Planned |
| G-015 | App prototype generator | Fase 5 | Planned |
| G-016 | Campaign automation | Fase 6 | Planned |
| G-017 | Content factory (idea → publish) | Fase 6 | Planned |
| G-018 | Brand guardian AI | Fase 6 | Planned |
| G-019 | Monetization optimizer | Fase 6 | Planned |

---

## 3. ARSITEKTUR PRODUK

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAPISAN 1: SIDIX-SocioMeter CONNECTORS                                       │
│  ─────────────────────────────────────────────────────────────       │
│  sociometer-gpt │ sociometer-claude │ sociometer-cursor │ sociometer-kimi │ ... │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 2: MCP SERVER (FastMCP)                                     │
│  ─────────────────────────────────────────────────────────────       │
│  Tools: nasihah_* │ Resources: sidix://* │ Prompts: prompt_*         │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 3: GATEKEEPER (Maqashid + Naskh)                            │
│  ─────────────────────────────────────────────────────────────       │
│  Input → Maqashid Filter → Naskh Check → Route ke Core              │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 4: SIDIX CORE                                               │
│  ─────────────────────────────────────────────────────────────       │
│  Brain: Qwen2.5-7B + LoRA │ Raudah: Multi-agent DAG                 │
│  Tools: 35+ active │ Personas: AYMAN/ABOO/OOMAR/ALEY/UTZ             │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 5: HARVESTING (Jariyah)                                     │
│  ─────────────────────────────────────────────────────────────       │
│  Collector → Sanad Pipeline → Mizan Repository → Tafsir Engine       │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 6: PRESENTATION                                             │
│  ─────────────────────────────────────────────────────────────       │
│  Next.js Dashboard (port 3000) │ Chrome Extension │ CLI               │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow — End-to-End

```
1. User mengetik brief di ChatGPT + SIDIX-SocioMeter GPT Actions
   "Buatkan strategi konten Instagram untuk UMKM kopi"

2. SIDIX-SocioMeter Connector menerjemahkan ke SIDIX API call
   → POST /api/v1/sociometer/nasihah_creative
   → {brief: "...", persona: "AYMAN", maqashid_mode: "IJTIHAD"}

3. Gatekeeper (Maqashid) mengevaluasi input
   → Input valid (tidak harmful) → Lanjut ke Core
   → Mode: IJTIHAD (strategic planning)

4. SIDIX Core memproses:
   → AYMAN persona di-select (confidence: 0.89)
   → Raudah Protocol: 3 specialist agents (strategy + creative + market)
   → TaskGraph DAG: parallel execution
   → Output: strategi konten 30 hari + contoh konten + jadwal posting

5. Maqashid Filter v2 mengevaluasi output
   → CQF scoring: 8.2/10 → PASS
   → Maqashid tagging: [CREATIVE: 0.9, IJTIHAD: 0.85, SANAD: 0.8]

6. Output dikembalikan ke user via SIDIX-SocioMeter Connector
   → ChatGPT menampilkan: strategi lengkap dengan sanad chain

7. Harvesting Loop (Jariyah) berjalan di background:
   → Input + Output + Context = training pair
   → CQF score: 8.2 (melewati threshold 7.0)
   → MinHash dedup: unique (tidak ada duplikat)
   → Masuk ke Mizan Repository (corpus/training/)
   → Quarterly: LoRA retrain dengan data baru
```

---

## 4. Kriteria Kualitas

### 4.1 CQF (Content Quality Framework)

Setiap output harus melewati 10 kriteria CQF dengan skor minimum 7.0/10:

| # | Kriteria | Bobot | Cara Ukur |
|---|----------|-------|-----------|
| 1 | Kejelasan (Clarity) | 10% | Flesch Reading Ease ≥ 60 |
| 2 | Kelengkapan (Completeness) | 10% | Coverage checklist task |
| 3 | Akurasi (Accuracy) | 15% | Factual correctness vs corpus |
| 4 | Relevansi (Relevance) | 15% | Cosine similarity input-output |
| 5 | Kreativitas (Creativity) | 10% | Uniqueness score vs training set |
| 6 | Sanad (Attribution) | 15% | Presence of source chain |
| 7 | Maqashid (Alignment) | 10% | Mode-based evaluation score |
| 8 | Tindak lanjut (Actionability) | 5% | Count of actionable items |
| 9 | Konsistensi (Consistency) | 5% | Style coherence score |
| 10 | Keamanan (Safety) | 5% | Harmful content detection |

### 4.2 Performance Requirements

| Metrik | Target |
|--------|--------|
| Response time (text) | < 3 detik |
| Response time (image) | < 10 detik |
| Response time (video) | < 60 detik |
| MCP tool discovery | < 500ms |
| Chrome Extension load | < 2 detik |
| Offline sync | < 5 detik (batch) |
| Uptime | 99.5% |

---

## 5. RISIKO & MITIGASI

| Risiko | Probabilitas | Impact | Mitigasi |
|--------|-------------|--------|----------|
| Platform block MCP | Medium | High | Fallback ke API langsung + multi-transport |
| Chrome Extension rejected | Medium | High | Patuhi CWS policies, tidak deceptive |
| Model training gagal | Low | High | A/B test + auto-rollback (Naskh) |
| User tidak adopt extension | Medium | Medium | Demo HF Space + video tutorial |
| Rate limit Instagram | High | Medium | Smart polling + proxy rotation |
| Privacy concern | Medium | High | OpHarvest protocol + transparency dashboard |

---

## 6. DEFINISI "SELESAI" (Definition of Done)

Sprint selesai ketika:
1. ✅ Semua acceptance criteria fitur terpenuhi
2. ✅ Unit test coverage ≥ 80%
3. ✅ Integration test passed (MCP + browser + backend)
4. ✅ Maqashid benchmark: 20 creative queries PASS, 10 harmful BLOCK
5. ✅ Dokumentasi di-update (LIVING_LOG.md + module docs)
6. ✅ Code review oleh minimal 1 reviewer
7. ✅ Deploy ke staging + smoke test passed
