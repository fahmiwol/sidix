# Handoff Memo — Claude (SIDIX AI Agent Adik)

**Updated:** 2026-04-30  
**Branch kerja:** `work/gallant-ellis-7cd14d` (frontend) / `claude/gallant-ellis-7cd14d` (VPS backend)  
**Next session trigger:** Baca file ini + 20 baris terakhir `docs/LIVING_LOG.md`

---

## 🎯 North Star (LOCK)
SIDIX = AI Agent standing-alone Nusantara-Islam-native, multimodal, epistemically honest, self-hosted.  
Tagline: *"Autonomous AI Agent — Thinks, Learns & Creates"*  
3 Keunggulan: Transparansi epistemologis (4-label + sanad), Kedaulatan data (own model + corpus), Spesialisasi kultural.

---

## 📊 STATUS HARI INI (2026-04-30)

### Deployed & Live
| Komponen | URL | Stack | Status |
|----------|-----|-------|--------|
| Landing | `sidixlab.com` | Static HTML | ✅ Live |
| App | `app.sidixlab.com` | Vite + TS (`SIDIX_USER_UI/`) | ✅ Live — **Holistic default BARU deploy** |
| Backend | `ctrl.sidixlab.com` | FastAPI (`apps/brain_qa/`) | ✅ Live — port 8765 |
| OTAK+ Self-Critique | cron 03:00 | `daily_self_critique.py` | ✅ Live |

### Sprint Status
| Sprint | Status | Notes |
|--------|--------|-------|
| Sprint 6.5 (Maqashid/Naskh/Raudah/CQF) | ✅ DONE | All deployed |
| Sprint 7 (Social Radar MVP) | ⚠️ Partial | Backend + API done; real scrape + dashboard TODO |
| Sprint 8a/b/c | ✅ DONE | Merged to main |
| Sprint 8d | ⏳ IN PROGRESS | branch_manager.py, Piper TTS, PostgreSQL, Jariyah pairs |
| Jiwa Sprint 2 | ⏳ IN PROGRESS | Kimi lane: embodied taste + multimodal creative |
| **Holistic Default** | 🔄 **VERIFY** | Baru deploy 2026-04-30, perlu test live |

---

## 🚧 WORK IN PROGRESS (WIP)

### 1. Holistic Default Mode — Frontend (TOP PRIORITY)
**What:** User ketik langsung → Jurus Seribu Bayangan (8 sumber paralel) tanpa klik tombol.  
**File:** `SIDIX_USER_UI/src/main.ts`  
**Status:** Refactor selesai, deploy selesai, **tapi BELUM di-verify live**.  
**Next:** Test di `app.sidixlab.com` — tanya "Wapres Indonesia sekarang?" → harus jawab **Gibran Rakabuming Raka** dengan progress card 8-chip.

### 2. Sprint 8d — Backend Infrastructure
| Item | Priority | Status |
|------|----------|--------|
| `branch_manager.py` — Multi-tenant agency | HIGH | Not started |
| Piper TTS install di VPS | HIGH | Not started |
| PostgreSQL connection active | MED | Schema ada, tinggal apply + env var |
| FLUX.1 GPU (RunPod or local) | MED | Mock mode running, not blocking |
| Jariyah pairs → LoRA export | MED | Monitor `data/jariyah_pairs.jsonl` count |

### 3. UX Enhancement Queue (Bos request)
| Item | Status |
|------|--------|
| Auto-mode detection (coding/planning/deep-research) | ⏳ TODO |
| Persona "Mirror" default (analyze user style) | ⏳ TODO |
| Sticky mode toggle gold highlight | ✅ DONE |

---

## 🐛 BLOCKERS & RISIKO

1. **VPS branch divergence:** `claude/gallant-ellis-7cd14d` (VPS) vs `work/gallant-ellis-7cd14d` (origin). Frontend deploy pakai `git checkout origin/work/... -- file` workaround. Bisa jadi technical debt.
2. **sidix-brain restart count 75+** — perlu root cause analysis (dense_index dim mismatch + web_search bug history).
3. **Encoding corruption** — PowerShell copy-paste merusak UTF-8 emoji. Solusi: selalu pakai `git push → git pull` atau Python base64 untuk transfer file ke VPS.

---

## ✅ DECISION LOG (immutable)

- **2026-04-16:** Own-stack default untuk inference. API vendor HANYA untuk benchmark/POC, harus dilabeli.
- **2026-04-19:** North Star + Direction LOCK. SIDIX = AI agent, bukan cuma RAG.
- **2026-04-23:** UI dulu (bukan training dulu). Landing + App + Backend 3 subdomain.
- **2026-04-26:** Definition LOCK. 3 Fondasi (Mind/Hands/Drive), 4-Pilar, 5 Persona (UTZ/ABOO/OOMAR/ALEY/AYMAN).
- **2026-04-30:** Holistic = default send mode. Persona selector tetap ada. Sticky toggle, no popup.

---

## 📋 NEXT ACTIONS (concrete, verifiable)

### Immediate (hari ini / besok)
1. [ ] **VERIFY Holistic live:** Test 3 pertanyaan factual (Presiden, Wapres, PM Malaysia) → cek progress card muncul + jawaban benar + ada sanad.
2. [ ] **Hapus dead code:** `getInputOrPrompt()` kalau tidak dipakai mode Burst/TwoEyes/Foresight/Resurrect lagi.
3. [ ] **OTAK+ result check:** Cek `.data/critique/` hari ini — ada berapa session yang dievaluasi? Relevan_score trend?

### Short-term (minggu ini)
4. [ ] **Sprint 8d — Piper TTS:** Install di VPS, test endpoint `POST /tts/synthesize`.
5. [ ] **Sprint 8d — PostgreSQL:** Apply schema, set env var, test connection.
6. [ ] **Sprint 8d — branch_manager.py:** Scaffold dataclass + endpoint, test multi-tenant corpus filter.
7. [ ] **Auto-mode detection:** Frontend classifier sederhana (keyword-based) untuk coding/planning/research.

### Medium-term (2 minggu)
8. [ ] **Persona Mirror:** Track user behavior pattern, auto-route persona.
9. [ ] **Social Radar real scrape:** Wire `content.js` ke backend (bukan simulasi).
10. [ ] **Agency Kit 1-click:** Pipeline DAG brand → content → copy → campaign (Sprint 5 scope).

---

## 🔗 Quick Links

- `docs/NORTH_STAR.md` — visi immutable
- `docs/MASTER_ROADMAP_2026-2027.md` — timeline sprint
- `docs/LIVING_LOG.md` — riwayat keputusan/detail uji
- `apps/brain_qa/` — backend codebase
- `SIDIX_USER_UI/` — frontend codebase
- VPS: `root@72.62.125.6` `/opt/sidix`

---

**End of handoff. Lanjutkan dari WIP #1 (VERIFY Holistic live).**
