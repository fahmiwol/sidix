# PRD: SIDIX-SocioMeter
## Product Requirements Document

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Product Requirements

---

## 1. RINGKASAN PRODUK

SIDIX-SocioMeter = sistem ekspansi terdistribusi SIDIX:
1. **MCP plugin** untuk host AI dan IDE mitra (transport stdio/HTTP)
2. **Chrome Extension** (`sociometer-browser`) untuk universal data collection
3. **Jariyah self-training** — setiap interaksi = training pair
4. **Roadmap generatif 7 fase** — dari creative hingga autonomous AI

---

## 2. FITUR P0 (MVP)

### F-001: MCP Server
- 6 core tools: `nasihah_creative`, `nasihah_analyze`, `nasihah_design`, `nasihah_code`, `nasihah_raudah`, `nasihah_learn`
- Transport: stdio + streamable-http + SSE
- Auto-discovery, Maqashid auto-tag, Sanad metadata
- Persona routing: AYMAN/ABOO/OOMAR/ALEY/UTZ

### F-002: Chrome Extension (Manifest V3)
- Network interception: Instagram, TikTok, YouTube, LinkedIn, Facebook
- Sidebar panel: persona selector + quick actions + chat
- Auto-suggest saat mengetik (surel web, pesan web, mikroblog)
- Offline buffer (IndexedDB), privacy dashboard

### F-003: Jariyah Harvesting Loop
- Auto-capture: MCP + dashboard + browser + manual
- MinHash deduplication (similarity ≥ 0.85)
- CQF scoring (10 kriteria, threshold ≥ 7.0)
- Sanad validation + Naskh resolution + Maqashid filter
- QLoRA retrain trigger: 5,000 pairs OR quarterly

### F-004: Raudah Multi-Agent v0.2
- TaskGraph DAG dengan dependency tracking
- Parallel specialists dengan auto-select
- Progress tracking via SSE
- Retry: max 3, Timeout: 120s per agent

### F-005: Maqashid Filter v2.1 (Wired)
- Wire ke `run_react()` sebagai middleware
- 4 mode: CREATIVE, ACADEMIC, IJTIHAD, GENERAL
- Auto-select mode dari task + persona
- Block harmful: 0% false negative

### F-006: Naskh Handler v1.1 (Wired)
- Wire ke `learn_agent.py` corpus pipeline
- Sanad-tier: primer > ulama > peer-reviewed > aggregator
- `is_frozen` flag, auto-merge, conflict flag

---

## 3. FITUR ROADMAP (P1-P3)

| Kode | Fitur | Fase | Priority |
|------|-------|------|----------|
| G-001 | Vision understanding (Qwen2.5-VL) | Fase 1 | P2 |
| G-002 | FLUX image generation | Fase 2 | P2 |
| G-003 | Brand visual style transfer | Fase 2 | P2 |
| G-004 | Layout auto-generation | Fase 2 | P2 |
| G-005 | Infographic generation | Fase 2 | P2 |
| G-006 | Text-to-video (CogVideo) | Fase 3 | P3 |
| G-007 | Image-to-video animation | Fase 3 | P3 |
| G-008 | Reel/TikTok auto-generator | Fase 3 | P3 |
| G-009 | Video editing AI | Fase 3 | P3 |
| G-010 | Text-to-3D (Hunyuan3D) | Fase 4 | P3 |
| G-011 | Image-to-3D conversion | Fase 4 | P3 |
| G-012 | AR preview generation | Fase 4 | P3 |
| G-013 | Full-stack code generation | Fase 5 | P3 |
| G-014 | Website builder | Fase 5 | P3 |
| G-015 | App prototype generator | Fase 5 | P3 |
| G-016 | Campaign automation | Fase 6 | P3 |
| G-017 | Content factory | Fase 6 | P3 |
| G-018 | Brand guardian AI | Fase 6 | P3 |
| G-019 | Monetization optimizer | Fase 6 | P3 |

---

## 4. 5 PERSONA

| Nama | Karakter | Maqashid Mode | Kekuatan |
|------|----------|---------------|----------|
| **AYMAN** | Strategic Sage | IJTIHAD | Research, vision, strategy, long-form |
| **ABOO** | The Analyst | ACADEMIC | Data, logic, structured argument, code |
| **OOMAR** | The Craftsman | IJTIHAD | Technical deep-dives, system design, build |
| **ALEY** | The Learner | GENERAL | Teaching, curriculum, beginner-friendly |
| **UTZ** | The Generalist | CREATIVE | Daily tasks, flexible, creative output |

---

## 5. CQF — CONTENT QUALITY FRAMEWORK

| # | Kriteria | Bobot | Cara Ukur |
|---|----------|-------|-----------|
| 1 | Kejelasan (Clarity) | 10% | Flesch Reading Ease ≥ 60 |
| 2 | Kelengkapan (Completeness) | 10% | Coverage checklist |
| 3 | Akurasi (Accuracy) | 15% | Factual vs corpus |
| 4 | Relevansi (Relevance) | 15% | Cosine similarity |
| 5 | Kreativitas (Creativity) | 10% | Uniqueness score |
| 6 | Sanad (Attribution) | 15% | Source chain present |
| 7 | Maqashid (Alignment) | 10% | Mode-based score |
| 8 | Tindak lanjut (Actionability) | 5% | Action items count |
| 9 | Konsistensi (Consistency) | 5% | Style coherence |
| 10 | Keamanan (Safety) | 5% | Harm detection |

**Threshold:** Minimum 7.0/10 untuk masuk corpus.

---

## 6. ACCEPTANCE CRITERIA

- [ ] 50 creative queries PASS Maqashid
- [ ] 20 harmful queries BLOCK (0% false negative)
- [ ] Unit test coverage ≥ 80%
- [ ] MCP tool discovery < 500ms
- [ ] Response time: text < 3s, image < 10s
- [ ] All 6 P0 features functional
