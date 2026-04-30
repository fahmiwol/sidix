---
name: sidix-state
description: Auto-load SIDIX project state — BACKLOG digest + visi coverage + recent decisions + WIP. Pakai ini di awal sesi sebelum eksekusi apapun di proyek SIDIX.
---

# SIDIX State Skill

Sesi baru di proyek SIDIX wajib output state read dulu (per `CLAUDE.md` SESSION START PROTOCOL). Skill ini auto-load ringkasan state dari 9 docs anti-menguap.

## Cara Pakai

User invoke `/sidix-state` atau "show sidix state".

## Yang Saya Lakukan

1. **Read 5 docs canonical** dengan tail/head untuk hemat token:
   - `tail -80 docs/SIDIX_BACKLOG.md` (state sprint terkini)
   - `tail -50 docs/VISI_TRANSLATION_MATRIX.md` (coverage table)
   - `tail -100 docs/FOUNDER_IDEA_LOG.md` (5 ide bos terbaru)
   - `tail -150 docs/FOUNDER_JOURNAL.md` (decisions recent)
   - `tail -50 docs/LIVING_LOG.md` (ops recent)

2. **Output digest** ke user dalam format:

```
📋 SIDIX STATE READ:
- BACKLOG: [N completed, M in-progress, K queued]
- WIP carry-over: [list sprint belum kelar]
- Visi gap utama: [point coverage terendah]
- Recent decisions: [3 item terbaru]
- Sprint berikutnya queued: [nama]
- Pertanyaan bos: [paraphrase kalau ada]
- Saya akan: [action konkret]
```

## Anti-Pattern (Dilarang Setelah Skill Ini)

- ❌ Eksekusi tanpa baca state ini dulu
- ❌ Tanya bos detail teknis (saya yang ambil otoritas per BACKLOG)
- ❌ Skip update BACKLOG di akhir sesi

## Reference

Detail protocol di `docs/AGENT_ONBOARDING.md` + `CLAUDE.md` SESSION START PROTOCOL.
Pattern lahir dari research note 306 (anti-menguap diagnose).
