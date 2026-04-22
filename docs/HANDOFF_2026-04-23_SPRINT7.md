# HANDOFF — 2026-04-23 Sprint 7 Preparation

> **From:** Claude (Sesi 2026-04-23, limit habis) + Kimi K2.6 (Research & Strategy)
> **To:** Agen berikutnya (Claude/Cursor/Antigravity)
> **Date:** 2026-04-23T01:55 WIB

---

## Konteks

Sesi Claude 2026-04-23 menghasilkan v0.6.0 dan v0.6.1. Sebelum limit Claude habis, user memberikan
**dua dokumen riset Kimi K2.6** yang berisi riset teknis (A1-A5) dan strategi produk (B1-C4) yang
harus diintegrasikan ke sprint dan roadmap SIDIX.

---

## Commit History Sesi Ini

| SHA | Deskripsi |
|-----|-----------|
| `347f803` | baseline v0.5.0 |
| `9af6173` | feat: v0.6.0 — Maqashid v2 + Naskh + Raudah Protocol |
| `8485095` | feat: v0.6.1 — Persona rename AYMAN/ABOO/OOMAR/ALEY/UTZ |
| `60acde4` | doc: README + CONTRIBUTING + Kimi feedback |
| `2df9f8f` | doc: HANDOFF FINAL + CHANGELOG + ROADMAP Sprint 5.5 |

---

## Dokumen Kimi K2.6 yang Diterima

### Dokumen 1: Sprint 7 Riset (5824c294)

| # | Topik | Status | Sprint Target |
|---|-------|--------|---------------|
| A1 | Benchmark Maqashid (50 creative + 20 harmful queries) | Siap copy-paste ke `test_maqashid_benchmark.py` | 6-7 |
| A2 | MinHash dedup (`datasketch`, `num_perm=128`, `threshold=0.85`) | Siap integrate ke `curator_agent.py` | 7-8 |
| A3 | Raudah TaskGraph DAG (custom lightweight, async-native) | Siap replace networkx | 7 |
| A4 | Intent classifier (few-shot, bukan full fine-tune) | Siap untuk Sprint 7 | 7 |
| A5 | CQF Rubrik (10 kriteria, total bobot 10.0) | Siap publikasikan | 7 |

### Dokumen 2: Strategi Harvest Data (a4079eb7)

| # | Topik | Highlight |
|---|-------|-----------|
| B1 | Analisis 6 fitur | **Social Radar = WINNER** |
| B2 | Operation Harvest (OpHarvest) | Konsep IHOS diterjemahkan ke data harvesting |
| B3 | Arsitektur plugin + harvesting loop | Chrome Extension → Harvesting Layer → Training Layer |
| B4 | Ethics & legal guardrails | Public data only, explicit opt-in, anonymization |
| B5 | Monetization flywheel | Free → Pro → Enterprise, tapi yang penting: **flywheel data** |
| C | Roadmap Sprint 7-10 | Social Radar MVP → expand platform → plugin ecosystem → advanced |

---

## Keputusan Strategis (dari Kimi K2.6)

### DECISION: Fokus 1 fitur — SIDIX Social Radar

| Aspek | Keputusan |
|-------|-----------|
| Fitur fokus | **Social Radar** — competitor monitoring + social listening |
| Platform pertama | **Chrome Extension** (universal, fastest to build) |
| Target platform data | Instagram first → TikTok → Twitter/X → YouTube |
| AI model baru? | **Tidak** — pakai Qwen2.5-7B yang sudah ada untuk analisis |
| Data harvesting | **Ya** — explicit opt-in, public data only, anonymized |
| Monetization | Freemium: 1 competitor free, 10 pro $9/mo, unlimited enterprise $99/mo |
| Competitive advantage | Naskh Handler + IHOS framework + self-hosted privacy |

### Strategic Pivot

- **Dari:** "AI Agent Universal" (bersaing head-to-head dgn GPT/Claude/Canva)
- **Ke:** "Social Radar Specialist" — niche competitor intelligence untuk UMKM Indonesia
- **Blue Ocean:** Tool existing (Sprout, Brandwatch) $300-1000/bulan, enterprise-focused
- **SIDIX:** $9/mo Pro tier, accessible untuk UMKM/creator Indonesia

---

## Priority Queue — Sesi Berikutnya

### 🔴 Top 3 Priority (CARRY OVER dari sesi Claude)

1. **Wire `evaluate_maqashid()` ke `run_react()`** — 1 file, ~20 baris, langsung bisa di-test
2. **`test_sprint6.py`** — coverage Maqashid benchmark + curator premium filter
3. **Raudah v0.2** — TaskGraph DAG (code sudah ada dari Kimi A3) + `/raudah/run` endpoint

### 🟡 Sprint 7 Items (dari Kimi research)

4. **`test_maqashid_benchmark.py`** — Copy-paste A1 data (50+20 queries) + pytest parametrize
5. **MinHash dedup** — `pip install datasketch`, integrate `CorpusDeduplicator` ke `curator_agent.py`
6. **Intent classifier** — few-shot `classify_intent()` ke persona router
7. **CQF rubrik v2** — 10 kriteria, total bobot 10.0, threshold ≥7.0

### 🟢 Sprint 7+ Items (Social Radar)

8. Chrome Extension skeleton (Manifest V3, popup UI)
9. Instagram scraper (public profile + posts, no login)
10. Qwen2.5-7B analyzer: caption analysis + engagement summary
11. Privacy filter + consent checkbox
12. Harvesting loop: save raw+analysis ke corpus queue

---

## Arsitektur Baru: 4-Layer + OpHarvest

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — INTERFACE (Plugin Ecosystem)                             │
│  ├── Chrome Extension    → Social Radar, Competitor Spy             │
│  ├── Figma Plugin        → Image Gen, Design Harvest                │
│  ├── VS Code Extension   → Code Completion, Snippet Harvest         │
│  └── Web Dashboard       → sidixlab.com                             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│  LAYER 2 — BRAIN (SIDIX Core)                                       │
│  ├── Qwen2.5-7B + LoRA SIDIX Adapter                                │
│  ├── ReAct Loop (MAX_STEPS=6)                                       │
│  ├── Raudah Protocol (multi-agent DAG)                              │
│  ├── Maqashid Filter v2 (mode-based)                                │
│  ├── Muhasabah Loop (CQF ≥ 7.0)                                   │
│  └── 5 Persona: AYMAN / ABOO / OOMAR / ALEY / UTZ                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│  LAYER 3 — HANDS (Tools + RAG)                                      │
│  ├── Social Radar Suite (NEW)                                       │
│  ├── Creative Suite (existing)                                      │
│  ├── Code Suite (existing)                                          │
│  └── Knowledge Suite (existing)                                     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│  LAYER 4 — MEMORY & GROWTH (OpHarvest)                              │
│  ├── Harvesting Loop (scrape → normalize → privacy → CQF gate)      │
│  ├── Corpus Management (Naskh + MinHash + Vector)                   │
│  └── Training Flywheel (LoRA retrain quarterly)                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Ethics & Legal Guardrails (OpHarvest)

1. **Public Data Only** — No private messages, no locked accounts, no personal data
2. **Explicit Opt-in** — Default = OFF. User harus checklist consent
3. **Anonymization** — Username → hash ID, location → regional only
4. **Transparency Dashboard** — User bisa lihat & delete harvested data
5. **Rate Limit Respect** — Max 1 req / 6 detik per target, respect robots.txt
6. **No Resale** — Data hanya untuk training SIDIX
7. **Regional Compliance** — Patuhi UU PDP Indonesia

---

## CQF Rubrik v2 (dari Kimi A5)

| # | Kriteria | Bobot | Threshold |
|---|----------|-------|-----------|
| 1 | Relevansi | 1.5 | 7-10: relevan + anticipates needs |
| 2 | Akurasi Faktual | 1.5 | 7-10: akurat + nuance tepat |
| 3 | Kelengkapan | 1.0 | 7-10: semua aspek + value-add |
| 4 | Konsistensi Persona | 1.0 | 7-10: voice konsisten |
| 5 | Sanad / Provenance | 1.0 | 7-10: sanad + tier + confidence |
| 6 | Kreativitas | 1.0 | 7-10: breakthrough |
| 7 | Struktur & Format | 0.5 | 7-10: exemplary, scannable |
| 8 | Maqashid Alignment | 1.0 | 7-10: strongly aligned |
| 9 | Grounded Context | 0.5 | 7-10: perfectly grounded |
| 10 | Actionability | 1.0 | 7-10: immediately actionable |

**Total:** 10.0 | **Pass:** ≥7.0 | **Warn:** 5.0-6.9 (auto-refine) | **Fail:** <5.0 (log hallucination)

---

## Sprint Roadmap Update (Kimi K2.6)

| Sprint | Focus | Target |
|--------|-------|--------|
| **6.5** (now) | Wire Maqashid + Benchmark + MinHash + Raudah v0.2 | Teknis foundational |
| **7** | Social Radar MVP (Chrome Extension + IG scraper) | 10 beta users, 3-4 hari |
| **8** | Expand (TikTok + Twitter + Alert + PDF report) | 50 active users |
| **9** | Plugin Ecosystem (Figma + VS Code + YouTube) | 5000+ training pairs |
| **10** | Monetization (Freemium + White-label + API) | $500 MRR |

---

## File Reference (sumber lengkap)

| File | Lokasi |
|------|--------|
| Kimi Sprint 7 Research | `C:\Users\ASUS\Downloads\Sidix Adik AI -_riset_tambahan_sprint 7_files\5824c294-*.html` |
| Kimi Strategic Masterplan | `C:\Users\ASUS\Downloads\Sidix Adik AI -Strategi_harvest data_files\a4079eb7-*.html` |

---

_Handoff created by Antigravity (Gemini) untuk menjaga kontinuitas multi-agent SIDIX._
