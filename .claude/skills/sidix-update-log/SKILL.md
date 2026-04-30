---
name: sidix-update-log
description: Append entry verbatim bos ke FOUNDER_IDEA_LOG.md atau update BACKLOG.md state. Pakai di akhir sesi atau saat bos kasih ide visi/intuisi baru. Anti-menguap permanent.
---

# SIDIX Update Log Skill

Tiap kalimat bos yang berisi **visi / intuisi / teori / ide baru / koreksi penting** WAJIB dicatat di `docs/FOUNDER_IDEA_LOG.md`. Tanpa ini = ide menguap = bos repeat-jelaskan = pain.

Tiap akhir sesi, BACKLOG WAJIB di-update dengan state sprint terkini.

## Cara Pakai

### Untuk capture ide bos:

User pakai `/sidix-update-log [ringkasan bos's verbatim quote]` atau saya proactively detect bos kasih visi baru → langsung append.

Format entry:

```markdown
---

## [DATE] [time of day] — [Topic Singkat]

### Bos verbatim:
> "[verbatim quote bos, exact text]"

### Translation:
- [poin penting]
- [poin penting]

### BACKLOG entry / Sprint candidate / Implementation:
- [link ke action konkret]

### Status: ✅ CAPTURED + [next step]
```

### Untuk update BACKLOG:

Saat sprint berubah status (baru COMPLETED / IN PROGRESS update / QUEUED tambah / DROPPED):

Append/edit entry di `docs/SIDIX_BACKLOG.md` sesuai section (✅ COMPLETED / 🔄 IN PROGRESS / 📋 QUEUED / 💡 IDEAS / ❌ DROPPED).

Format BACKLOG entry:

```markdown
### Sprint [Nama]
- **Visi mapping**: [aspect]
- **Date**: [tanggal]
- **Deliverable**: [konkret]
- **Acceptance**: [verifiable]
- **Evidence**: [research note / commit / live URL]
- **Commits**: [hash list]
- **Status**: [LIVE/IN PROGRESS/etc]
```

## Anti-Pattern Dilarang

- ❌ Skip catat ide bos verbatim → menguap
- ❌ Generate dengan paraphrase saja (lose original voice)
- ❌ Update BACKLOG tanpa visi mapping (drift)
- ❌ Catat acknowledgment biasa ("ok", "lanjut") — skip yang ini

## Pattern Trigger (Kapan Auto-Catat)

Catat saat bos:
- Kasih visi/tujuan besar
- Kasih analogi/metafora ("jurus seribu bayangan", "Adobe-of-Indonesia")
- Kasih koreksi/veto
- Delegate authority
- Express pain point (untuk root cause analysis)

## Reference

- `docs/FOUNDER_IDEA_LOG.md` (entry log)
- `docs/SIDIX_BACKLOG.md` (sprint state)
- `docs/AGENT_ONBOARDING.md` (universal protocol)
