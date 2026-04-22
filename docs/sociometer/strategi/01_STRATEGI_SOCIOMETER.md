# STRATEGI SOCIO-METER
## Sistem Ekspansi SIDIX ke Ekosistem AI Global

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Dokumen Strategis

---

## 1. VISI

Socio-Meter adalah arsitektur ekspansi SIDIX yang memungkinkan SIDIX menjadi **tool/plugin** yang dapat dipasang di agen AI dan platform mitra (host obrolan, IDE, peramban) — tanpa kehilangan identitas sebagai sistem **self-hosted** yang **standing alone**.

> *"SIDIX tidak pergi ke platform lain. SIDIX membuka pintu, dan platform lain yang datang ke SIDIX."*

Penamaan konektor mengikuti **profil teknis** (stdio, HTTP stream, plugin IDE, ekstensi peramban), bukan merek pihak ketiga.

---

## 2. ARSITEKTUR 6 LAPISAN

| Lapis | Nama | Fungsi |
|-------|------|--------|
| 1 | **Connectors** | Adapter per saluran: `sociometer-stdio`, `sociometer-stream`, `sociometer-ide`, `sociometer-browser`, `sociometer-embed` — dipetakan ke host mitra tanpa menyematkan merek sebagai identitas SIDIX |
| 2 | **MCP Server** | FastMCP: 6 tools + resources + prompts |
| 3 | **Gatekeeper** | Maqashid Filter + Naskh Handler |
| 4 | **SIDIX Core** | Qwen2.5-7B + LoRA, Raudah Protocol, 35+ Tools, 5 Persona |
| 5 | **Jariyah Harvesting** | Collector → Sanad Pipeline → Mizan Repository → Tafsir Engine |
| 6 | **Presentation** | Next.js Dashboard (port 3000), Chrome Extension, CLI |

---

## 3. SELF-TRAINING: Sistem Jutaan Agen (Jariyah)

**Jariyah** = sistem self-training terdistribusi. Setiap interaksi = sedekah ilmu yang terus mengalir.

**Pipeline:**
```
Socio-Meter Nodes (Chrome Ext / MCP / API / Widget)
    ↓
Collector — Gathering interaction logs + context + quality signals
    ↓
Sanad Pipeline — MinHash dedup (≥0.85) → CQF scoring (≥7.0) → Sanad validation → Naskh resolution → Maqashid filter
    ↓
Mizan Repository — PostgreSQL + MinIO + Corpus + Knowledge Graph
    ↓
Tafsir Engine — QLoRA retrain (r=16, alpha=32, 3 epochs), A/B test, auto-deploy/rollback
```

---

## 4. ROADMAP GENERATIVE — 7 FASE

| Fase | Versi | Kemampuan Baru |
|------|-------|---------------|
| **Fase 0** | v0.6.1 (sekarang) | Text, Image (SDXL), Voice, RAG, ReAct |
| **Fase 1** | v0.7.0 | +Vision (Qwen2.5-VL), Video analysis, Audio gen |
| **Fase 2** | v0.8.0 | +FLUX image, Style transfer, Layout auto-gen |
| **Fase 3** | v0.9.0 | +Text-to-video (CogVideo), Reel/TikTok creator |
| **Fase 4** | v1.0.0 | +Text-to-3D (Hunyuan3D), AR preview |
| **Fase 5** | v1.1.0 | +Full-stack code, Website builder, App prototype |
| **Fase 6** | v1.2.0 | +Campaign auto, Content factory, Brand guardian |
| **Fase 7** | v2.0.0 | +Autonomous creative, Cross-modal, Meta-learning |

---

## 5. GROWTH STRATEGY

| Fase | Target | Strategi |
|------|--------|----------|
| Penanaman | 10 users | Founding Circle — personal invite |
| Perkecambahan | 50 users | Case study reels, TikTok tutorials, referral |
| Pertumbuhan | 500 users | Product Hunt, SEO, podcast, webinar |
| Pembesaran | 5,000 users | Chrome Web Store featured, HF Space |
| Maturity | 50,000 users | White-label, enterprise API |

---

## 6. MONETISASI (3 Tier)

| Tier | Nama | Harga | Fitur |
|------|------|-------|-------|
| Free | **Sadaqah** | $0 | 1 competitor, IG only, basic |
| Pro | **Infaq** | $9/bulan | 10 competitors, multi-platform, PDF |
| Enterprise | **Wakaf** | $99/bulan | Unlimited, real-time, API, white-label |

---

## 7. IMPLEMENTATION — 12 SPRINT (24 Minggu)

| Sprint | Fokus | ETA |
|--------|-------|-----|
| 7 (sekarang) | MCP Server + Wire Maqashid/Naskh | Week 1-2 |
| 8 | Chrome Extension MVP | Week 3-4 |
| 9 | Jariyah Harvesting Loop | Week 5-6 |
| 10 | Dashboard Semrawut + Privacy | Week 7-8 |
| 11 | Distribution (hub MCP, Chrome Web Store) | Week 9-10 |
| 12-17 | Generative Fase 1-6 | Week 11-22 |
| 18 | v1.0 Launch | Week 23-24 |

---

## 8. KESIMPULAN

Prinsip yang tidak berubah:
- **Standing alone** — model sendiri, corpus sendiri, infra sendiri
- **Transparansi epistemologis** — sanad chain, 4-label, maqashid scoring
- **Kedaulatan data** — data user tetap milik user, anonim untuk training
- **Jariyah ilmu** — setiap interaksi = sedekah ilmu yang terus mengalir

SIDIX bukan produk — SIDIX adalah **amanah**.
