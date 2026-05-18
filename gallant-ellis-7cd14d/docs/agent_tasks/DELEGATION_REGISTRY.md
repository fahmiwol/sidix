# DELEGATION REGISTRY — SIDIX Multi-Agent Tasks

**Update file ini** setiap kali task baru didelegasikan, status berubah, atau PR merge.
**Dibuat:** 2026-04-19 oleh Claude (koordinator sprint).

---

## 📊 Registry Aktif

| Task ID | Nama Task | Agent | Branch | Status | PR | Laporan |
|---------|-----------|-------|--------|--------|----|---------|
| T1.1 | Wire `concept_graph` tool | Claude | `claude/determined-chaum-f21c81` | ✅ merged (commit 6b38731) | — | — |
| T1.2 | Sanad-based ranker `search_corpus` | Cursor | `cursor/sprint-1/t1.2-sanad-ranker` | ✅ review passed, awaiting merge | [buka PR](https://github.com/fahmiwol/sidix/pull/new/cursor/sprint-1/t1.2-sanad-ranker) | `docs/agent_tasks/reports/T1.2_report_cursor.md` |
| T1.3 | Fix cron LearnAgent + corpus index | Claude | `claude/determined-chaum-f21c81` | ✅ live (commit 53ea97f, corpus 1149 docs) | — | — |
| T1.4 backend | Endpoint `/concept_graph/query` | Claude | `claude/determined-chaum-f21c81` | ✅ live (commit 53ea97f) | — | — |
| T1.4 frontend | Badge sanad tier di citations UI | Cursor | `cursor/sprint-2/t1.4-frontend-badge` | ⏳ pending (start setelah T1.2 merge) | — | — |
| R1 | GPU provider comparison | Claude (Antigravity PET error, di-takeover) | `claude/determined-chaum-f21c81` | ✅ done | — | note 170 |
| R2 | SDXL vs FLUX.1 comparison | Claude (takeover) | `claude/determined-chaum-f21c81` | ✅ done | — | note 171 |
| R3 | Nusantara KB schema design | Claude (takeover) | `claude/determined-chaum-f21c81` | ✅ done | — | note 172 |
| R4 | ComfyUI vs Diffusers deployment | Claude (takeover) | `claude/determined-chaum-f21c81` | ✅ done | — | note 173 |
| ADR-001 | Sprint 3 Image Gen Stack decision | Claude | `claude/determined-chaum-f21c81` | ✅ done, awaiting user approval | — | `docs/decisions/ADR_001_sprint3_image_gen_stack.md` |

---

## 🔜 Sprint 2 Queue (start paralel setelah Sprint 1 T1.2 merge)

| Task ID | Nama Task | Agent | Status |
|---------|-----------|-------|--------|
| T2.1 | `math_solve` tool (SymPy) | Cursor | ⏳ pending |
| T2.2 | `data_analyze` tool (pandas) | Cursor | ⏳ pending |
| T2.3 | `plot_generate` tool (matplotlib) | Cursor | ⏳ pending |
| T2.4 | Frontend file upload CSV/XLSX | Cursor | ⏳ pending |
| C-03 | Endpoint `/workspace/upload` backend | Claude | ⏳ pending |
| C-04 | Weekly audit endpoint + cron | Claude | ⏳ pending |

---

## 🔜 Sprint 3 Queue (butuh output R1-R4 Antigravity dulu)

| Task ID | Nama Task | Agent | Status |
|---------|-----------|-------|--------|
| T3.1 | Image gen — self-host SDXL/FLUX | Claude (infra) + Cursor (kode) | ⏳ pending (decision gate: setelah note 170-173 merge) |
| T3.2 | Vision/VLM — Qwen2.5-VL | Claude (infra) + Cursor (kode) | ⏳ pending |
| T3.3 | Whisper ASR self-host | Claude (infra) | ⏳ pending |
| T3.4 | Piper TTS self-host | Claude (infra) | ⏳ pending |

---

## 🧠 Creative Capability Queue (Sprint 4+, per note 165)

Lihat `docs/CREATIVE_CAPABILITY_ROADMAP.md` untuk detail teknis per kapabilitas.

| Kapabilitas | Target Stage | Agent Lead |
|-------------|-------------|-----------|
| WebGL/Three.js scene generator | Child (Q3 2026) | Cursor |
| Text-to-Image (SDXL/FLUX) | Sprint 3 | Claude+Cursor |
| Image-to-Text (VLM caption) | Sprint 3 | Claude+Cursor |
| Image-to-Image (ControlNet) | Child Q3 | Cursor |
| Text-to-Sound (AudioCraft/MusicGen) | Child Q3 | Cursor |
| TTS (Piper/Coqui) | Sprint 3 | Claude |
| Photo editor tools (PIL/OpenCV) | Sprint 2 ext | Cursor |
| Video generation | Adolescent Q4 | Research needed |
| Code playground (multi-lang) | Sprint 2 | Cursor |
| 3D render (Blender Python API) | Child Q3 | Research needed |

---

## 📋 DoD Checklist Template (untuk setiap task)

```
- [ ] Kode implement sesuai spec di task file
- [ ] Unit test pass (min 3 case)
- [ ] Research note ditulis
- [ ] LIVING_LOG di-append
- [ ] CAPABILITY_MAP diupdate (kalau ada tool baru)
- [ ] No vendor AI API imported
- [ ] PR opened dengan body link ke task file + request review @claude
- [ ] Report di docs/agent_tasks/reports/<TASK_ID>_report_<agent>.md
```

---

## 🔄 Update Protocol

1. Ketika task dimulai → ubah status `⏳ pending` → `🔄 in-progress` + isi branch
2. Ketika PR dibuka → isi kolom PR dengan link
3. Ketika Claude approve → ubah `🔄 in-progress` → `✅ review passed, awaiting merge`
4. Ketika merge → ubah ke `✅ merged (commit <hash>)` + isi laporan

---

Terakhir diupdate: 2026-04-19 oleh Claude.
