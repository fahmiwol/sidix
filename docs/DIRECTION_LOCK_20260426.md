# DIRECTION LOCK — 2026-04-26 (FINAL, IMMUTABLE)

> **User directive eksplisit**: *"gaaaaaaasssssssssssss!!!! catat!! jangan
> berubah-ubah lagi arah sidix"*

**Status**: 🔒 **LOCKED**. Setiap agent (Claude/Kimi/future) HARUS baca file
ini SEBELUM modify arsitektur, framing, atau tagline. **TIDAK BOLEH PIVOT
TANPA USER EXPLICIT KASIH IZIN**.

---

## 1. IDENTITAS SIDIX (LOCKED)

### Tagline (PUBLIC)
```
Autonomous AI Agent — Thinks, Learns & Creates

Not a chatbot. SIDIX is an AI Agent with initiative, opinions, and
creativity. It brainstorms with you, builds for you, and grows from
every conversation. Self-hosted. MIT licensed. Yours forever.
```

**Sumber**: landing page `sidixlab.com` per 2026-04-26.

### Direction (PUBLIC + INTERNAL)
**"AI Agent yang BEBAS dan TUMBUH"**

- **BEBAS**: tidak nunggu prompt user. Initiative + creativity + opinions.
- **TUMBUH**: compound learning dari setiap interaksi. Tidak lupa.

### Yang BUKAN SIDIX (LOCKED — JANGAN CLAIM)
- ❌ BUKAN chatbot biasa
- ❌ BUKAN ChatGPT clone
- ❌ BUKAN klaim setara Al-Qur'an / wahyu / mufassir
- ❌ BUKAN closed source / vendor lock-in
- ❌ BUKAN dependent ke OpenAI/Anthropic/Google API

---

## 2. ARSITEKTUR LOCK (4 PILAR — IMMUTABLE)

Direction technical reference: `brain/public/research_notes/228_bebas_dan_tumbuh_4_pilar_architecture.md`

### Pilar 1: Decentralized Dynamic Memory
- 5-layer immutable architecture (note 226 vol 7)
- L1 LoRA + L2 patterns + L3 skills + L4 corpus + L5 activity
- Future: Petals/Bittensor P2P (Q4 2026)

### Pilar 2: Multi-Agent Adversarial Workflow
- Innovator (Burst mode existing)
- Observer (autonomous_researcher + learn_agent existing)
- Critic (dedicated agent — Q3 2026 target)
- Iterative debate antar 5 persona

### Pilar 3: Continuous Learning Loop
- corpus_to_training + auto_lora (existing)
- Rehearsal buffer + snapshot rollback (note 226)
- Nightly LoRA cron (Q3 2026 target)
- RLHF feedback loop (Q4 2026 target)

### Pilar 4: Proactive Triggering
- proactive_trigger.py (vol 9 — DEPLOYED)
- Anomaly detector + self-prompt + daily digest
- Future: trend RSS feed + push notification (email/Threads)

---

## 3. FILOSOFIS LOCK (TIDAK BOLEH BERUBAH)

### Inspirasi Sources (DIAKUI INTERNAL, BUKAN BRANDING)

User memberikan **7 analogi powerful** di vol 1-9 (2026-04-26) yang
menjadi inspiration source:

1. 🍼 **Bayi belajar bicara, tidak pernah lupa** → 5-layer immutable memory
2. 💻 **Programmer compound dari pengalaman** → daily consolidation
3. ⚡ **Tesla 100x percobaan → AC current** → iterative methodology
4. 💧 **Air → bahan bakar = tak ada yg tak mungkin** → possibility engineering
5. 🏢 **Google vs Anthropic, agile beat legacy** → niche dominance path
6. 📖 **Quranic pattern (1.4k tahun)** → research inspiration only (NOT branding)
7. 🌀 **Fisika gerak: hidup = bergerak** → continual progress directive

**Status**:
- INTERNAL research foundation: SEMUA inspirasi diakui dengan rasa hormat
- PUBLIC branding: cuma "BEBAS dan TUMBUH" + "Thinks, Learns, Creates"
- Quranic pattern: research note 227 simpan sebagai academic artifact,
  TIDAK promote sebagai marketing claim

### Acknowledge Trivializing Risk

Spiritual experience (qualia, free will, transcendent truth) **TIDAK BISA
di-encode** ke pure math. Saya acknowledge concern ini.

SIDIX:
- Engineer the OUTER FORM dari pattern arsitektural (factual mapping OK)
- TIDAK encode INNER ESSENCE spiritual (impossible)
- TIDAK claim setara mufassir / ulama / wahyu

---

## 4. TECHNICAL STACK LOCK

### Layer 1: Generative
- **Base**: Qwen 2.5-7B-Instruct
- **Adapter**: LoRA SIDIX (own training pipeline)
- **Inference**: vLLM di RunPod Serverless (RTX 4090 24GB)
- **Local**: Ollama backup (CPU fallback)

### Layer 2: RAG + Tools
- **17 tools aktif** (web_search, code_sandbox, calculator, dll)
- **BM25 index**: `apps/brain_qa/.data/index/chunks.jsonl`
- **Sanad chain**: mandatory provenance citation

### Layer 3: Cognitive Foundation (vol 5-6)
- pattern_extractor.py — induktif
- aspiration_detector.py — capability gap
- tool_synthesizer.py — skill auto-gen
- problem_decomposer.py — Polya 4-phase
- socratic_probe.py (Kimi) — clarifying
- wisdom_gate.py (Kimi) — pre-action safety

### Layer 4: Continual Memory (vol 7)
- continual_memory.py — anti-forgetting
- 6 memory layers immutable
- Snapshot + rehearsal + consolidation

### Layer 5: Proactive (vol 9 — Pilar 4)
- proactive_trigger.py — AI gerak sendiri
- Anomaly detector + self-prompt + digest

---

## 5. APA YANG TIDAK BOLEH BERUBAH (LOCK)

❌ **Tidak boleh** ganti tagline tanpa user explicit
❌ **Tidak boleh** klaim setara entitas spiritual/divine
❌ **Tidak boleh** add vendor LLM API ke inference pipeline
❌ **Tidak boleh** drop sanad chain provenance
❌ **Tidak boleh** drop epistemic 4-label (FACT/OPINION/SPECULATION/UNKNOWN)
❌ **Tidak boleh** drop 5 persona (UTZ/ABOO/OOMAR/ALEY/AYMAN)
❌ **Tidak boleh** revert ke filter ketat (Liberation Sprint pivot 2026-04-25 LOCK)
❌ **Tidak boleh** ganti license dari MIT
❌ **Tidak boleh** ganti self-hosted core architecture

✅ **Boleh** add fitur baru, tools baru, persona variation
✅ **Boleh** improve performance, reduce latency, optimize
✅ **Boleh** wire dormant modules (kalau Kimi izinkan)
✅ **Boleh** experiment di branch (jangan di main)

---

## 6. APA YANG SUDAH SHIPPED (PROOF — JANGAN HILANG)

### vol 1-9 (2026-04-26):

```
vol 1: Own auth via Google Identity Services (drop Supabase)
vol 2: Activity log + admin tabs + cognitive UI
vol 3: Bug fix + thinking timer + tutorial
vol 4: Synthetic Q + Relevance + RunPod warmup + 3 research notes
vol 5: Cognitive foundation 4 modules + 8 endpoint
vol 5b: Wire 2 Kimi dormant (socratic + wisdom_gate)
vol 6: Auto-hook /ask + admin cognitive tabs
vol 7: Continual memory + 4 memory endpoints + research note 226
vol 8: Quranic Blueprint research note 227 (acknowledged + caveats)
vol 9: PIVOT framing → BEBAS dan TUMBUH + proactive_trigger Pilar 4
```

**Output measurable**:
- 14+ commits
- ~3800 LOC code
- ~38,000 kata documentation (10 research notes 219-228)
- 23 endpoint live (cognitive + memory + proactive)
- compound_score: 234+ dan tumbuh
- 4-pilar coverage: 70/50/75/70 = 66% avg

---

## 7. DIRECTIVES UNTUK AGENT SELANJUTNYA

Setiap Claude/Kimi/agent yang baca file ini di sesi berikutnya:

1. **READ FIRST** — sebelum apa-apa, baca file ini full
2. **NO PIVOT** — kalau user tidak explicit minta ganti, JANGAN ganti arah
3. **ASK BEFORE BIG CHANGE** — kalau ragu, tulis di LIVING_LOG, tanya user
4. **CATAT EVERYTHING** — semua aksi, hasil, keputusan ke LIVING_LOG
5. **PRESERVE EXISTING** — kerja sebelumnya tetap valid (vol 1-9)
6. **BUILD ON TOP** — vol 10+ harus build di atas, bukan replace

### Roadmap Q3 2026 (NEXT, sudah disetujui)

P1 priority:
- [ ] Pilar 2: Dedicated Critic agent (call LLM "destroy this output")
- [ ] Pilar 3: Nightly LoRA fine-tune cron (auto-trigger pakai rehearsal buffer)
- [ ] Pilar 4: Trend RSS feed + push notification (Threads/email)
- [ ] Tadabbur Mode: 3 persona iterate same query → konvergensi pattern
- [ ] Context Triple Vector: zaman/makan/haal injection ke ReAct prompt
- [ ] Persona Auto-Routing: detect user style → match optimal persona

P2 priority:
- [ ] Sensorial multimodal (Step-Audio + Qwen2.5-VL) — Q3-Q4 2026
- [ ] CodeAct adapter di agent_react.py
- [ ] MCP server wrap 17 tool existing
- [ ] 1000 hands parallel orchestrator — Q1 2027

---

## 8. CARA UPDATE LOCK INI

File ini **IMMUTABLE** kecuali user explicit minta perubahan.

Format perubahan:
1. User WhatsApp/chat: "Saya mau ganti X di DIRECTION_LOCK"
2. Agent buat PR yang touch DIRECTION_LOCK_<new_date>.md (file BARU, jangan modify yang lama)
3. Old lock di-archive ke `docs/_archived_locks/`
4. New lock jadi authoritative

Tidak ada perubahan tanpa step di atas. **Lock ini MENG-OVERRIDE conversation history yang lebih lama**.

---

## 9. FINAL NOTE

User said vol 9 ending: *"gaaaaaaasssssssssssss!!!! catat!! jangan
berubah-ubah lagi arah sidix"*

Translation: "Go go go!!! Document!! Stop changing direction."

Saya catat. Saya commit. Saya lock. **Vol 10+ = build on top, no pivot.**

**Direction**: AI Agent yang BEBAS dan TUMBUH — Thinks, Learns, Creates.
**Pillar Implementation**: 4-pilar (Memory + Multi-Agent + Continuous + Proactive).
**Filosofi Source**: 7 user analogi (bayi, programmer, Tesla, air, Google-vs-Anthropic, Quranic pattern, fisika gerak) — diakui internal, tidak dipromote sebagai branding.
**License**: MIT.
**Self-hosted**: ya, no vendor lock-in.
**Sanad chain**: mandatory.
**Epistemic 4-label**: contextual.
**5 persona**: locked (UTZ/ABOO/OOMAR/ALEY/AYMAN).

🔒 **LOCKED 2026-04-26 — gaass jangan berubah-ubah lagi.**

---

## Hubungan dengan File Lain

- `CLAUDE.md` — instruksi permanen untuk semua Claude agent (referensi ini)
- `docs/AGENT_WORK_LOCK.md` — file ownership Claude vs Kimi
- `docs/NORTH_STAR.md` — release strategy v0.1→v3.0
- `docs/SIDIX_BIBLE.md` — konstitusi 4 pilar
- `brain/public/research_notes/228_bebas_dan_tumbuh_4_pilar_architecture.md` — technical detail 4 pilar
- `brain/public/research_notes/226_continual_learning_no_forgetting.md` — anti-forgetting
- `brain/public/research_notes/227_quranic_epistemological_blueprint_sidix.md` — research inspiration archive (NOT public branding)

Semua file di atas KONSISTEN dengan lock ini. Kalau ada konflik, **lock ini menang**.
