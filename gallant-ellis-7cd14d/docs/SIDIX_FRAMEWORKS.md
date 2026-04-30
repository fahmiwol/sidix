# SIDIX FRAMEWORKS — Capture Permanen Semua Framework Bos

**Pain founder**: *"framework yang saya jelaskan setiap hari selalu ilang dan menguap"*. File ini adalah anti-menguap khusus untuk frameworks — capture once, persist forever.

**Aturan**: setiap kali bos sebut framework (dengan metafora atau eksplisit), agent WAJIB cek file ini dulu. Kalau sudah ada → refer. Kalau baru → tambahkan + translate ke implementation.

Last updated: 2026-04-30 evening

---

## Visi Chain (Locked, Verbatim)

> "**genius, creative, tumbuh → cognitive & semantic → iteratif → inovasi → pencipta**"

7-aspect capability chain. Detail per aspect: `docs/VISI_TRANSLATION_MATRIX.md`. Coverage saat ini ~73%.

---

## 4 Operating Principles (Locked 2026-04-28)

1. **ANTI-HALUSINASI** — claim grounded di basis konkret (file:line, command output, test result). *"Saya tidak yakin"* > tebak.
2. **JAWABAN HARUS BENAR** — correctness > speed untuk fakta/data/historical/sains. Multi-source validation.
3. **IDE BOS DIOLAH SAMPAI SEMPURNA** — multi-dimensi (5 persona × wisdom × KITABAH refine). Bukan reduce-to-simpler.
4. **RESPOND CEPAT · TEPAT · RELEVAN** — tier-aware latency, no off-topic verbose.

---

## Framework 1: JURUS SERIBU BAYANGAN

**Bos verbatim** (2026-04-30):
> "ga routing otmatis, tapi mengerahkan segala resource berbarengan intinya. jurus seribu bayangan dll, sanad"
> "web_search + search_corpus + persona_fanout (5 persona ringkas) simultan + API + index + tools + multi agent (1000 bayangan) dll + dan sumber lainnya"

**Translation**: multi-source paralel orchestrator — fan-out semua resource SIDIX simultan, lalu sintesis.

**Implementation**:
- ✅ `apps/brain_qa/brain_qa/multi_source_orchestrator.py` — Sprint Α LIVE
- ✅ `apps/brain_qa/brain_qa/cognitive_synthesizer.py` — Sprint Α LIVE
- ✅ Endpoint `/agent/chat_holistic` — LIVE 2026-04-30 evening (commit e02dad4)

**Status**: ✅ FOUNDATION LIVE, 3 bug iteration pending

---

## Framework 2: SANAD MULTI-SOURCE

**Bos verbatim** (multiple chats, locked):
> "sanad chain di setiap output"
> "kalo pake sanada, dia akan mencari langsung banyak sumber"

**Translation**: cross-verification multi-source. Setiap claim spesifik harus di-verify lewat 2+ sumber. Brand-specific terms (persona/IHOS/dll) overrideable ke canonical.

**Implementation**:
- ✅ `apps/brain_qa/brain_qa/sanad_verifier.py` — 13 brand canon entries, intent detection, multi-source verification
- ✅ Wired ke `_apply_sanad()` di `agent_react.py` (4 hook points)

**Status**: ✅ LIVE Sprint Anti-Halu Q1

---

## Framework 3: 5 PERSONA (Locked 2026-04-26)

**Bos verbatim**:
> "5 persona LOCKED: UTZ · ABOO · OOMAR · ALEY · AYMAN"

**Karakter**:
- **UTZ** — Creative Director, voice kreatif/visual, design thinking & inovasi
- **ABOO** — Systems Builder, voice engineer/presisi, system design & coding
- **OOMAR** — Strategic Architect, voice strategist/bisnis, roadmap & GTM
- **ALEY** — Polymath Researcher, voice akademik/riset, literature review & epistemologi
- **AYMAN** — Empathic Integrator, voice hangat/komunitas, daily tasks & user empathy

**Mode 3 SIDIX** (locked 2026-04-30 evening):
- **Basic / Natural (DEFAULT)** — no persona forced, internal jurus seribu bayangan
- **Single Persona** (5 optional advanced) — pilih lens spesifik
- **Pro / Multi-Perspective** — synthesizer dari 5 persona, no own brain

**Implementation**:
- ✅ `cot_system_prompts.py` — 5 persona descriptions distinct voice
- ✅ `persona_research_fanout.py` — paralel fan-out (Sprint 40 Phase 1)
- ✅ Sigma-3D Creative Methodology di UTZ (5 rules: METAFORA VISUAL/KEJUTAN SEMANTIK/NILAI BRAND/NO ECHO/MIN 3 ALT)

**Anti-pattern**:
- ❌ Drop salah satu persona — IMMUTABLE, locked
- ❌ Forced persona pilih (DEFAULT harus Basic, persona optional)
- ❌ Synthesizer pakai 1 persona (harus neutral LLM)

---

## Framework 4: SIGMA-3D CREATIVE METHODOLOGY

**Lokasi**: `cot_system_prompts.py` UTZ persona description.

**5 Rules wajib untuk creative queries** (brand/visual/copywriting/naming):
1. **METAFORA VISUAL** — imaji sensorik kuat, bukan abstract
2. **KEJUTAN SEMANTIK** — kata tak-expected tapi perfect-fit
3. **NILAI BRAND/AUDIENCE** — kaitkan ke karakter spesifik audience
4. **JANGAN ECHO PERTANYAAN** — skip ulang brief, langsung jawaban distinctive
5. **MIN 3 ALT** — untuk naming/tagline/caption, kasih 3+ opsi DENGAN reasoning

**Status**: ✅ LIVE — terbukti aktif di production (probe brainstorm "design tools" → output uses "Metafora Visual: kotak sorotan penuh fit...")

---

## Framework 5: IHOS (Islamic Holistic Ontological System)

**Bos verbatim**:
> "Sanad chain di setiap output ([FACT]/[OPINION]/[UNKNOWN])"
> "Muhasabah → Self-refinement loop"
> "Maqashid → 5 objective filter gates"
> "Ijtihad → ReAct agentic reasoning loop"

**Translation**: framework epistemologi yang map konsep keilmuan Islam klasik ke arsitektur AI modern.

**Implementation**:
- ✅ Sanad chain LIVE (sanad_verifier.py)
- ✅ Maqashid LIVE (maqashid_profiles.py — 5 mode persona)
- ⏳ Muhasabah self-refinement loop — partial (Constitutional AI critique exists)
- ⏳ Ijtihad ReAct — LIVE via agent_react.py

---

## Framework 6: CARA SIDIX ACTION (Note 279)

**Bos visi**: SIDIX ber-tindak seperti otak manusia (mirror metafora):
- **Multi-sensory** — multiple input modalities
- **Multi-perspective** — jurus seribu bayangan
- **Iterative** — loop refine
- **Embodied** — ground di sensor + tools, bukan abstract reasoning saja

**Implementation**: jadi spirit guide untuk semua arsitektur. Concrete: `multi_source_orchestrator` (multi-perspective), `senses` (multi-sensory placeholder), `agent_react` (iterative).

---

## Framework 7: STATIC-GENERATIVE PATTERN (Note 280)

**Bos analogy**: pattern Quran/DNA/Brain (static template + generative variation) → SIDIX:
- LoRA adapter = static template (knowledge yang locked)
- Inference time generation = generative variation
- Sanad chain = DNA-like provenance

**Implementation**: ✅ LoRA Qwen2.5-7B + sanad chain LIVE.

---

## Framework 8: SINTESIS MULTI-DIMENSI (Note 281)

**Bos visi**: gabungan 4 inisiasi:
- Claude-as-guru (mentor agent)
- SIDIX-hadir (always-on observation)
- Hyperx-browser (data ingestion)
- 24-jam AI-to-AI (autonomous loop)

**Implementation**:
- ✅ Conversation Synthesizer LIVE (Sprint 41) — discovery 12 sesi Claude
- ✅ SIDIX-Pixel Chrome ext (Sprint 42 Phase 1)
- ⏳ 24-jam AI-to-AI loop — DNA cron aktif, full self-conversation belum

---

## Framework 9: COGNITIVE SYNTHESIS KERNEL (Note 288)

**Bos visi**: pattern iterative refinement antara multiple agent/persona output → 1 jawaban koheren.

**Implementation**:
- ✅ `cognitive_synthesizer.py` Sprint Α — neutral LLM merge multi-source

---

## Framework 10: CIPTA DARI KEKOSONGAN — Tesla Pattern (Note 278)

**Bos visi**: SIDIX bukan "execute perintah", tapi "create dari minimal prompt". Tesla 100x percobaan pattern. Compound iteratif.

**Implementation**: spirit guide. Concrete: setiap sprint compound atas sebelumnya (Sigma-1/2/3/4 → Sprint Α → Meta-Process Reform).

---

## Framework 11: AUTONOMOUS DEVELOPER (Sprint 40)

**Bos vision tertinggi** (2026-04-30 evening):
> "harusnya hari ini SIDIX sudah bisa menggantikan kamu, sudah bisa membangun dirinya sendiri"

**Translation**: SIDIX bisa scaffold-to-prod sendiri tanpa Claude. SCM, plan, code, test, commit, deploy autonomous.

**Implementation**:
- ✅ Scaffold ada (Sprint 40 Phase 1) — `autonomous_developer/` + `cloud_run_iterator` + `quarantine_manager` + `code_sandbox`
- ⏳ Wire to `/autonomous_dev/queue` endpoint LIVE
- ⏳ Per-persona research fanout integration
- ⏳ Owner-approval gated workflow (no auto-merge ke main)

**Detail**: `docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md`

---

## Framework 12: TIRANYX 4-PRODUK ECOSYSTEM

**Bos verbatim**:
> "membangun perusahaan teknologi creative pertama di indonesia, seperti adobe, canva, corel, unity, unreal engine, blender, sketcup, design, audio, video, film"

**Mapping**:
1. **SIDIX** — AI Agent BRAIN (saat ini 73% visi cover)
2. **Mighan-3D** — 3D toolkit (kompetitor Blender/SketchUp/Unity)
3. **Ixonomic** — creator platform
4. **Platform-X** — TBD
5. **Film-Gen** (sub-product) — bundle image+video+TTS+audio+3D

**SIDIX positioning**: BRAIN, creative tools ride di atasnya. Setiap tool panggil SIDIX untuk reasoning + planning + multi-perspective synthesis.

---

## Pattern Capture Framework Baru

Setiap kali bos sebut framework baru (verbatim atau implicit):

1. Cek file ini — ada belum?
2. Kalau ada: refer + extend (jangan duplicate)
3. Kalau baru:
   - Add entry baru dengan format di atas (Bos verbatim → Translation → Implementation → Status)
   - Update `VISI_TRANSLATION_MATRIX.md` kalau coverage shift
   - Update `BACKLOG.md` kalau ada sprint kandidat baru
   - Append `FOUNDER_IDEA_LOG.md`
   - Commit + push

**Tanpa pattern ini = framework menguap = bos repeat-jelaskan = bos pain.**
