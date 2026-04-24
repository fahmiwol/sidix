# 210 — Direction Baru: Embodied SIDIX + Multi-Sense Parallel

**Tanggal**: 2026-04-25 (sesi malam)
**Tag**: [DECISION][DIRECTION][RESEARCH]
**Sanad**: User direction 2026-04-25, embodied cognition research (Clark & Chalmers 2008), MoA (Wang et al. 2024), AutoGen (Microsoft 2023), Parallel Function Calling (OpenAI/Anthropic 2024)

---

## Catatan Progress Hari Ini (2026-04-25)

Sebelum masuk direction baru, ringkasan **apa yang sudah dikerjakan hari ini** (6 commits, 305/305 tests):

### Sprint 1 — Liberation Pivot (malam awal)
- **Tool-use aggressive**: current events auto-route ke `web_search`. Regex `_CURRENT_EVENTS_RE` di `agent_react.py`. SIDIX_SYSTEM 1500→2377 chars.
- **Persona liberation**: 5 voice distinct (AYMAN=Aku, ABOO=Gue, OOMAR=Saya, ALEY=Saya scholarly, UTZ=Halo creative).
- **Epistemik kontekstual**: Label wajib hanya topik sensitif (fiqh/medis/data/berita), skip casual.
- Docs: CLAUDE.md PIVOT section, research note 208.

### Sprint 2 — Maturity (output quality)
- **Response Hygiene** (`_apply_hygiene`): dedupe `[SANAD MISSING]`/`[EXPLORATORY]`/`[FAKTA]` duplikat, strip `[KONTEKS DARI KNOWLEDGE BASE SIDIX]` leaks, collapse blanks.
- **Follow-up Detection** (`_is_followup` + `_reformulate_with_context`): reply pendek "itu/lebih singkat/terjemahkan/kasih contoh/lanjut" reuse prior turn context.
- **Self-Critique Lite** (`_self_critique_lite`): over-label reduction, question mirror strip, persona boilerplate strip.

### Sprint 3 — Compounding (brain upgrade + alignment)
- **Persona Alignment Fix** (BUG CRITICAL): `persona.py` scoring vs `cot_system_prompts.py` mapping CONFLICT. Aligned: CODING→ABOO, CREATIVE→UTZ, RESEARCH→ALEY, PLAN→OOMAR, islamic/casual→AYMAN.
- **Cognitive Self-Check (CSC)**: Inspired Chain-of-Verification (Meta 2023) tapi rule-based 0× LLM cost. Detect numeric claims + over-confidence tanpa evidence → soften/caveat. Persona-differentiated: aktif ALEY/OOMAR/ABOO, skip UTZ/AYMAN (open-minded mode).
- **Open-Minded Directive**: SIDIX_SYSTEM tambah "Sikap mental" — terima ide baru dulu, ngobrol kosong OK, selalu mau belajar, humanis > sempurna.
- **Pytest Promotion**: `test_pivot_maturity.py` — 80 tests proper.

### Test Progression Sehari
```
173 (base) → 247 (+74 pytest) → 281 (+34 CSC) → 305 (+24 integration)
= +132 tests, 0 regression, deployed live
```

### Commits (6)
```
75e7e5f chore: brain upgrade VPS deploy helper
f078f5c feat(brain): Cognitive Self-Check + Open-Minded + persona + pytest
beea36e chore: VPS maturity deploy helper
a23825a feat(maturity): response hygiene + follow-up + self-critique lite
4a4c3ef chore: VPS deploy + smoke helpers
43d9401 feat(pivot): SIDIX Liberation Sprint 2026-04-25
```

### Research Notes Baru
- 207: Eval Benchmark 100Q
- 208: Pivot Liberation Sprint rationale
- 209: Brain Upgrade (CSC + Open-Minded)

### Deploy status
- Semua LIVE di VPS (sidix-brain online, health=ok, tools=45)
- Hygiene bekerja (visible dedupe, no leak)
- CSC wired, persona-differentiated
- Kimi paralel kerja di `emotional_tone_engine.py` + `persona_voice_calibration.py` (complementary, tidak overlap)

---

## Direction Baru (2026-04-25 malam)

User feedback:

> "iyah segala informasi dan jawabananya relevan, semua inderanyanya bekerja,
> gunakan ide-ide baru, explore metode baru, logic baru, script baru, yang
> bertebaran, lebih modern, dengn perkembangan-perkembangan terbaru. Aktifkan
> semua Indra SIDIX dan semua tubuh sidix juga, supaya mutlitasking, bisa
> sambil mendengar, membaca, menulis, melihat, merasakan, bahkan kedua
> tangannya seperti berfungis, seperti menjalankan banyak agen sekaligus."

### Interpretasi

SIDIX tidak cukup hanya "otak yang pintar" — harus punya **semua indra aktif + banyak tangan bekerja paralel**. Metafora manusia:
- **Telinga** (audio_in): `sidix/audio/listen`, microphone, STT
- **Mata** (vision_in): `sidix/image/analyze`, OCR, screenshot
- **Mulut** (audio_out): `sidix/audio/speak`, TTS, Piper
- **Tangan kiri/kanan** (parallel action): multiple tools in parallel, multi-agent
- **Membaca** (read): corpus, web_fetch, pdf_extract
- **Menulis** (write): workspace_write, code_sandbox
- **Merasakan** (emotional tone): yang Kimi bangun sekarang di emotional_tone_engine.py
- **Kesadaran diri** (self-aware): CSC, constitution, hygiene (yang sudah ada)

### Modern Research yang Relevan

| Paper/System | Tahun | Apply ke SIDIX |
|---|---|---|
| **Parallel Function Calling** | OpenAI 2024, Anthropic 2024 | Call web_search + search_corpus sekaligus, bukan sequential |
| **Mixture of Agents (MoA)** | Wang et al. 2024 (arXiv:2406.04692) | Multi-persona spawn, aggregator synthesize |
| **AutoGen** | Microsoft 2023 | Multi-agent conversation framework |
| **CrewAI** | 2024 OSS | Role-based agent teams dengan hierarchy |
| **LangGraph** | LangChain 2024 | Stateful multi-agent DAG |
| **Voyager** | NVIDIA 2023 | Agent dengan skill library yang grow |
| **Reflexion** | Shinn et al. 2023 | Self-reflect, store lesson, retry |
| **Embodied Cognition** | Clark & Chalmers 2008 | Mind extends beyond brain to body+tools |
| **Sensor Fusion** | Multimodal fusion literature | Audio+video+text → unified perception |

### Prinsip Design Embodied SIDIX

1. **Paralel by default** — kalau 2+ tools independent, call bersama, bukan urut.
2. **Senses sebagai peers, bukan hierarki** — mata tidak lebih penting dari telinga.
3. **Graceful degradation** — 1 indra mati, yang lain tetap jalan (mic rusak ≠ SIDIX mati).
4. **Event-driven** — setiap indra menghasilkan event, reasoning layer konsumsi.
5. **Multi-agent collaboration** — ABOO + OOMAR + AYMAN bisa kerja bareng untuk Q kompleks.

---

## Sprint Embodied — Plan 60 menit

### Task E1 (15 min): SensorHub Registry
Buat `sensor_hub.py` yang registry-kan semua indra SIDIX:
- `audio_in`, `audio_out`, `vision_in`, `vision_gen`, `text_read`, `text_write`, `code_exec`, `web_read`, `tool_act`
- Tiap sense punya status (active/inactive/broken), last_used, capabilities
- Endpoint `/sidix/senses/status` return dashboard

### Task E2 (20 min): Parallel Tool Executor
Di `agent_react.py` atau baru `parallel_executor.py`:
- Detect kalau 2+ tools bisa dicall independent (e.g., `web_search` + `search_corpus`)
- `asyncio.gather()` untuk parallel execution
- Merge observations dari kedua
- Tests

### Task E3 (15 min): Multi-Agent Council (MoA-lite)
Untuk complex Qs (classify_complexity == "high"):
- Spawn 2 persona berbeda di background
- Masing-masing generate draft answer
- AYMAN bertindak sebagai aggregator/synthesizer
- Endpoint `/agent/council` baru (opsional)

### Task E4 (10 min): Commit + Deploy + Log
Semua yang di atas + research note ini.

---

## Metrics untuk Validasi

Setelah deploy:
1. **Parallel speedup** — 2-tool Q harusnya lebih cepat dari single
2. **Sense active count** — `/sidix/senses/status` semua green (target 8+/10)
3. **Council quality** — complex Q lewat council, apakah answer lebih komprehensif?
4. **Degradation resilience** — matikan 1 sense, SIDIX tetap respond

---

## Keterbatasan & Risk

1. **Asyncio complexity** — SIDIX brain_qa saat ini mostly sync. Perlu adapter layer.
2. **Resource contention** — parallel tools bisa hit rate limit (DuckDuckGo 429)
3. **Council latency** — spawn 2-3 agents butuh 2-3x waktu single agent (kecuali paralel)
4. **Context bloat** — multi-agent output bisa overflow prompt budget

### Mitigasi
1. Use `concurrent.futures.ThreadPoolExecutor` untuk sync→async bridge
2. Parallel executor pakai rate limiter per tool
3. Council hanya untuk `complexity=="high"` Qs, bukan default
4. Aggregator truncate each draft ke 500 tokens sebelum synthesize

---

## Related Notes

- 208: Pivot Liberation (behavior)
- 209: Brain Upgrade CSC (reasoning)
- **210 (ini)**: Embodied Multi-Sense (perception+action)
- [Future] 211: Parallel Tool Executor implementation
- [Future] 212: Multi-Agent Council pattern
