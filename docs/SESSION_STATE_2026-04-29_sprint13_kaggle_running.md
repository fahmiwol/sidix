# Session State — Sprint 13 Phase 3b Kaggle Training In-Flight

**Tanggal**: 2026-04-29  
**Trigger**: bos kasih kaggle.json + HF token, saya remote pipeline end-to-end  
**Status**: Kaggle kernel v4 RUNNING (after 3 iterasi fix)

---

## TL;DR untuk agent next session

1. **Cek kernel status**: `cat /opt/sidix/.data/kaggle_kernel_state.json` di VPS (cron auto-update tiap 15 min)
2. **Kalau status `COMPLETE`**: jalankan [note 287](../brain/public/research_notes/287_sprint13_phase3c_dispatch_wire_plan.md) Step 1-6 untuk wire ke production
3. **Kalau status `ERROR`**: parse log, iterate notebook, push v(N+1)
4. **Kalau status `RUNNING`**: tunggu, atau lanjut Phase 3c module wiring (persona_adapter_loader + blind_ab_test sudah scaffolded)

---

## Asset tersedia (semua LIVE atau READY)

### Code (committed ke main, VPS synced)
| File | Status | Purpose |
|---|---|---|
| `apps/brain_qa/brain_qa/persona_qa_generator.py` | ✅ LIVE | Phase 3a — 5 persona signature_voice templates |
| `apps/brain_qa/brain_qa/merge_persona_dataset.py` | ✅ LIVE | Phase 3a → 3b bridge — train/val split |
| `apps/brain_qa/brain_qa/persona_adapter_loader.py` | ✅ SCAFFOLD | Phase 3c — adapter dispatch (stub sampai HF upload) |
| `apps/brain_qa/brain_qa/blind_ab_test.py` | ✅ SCAFFOLD | Phase 3c quality gate (smoke test 92% pass) |
| `training/sprint13_dora_persona_kaggle.ipynb` | ✅ LIVE v4 | Kaggle T4/P100 DoRA training notebook |
| `training/kernel-metadata.json` | ✅ LIVE | Kernel id slug match Kaggle expectation |

### Data (di VPS `/opt/sidix/.data/training/`)
| File | Lines | Size |
|---|---|---|
| persona_qa_UTZ.jsonl | 1500 | 880 KB |
| persona_qa_ABOO.jsonl | 1500 | 922 KB |
| persona_qa_OOMAR.jsonl | 1500 | 1.0 MB |
| persona_qa_ALEY.jsonl | 1500 | 1.0 MB |
| persona_qa_AYMAN.jsonl | 1500 | 957 KB |
| **persona_qa_train.jsonl** | **6750** | **4.2 MB** |
| **persona_qa_val.jsonl** | **750** | **476 KB** |

Avg signature_score: 0.639-0.767 stable di scale.

### Cloud resources (live)
| Resource | URL |
|---|---|
| Kaggle Dataset | https://www.kaggle.com/datasets/mighan/sidix-persona-qa-v1 |
| Kaggle Kernel | https://www.kaggle.com/code/mighan/sidix-dora-persona-train-v1 |
| HF Repo (target) | https://huggingface.co/Tiranyx/sidix-dora-persona-v1 |

### Credentials (di VPS, chmod 600)
- `/opt/sidix/.env.kaggle_hf` — KAGGLE_API_TOKEN, HF_TOKEN, KAGGLE_USERNAME
- `/root/.kaggle/kaggle.json` — Legacy format `{"username":"mighan","key":"..."}`

⚠️ **SECURITY ACTION ITEM**: Setelah Sprint 13 Phase 3c selesai, **wajib revoke** kedua token (Kaggle Legacy + HF SIDIX123) karena pernah di-paste ke chat history per memory `security_credential_redact_pattern.md`.

### Monitor automation
- Cron `*/15 * * * * /opt/sidix/scripts/sidix_kaggle_monitor.sh`
- Outputs:
  - `/opt/sidix/.data/kaggle_monitor.log` — append timestamp + status
  - `/opt/sidix/.data/kaggle_kernel_state.json` — current snapshot

---

## Iterasi log Kaggle kernel push

| Version | Status | Root cause | Fix applied |
|---|---|---|---|
| v1 | ❌ ERROR (cell 5) | Dataset belum ter-mount (race) | Wait until indexed |
| v2 | ❌ ERROR (cell 5) | Title→slug mismatch + path issue persist | id align to `mighan/sidix-dora-persona-train-v1` |
| v3 | ❌ ERROR (cell 5) | Private dataset mount `/kaggle/input/datasets/<owner>/<slug>/` (bukan `/kaggle/input/<slug>/`) | Auto-detect via `glob.glob('/kaggle/input/**/persona_qa_train.jsonl', recursive=True)` |
| v4 | 🟡 RUNNING | bitsandbytes 0.44.1 incompat triton 3.x | Remove pin, `pip install -U bitsandbytes peft trl accelerate datasets huggingface_hub` |

Diagnostic kernel `mighan/sidix-diag-mount` (COMPLETE) confirmed actual mount structure sebelum v3 patch — anti-halusinasi pattern.

---

## Mandatory loop status (CLAUDE.md 6.5)

| Step | Status |
|---|---|
| 1. CATAT (pre-exec) | ✅ done — note 287 architecture + this doc |
| 2. TESTING | ✅ done — 4 kernel iterations + diag kernel + blind_ab_test smoke 92% |
| 3. ITERASI | ✅ done — 4 iterations (race → slug → path → bnb pin) |
| 4. TRAINING | 🟡 IN-FLIGHT — Kaggle kernel v4 |
| 5. REVIEW | ✅ done — code + architecture self-audit |
| 6. CATAT (validasi findings) | ✅ done — LIVING_LOG + note 287 |
| 7. VALIDASI | 🟡 PENDING training complete — blind A/B test post-adapter |
| 8. QA | 🟡 PENDING — HF upload + regression check |
| 9. CATAT (final) | 🟡 PENDING |

---

## Sprint queue context (next priorities setelah Sprint 13)

Per [ROADMAP_DORA_SPRINT13.md](ROADMAP_DORA_SPRINT13.md):

```
SEKARANG: Sprint 13 Phase 3b RUNNING (Kaggle), Phase 3c SCAFFOLD READY
NEXT: Phase 3c wire (post-training) — wait kernel COMPLETE
QUEUE setelah Sprint 13 done:
  Sprint 13b — expand 3 persona (kalau Sprint 13 success)
  Sprint 39c — macro dispatch wire (compound dengan persona dispatch)
  Sprint 40 — Telegram approve flow
  Sprint 41 — Sanad multi-source 3-way
  Sprint 42 — Bunshin Worker re-arch
```

---

## Decision tree untuk agent next session

```
START sesi baru
  │
  ├─ Read this file (SESSION_STATE_2026-04-29...)
  ├─ Read note 287 (Phase 3c plan detail)
  ├─ Check /opt/sidix/.data/kaggle_kernel_state.json
  │
  ├─ STATUS == "COMPLETE":
  │    └─ Run note 287 Step 1: kaggle kernels output → verify adapter files
  │    └─ Run Step 2-6: HF upload + wire ReAct + blind A/B test
  │    └─ Append LIVING_LOG + commit + push
  │
  ├─ STATUS == "ERROR":
  │    └─ kaggle kernels output → parse stderr → identify cell + error
  │    └─ Edit notebook (cell N) → push v(N+1)
  │    └─ Update iterasi log table di note 287
  │
  ├─ STATUS == "RUNNING":
  │    └─ Wait, atau lanjut prep Phase 3c module wire (sudah scaffolded)
  │    └─ Cek `/opt/sidix/.data/kaggle_monitor.log` last 5 entries
  │
  └─ STATUS == "UNKNOWN" (cron error):
       └─ Manual: ssh sidix-vps 'kaggle kernels status mighan/sidix-dora-persona-train-v1'
```
