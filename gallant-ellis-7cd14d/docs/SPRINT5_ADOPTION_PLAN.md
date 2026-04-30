# Sprint 5 Adoption Plan — dari RiSet SIDIX
**[FACT]** — 2026-04-21  
**Sumber**: `D:\RiSet SIDIX\` — sidix_framework_methods_modules.md, sidix_technical_architecture_ref.md, sidix_corpus_05_evolution_mechanisms.md, sidix_implementation_roadmap.md

---

## 1. Temuan Kunci dari Riset

### 1.1 Arsitektur 3-Level Evolusi (L1-L2-L3)

Riset memetakan tiga level self-evolution yang harus dibangun secara bertahap:

| Level | Nama | Mekanisme | Sprint Target |
|-------|------|-----------|---------------|
| L1 | Prompt Optimization | Edit prompt template dari accepted outputs | **Sprint 5 ✅ DONE** — `prompt_optimizer.py` |
| L2 | Skill Generation (Voyager) | Auto-write YAML skill baru saat ada gap | Sprint 6 |
| L3 | LoRA Fine-Tuning | Extract high-score outputs → JSONL → retrain | Sprint 6-7 (cron monthly) |

**Key insight dari `sidix_corpus_05_evolution_mechanisms.md`**:
> "SIDIX meralih ke Konstitusi AI di mana Agen Critic/Judge meregulasi karya seni rekannya sendiri."
→ Ini yang sudah kita build: `debate_ring.py` (Critic) + `llm_judge.py` (Judge) di Sprint 5.

### 1.2 Data Flywheel yang Belum Tersambung

Dari `sidix_technical_architecture_ref.md §7.2`:
```
accepted_outputs → few-shot demos → prompt optimization → better outputs → more accepted
```

Sprint 5 sudah punya semua komponen tapi belum tersambung end-to-end:
- ✅ `quality_gate()` di `creative_quality.py` — menentukan output accepted/tidak
- ✅ `log_accepted_output()` di `prompt_optimizer.py` — catat output diterima
- ❌ **Missing link**: pipeline agent belum memanggil `log_accepted_output()` setelah output lulus

**Action**: Sprint 6 — patch `muhasabah_loop.py` untuk auto-call `log_accepted_output()` saat `final_score ≥ 7.0`.

### 1.3 BaseAgent Pattern (sidix-creative-agent) — Sebagian Bisa Diadopsi

Dari `D:\RiSet SIDIX\sidix-creative-agent\services\agents\base.py`:
- Pattern `AgentConfig`, `AgentInput`, `AgentOutput` dataclasses → clean contract
- `_generate()` async dengan iteration support → mirip `muhasabah_loop` tapi lebih terstruktur
- `_get_evaluation_criteria()` abstractmethod → forcing explicit QA criteria per agent

**Verdict**: Pola ini bagus tapi belum wajib Sprint 5. Adopsi bertahap di Sprint 6 saat refactor agent base class.

---

## 2. Rekomendasi Adopsi Terurut

### T5.5 prompt_optimizer.py ✅ SELESAI Sprint 5
- **Implementasi**: `D:\MIGHAN Model\sprint5\apps\brain_qa\brain_qa\prompt_optimizer.py`
- **Tool**: `prompt_optimizer` di `agent_tools.py` (permission: restricted)
- **Research note**: `180_prompt_optimizer_l1_self_evolution.md`

### Sprint 6 — T6.1: Sambungkan Data Flywheel
**File yang perlu dipatch**: `muhasabah_loop.py`, `copywriter.py`, `brand_builder.py`

```python
# Di muhasabah_loop.py, setelah quality gate lulus:
if gate["total"] >= float(min_score):
    try:
        from .prompt_optimizer import log_accepted_output
        log_accepted_output(
            agent=domain,           # atau nama agent yang memanggil
            prompt_params={"brief": brief},
            output_text=current,
            score=gate["total"],
            domain=domain,
        )
    except Exception:
        pass  # non-blocking
    return {"ok": True, "passed": True, ...}
```

**Effort**: S (1-2 jam)
**Impact**: H — mengaktifkan data flywheel L1 secara otomatis

### Sprint 6 — T6.2: A/B Testing Framework untuk Skills
**Inspirasi**: `sidix_implementation_roadmap.md EVO-005`  
**Spec**: Test dua versi prompt (current vs optimized) pada sample kecil, catat win rate.  
**Effort**: M  
**Impact**: M — validasi improvement sebelum fully adopt

### Sprint 6 — T6.3: Experience Logging System
**Inspirasi**: `sidix_implementation_roadmap.md EVO-001`  
**Spec**: Log semua traces (input, output, score, timing) ke `.data/experience_log.jsonl`  
**Effort**: S  
**Impact**: H — fondasi untuk L2/L3 evolution

### Sprint 7 — T7.1: Skill Evolver L2 (Voyager-style)
**Inspirasi**: `sidix_corpus_05_evolution_mechanisms.md §2 Level 2`  
**Spec**: Deteksi gap (request types yang sering gagal) → auto-write YAML skill baru  
**Effort**: L  
**Impact**: H (but complex)

---

## 3. Code yang Bisa Langsung Copy/Adapt dari Riset

### 3.1 CopywriterSignature pattern (dari tech_arch_ref §7.2)
Konsep Signature sebagai typed contract untuk LLM call:
```python
# Adaptasi tanpa DSPy:
@dataclass
class CopywriterSignature:
    brand_context: str   # Brand voice, values, audience
    topic: str           # What to write about
    platform: str        # Target platform
    goal: str            # Marketing goal
    # → output: caption (str)
```
→ Bisa dipakai untuk dokumentasi input/output contract di setiap agent function.

### 3.2 Level 3 LoRA scoring filter
Dari riset: "Extract semua transaksional yang score > 8.5 → .jsonl → LoRA"
→ `curator_agent.py` sudah implementasikan ini! Tapi threshold saat ini MIN_SCORE=0.45 (0-1 scale).  
→ **Action**: tambah filter `score_gte_85` di `run_curation()` untuk pisahkan "regular training" vs "LoRA premium tier".

---

## 4. Gap Analysis

| Konsep di Riset | Status di SIDIX | Action |
|---|---|---|
| L1 Prompt Optimization | ✅ ADA — `prompt_optimizer.py` | Monitor + tune threshold |
| L2 Skill Generation (Voyager) | ❌ BELUM ADA | Sprint 7 |
| L3 LoRA Pipeline | ⚠️ PARTIAL — `corpus_to_training.py` + `auto_lora.py` ada, cron belum | Sprint 6-7 |
| Data flywheel log | ⚠️ ADA tapi tidak auto-connected | Sprint 6 patch muhasabah_loop |
| A/B testing framework | ❌ BELUM ADA | Sprint 6 |
| Experience logging | ⚠️ Partial via LIVING_LOG | Sprint 6 structured log |
| BaseAgent typed contract | ⚠️ Informal saat ini | Sprint 6 refactor |
| Debate Ring / Critic | ✅ ADA — `debate_ring.py` | Done |
| LLM Judge / RLAIF | ✅ ADA — `llm_judge.py` | Done |
| Agency Kit 1-click | ✅ ADA — `agency_kit.py` | Done |

---

## 5. Quick Wins Sprint 6 (estimasi < 2 jam each)

1. **Patch `muhasabah_loop.py`** → auto-call `log_accepted_output()` → flywheel aktif (S, H)
2. **Add `score_gte_85` filter ke `curator_agent.py`** → LoRA premium tier feed (S, M)
3. **Extend `test_sprint5.py`** → test prompt_optimizer dengan mock accepted outputs (S, M)
4. **Add `POST /creative/prompt_optimize` endpoint** ke `agent_serve.py` (S, M)
5. **Cron weekly** untuk `optimize_all_agents()` → Senin 04:00 UTC (S, H)
