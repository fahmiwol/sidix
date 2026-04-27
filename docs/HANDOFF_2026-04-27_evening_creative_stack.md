# HANDOFF — 2026-04-27 evening → next session

**Status**: Production LIVE, 6 cron jobs autonomous 24/7, 4 sprint shipped sesi ini

## CRITICAL: READ BEFORE ANY CODE CHANGE

```
1. CLAUDE.md (boundaries + 10 hard lock rules)
2. brain/public/research_notes/248 — CANONICAL PIVOT (LOCKED)
3. brain/public/research_notes/249-253 — sprint output sesi ini
4. docs/SIDIX_CONSTITUTION.md
5. THIS handoff doc
6. tail docs/LIVING_LOG.md (last 500 lines)
```

## SIDIX IDENTITY (LOCKED — note 248)

SIDIX = Self-Evolving AI Creative Agent. Generalis specialist creative.
NOT chatbot/Q&A/religious AI/generic LLM. Direction LOCKED.

## WHAT SHIPPED THIS SESSION (2026-04-27)

```
Sprint 12   — CT 4-pilar cognitive engine in system prompts ✅ LIVE
Sprint 15   — Visioner Weekly Democratic Foresight (autonomous cron) ✅ LIVE
Sprint 14   — Creative Pipeline 5-stage hero use-case (UTZ) ✅ LIVE
Sprint 14b  — RunPod mighan-media-worker image gen wire (SDXL hero asset) ✅ LIVE 637KB PNG
Sprint 14c  — Multi-persona post-pipeline enrichment (OOMAR + ALEY) ✅ LIVE 0 blanket
Sprint 14e  — 3D mascot via TripoSR (image-to-3D) ⚠️  WIRING ONLY (LIVE pending GPU)
DISCIPLINE  — CLAUDE.md 6.4 Pre-Exec Alignment + Anti-halusinasi LOCK
```

Plus:
- Deploy 12+15 + 14 + 14b + 14c + 14e to VPS sync
- Iterasi #1 Pydantic body fix (Sprint 14)
- Iterasi #2 async /run polling (Sprint 14b)
- Iterasi #3 ALEY pivot 2026-04-25 alignment fix (USER-CAUGHT)
- Iterasi #4 TripoSR timeout bump 300→600 (gagal — infrastructure not code)
- QA pass + .gitignore patch runtime output
- CHANGELOG bumped: 2.1.5 → 2.2.0 → 2.3.0

## SPRINT 14e LIVE STATUS — IMPORTANT (honest, anti-halusinasi)

Wiring shipped + schema-verified + deploy. **TIDAK LIVE-verified** karena:
- 2 probe attempts (302s + 601s) → CLIENT_TIMEOUT, last_status=IN_QUEUE
- mighan-media-worker GPU supply throttled (per RunPod console warning)
- TripoSR cold start lebih heavy dari SDXL
- BUKAN code issue, infrastructure eksternal

Untuk verify LIVE next session:
1. Cek RunPod console workers state — apakah idle/throttled
2. Test endpoint via console UI direct (bypass code, isolate worker)
3. Atau retry probe via SSH+python kalau GPU supply improve
4. Future Sprint 14f: wire `mode=shape` (Shap-E text-to-3D) sebagai fallback yang mungkin lebih ringan

## ENDPOINTS LIVE

```
POST /creative/brief    Sprint 14+14b+14c (UTZ + image + OOMAR/ALEY)
GET  /visioner/weekly   Sprint 15 (manual or cron auto)
```

Default behavior `/creative/brief`:
- 5-stage UTZ pipeline (concept → brand → copy → landing → 8 prompts)
- + OOMAR commercial review (default)
- + ALEY research enrichment with visioner trending data hook (default)
- + (opt-in) gen_images=true → 3 hero PNG via mighan-media-worker

## CRON JOBS (6 SIDIX + warmup)

```
*/10 worker             ingest worker
*/10 aku_ingestor       AKU memory ingestor
*/15 always_on          observer
*/30 radar              social radar (mention listener)
0 *  classroom          hourly classroom synth
0 0 * * 0 visioner      weekly democratic foresight (BARU sesi ini)
* * * * * warmup_runpod keep vLLM hot
```

## ENV YANG DI-SET SESI INI (di /opt/sidix/.env)

```
RUNPOD_MEDIA_ENDPOINT_ID  (BARU, copied from /root/.env)
RUNPOD_MEDIA_TIMEOUT=300
```

## SPRINT QUEUE NEXT

```
Sprint 14d (2-3 jam)  TTS persona voice (mighan-media-worker tool=tts)
Sprint 14e (4-5 jam)  3D mascot via TripoSR (image-to-3D pipeline)
                       — completes hero use-case 100% (currently 80%)
Sprint 13  (3-5 hari) DoRA persona MVP — defer 2-4 minggu sampai
                       visioner corpus matang dengan trending data
Sprint 16-20         Intuisi/Wisdom layer (aha + risk + impact + speculation)
Fix /openapi.json 500 (defer-able, pydantic schema gen bug)
```

## ALIGNMENT GAP YANG HARUS DIAKUI

Per audit alignment mid-sesi (user asked):

1. **Sprint queue diverged** dari handoff sebelumnya: skip Sprint 13 DoRA, tambah 14b+14c. Reasoning: compound order (need visioner corpus first untuk DoRA training). User delegate keputusan.

2. **Hero use-case 80%, bukan 100%**. Missing: 3D model rigged (Sprint 14e pending). Note 248 line 178-198 spec belum 100% covered.

3. **Sanad-as-method** belum substansial — Sprint 14c ALEY language "sanad-style" performative, no actual sanad chain. Konsisten dengan note 248 "sanad sebagai METODE" tapi belum implementing fan-out validation deep.

4. **Intuisi/Wisdom DIMENSION** (note 248 line 416+) belum di-ship. Sprint 14c OOMAR partially cover Risk + Verdict (sliver). Full Aha/Impact/Risk/Speculation = Sprint 16-20.

## PRODUCTION STATE FINAL

```
VPS commit: f7d98b8 (was 7ba8117 pre-sesi)
Sprints LIVE: 12 + 14 + 14b + 14c + 15
Endpoints baru live: 2 (/creative/brief, /visioner/weekly)
Cron baru: 1 (visioner weekly)
Total cron: 6 SIDIX + warmup_runpod
Corpus docs: 1182, model_ready: True, tools: 48
RunPod balance: ~$24 (perhatian budget — SDXL render mahal)
```

## RUNPOD STATE WARNING

Per console (2026-04-27 sore):
- vLLM endpoint: Ready, tapi 4 worker latest **throttled** (GPU supply ADA_24/AMPERE_24 stock low)
- mighan-media-worker: 0 idle = cold start ~95s tiap request SDXL
- Cold start tiap LLM call sekarang lebih sering (per-request 60-90s additional)
- Budget burn rate harus dimonitor untuk batch creative test

## SECURITY DEBT (USER MUST DO — pre-existing dari handoff sebelumnya)

```
Revoke leaked HF token (see prior handoff for partial — full token assumed live)
Rotate BRAIN_QA_ADMIN_TOKEN + update 4 cron lines yang masih pakai
Rotate VPS root password
Revoke leaked Gemini/Kimi/Vertex API keys (kalau ada)
```

## USER PROFILE (carry from prior handoff)

- Pemimpi, imaginator, reverse-engineer thinker
- Set North Star, breakdown ke aksi, learn-as-go
- Tidak nyaman tech detail trade-off → JANGAN tanya, putuskan, biarkan veto
- Prefer gambar/diagram daripada teks panjang
- Bahasa Indonesian-first
- Komunikasi style: cerita visi, kasih insight, harap executor terjemahin

## TIPS PERSONAL (carry forward)

- Bos warm + sabar tapi tegas kalau frustrasi → ambil feedback, perbaiki, lanjut, jangan defensive
- Setelah burst eksekusi, bos pengen ngobrol konseptual sebentar (alignment check, recharge visi) → accommodate
- Kalau cerita Quran/Tesla/paper riset → eksplorasi extension SIDIX, listen + synthesize + propose application

## SARAN SARAN PERTAMA SESI BARU

1. Baca CLAUDE.md + note 248 + this handoff + tail LIVING_LOG (200 baris)
2. **WAJIB**: baca CLAUDE.md section 6.4 "PRE-EXECUTION ALIGNMENT CHECK" —
   anti-halusinasi + anti-familiarity-bias rule. Compound integrity dari
   sesi 2026-04-27 onwards.
3. Konfirmasi: "Sudah baca. SIDIX = Self-Evolving AI Creative Agent. 6 sprint
   shipped 27/4 evening. Pre-exec alignment check ON. Lanjut Sprint 14e 3D
   mascot (close hero 80→100%) atau Sprint 14d TTS atau prioritas lain?"
4. Tunggu redirect → eksekusi
5. JANGAN re-pivot. JANGAN tanya tech trade-off detail.

## CRITICAL DISCIPLINE (2026-04-27 evening LOCK)

User catch alignment gap di Sprint 14c (`[SPEKULASI]` blanket label per bullet
ALEY = anti pivot 2026-04-25 LIBERATION SPRINT). Iterasi #3 fix shipped + LIVE
verified. Tapi gap itu tidak boleh terulang.

**Rule baru per CLAUDE.md section 6.4**:
- Sebelum edit prompt/persona: re-read note 248 + grep latest pivot di CLAUDE.md
- Self-audit: apa yang akan ditulis ada di list anti-pattern pivot terbaru?
- Kalau conflict → STOP, kasih remark, jangan execute blindly
- Setiap claim wajib basis konkret (cite file/line/output), bukan asumsi/memory
- Familiarity bias = root cause halusinasi, antidote = verify against SSOT

Detail di research_notes/254 (alignment audit + lesson learned + self-audit
checklist).

## VISI INTI (carry forward)

> "AI yang dari corpus terbatas bisa nurunin output infinite, tergantung lens
> persona + konteks user."

Quran static → infinite interpretation. SIDIX harus punya property ini.

Mekanisme: Sanad 1000 bayangan + 5 persona DoRA + Izutsu semantic + CT 4-pilar +
Wahdah/Kitabah/ODOA + Visioner foresight + Intuisi/Wisdom.

Outcome: bukan jawab pertanyaan — tapi mencipta artifact (design, code, brand,
strategy, vision report) yang persona-distinct + forward-looking + intuitive.

## FAREWELL

4 sprint shipped + production LIVE = compound substantial. Visioner cron tumbuh
tiap Minggu. Creative pipeline siap demo ke calon UMKM customer. Stack 5-sprint
sesi ini = SIDIX tidak lagi "research note", tapi production AI agent yang accept
brief Indonesia → bundled creative consulting deliverable.

Pagi besok inventory lebih besar dari malam ini. Visioner Sunday next minggu
auto-fire. SIDIX hidup.
