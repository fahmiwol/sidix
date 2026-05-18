# FITUR SPECS: SIDIX-SocioMeter

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Feature Specification

---

## P0 — MUST HAVE

### F-001: MCP Server
**Modul**: `brain/sociometer/mcp_server.py`
**Persona**: Router (semua)

6 tools via FastMCP:
- `nasihah_creative(brief, persona="AYMAN")` → copywriting, branding, marketing
- `nasihah_analyze(data, analysis_type="competitor")` → competitor, market, trends
- `nasihah_design(prompt, format="image")` → images, thumbnails, logos
- `nasihah_code(task, language="python")` → scripts, functions, apps
- `nasihah_raudah(task, specialists=None)` → multi-agent collaboration
- `nasihah_learn(topic, level="beginner")` → teaching mode

Resources: `sidix://personas`, `sidix://tools`, `sidix://maqashid/modes`, `sidix://benchmarks/{niche}`

Prompts: `prompt_brand_audit(brand, platform)`, `prompt_content_strategy(niche, platforms)`

---

### F-002: Chrome Extension (`sociometer-browser`)
**Manifest**: V3 | **Komponen**: background.js, content.js, injector.js, panel.html, popup.html

4 komponen utama:
1. **Content Script** — Network interceptor (fetch/XHR override)
2. **Service Worker** — Queue management, batch upload ke backend
3. **Sidebar Panel** — Persona selector, quick actions, chat
4. **Injection Engine** — Auto-suggest saat mengetik

Platform support: Instagram, TikTok, YouTube, LinkedIn, Facebook, mikroblog + surel web, pesan web, dokumen kolaboratif web

---

### F-003: Jariyah Harvesting Loop
**Modul**: `brain/sociometer/harvesting/`

Pipeline 4 komponen:
1. **collector.py** — Redis queue, async, 4 sumber (MCP, dashboard, browser, manual)
2. **sanad_pipeline.py** — MinHash dedup → CQF scoring → Sanad validate → Naskh resolve → Maqashid filter
3. **mizan_repository.py** — PostgreSQL + MinIO + Corpus + Knowledge Graph
4. **tafsir_engine.py** — Auto-retrain QLoRA, A/B test, deploy/rollback

---

### F-004: Raudah Multi-Agent v0.2
**Modul**: `brain/raudah/`

- TaskGraph DAG dengan topological sort
- Parallel execution per level
- SSE progress stream
- Retry: max 3, Timeout: 120s

---

### F-005: Maqashid Filter v2.1 (Wired)
**Modul**: `brain_qa/maqashid_profiles.py` → wire ke `run_react()`

4 mode:
| Mode | Gunakan Untuk | Persona |
|------|--------------|---------|
| CREATIVE | Iklan, konten, desain | UTZ |
| ACADEMIC | Riset, analisis, argumentasi | ABOO |
| IJTIHAD | Visi, inovasi, strategi | AYMAN, OOMAR |
| GENERAL | QA, penjelasan, ringkasan | ALEY |

---

### F-006: Naskh Handler v1.1 (Wired)
**Modul**: `brain_qa/naskh_handler.py` → wire ke `learn_agent.py`

Sanad-tier priority:
1. Sumber Primer (Quran, Hadits) — weight: 1.0
2. Ulama & Fuqaha — weight: 0.8
3. Peer-reviewed — weight: 0.6
4. Aggregator — weight: 0.4

Actions: accept, merge, conflict (flag for review), reject

---

## P1 — SHOULD HAVE

### F-007: Dashboard Semrawut
Dense analytics UI: AccountCards, EngagementGauge, ContentGrid, PostingHeatmap, TrendRadar, AIInsightPanel

### F-008: OpHarvest Privacy Dashboard
Data overview, consent manager (4 levels: none/basic/full/research), export, delete, opt-out

---

## P2-P3 — ROADMAP

| Kode | Fitur | Fase |
|------|-------|------|
| G-001~005 | Vision, FLUX, Style transfer, Layout, Infographic | 1-2 |
| G-006~009 | Text-to-video, Image-to-video, Reel creator, Video edit | 3 |
| G-010~012 | Text-to-3D, Image-to-3D, AR preview | 4 |
| G-013~015 | Code generation, Website builder, App prototype | 5 |
| G-016~019 | Campaign auto, Content factory, Brand guardian, Monetize | 6 |
