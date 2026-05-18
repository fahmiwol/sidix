# AGENT_WORK_LOCK.md — Koordinasi Anti-Bentrok Claude × Kimi

**Tujuan**: Mencegah dua agent AI (Claude + Kimi) mengedit file yang sama secara bersamaan,
yang bisa menghasilkan merge conflict atau logic yang saling override.

**Dibuat**: 2026-04-25 (Jiwa Sprint 4 — insiden bentrok pertama terdeteksi)

---

## ⚙️ Protokol Anti-Bentrok

### Sebelum edit file apapun:
1. Baca section "FILE OWNERSHIP" di bawah
2. Kalau file masuk zona "MILIK KIMI" → **STOP, jangan edit**
3. Kalau file masuk zona "MILIK CLAUDE" → **STOP, jangan edit** (untuk Kimi)
4. Kalau file masuk "SHARED" → baca aturan khusus di bawah
5. Kalau tidak yakin → **tulis di LIVING_LOG dulu, minta konfirmasi user**

### Aturan SHARED files:
- Selalu edit di section yang terpisah (tandai dengan `# ── [NAMA AGENT] ──`)
- Jangan hapus atau restructure kode milik agent lain
- Kalau terpaksa overlapping → **komit TERPISAH dengan pesan "MERGE: [alasan]"**

---

## 🗂️ FILE OWNERSHIP

### 🔵 MILIK CLAUDE (Core Brain, Deploy, Tests)

```
agent_serve.py          ← HTTP endpoints, ChatResponse model, helpers
agent_react.py          ← ReAct loop orchestration, AgentSession dataclass
agent_tools.py          ← Tool registry, TOOL_REGISTRY
sensor_hub.py           ← Sense registry + probe_all()
stream_buffer.py        ← Persistent stream buffer (Jiwa Sprint 4)
scripts/_vps_deploy*.py ← Deploy helpers
scripts/_test_*.py      ← Smoke tests
docs/LIVING_LOG.md      ← Log harian (both dapat append, TIDAK overwrite)
docs/AGENT_WORK_LOCK.md ← File ini
brain/public/research_notes/  ← Both dapat tambah note baru (tidak edit punya orang lain)
```

**Claude yang handle**: wiring semua Jiwa modules ke agent_serve + agent_react,
endpoint baru, deploy ke VPS, full test suite run, commit final.

---

### 🟠 MILIK KIMI (Jiwa Modules, Creative, Emotional)

```
parallel_executor.py         ← Parallel tool execution engine
jiwa/                        ← Semua file dalam folder jiwa/
emotional_tone_engine.py     ← Emotion detection
persona_voice_calibration.py ← Voice calibration per persona
creative_writing.py          ← Creative writing engine
multimodal_creative.py       ← Multimodal creative pipeline
emotional_orchestrator.py    ← Multi-sense emotion aggregation
aesthetic_judgment.py        ← Aesthetic scorer
sensor_fusion.py             ← Sensor fusion engine
sense_stream.py              ← Event bus (kecuali method event_count() milik Claude)
multimodal_input.py          ← Multimodal input handler
parallel_planner.py          ← Parallel tool planner
wisdom_gate.py               ← Wisdom/reflection gate
socratic_probe.py            ← Socratic reasoning
analogical_reasoning.py      ← Analogy engine
jariyah_monitor.py           ← Rate monitor
identity.py                  ← SIDIX character/identity
```

**Kimi yang handle**: implement, test, refine semua modul Jiwa. Kimi TIDAK
deploy ke VPS langsung — serahkan ke Claude setelah modul siap.

---

### 🟡 SHARED — Hati-hati, gunakan section marker

```
cot_system_prompts.py    ← Kimi edit PERSONA_DESCRIPTIONS, Claude edit EPISTEMIK_REQUIREMENT
sidix_constitution.py   ← Kimi tambah etika Jiwa, Claude tambah epistemic rules
agent_react.py          ← KHUSUS: Kimi edit di bagian "# ── Jiwa/Emotion wiring ──"
                          Claude edit di bagian "# ── Core ReAct logic ──"
ollama_llm.py           ← Kimi: PERSONA tone, Claude: routing + SIDIX_SYSTEM
```

**ATURAN KHUSUS agent_react.py**:
- Kimi: tambah wiring di blok yang ditandai `# ── JIWA INTEGRATION ──`
- Claude: tidak sentuh parallel_executor integration (biarkan Kimi)
- Kedua agent: TIDAK restructure function signature `run_react()` tanpa diskusi

---

## 🚦 Zona Merah Aktif (Update saat bekerja)

| Tanggal | Agent | File | Status |
|---|---|---|---|
| 2026-04-25 | Kimi | `parallel_executor.py` | 🔄 IN PROGRESS — tambah `execute_plan()` |
| 2026-04-25 | Kimi | `agent_react.py` | 🔄 IN PROGRESS — wire `execute_plan()` ke parallel path |
| 2026-04-25 | Claude | `agent_serve.py` | ✅ DONE — Sprint 4 committed (99c6359) |
| 2026-04-25 | Claude | `agent_react.py` | ✅ DONE — planner_used fields + metadata wiring |

**⚠️ CONFLICT WARNING**: Kimi dan Claude sama-sama sentuh `agent_react.py` parallel section.
Setelah Kimi commit, harus dilakukan merge manual: pertahankan `session.planner_used`,
`session.planner_savings` dari Claude + `execute_plan()` dari Kimi.

---

## 🔀 Merge Protocol (saat ada overlap)

Ketika dua agent commit ke file yang sama:

```bash
# 1. Cek conflict
git diff HEAD..origin/main -- <file>

# 2. Aturan merge:
#    - Kode Kimi (Jiwa modules) → keep Kimi's version
#    - Kode Claude (session fields, endpoint logic) → keep Claude's version
#    - Kalau truly overlap → tanya user

# 3. Setelah merge, WAJIB run full test suite
python -m pytest apps/brain_qa/tests/ -q --tb=short

# 4. Commit merge dengan prefix "merge:"
git commit -m "merge: [Kimi execute_plan + Claude planner metadata] agent_react.py"
```

---

## 📋 Checklist Sebelum Commit (kedua agent)

- [ ] Baca FILE OWNERSHIP di atas
- [ ] Tidak ada edit ke file milik agent lain
- [ ] Kalau SHARED → section marker terpasang
- [ ] `python -m pytest apps/brain_qa/tests/ -q --tb=no` → 0 fail
- [ ] LIVING_LOG diupdate dengan tag yang benar
- [ ] Research note ditulis (kalau ada knowledge baru)

---

## 📚 Sejarah Insiden

| Tanggal | Tipe | File | Resolusi |
|---|---|---|---|
| 2026-04-25 | Near-miss overlap | `agent_react.py` parallel section | Deteksi dini via screenshot user. Kimi finish dulu, Claude merge setelah. |
