# 🤝 HANDOFF — Claude session, 2026-04-26

> **State:** SIDIX 2.0 LIVE production-ready beta. Backend hybrid Hostinger CPU + RunPod GPU. 4 Supermodel endpoints. Admin panel + Whitelist + Feedback.
> **Untuk:** Claude/Kimi/agent berikutnya yang melanjutkan kerja.

---

## 🎯 TL;DR

SIDIX 2.0 sekarang punya:
- **3 domain live**: sidixlab.com (landing), app.sidixlab.com (chat UI), ctrl.sidixlab.com (admin panel + API)
- **Backend FastAPI** di Hostinger VPS port 8765 (PM2: `sidix-brain`)
- **LLM inference** offloaded ke RunPod Serverless RTX 4090 24GB (qwen2.5:7b vLLM)
- **4 Supermodel endpoints** unik: Burst (Gaga) / Two-Eyed (Mi'kmaq) / Foresight (Tetlock) / Resurrect (Noether)
- **Admin tools** di ctrl.sidixlab.com: Whitelist Manager + Feedback inbox + System Health
- **Whitelist 2-layer**: env + JSON store (admin-managed UI)
- **Feedback feature**: user submit dengan screenshot drag/drop/paste, admin manage di dashboard
- **520 tests pass**

---

## 📐 Arsitektur

```
                    User (browser)
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  app.sidixlab.com (sidix-ui)      │
         │  - Chat UI v2.0                   │
         │  - 4 Supermodel buttons           │
         │  - Login Google (Supabase)        │
         │  - Feedback modal                 │
         │  - Bantuan modal (help)           │
         └─────────────┬─────────────────────┘
                       │ HTTPS POST /ask, /agent/*
                       ▼
         ┌───────────────────────────────────┐
         │  ctrl.sidixlab.com (sidix-brain)  │
         │  Hostinger VPS CPU (15GB RAM)     │
         │  - FastAPI router                 │
         │  - 48 tools (RAG, web, image, ...) │
         │  - Whitelist + Feedback store     │
         │  - Admin UI (/admin)              │
         └─────────────┬─────────────────────┘
                       │ HTTPS (hybrid_generate)
                       ▼
         ┌───────────────────────────────────┐
         │  RunPod Serverless                │
         │  Endpoint: ws3p5ryxtlambj         │
         │  GPU: RTX 4090 24GB (ADA_24)      │
         │  Workers: min=0, max=3            │
         │  Idle timeout: 60s                │
         │  Flash Boot: ON                   │
         │  Model: Qwen/Qwen2.5-7B-Instruct  │
         └───────────────────────────────────┘
```

## 💰 Cost Profile (saat ini)

- Day 1 spent: $1.86 (intensive testing)
- Projected: ~$10-15/month at similar rate
- Budget cap: $30/month
- Per-request average: ~$0.005-0.01 warm, ~$0.05-0.20 cold start
- Idle cost: $0 (workers_min=0 + idleTimeout=60s)

## 🔐 Credentials & Env

**VPS** `/opt/sidix/.env` (TIDAK di git):
```
SIDIX_LLM_BACKEND=runpod_serverless
RUNPOD_API_KEY=rpa_...
RUNPOD_ENDPOINT_ID=ws3p5ryxtlambj
RUNPOD_MODEL=Qwen/Qwen2.5-7B-Instruct
RUNPOD_TIMEOUT=180
SIDIX_WHITELIST_EMAILS=fahmiwol@gmail.com
BRAIN_QA_ADMIN_TOKEN=d76f59a4...
OLLAMA_MODEL=qwen2.5:7b      # fallback CPU local
OLLAMA_TIMEOUT=180
```

**SSH alias** (di `~/.ssh/config` mesin Claude):
```
Host sidix-vps
    HostName 72.62.125.6
    User root
    IdentityFile ~/.ssh/galantara_deploy_ed25519
    IdentitiesOnly yes
```

## 🗂️ Code Map

### Backend (`apps/brain_qa/brain_qa/`)
| File | Owner | Purpose |
|---|---|---|
| `agent_serve.py` | Claude | FastAPI app, all endpoints, Pydantic schemas |
| `agent_react.py` | Claude (core) + Kimi (Jiwa wiring) | ReAct loop orchestration |
| `agent_tools.py` | Claude | Tool registry, 48 tools |
| `agent_burst.py` | Claude (NEW) | Burst+Refinement (Gaga) — `burst_single_call` optimization |
| `agent_two_eyed.py` | Claude (NEW) | Two-Eyed Seeing (Mi'kmaq) |
| `agent_foresight.py` | Claude (NEW) | Foresight scenario planning (Tetlock) |
| `agent_resurrect.py` | Claude (NEW) | Hidden Knowledge Resurrection (Noether) |
| `runpod_serverless.py` | Claude (NEW) | Hybrid GPU/CPU router, 3-format response parser |
| `whitelist_store.py` | Claude (NEW) | Persistent JSON whitelist store |
| `feedback_store.py` | Claude (NEW) | Persistent JSON feedback store |
| `static/admin.html` | Claude (NEW) | Single-page admin dashboard with sidebar |
| `maqashid_profiles.py` | Kimi (mostly) | Casual gate + persona-mode mapping |
| `epistemology.py` | Kimi (mostly) | Audience register + citation format |
| `cot_system_prompts.py` | SHARED — Kimi: PERSONA_DESCRIPTIONS, Claude: EPISTEMIK_REQUIREMENT |
| `ollama_llm.py` | SHARED — Kimi: SIDIX_SYSTEM tone, Claude: routing |

### Frontend (`SIDIX_USER_UI/src/`)
| File | Purpose |
|---|---|
| `main.ts` | Entry, all event handlers, modal logic, auth |
| `api.ts` | BrainQA client (askStream, agentBurst, agentTwoEyed, agentForesight, agentResurrect) |
| `lib/supabase.ts` | Auth + user profile |

### Static
- `SIDIX_LANDING/index.html` — landing page (sidixlab.com)
- `SIDIX_USER_UI/index.html` — chat UI (app.sidixlab.com)
- `apps/brain_qa/brain_qa/static/admin.html` — admin dashboard (ctrl.sidixlab.com/admin)

## 🧪 Tests

`apps/brain_qa/tests/test_sidix2_quality.py` — 10 golden tests SIDIX 2.0:
- Casual greeting clean (no [EXPLORATORY])
- Web search regex (EN+ID variants)
- 4 Supermodel modules importable
- Pareto select logic
- Persona-mode map alignment
- Web search multi-engine fallback chain
- Pydantic schemas top-level

Total: 520 passed, 1 deselected (perf-flaky parallel test, unrelated).

## 🚀 Deployment

### Frontend deploy:
```bash
ssh sidix-vps
cd /opt/sidix
git pull --ff-only origin main
bash deploy-scripts/deploy-frontend.sh
# Builds SIDIX_USER_UI/dist + rsync landing + restarts sidix-ui
```

### Backend restart:
```bash
ssh sidix-vps
pm2 restart sidix-brain --update-env
# start_brain.sh source .env, runs uvicorn
```

### RunPod config:
- Console: https://console.runpod.io/serverless/user/endpoint/ws3p5ryxtlambj
- Or via GraphQL API: see `setup-runpod-serverless.md`

## 📊 Known Issues & TODO

### ✅ Fixed today
- Login overlay before dashboard ✓
- Avatar profile saat login (bukan Sign In) ✓
- Tooltip help di checkbox + Bantuan modal ✓
- Adaptive max_tokens (code 1200, reasoning 1000) ✓
- Auto-suggest mode setelah response ✓
- Citation merge bug (web showing as 'corpus') ✓
- Burst optimization (single-call, 5 parser strategies) ✓
- GPU switch A100 → RTX 4090 (cost optimize) ✓
- Feedback feature (frontend + backend + admin tab) ✓

### 🟡 Outstanding (P1)
- Real-time streaming UI (token-by-token rendering — currently batch)
- Persona Lifecycle (Bowie state machine) — designed, not implemented
- MCP-compatible tool listing endpoint
- Constitutional Kaizen (rule evolution)
- Wabi-Sabi mode (`?mode=wabi-sabi`)

### 🔵 Outstanding (P2)
- Backup cron daily (whitelist.json, feedback.json, .env, sidix-lora-adapter)
- Privacy policy + ToS draft
- Mobile responsive polish (admin panel sidebar collapse)
- Email notification untuk new feedback (admin alert)
- RunPod budget alert webhook ($25 cap)

### 📝 Cosmetic
- Persona docs di About modal (currently nav has "Tentang SIDIX")
- Onboarding flow untuk first-time users
- Avatar fallback kalau Google avatar URL gagal load

## 🎬 Untuk Agent Berikutnya

1. **Baca `docs/LIVING_LOG.md`** dari bagian akhir — semua state recent ada di sana
2. **Cek `docs/AGENT_WORK_LOCK.md`** untuk file ownership protocol
3. **SSH ke VPS** dengan alias `sidix-vps` (key sudah authorized)
4. **Test live** di app.sidixlab.com sebelum modify (verify current state)
5. **Update LIVING_LOG** untuk setiap perubahan substansial

## ⚠️ Anti-Bentrok Reminders

- Jangan touch `agent_memory.py`, `parallel_executor.py`, `jiwa/*` — itu Kimi
- File SHARED (`cot_system_prompts.py`, `agent_react.py`, `ollama_llm.py`) — section markers wajib
- Setelah Kimi commit → `git pull` + resolve + full pytest SEBELUM commit Claude

## 🔗 Quick Links

- **Repo**: https://github.com/fahmiwol/sidix
- **Live**:
  - Landing: https://sidixlab.com
  - Chat UI: https://app.sidixlab.com
  - Admin: https://ctrl.sidixlab.com/admin
  - API docs: https://ctrl.sidixlab.com/docs
- **RunPod console**: https://console.runpod.io/serverless/user/endpoint/ws3p5ryxtlambj
- **Branch**: `claude/zen-yalow-8d0745` (synced ke `main`)

---

**Generated by Claude — 2026-04-26**
