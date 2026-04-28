# Note 287 — Sprint 13 Phase 3c: Persona Dispatch Wire Plan

**Sanad**: Sprint 13 Phase 3a (note 285) ✅ + Phase 3b prep (note 286) ✅ + Phase 3b training (kernel v4 RUNNING) → Phase 3c arsitektur disiapkan PARALEL agar zero-wait setelah training selesai.  
**Tanggal**: 2026-04-29  
**Status**: SCAFFOLD READY (modules disiapkan, wire ke production tunggu adapter LIVE)

---

## Tujuan Phase 3c

Setelah HF upload `Tiranyx/sidix-dora-persona-v1` LIVE (post-training), wire ke production:

1. **Persona dispatch** — `agent_react.py` resolve persona → load matching adapter
2. **Multi-LoRA hot-swap** — RunPod inference path bisa swap antara base SIDIX LoRA dan 5 persona DoRA adapter
3. **Quality gate** — blind A/B test 50 prompts × 5 persona, target ≥80% voice_match
4. **Regression check** — corpus answer accuracy delta < 5% (DoRA tidak boleh break generative ability)

---

## Modules yang sudah disiapkan (Phase 3c scaffold)

### A. `apps/brain_qa/brain_qa/persona_adapter_loader.py`

Manage adapter state + dispatch logic (STUB sampai training done).

```python
PersonaRouter           # in-memory registry per persona
download_adapter(p)     # snapshot_download dari HF (Phase 3c implementation)
select_adapter_for_request(persona, router) → resolved persona dengan fallback
list_adapter_status()   # diagnostic untuk admin endpoint
```

**Fallback logic**:
- persona None → AYMAN (voice paling general)
- persona unknown → AYMAN
- persona valid tapi belum loaded → AYMAN (avoid blocking ReAct)
- persona valid + loaded → return persona

**Phase 3c full implementation** (post-training, sesi berikutnya):
```python
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id=HF_REPO,
    local_dir=str(target_dir),
    allow_patterns=["adapter_*", "tokenizer.*"]
)
```

### B. `apps/brain_qa/brain_qa/blind_ab_test.py`

Quality gate scaffold — 50 prompts × 5 persona × 2 conditions (base LoRA vs DoRA).

```python
BLIND_TEST_PROMPTS  # 50 prompts (5 categories × 10)
auto_grade_response(response, expected_persona) → grade dict
run_blind_test(persona_responder, sample_n=None) → summary
stub_responder(prompt, persona)  # for pipeline verification
```

**Quality gates**:
- DoRA accuracy ≥80% (voice_match per persona × all responses)
- Base LoRA accuracy < DoRA (DoRA harus add signal, bukan break)
- Per-persona accuracy ≥75% (no one persona drag down)

**Auto-grader methodology** (konsisten dengan Phase 3a generation gate):
- `signature_score(response, expected) - cross_avg ≥ 0.20` = voice_match
- Pakai PERSONA_MARKERS yang sudah verified Sprint 13 Phase 3a (gap ≥0.43 cross-persona)

**Smoke test verified offline**: stub responder → 92% overall accuracy (sanity check pipeline jalan benar).

---

## Wire plan — Phase 3c sesi berikutnya

### Step 1 — Verify adapter HF (post-training)

```bash
# Setelah Kaggle kernel COMPLETE, dari VPS:
mkdir -p /tmp/adapter_dl && cd /tmp/adapter_dl
kaggle kernels output mighan/sidix-dora-persona-train-v1 -p .
ls -la sidix-dora-persona-v1/
# Expected: adapter_config.json + adapter_model.safetensors (~150MB DoRA rank-16)

# Upload ke HF
hf upload Tiranyx/sidix-dora-persona-v1 ./sidix-dora-persona-v1/ --repo-type model
```

### Step 2 — Wire `agent_react.py`

Tambah di awal `run_react()`:
```python
from .persona_adapter_loader import select_adapter_for_request, _GLOBAL_ROUTER

resolved_persona = select_adapter_for_request(persona, _GLOBAL_ROUTER)
# pass resolved_persona ke local_llm.generate_sidix(persona=resolved_persona)
```

### Step 3 — Wire `local_llm.py` / inference path

Untuk RunPod vLLM:
```python
# Multi-LoRA endpoint param
runpod_payload = {
    "input": {
        "prompt": ...,
        "lora_id": f"sidix-dora-{resolved_persona.lower()}",
        # Fallback: lora_id = "sidix-base-lora" kalau persona None
    }
}
```

Untuk local PEFT inference (kalau VPS pernah jalanin):
```python
model.set_adapter(f"dora_{resolved_persona.lower()}")
```

### Step 4 — Update `runpod_warmup.sh`

Download adapter dari HF di warmup (avoid cold-start lag):
```bash
huggingface-cli download Tiranyx/sidix-dora-persona-v1 \
    --local-dir /opt/sidix/.data/adapters/dora_persona/
```

### Step 5 — Run blind A/B test

```bash
PYTHONPATH=/opt/sidix/apps/brain_qa python3 -c "
from brain_qa.blind_ab_test import run_blind_test
from brain_qa.local_llm import generate_sidix

def real_responder(prompt, persona):
    return generate_sidix(prompt, persona=persona, max_tokens=200)

result = run_blind_test(real_responder, out_path='/opt/sidix/.data/blind_test_v1.json')
print(f'Overall accuracy: {result[\"overall_accuracy\"]}')
print(f'Quality gate 80: {result[\"quality_gate_80\"]}')
"
```

### Step 6 — Decision gate

| Result | Action |
|---|---|
| ≥80% overall + ≥75% per-persona | ✅ Promote ke production, proceed Sprint 13b (expand UTZ+ABOO → all 5) |
| 60-80% | Iterate Phase 3a iter2 (LLM-amplify dataset) → retrain Phase 3b |
| <60% | Rollback DoRA, root cause analysis (training bug? data quality?) |

---

## Risk + mitigation

| Risk | Mitigation |
|---|---|
| Adapter file size besar (>500MB) | DoRA rank-16 typically ~150MB. Kalau >500MB indicate training save full base — verify only adapter_*.safetensors saved |
| Multi-LoRA inference latency naik | Cache adapter di GPU memory di warmup, swap pointer not weights |
| Persona dispatch break ReAct loop | Fallback ke AYMAN kalau adapter unavailable; log warning, jangan exception |
| Blind test bias (auto-grader hanya lexical) | Phase 3c iter2: human-grader sample 10% subset untuk validate auto-grader |
| Catastrophic forgetting (corpus accuracy drop) | Run regression eval: 30 corpus queries pre/post-DoRA, delta < 5% |

---

## State pipeline saat note ini ditulis

```
Phase 3a synthetic data ✅ LIVE — 7500 pairs di /opt/sidix/.data/training/
Phase 3a merge ✅ LIVE — 6750 train + 750 val stratified
Phase 3b setup ✅ LIVE — Kaggle dataset + HF repo + kernel pushed
Phase 3b training 🟡 RUNNING — kernel v4 (after 3 iterasi fix)
Phase 3c scaffold ✅ MODULES READY — persona_adapter_loader + blind_ab_test
Phase 3c wire 🟡 PENDING — wait HF upload
```

---

## Iterasi log Phase 3b kernel push

| Version | Result | Root cause | Fix |
|---|---|---|---|
| v1 | ❌ ERROR | Race condition: kernel push <5s setelah dataset upload | Wait until dataset indexed |
| v2 | ❌ ERROR | id mismatch dgn Kaggle title-derived slug + dataset path masih invisible | id align ke `mighan/sidix-dora-persona-train-v1` |
| v3 | ❌ ERROR | Private dataset mount path: `/kaggle/input/datasets/<owner>/<slug>/` bukan `/kaggle/input/<slug>/` | Auto-detect via `glob.glob('/kaggle/input/**/persona_qa_train.jsonl', recursive=True)` |
| v4 | 🟡 RUNNING | bitsandbytes 0.44.1 incompat triton 3.x di Python 3.12 | Remove version pin, let pip resolve latest compatible (≥0.45) |

Verified via diagnostic kernel `mighan/sidix-diag-mount` (lulus COMPLETE) untuk dapetin actual mount structure.

---

## Untuk agent next session

**Kalau Kaggle kernel COMPLETE**:
1. Cek `/opt/sidix/.data/kaggle_kernel_state.json` (cron monitor breadcrumb)
2. Run Step 1-6 di atas urut
3. Goal: blind test ≥80% → publish hasil ke `/opt/sidix/.data/blind_test_v1.json`

**Kalau Kaggle kernel ERROR lagi**:
1. `kaggle kernels output mighan/sidix-dora-persona-train-v1 -p /tmp/log_vN`
2. Parse log untuk identify root cause (cell number + error message)
3. Iterate notebook, push vN+1
4. Append iterasi entry ke tabel di section atas

**Kalau bos kasih signal "stop Sprint 13"**:
- Sprint 13 Phase 3a + scaffold tetap valuable (synthetic data + persona_adapter_loader scaffold)
- Resume kapan-kapan, atau jadikan reference untuk Sprint approach berbeda
