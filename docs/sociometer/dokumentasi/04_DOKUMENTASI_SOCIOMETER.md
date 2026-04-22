# DOKUMENTASI ARSITEKTUR: SIDIX-SocioMeter

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Technical Documentation

---

## 1. 5 PRINSIP ARSITEKTURAL (Non-Negotiable)

| # | Prinsip | Implementasi |
|---|---------|--------------|
| 1 | **Standing Alone** | Model (Qwen+LoRA), corpus, infra — semua self-hosted. Tanpa API inferensi vendor asing untuk inti. |
| 2 | **Transparansi Epistemologis** | Sanad chain, 4-label [FACT/REASONING/OPINION/UNCERTAIN], Maqashid scoring. |
| 3 | **Keadilan Data** | Local-first, opt-in granular, anonymization (hash+bucket), delete anytime. |
| 4 | **Evolusi Mandiri** | Jariyah loop: every interaction → CQF scoring → corpus → QLoRA retrain. |
| 5 | **Tawarruq** | Buka pintu ke platform mitra via MCP tanpa kehilangan identitas SIDIX. |

---

## 2. ARSITEKTUR 6 LAPISAN

### Lapisan 1: Connectors (`sociometer-*`)
Adapter teknis: host obrolan (stdio/HTTP), plugin IDE, ekstensi peramban — **slug deployment** disimpan sebagai profil konektor, bukan merek dagang.

### Lapisan 2: MCP Server (FastMCP)
- **Tools**: nasihah_creative, nasihah_analyze, nasihah_design, nasihah_code, nasihah_raudah, nasihah_learn
- **Resources**: `sidix://personas`, `sidix://tools`, `sidix://maqashid/modes`, `sidix://benchmarks/{niche}`
- **Prompts**: brand_audit, content_strategy, competitor_analysis, trend_detection
- **Transport**: stdio (lokal), streamable-http (produksi), SSE (real-time)

### Lapisan 3: Gatekeeper
```
Input → Validation (harmful?) → Maqashid Filter (mode select) → Naskh Check → Route ke Core
```

### Lapisan 4: SIDIX Core
- **Brain**: Qwen2.5-7B-Instruct + LoRA adapter (Ollama local)
- **Raudah**: TaskGraph DAG, multi-agent orchestration
- **Tools**: 35+ active (search, generate, code, image, dll)
- **Personas**: AYMAN, ABOO, OOMAR, ALEY, UTZ

### Lapisan 5: Harvesting (Jariyah)
```
Collector (Redis queue) → Sanad Pipeline → Mizan Repository → Tafsir Engine
```
**Sanad Pipeline** 5 steps:
1. MinHash deduplication (threshold 0.85)
2. CQF scoring (10 kriteria, threshold 7.0)
3. Sanad validation (source chain)
4. Naskh resolution (conflict: baru vs lama)
5. Maqashid filter (mode-based)

### Lapisan 6: Presentation
| Komponen | Teknologi | Port |
|----------|-----------|------|
| Dashboard | Next.js 15 + Tailwind + Recharts | 3000 |
| Chrome Ext | Vanilla JS, Manifest V3 | — |
| CLI | Python Click | — |

---

## 3. DATA FLOW — END TO END

```
[MCP Request dari host mitra]
    → [connector] translate ke SIDIX API
    → [MCP Server] tool routing
    → [Gatekeeper] Maqashid mode = IJTIHAD
    → [Persona Router] AYMAN selected (confidence 0.89)
    → [Raudah Protocol] 3 specialists (strategy + creative + market)
    → [Qwen2.5-7B] generate output
    → [Maqashid v2] CQF = 8.2/10 → PASS
    → [Sanad Tagging] 4-label applied
    → [Response] ke user via Connector
    → [Background: Harvesting] → Training Pair → Corpus
```

---

## 4. MODULE STRUCTURE

```
sidix/
├── brain/
│   ├── sociometer/
│   │   ├── mcp_server.py
│   │   ├── connectors/ (stdio.py, http.py, ide.py, ...)
│   │   ├── harvesting/ (collector.py, sanad_pipeline.py, mizan_repository.py, tafsir_engine.py)
│   │   └── browser/ (ingest_api.py, sync_handler.py)
│   ├── raudah/ (core.py, taskgraph.py, specialists.py)
│   └── naskh/ (handler.py, sanad_tier.py)
├── tools/ — 35+ Hands
├── apps/brain_qa/ — Inference (port 8765)
├── apps/SIDIX_USER_UI/ — Next.js (port 3000)
├── sociometer-browser/ — Chrome Extension
└── docs/ — Dokumentasi
    └── sociometer/ ← [KITA DISINI]
```

---

## 5. ENVIRONMENT VARIABLES

| Variable | Default | Keterangan |
|----------|---------|------------|
| SIDIX_MCP_TRANSPORT | streamable-http | stdio / streamable-http / sse |
| SIDIX_MCP_PORT | 8765 | Port MCP server |
| SIDIX_DB_HOST/PORT/NAME/USER/PASS | — | PostgreSQL credentials |
| SIDIX_REDIS_URL | redis://localhost:6379/0 | Queue + cache |
| SIDIX_MINIO_ENDPOINT/ACCESS_KEY/SECRET_KEY/BUCKET | — | Media storage |
| SIDIX_HARVEST_CQF_THRESHOLD | 7.0 | Minimum CQF score |
| SIDIX_LORA_RETRAIN_MIN_PAIRS | 5000 | Trigger retrain |
| SIDIX_ANON_SALT | — | HMAC salt untuk anonymization |
| SIDIX_DATA_RETENTION_DAYS | 365 | Retention policy |
