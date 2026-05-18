# SCRIPT & MODULE REFERENCE: SIDIX-SocioMeter

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Technical Reference

---

## NEW MODULES

| Module | Path | Fungsi |
|--------|------|--------|
| MCP Server | `brain/sociometer/mcp_server.py` | FastMCP instance, 6 tools, resources, prompts |
| Connectors | `brain/sociometer/connectors/` | Adapter stdio, HTTP, IDE, peramban (tanpa menyematkan merek host) |
| Collector | `brain/sociometer/harvesting/collector.py` | JariyahCollector — Redis queue, async |
| Sanad Pipeline | `brain/sociometer/harvesting/sanad_pipeline.py` | MinHash + CQF + Sanad + Naskh + Maqashid |
| Mizan Repository | `brain/sociometer/harvesting/mizan_repository.py` | PostgreSQL + MinIO + Corpus + KG |
| Tafsir Engine | `brain/sociometer/harvesting/tafsir_engine.py` | Auto-retrain QLoRA, A/B test, deploy/rollback |
| Browser API | `brain/sociometer/browser/ingest_api.py` | POST /api/v1/sociometer/browser/ingest |
| Chrome Extension | `sociometer-browser/` | manifest.json, background.js, content.js, injector.js, panel.html, popup.html |

## MODIFIED MODULES

| Module | Change |
|--------|--------|
| `brain_qa/agent_react.py` | Wire Maqashid middleware ke `run_react()` |
| `brain_qa/learn_agent.py` | Wire Naskh resolution sebelum `store_corpus()` |

## SCRIPTS

| Script | Path | Fungsi |
|--------|------|--------|
| Setup | `scripts/setup_sociometer.py` | Create dirs, install deps, init files |
| Benchmark | `scripts/benchmark_maqashid.py` | 50 creative PASS + 20 harmful BLOCK |
| Deploy | `scripts/deploy_sociometer.sh` | Test → build → migrate → restart → health check |

## TESTS

| Test | Path | Coverage |
|------|------|----------|
| MCP Server | `tests/sociometer/test_mcp_server.py` | 6 tools, response format |
| Harvesting | `tests/sociometer/test_harvesting.py` | Dedup, CQF, pipeline |
| Integration | `tests/sociometer/test_integration.py` | E2E: MCP → Core → Dashboard → Harvesting |

## ENVIRONMENT VARIABLES

```bash
SIDIX_MCP_TRANSPORT=streamable-http
SIDIX_MCP_PORT=8765
SIDIX_DB_HOST=localhost
SIDIX_DB_PORT=5432
SIDIX_DB_NAME=sidix
SIDIX_REDIS_URL=redis://localhost:6379/0
SIDIX_MINIO_ENDPOINT=localhost:9000
SIDIX_MINIO_BUCKET=sidix-media
SIDIX_HARVEST_CQF_THRESHOLD=7.0
SIDIX_LORA_RETRAIN_MIN_PAIRS=5000
SIDIX_ANON_SALT=your-secret-salt-here
SIDIX_DATA_RETENTION_DAYS=365
```
