═══════════════════════════════════════════════════════════
TASK CARD: Agency Kit 1-Click + Debate Ring REAL + Self-Train Fase 1

WHAT (1 kalimat konkret):
Implementasi 3 sprint paralel: Agency Kit 1-Click (branding pipeline DAG), Debate Ring REAL (multi-agent consensus via Qwen), dan Self-Train Fase 1 (curator agent + weekly JSONL auto-generation).

WHY:
- Visi mapping: Pencipta (Agency Kit) + Cognitive (Debate Ring) + Tumbuh (Self-Train)
- Sprint context: BACKLOG Sprint 5 (Agency Kit + Debate Ring + Self-Train Fase 1)
- Founder request: "kamu atur sesuai dampak dan dependencinya"
- Coverage shift: Pencipta 75%→90%, Cognitive 90%→95%, Tumbuh 40%→70%

ACCEPTANCE (verifiable):
1. Agency Kit: POST /creative/agency_kit — input business_name + niche + target_audience + budget → output brand kit + logo prompt + 10 captions + 5 threads + 3 scripts + 30-day campaign + 9 IG grid + 3 thumbnails. Pipeline DAG dengan Debate Ring di setiap layer.
2. Debate Ring REAL: POST /creative/debate — input: topic + 2 persona (e.g., Copywriter vs Strategist) → Qwen-powered debate 3 rounds → consensus output + critique score.
3. Self-Train Fase 1: curator_agent.py — rule-based scoring (relevance × sanad_tier × maqashid × dedupe). Cron weekly corpus_to_training.py → JSONL (min 100-300 pair/minggu). Endpoint /training/stats — dashboard.

PLAN (10 step konkret):
1. Agency Kit: Buat apps/brain_qa/brain_qa/agency_kit.py — Pipeline DAG (brand_builder → content_planner → copywriter ×3 + campaign_strategist → thumbnail_generator ×3). Wire ke generate_sidix (self-hosted).
2. Agency Kit: Tambah endpoint POST /creative/agency_kit + GET /creative/agency_kit/{job_id}/status di agent_serve.py.
3. Debate Ring: Buat apps/brain_qa/brain_qa/debate_ring.py — 3-round debate (Creator vs Critic), wire ke generate_sidix, consensus aggregation, CQF scoring.
4. Debate Ring: Tambah endpoint POST /creative/debate di agent_serve.py.
5. Self-Train: Update apps/brain_qa/brain_qa/curator_agent.py — rule-based scoring, PREMIUM_SCORE=0.85 filter → lora_premium_pairs.jsonl.
6. Self-Train: Buat scripts/corpus_to_training.py — convert corpus ke JSONL instruction-tuning format, weekly cron.
7. Self-Train: Tambah endpoint GET /training/stats di agent_serve.py.
8. Frontend: Agency Kit wizard UI di index.html + main.ts (form input, progress bar, result gallery).
9. Integration test: py_compile semua backend, build frontend, smoke test endpoint.
10. Commit + deploy ke VPS.

RISKS:
- Agency Kit pipeline bisa lambat (5-10 menit) → mitigation: async background job dengan status polling.
- Debate Ring 3 round × 2 persona = 6 LLM calls → mitigation: parallel call, timeout per round 30s.
- Self-Train JSONL quality → mitigation: curator scoring strict, human review gate sebelum masuk training.
═══════════════════════════════════════════════════════════
