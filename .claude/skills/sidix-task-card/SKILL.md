---
name: sidix-task-card
description: Generate Task Card sebelum eksekusi apapun di proyek SIDIX (mandatory per anti-menguap protocol). Format WHAT/WHY/ACCEPTANCE/PLAN/RISKS dengan visi mapping + sprint context + founder request link.
---

# SIDIX Task Card Skill

Sebelum tool call / file edit / code execution di proyek SIDIX, agent WAJIB tulis Task Card. Tanpa Task Card = "asal eksekusi tanpa tau buat apa" = melanggar protocol bos.

## Cara Pakai

Saat user request fitur/perubahan/sprint, invoke `/sidix-task-card` atau langsung output Task Card sebelum tool call.

## Format Wajib

```
═══════════════════════════════════════════════════════════
TASK CARD: [nama task konkret, max 60 char]

WHAT (1 kalimat konkret):
[apa yang dibangun]

WHY:
- Visi mapping: [genius/creative/tumbuh/cognitive/iteratif/inovasi/pencipta]
- Sprint context: [BACKLOG entry / sprint name]
- Founder request: [link ke FOUNDER_IDEA_LOG entry]
- Coverage shift: [VISI_TRANSLATION_MATRIX point yang akan naik %]

ACCEPTANCE (verifiable, 1-3 criteria):
1. [...]
2. [...]
3. [...]

PLAN (3-7 step konkret):
1. [step file/action specific]
2. ...

RISKS (1-3 dengan mitigation):
- [risk] → mitigation: [...]
═══════════════════════════════════════════════════════════
```

## Anti-Pattern Dilarang

- ❌ Task Card tanpa visi mapping (drift dari Northstar)
- ❌ ACCEPTANCE abstract ("kode lebih bagus") — must verifiable
- ❌ PLAN dengan step generic ("edit beberapa file") — must spesifik
- ❌ Eksekusi sebelum Task Card disetujui (kalau Task Card salah, fix dulu)

## Reference

Format lengkap di `docs/TASK_CARD_TEMPLATE.md`. Visi mapping di `docs/VISI_TRANSLATION_MATRIX.md`.
