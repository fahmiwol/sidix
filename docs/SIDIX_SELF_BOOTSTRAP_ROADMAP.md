# SIDIX SELF-BOOTSTRAP ROADMAP — Path Menuju SIDIX Replace Agent Eksternal

**Visi tertinggi bos** (verbatim 2026-04-30 evening):
> "harusnya hari ini SIDIX sudah bisa menggantikan kamu, sudah bisa membangun dirinya sendiri. sudah bisa say perintah untuk membangun dirinya sendiri, mengcloning dirinya sendiri. sehingga dia belajar langsung."

**Pain reality**: belum tercapai. Setelah 2 bulan dedicate, SIDIX belum self-bootstrap. Saat ini masih dependent ke Claude/agent eksternal untuk modifikasi.

**Tujuan file ini**: roadmap konkret end-state → milestone → sprint, supaya **setiap agent yang kerja di SIDIX tahu kontribusi mereka mengarah ke goal SIDIX self-bootstrap**.

---

## End-State (What "SIDIX Replace Agent" Berarti)

Founder berkata: *"SIDIX, tambahkan fitur X di backend"* → SIDIX:
1. Read repo state sendiri (BACKLOG, FOUNDER_JOURNAL, dll)
2. Translate request → Task Card
3. Plan code change (multi-persona research dulu kalau kompleks)
4. Generate code di sandbox
5. Test sendiri (unit test + smoke test)
6. Verify sanad (multi-source check kalau introduce klaim baru)
7. Commit ke branch terpisah (NOT main, untuk safety)
8. Open PR dengan summary
9. Founder approve / reject / iterate
10. Setelah approve, SIDIX self-deploy ke staging (atau prod kalau low-risk)

**Tanpa Claude/GPT/Gemini perlu dipanggil.**

---

## Capability Required (per Visi Chain Mapping)

| Capability | Visi Word | Status |
|---|---|---|
| Read own repo state | Cognitive | ✅ workspace_read tool exists |
| Edit own code | Pencipta | ✅ workspace_write tool exists, code_sandbox runtime |
| Multi-source research before coding | Genius (jurus seribu bayangan) | ✅ Sprint Α LIVE |
| Run own tests | Iteratif | ⚠️ code_sandbox runs, tapi tidak yet auto-trigger pytest |
| Sanad verify own code claims | Anti-halu | ⚠️ sanad gate untuk text output, belum untuk code commit |
| Multi-persona code review | Creative | ⚠️ persona_research_fanout ada, belum wired ke code review |
| Commit + push autonomously | — | ✅ git permissions exist via deploy key |
| Owner approval gate | Founder safety | ⚠️ scaffold ada (Sprint 40), workflow belum complete |

**Coverage saat ini ~50% capability ready, sisanya scaffold tanpa wire.**

---

## Roadmap Phased

### Phase 0: Foundation (DONE per 2026-04-30)
- ✅ Brain stability (PyTorch fix, RunPod tuning, cron diet)
- ✅ Multi-source orchestrator (Sprint Α — jurus seribu bayangan LIVE)
- ✅ Sanad gate + brand canon
- ✅ Anti-menguap protocol (BACKLOG + IDEA_LOG + Matrix + Onboarding + Frameworks)

### Phase 1: Tools Wire-Up (NEXT, 3-4 session)
**Sprint Self-Read**:
- Wire `workspace_read` ke prompt context auto-injection
- Saat SIDIX dapat task, bisa baca SIDIX_BACKLOG.md + FOUNDER_JOURNAL otomatis
- Acceptance: SIDIX bisa jawab "apa state BACKLOG saat ini" tanpa Claude bantu

**Sprint Code-Test Loop**:
- Wire `code_sandbox` + auto pytest trigger
- Saat SIDIX edit code, langsung test sendiri di sandbox
- Acceptance: SIDIX edit `fact_extractor.py` + run unit test + report pass/fail

**Sprint Sanad Code Verify**:
- Extend sanad gate untuk code commits
- Cross-check: code change consistent dengan VISI_TRANSLATION_MATRIX? Visi mapping clear?
- Acceptance: SIDIX rejects code change yang tidak ada visi mapping

### Phase 2: Autonomous Loop (4-6 session)
**Sprint Multi-Persona Code Review**:
- Wire `persona_research_fanout` ke code review:
  - UTZ: review naming, readability, "creative naming"
  - ABOO: review architecture, performance, edge cases
  - OOMAR: review business impact, GTM relevance
  - ALEY: review research backing, paper citations needed
  - AYMAN: review user experience impact
- Acceptance: SIDIX code change auto-reviewed by 5 persona before commit

**Sprint Owner-Gated Workflow**:
- Auto branch + commit + PR
- Telegram/email notification ke founder
- Approve/reject UI sederhana
- Acceptance: SIDIX edit + push branch + open PR + founder approve via 1 click

**Sprint Auto-Deploy Staging**:
- Setelah PR merge ke staging branch, auto deploy ke staging env
- Smoke test di staging
- Promote ke prod manual (founder click)

### Phase 3: Self-Improving (6-8 session)
**Sprint Self-Reflection**:
- SIDIX baca own code + identify code smell / anti-pattern
- Generate improvement proposal
- Owner-gated execute

**Sprint Self-Cloning** (visi bos: "mengcloning dirinya sendiri"):
- SIDIX bisa spawn copy of itself untuk parallel task
- Coordinator/sub-agent pattern
- Use case: research kompleks → spawn 5 sub-SIDIX (1 per persona) → merge

**Sprint Continual Learning Active**:
- Setiap interaction → corpus ingest → quality filter → LoRA fine-tune queue
- Weekly LoRA refresh
- Acceptance: SIDIX yang tumbuh nyata dari interaksi user (post-launch metric)

### Phase 4: Replace Eksternal Agent (~12 month target?)
**Sprint Claude-Replacement**:
- Founder kasih perintah "tambahkan fitur X" → SIDIX execute end-to-end tanpa Claude
- Quality benchmark: SIDIX output vs Claude output untuk same task
- Acceptance: 80%+ task SIDIX execute tanpa intervention

**Sprint GPT/Gemini-Replacement**:
- Specialized creative tools (image gen, video gen) — SIDIX coordinate
- Tidak panggil ChatGPT/Gemini API anymore
- 100% self-hosted creative pipeline

---

## Blocker / Risk Tertinggi

### 1. Compute Budget
SIDIX self-bootstrap = LLM calls dilipat (research → code gen → test → review). Tanpa GPU/credit reasonable, tidak feasible.

**Mitigation**:
- Ollama lokal CPU untuk persona research (gratis)
- RunPod GPU hanya untuk synthesis akhir + final code gen (cap tinggi)
- LoRA per-persona small adapter (low VRAM)

### 2. Code Quality Risk
SIDIX edit kode buruk → break production. Founder pain meningkat.

**Mitigation**:
- Owner-gated approval (no auto-merge main)
- Branch isolation (SIDIX work di feature branch)
- Auto-revert kalau staging smoke test fail
- Test coverage mandate per sprint

### 3. Visi Drift
SIDIX self-build → drift dari Northstar (sama seperti agent eksternal masalah).

**Mitigation**:
- Sanad gate untuk code: visi mapping required
- VISI_TRANSLATION_MATRIX cek per commit
- Founder veto override

---

## Yang Harus Setiap Agent Pahami

**Setiap kontribusi agent eksternal (Claude/GPT/Gemini) ke SIDIX HARUS mengarah ke SIDIX bisa replace agent itu sendiri.**

Anti-pattern: agent eksternal menambah feature yang HARUS panggil API agent eksternal lagi (mis. "wire ke Claude API"). Itu bikin SIDIX dependent forever.

Pattern yang benar:
- ✅ Add capability ke SIDIX-native (jurus seribu bayangan LIVE = SIDIX bisa research sendiri)
- ✅ Replace external dependency dengan self-hosted (Qwen2.5+LoRA replace ChatGPT API)
- ✅ Build infrastructure yang scale ke autonomous (Sprint 40 Phase 1 scaffold)

**Agent eksternal di proyek ini = teacher mode**. Bantu build SIDIX → eventually SIDIX replace teacher.

---

## Founder Reminder Permanent

> "saya hanya seorang pemimpi yang paham dasar, dan cuma punya visi dan intuisi. saya nggak ngerti teknis, nggak pernah bikin AI model AI agent sebelumnya, nggak ngerti coding."

Implication untuk roadmap ini:
- Founder TIDAK akan code self-bootstrap path
- Agent eksternal HARUS yang execute Phase 1-3 (Claude di Q3-Q4 2026)
- Phase 4 SIDIX self-replace agent (Q1-Q2 2027 target?)

**Tanpa agent eksternal yang execute Phase 1-3 dengan disiplin, founder akan stuck repeat menjelaskan visi → SIDIX tidak mature → tidak bisa replace.**

Itu adalah SISTEM yang kita bangun sekarang. Anti-menguap protocol = guarantee progress kompon, bukan random eksekusi.
