# SIDIX Handoff — 2026-04-23 Jiwa + Typo + Kimi Sprint

> Dokumen ini adalah **memori sesi** lengkap untuk agent/developer berikutnya.
> Baca ini sebelum menyentuh kode apapun hari ini.

---

## 🧭 State Saat Ini (Per Akhir Sesi 2026-04-23)

### Yang sudah LIVE di Production (VPS)

| Komponen | Status | Lokasi |
|---|---|---|
| Jiwa 7-Pilar (layer tipis) | ✅ LIVE | `apps/brain_qa/brain_qa/jiwa/` |
| NafsRouter 7-topik | ✅ LIVE, 7/7 correct | `apps/brain_qa/brain_qa/jiwa/nafs.py` |
| Hayat self-iteration | ✅ LIVE (non-blocking) | `apps/brain_qa/brain_qa/jiwa/hayat.py` |
| Aql learning pairs | ✅ LIVE, pairs aktif | `apps/brain_qa/brain_qa/jiwa/aql.py` |
| Qalb health monitor | ✅ LIVE | `apps/brain_qa/brain_qa/jiwa/qalb.py` |
| JiwaOrchestrator singleton | ✅ LIVE | `apps/brain_qa/brain_qa/jiwa/orchestrator.py` |
| agent_react.py wired | ✅ LIVE | Nafs routing + Hayat + Aql terpasang |
| Smithery.yaml (marketplace) | ✅ Di repo | `/smithery.yaml` (belum submit manual) |
| openapi.yaml (GPT Actions) | ✅ Di repo | `apps/sidix-mcp/openapi.yaml` |
| Kimi/Cursor MCP configs | ✅ Di repo | `apps/sidix-mcp/configs/` |
| SIDIX Socio Bot MCP | ✅ LIVE | `apps/sidix-mcp/` (13 tools) |
| Social Radar Extension | ✅ LIVE | `browser/social-radar-extension/` |
| Extension Bridge (7788) | ✅ Di repo | `apps/sidix-extension-bridge/` |
| WA Bridge (7789) | ✅ Di repo | `apps/sidix-wa-bridge/` (npm install VPS belum) |

### Yang BARU diimplementasi (sesi ini — belum di-deploy ke VPS)

| Komponen | Status | Lokasi |
|---|---|---|
| brain/jiwa/ — 7 pilar STANDALONE | ✅ Di repo | `brain/jiwa/`, `brain/nafs/`, `brain/aql/`, dll |
| brain/typo/ — Typo Resilient Framework | ✅ Di repo | `brain/typo/` |
| kimi-plugin/ — Kimi Integration | ✅ Di repo | `kimi-plugin/` |

---

## 🏗️ Arsitektur Dua-Level Jiwa (PENTING)

Ada **dua implementasi Jiwa** — ini bukan duplikat, ini **dua layer yang berbeda**:

### Layer A: `apps/brain_qa/brain_qa/jiwa/` (INTEGRATION LAYER)
- **Tujuan**: thin adapter antara Jiwa dan agent_react.py FastAPI
- **Status**: deployed, production-ready
- **Isi**: nafs.py (routing), hayat.py (iteration), aql.py (learning), qalb.py (health), orchestrator.py
- **Cara kerja**: dipanggil di dalam `run_react()` → inject persona + routing + post-response learning

### Layer B: `brain/jiwa/` (STANDALONE ARCHITECTURE)
- **Tujuan**: full standalone 7-pilar dengan 3-layer knowledge fusion (60%+30%+10%)
- **Status**: di repo, BELUM di-wire ke agent_react.py
- **Isi**: semua pilar sebagai modul independen dengan KG, CQF, self-train
- **Rencana**: ganti/augment Layer A saat KG (Knowledge Graph) sudah production-ready

**Jangan hapus Layer A** sampai Layer B sudah fully tested end-to-end.

---

## 📁 File-File Kunci

### brain/jiwa/ (Standalone — BARU)
```
brain/
├── jiwa/
│   ├── __init__.py              # exports JiwaOrchestrator + convenience API
│   └── orchestrator.py          # master coordinator 7 pilar
├── nafs/
│   ├── __init__.py
│   └── response_orchestrator.py # 3-layer fusion: 60% parametric + 30% KG + 10% static
├── aql/
│   ├── __init__.py
│   └── learning_loop.py         # Jariyah v2: capture→CQF→validate→KG storage
├── qalb/
│   ├── __init__.py
│   └── healing_system.py        # auto-heal: healthy→degraded→sick→critical
├── ruh/
│   ├── __init__.py
│   └── improvement_engine.py    # weekly evaluation + gap analysis + improvement plan
├── hayat/
│   ├── __init__.py
│   └── iteration_engine.py      # generate→evaluate→refine (max 3 rounds, CQF ≥8.0)
├── ilm/
│   ├── __init__.py
│   └── crawling_engine.py       # knowledge gap → auto-crawl → corpus queue
└── hikmah/
    ├── __init__.py
    └── training_engine.py       # 5k pairs → QLoRA retrain → validate → deploy
```

### brain/typo/ (BARU)
```
brain/typo/
├── __init__.py
├── normalizer.py        # Layer 1: koreksi typo + expand abbreviasi (200+ dict)
├── semantic_matcher.py  # Layer 2: intent detection via cosine similarity
├── confidence_scorer.py # Layer 3: combined confidence (40% norm + 60% intent)
└── context_responder.py # Layer 4: response generation based on confidence tier
```

### kimi-plugin/ (BARU)
```
kimi-plugin/
├── manifest.json        # plugin manifest: 6 skills, 2 endpoints (MCP + HTTP)
├── sidix_action.py      # HTTP action wrapper untuk Kimi
└── sidix_skill.py       # /sidix <query> skill shortcut
```

---

## 🔧 Cara Deploy Layer B (brain/jiwa/) ke Production

Layer B bisa diaktifkan sebagai standalone Python module:

```bash
# Di VPS
cd /opt/sidix
python3 -c "from brain.jiwa import JiwaOrchestrator; j = JiwaOrchestrator(); print(j.health)"
```

Untuk wire ke agent_react.py (FUTURE — jangan sekarang):
```python
# Di agent_react.py, ganti import jiwa:
# from .jiwa.orchestrator import jiwa as _jiwa  # Layer A
from brain.jiwa import JiwaOrchestrator as _jiwa  # Layer B
```

---

## 📊 Test Terakhir (VPS — 2026-04-23)

```
T1 jiwa import:    PASS — jiwa imports OK, jiwa.health: healthy
T2 nafs routing:   7/7 correct (fix: len < 25 threshold + substantif check)
T3 chat ngobrol:   PASS — SIDIX merespons dengan persona UTZ
T4 chat koding:    PASS — jawaban bilangan prima dari model knowledge
T5 training pairs: PASS — pairs_2026-04-23.jsonl EXISTS (Aql belajar!)
T6 openapi.yaml:   PASS — GitHub raw accessible
```

---

## 🚧 TODO untuk Sesi Berikutnya

### Prioritas Tinggi
1. **Submit Smithery** — buka smithery.ai, submit `sidix-socio-mcp` (file sudah ada)
2. **WA Bridge npm install di VPS** — `cd /opt/sidix/apps/sidix-wa-bridge && npm install && pm2 start src/index.js --name sidix-wa-bridge`
3. **Extension Bridge pm2** — sama, `apps/sidix-extension-bridge`
4. **Wire brain/typo ke agent_react** — inject di awal `run_react()` sebelum routing

### Prioritas Sedang
5. **KG Storage (PostgreSQL)** — `brain/aql/learning_loop.py` siap, tapi PostgreSQL+GraphRAG perlu setup
6. **Kimi Plugin test** — jalankan `kimi-plugin/sidix_skill.py` secara lokal
7. **brain/ilm crawl schedule** — wiring ke `learn_agent.py` yang sudah ada

### Nice to Have
8. **Nafs regex → NER model** — ganti regex detection dengan ML-based NER untuk akurasi ~95%
9. **Hikmah auto-retrain trigger** — saat pairs >= 5000, auto-trigger QLoRA
10. **Ruh weekly evaluation** — `brain/ruh/improvement_engine.py` perlu scheduler (cron)

---

## 🌐 Endpoint Production

| Endpoint | URL | Keterangan |
|---|---|---|
| Brain API | `https://ctrl.sidixlab.com` | FastAPI, PM2: sidix-brain |
| Frontend | `https://app.sidixlab.com` | Vite+TS, PM2: sidix-ui |
| Landing | `https://sidixlab.com` | Static nginx |
| Health | `https://ctrl.sidixlab.com/health` | JSON health check |
| Chat | `https://ctrl.sidixlab.com/agent/chat` | POST, field: question + persona |

---

## 🔑 Keputusan Arsitektur (ADR)

### ADR-001: Dua Layer Jiwa
- **Keputusan**: pertahankan Layer A (thin adapter) dan Layer B (standalone) secara bersamaan
- **Alasan**: Layer A sudah production, Layer B perlu KG untuk full function
- **Review**: setelah KG production-ready, merge ke satu layer

### ADR-002: Typo Framework — Regex + Levenshtein (bukan ML)
- **Keputusan**: gunakan rule-based + Levenshtein distance, bukan ML model
- **Alasan**: zero dependency, zero latency, predictable behavior
- **Trade-off**: akurasi ~85% vs ML yang ~95% tapi butuh model tambahan

### ADR-003: Kimi Plugin — Method 4 (Skill) sebagai default
- **Keputusan**: prioritaskan `/sidix` slash command via `sidix_skill.py`
- **Alasan**: paling simple, no config, langsung pakai
- **Upgrade path**: Method 3 (HTTP Action) saat perlu custom UI

---

## 📖 Narasi Perjalanan Sesi Ini

Sesi ini dimulai dari **validasi Jiwa Sprint** yang sebelumnya diimplementasi tapi belum diuji.
Test `test_jiwa_final.py` dijalankan ke VPS — hasilnya 6/7, satu gagal karena "GPU A100 vs H100?"
salah ter-route ke `ngobrol` (panjang string < 30 char menjadi fallback ngobrol).

Fix ditemukan: pisahkan cek panjang dari cek regex — pertanyaan pendek bisa tetap `umum`
kalau mengandung kata substantif seperti "vs", "apa", "jelaskan". Setelah fix, 7/7 correct.

Kemudian user membuka folder `Arsitektur jiwa dan Plugin/sidix-cursor-brief/` yang berisi
tiga dokumen lengkap: ARSITEKTUR_JIWA_SIDIX.md (66KB), TYPO_RESILIENT_FRAMEWORK.md (25KB),
KIMI_INTEGRATION_GUIDE.md (17KB). Dokumen-dokumen ini berisi arsitektur penuh 7 pilar
dengan kode implementasi lengkap.

Implementasi kemudian dilakukan untuk tiga sistem sekaligus:
1. **brain/jiwa/** — standalone 7-pilar dengan 3-layer knowledge fusion (berbeda dari Layer A)
2. **brain/typo/** — 4-layer typo resilience tanpa ML model
3. **kimi-plugin/** — plugin SIDIX untuk Kimi AI

Semua diimplementasi dalam satu sesi dengan prinsip standing alone (no vendor API).
