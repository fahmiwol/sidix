# Handoff — Sprint 6 Full Ready (3D Pipeline)
**Tanggal**: 2026-04-21  
**Status**: Sprint 6 QW complete. 3D pipeline PLANNED, belum diimplementasi.

---

## ✅ State Sekarang (commit `5c91528` + `4b9892d` + `7574676`)

- `curator_agent.py` — score_gte_85 premium tier ✅ live di branch
- `test_sprint6.py` — 14/14 tests pass ✅
- Branch `claude/focused-ardinghelli-5b52ae` — pushed ke fahmiwol + tiranyx ✅
- **VPS belum di-deploy** — perlu `git pull` + `pm2 restart sidix-brain`

---

## 🔲 Sesi Berikutnya — Sprint 6 Full

### Step 1: Merge + Deploy (S, lakukan dulu)
```bash
# 1. Buat PR di GitHub: claude/focused-ardinghelli-5b52ae → main
# 2. Merge PR
# 3. SSH ke VPS:
cd /opt/sidix && git pull && pm2 restart sidix-brain
# 4. Verify: curl https://ctrl.sidixlab.com/health
```

### Step 2: Implementasi 3D Pipeline (L, urutan lengkap ada di note 184)

**Baca dulu sebelum kode:**
- `brain/public/research_notes/184_3d_pipeline_architecture_plan.md` — **arsitektur + skeleton lengkap**
- `docs/MASTER_ROADMAP_2026-2027.md` §Sprint 6 — DoD

**File yang perlu dibuat (urutan):**
1. `apps/brain_qa/brain_qa/text_to_3d.py`
   - Provider chain: Sloyd → Meshy → mock
   - Env vars: `SLOYD_API_KEY`, `MESHY_API_KEY`
2. `apps/brain_qa/brain_qa/image_to_3d.py`
   - Provider: TripoSR (pip) → Meshy → mock
3. Daftarkan ke `agent_tools.py` sebagai tool #36 + #37
4. Tambah endpoint `POST /3d/text` + `POST /3d/image` di `agent_serve.py`
5. Test: `apps/brain_qa/tests/test_3d_pipeline.py` (mock provider)
6. `npc_generator.py` — setelah mesh tools live

**Env vars baru yang dibutuhkan** (tambah ke `.env` VPS + `.env.sample`):
```
SLOYD_API_KEY=
MESHY_API_KEY=
```

### Step 3: NPC Generator (M)
- `npc_generator.py` — skeleton di note 184
- Tool #38

### Step 4: Voyager Protocol (L, HIGH RISK — review dulu)
- AST security scan wajib
- HITL approval gate sebelum eksekusi tool baru
- Ref: note 169

---

## 📌 TODO Fahmi (manual — jangan lupa)

- [ ] Merge PR `claude/focused-ardinghelli-5b52ae` → main di GitHub
- [ ] Deploy VPS: `git pull && pm2 restart sidix-brain`
- [ ] Daftar Sloyd API key: sloyd.ai/developers (gratis 100 model/bulan)
- [ ] Daftar Meshy API key: meshy.ai (gratis tier ada)
- [ ] Kaggle: upload `sidix_lora_batch_20260419_0545` untuk LoRA v1
- [ ] GA4: fix URL `app.sixlab.com` → `app.sidixlab.com`
- [ ] Cron VPS: `0 4 * * MON curl POST .../creative/prompt_optimize/all`

---

## File Kunci untuk Sesi Berikutnya
```
brain/public/research_notes/184_3d_pipeline_architecture_plan.md  ← BACA INI DULU
docs/MASTER_ROADMAP_2026-2027.md §Sprint 6
apps/brain_qa/brain_qa/agent_tools.py      ← tambah tool #36-#38
apps/brain_qa/brain_qa/agent_serve.py      ← tambah /3d/* endpoints
.env.sample                                ← tambah SLOYD/MESHY keys
```

## Commits di branch ini
```
5c91528  doc: LIVING_LOG + handoff Sprint 6 QW complete
7574676  test: test_sprint6 — 10 tests curator premium
4b9892d  feat: curator_agent score_gte_85
```
