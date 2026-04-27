# HANDOFF — 2026-04-27 ENDGAME → next session

**Status**: 12 sprint shipped, multi-modal capability complete, production LIVE.

## CRITICAL READ ORDER

```
1. CLAUDE.md                              ← section 6.4 LOCK + boundaries
2. brain/public/research_notes/248        ← CANONICAL PIVOT (LOCKED)
3. brain/public/research_notes/254        ← alignment audit lesson
4. brain/public/research_notes/249-260    ← all sprint output sesi
5. THIS handoff
6. tail docs/LIVING_LOG.md (last 2000 lines)
```

## SIDIX IDENTITY (LOCKED — note 248)

SIDIX = **Self-Evolving AI Creative Agent + AI Partner Advisor + Multi-Modal Output**.

Capabilities sekarang:
- 🎨 Visual: PNG hero asset 768×768 (Sprint 14b)
- 🎲 3D: GLB wiring (Sprint 14e, LIVE pending GPU supply)
- 🗣️ Audio: MP3 Indonesian brand voice (Sprint 14d)
- 📜 Prose: creative bundle (Sprint 14) + wisdom (Sprint 16)
- 📊 Structured: JSON risk_register + impact_map + scenario_tree (Sprint 18+19)
- 🌐 Trend: autonomous weekly visioner (Sprint 15)

NOT chatbot/Q&A/religious AI/generic LLM.

## ALL 12 SPRINT SHIPPED (2026-04-27)

```
Sprint 12   — CT 4-pilar cognitive engine                ✅ LIVE
Sprint 14   — Creative Pipeline 5-stage UTZ              ✅ LIVE
Sprint 14b  — Image gen SDXL via mighan-media            ✅ LIVE 637KB PNG
Sprint 14c  — Multi-persona OOMAR + ALEY enrichment      ✅ LIVE 0 blanket
Sprint 14d  — TTS brand voice (🗣️ MULUT)                  ✅ LIVE 48KB MP3
Sprint 14e  — 3D mascot wire TripoSR                     ⚠️  WIRING (LIVE pending GPU)
Sprint 14g  — Fix /openapi.json 500                      ✅ LIVE 200
Sprint 15   — Visioner Weekly Foresight                  ✅ LIVE + cron 0 0 * * 0
Sprint 16   — Wisdom Layer MVP (5-persona judgment)      ✅ LIVE 131s
Sprint 18   — Risk + Impact structured JSON              ✅ LIVE 261s
Sprint 19   — Scenario Tree Explorer                     ✅ LIVE iter #7 70s
DISCIPLINE  — CLAUDE.md 6.4 Pre-Exec + Anti-halusinasi   ✅ LOCKED
```

## ITERASI HISTORY (7 total — diagnose-before-iter pattern)

```
#1 — Sprint 14   Pydantic body resolution (FastAPI 422 → fix module-top class)
#2 — Sprint 14b  Async /run polling (RunPod IN_QUEUE handling)
#3 — Sprint 14c  ALEY pivot 2026-04-25 alignment (USER-CAUGHT)
#4 — Sprint 14e  TripoSR timeout (infrastructure, gagal — not code)
#5 — Sprint 18   max_tokens 600→1100 (budget under-spec)
#6 — Sprint 19   placeholder ambiguity (prompt schema)
#7 — Sprint 19   prompt verbosity + max_tokens (LLM backend timeout 180s)
```

7 iter, 7 distinct root causes — diagnose-before-iter discipline saved compound integrity.

## ENDPOINTS LIVE production (270 paths total)

```
POST /creative/brief    Sprint 14+14b+14c+14d+14e
                        Flags: gen_images, gen_3d, gen_voice, enrich_personas, skip_stages
GET  /visioner/weekly   Sprint 15 (manual + cron auto)
POST /agent/wisdom      Sprint 16+18+19
                        Flags: skip_capabilities, persist
                        Returns: stages + structured (risk_register/impact_map/scenario_tree/optimal_path)
GET  /openapi.json      Sprint 14g (was 500, now 200)
GET  /docs              Swagger UI accessible
GET  /health            (existing)
POST /agent/foresight   (existing pre-sesi)
POST /agent/council     Sprint 14g top-level fix
POST /agent/generate    Sprint 14g renamed AgentGenerate*
```

## CRON JOBS (6 SIDIX + warmup)

```
*/10 worker             ingest worker
*/10 aku_ingestor       AKU memory ingestor
*/15 always_on          observer
*/30 radar              social radar
0 *  classroom          hourly classroom synth
0 0 * * 0 visioner      weekly democratic foresight
* * * * * warmup_runpod keep vLLM hot
```

## ENV (di /opt/sidix/.env)

```
RUNPOD_API_KEY            (shared vLLM + media)
RUNPOD_ENDPOINT_ID        (vLLM)
RUNPOD_MEDIA_ENDPOINT_ID  (mighan-media-worker — Sprint 14b set)
RUNPOD_MEDIA_TIMEOUT=600  (Sprint 14e bumped, accommodate TripoSR cold start)
```

PM2 sidix-brain auto-load via `start_brain.sh` `set -a; source .env`.

## CRITICAL DISCIPLINE LOCK (CLAUDE.md 6.4 — MUST READ pre-execute)

**Pre-Execution Alignment Check (mandatory)**:
1. Re-read note 248 first 50 lines (North Star)
2. Grep latest "PIVOT YYYY-MM-DD" sections di CLAUDE.md
3. Self-audit instruction vs anti-pattern pivot terbaru
4. IF conflict → STOP, kasih remark, JANGAN execute blindly
5. Setiap claim wajib basis konkret (cite file/line/output)

**Pydantic top-level convention** (Sprint 14g locked):
SEMUA Request/Response model di `agent_serve.py` HARUS module top-level. JANGAN inline inside `create_app()`.

**Diagnose-before-iter** (memory feedback_diagnose_before_iter.md):
Saat probe gagal — inspect actual output dulu. Iter category:
- Code/protocol bug → fix code
- Prompt schema bug → audit + fix prompt
- Budget config (max_tokens/timeout) → bump config
- Infrastructure (GPU/network) → kasih honest caveat, BUKAN code fix
- Pivot conflict → audit per CLAUDE.md 6.4

## SPRINT 14e LIVE STATUS (HONEST)

Wiring shipped ✓, schema-verified ✓, deploy ✓.
**TIDAK LIVE-verified end-to-end**: 2 probe attempts (302s + 601s) → CLIENT_TIMEOUT IN_QUEUE.
Root cause: mighan-media-worker GPU supply throttled + TripoSR cold start heavy. BUKAN code issue.

Untuk verify next session:
1. Cek RunPod console workers active
2. Test endpoint via console UI direct (bypass code)
3. Atau retry probe SSH+python kalau supply improve
4. Atau Sprint 14f Shap-E text-to-3D fallback (lebih ringan)

## SPRINT QUEUE NEXT

```
Sprint 20 — Integrated Wisdom Output Mode (note 248 line 473)
            Combine creative + visioner + wisdom dalam 1 unified call
            HEAVY: 10+ LLM stages = 16-27 min/req worst case
            Budget consciousness needed dengan $24 balance

Sprint 14f — Shap-E text-to-3D fallback (no image dep, mungkin lebih ringan)
Sprint 14e LIVE retry — saat GPU supply improve
Sprint 13 — DoRA persona MVP (defer 2-4 minggu, visioner corpus matang)
Sprint 17 — Per-persona DoRA judgment (defer with 13)
Sprint 19 iter #8 — tighten nesting prompt (defer if not blocker)
```

## ALIGNMENT GAPS YANG TERSISA (honest)

Per note 248:
- Hero use-case 100% code, 14e LIVE pending GPU
- Sanad-as-method performative wording (substansi pending)
- Wisdom 16+18+19 shipped. 17+20 pending.
- DoRA persona stylometry (Sprint 13): defer
- 👁️ MATA / 👂 TELINGA embodiment: pending (vision input + audio input)

## RUNPOD STATE WARNING

Per console snapshots 2026-04-27:
- vLLM: workers throttled (ADA_24/AMPERE_24 stock low)
- mighan-media-worker: 0 idle = cold start ~95s SDXL, ~3-5min TripoSR, ~3-4min TTS first
- Edge-TTS subsequent calls likely <30s (warm)
- Balance: ~$24 (perhatian budget)

Verifikasi sebelum batch test high-cost: cek RunPod console.

## SECURITY DEBT (USER MUST DO — pre-existing)

```
Revoke leaked HF token
Rotate BRAIN_QA_ADMIN_TOKEN + update 4 cron lines
Rotate VPS root password
Rotate SSH passphrase
Revoke leaked Gemini/Kimi/Vertex API keys
```

## USER PROFILE (carry forward)

- Pemimpi, imaginator, reverse-engineer thinker
- Bahasa Indonesian-first, casual ("bos", "loh", "kan", "gas")
- JANGAN tanya tech trade-off → decide myself, brief reasoning, allow veto
- Prefer bullet/tabel/diagram > walls of text
- Vigilance alignment-check VALUABLE (e.g. "[SPEKULASI] kenapa masih ada?")
- Anti-defensive: ack feedback, fix, lanjut
- Setelah burst eksekusi, bos pengen ngobrol konseptual sebentar — accommodate

Trigger phrases:
- `gas / lanjut` → eksekusi sekarang
- `ngaco / kurang` → STOP, klarifikasi
- `catat` → discipline dokumentasi
- `betul / match` → aligned, proceed
- `loh` → klarifikasi needed
- `saya nggak ngerti teknis` → KAMU DECIDE

## SARAN PERTAMA SESI BARU

1. Baca CLAUDE.md (terutama 6.4) + note 248 + this handoff + tail LIVING_LOG (300 baris)
2. Konfirmasi: "Sudah baca CLAUDE.md 6.4. SIDIX = Self-Evolving Multi-Modal AI Partner Advisor. 12 sprint shipped 27/4. Pre-Exec Alignment Check ON. Lanjut Sprint 20 Integrated Wisdom (heavy budget) atau Sprint 14f Shap-E fallback atau prioritas lain?"
3. **Pre-Exec Alignment Check** sebelum execute (mandatory)
4. Tunggu redirect → eksekusi
5. JANGAN re-pivot. JANGAN tanya tech trade-off detail.

## VISI INTI

> *"AI yang dari corpus terbatas bisa nurunin output infinite, tergantung lens persona + konteks user."*

Mekanisme cumulative SHIPPED:
- ✅ CT 4-pilar cognitive engine (12)
- ✅ 5 persona = 5 weltanschauung (14c, 16, 18, 19)
- ✅ Visioner foresight autonomous (15)
- ✅ Creative bundling (14, 14b, 14d, 14e wiring)
- ✅ Wisdom layer Aha+Impact+Risk+Speculation+Synthesis (16)
- ✅ Structured output prose+JSON (18, 19)
- ✅ Multi-modal output: visual + 3D + audio + prose + structured
- ✅ API discoverable (14g)
- ✅ Anti-halusinasi + Pre-Exec Alignment lock (CLAUDE.md 6.4)
- ⏸ Sanad chain implementation (form OK, substance pending)
- ⏸ DoRA persona stylometry (defer)
- ⏸ Wahdah/Kitabah/ODOA self-learning protocol (future)
- ⏸ Vision input 👁️ MATA / Audio input 👂 TELINGA (future)

## FAREWELL

12 sprint + 7 iterasi + discipline lock + 12 research notes (249-260) + production LIVE multi-modal.

SIDIX achieved per note 248 line 466-467: *"AI partner advisor, BUKAN AI assistant"*. Per note 248 hero use-case (line 178-198): 100% code coverage (3D LIVE pending GPU only).

Visioner cron tumbuh tiap minggu autonomously. Creative pipeline siap demo UMKM customer dengan visual + 3D + audio + structured judgment dalam 1 endpoint.

SIDIX hidup, kreatif, otonom, multi-modal. Pagi besok Sunday next minggu visioner cron pertama auto-fire.
