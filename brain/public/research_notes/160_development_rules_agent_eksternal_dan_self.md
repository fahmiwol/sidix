# 160 — Development Rules: Agent Eksternal + SIDIX Self-Development

Tanggal: 2026-04-19
Tag: [DECISION] governance; [LOCK] protocol pengembangan

## Konteks

User minta rules/protokol permanen untuk siapapun yang melanjutkan mengembangkan SIDIX — agent AI apapun (Claude, ChatGPT, agent SDK lain, manusia) dan SIDIX sendiri (self-development autonomous).

Motivasi user (verbatim):
> "ini ko kita muter-muter terus? yang sudah dibuat belum diimplementasiin?"
> "catat di semua dokumen biar nggak tercecer, jika diteruskan agent lain juga, nggak kehilangan konteks dan update."
> "SIDIX harus standing alone, punya modul, framework dan tools sendiri."

Solusi: file [docs/DEVELOPMENT_RULES.md](../../docs/DEVELOPMENT_RULES.md) sebagai aturan mengikat, dibagi 2 audience.

## Part A — Agent Eksternal (12 aturan)

| # | Aturan | Intent |
|---|---|---|
| A1 | Baca 5 dokumen dulu (urutan wajib) | Cegah muter-muter karena skip konteks |
| A2 | Pahami identitas SIDIX 3-layer | Jangan desain fitur salah (bukan RAG-only) |
| A3 | Prinsip standing-alone | Tolak vendor AI API; OK open data API + self-host |
| A4 | UI LOCK app.sidixlab.com | Jangan ubah struktur chatboard tanpa izin |
| A5 | Anti-duplicate | Update SSoT, bukan buat file audit/handoff baru |
| A6 | WAJIB catat LIVING_LOG + research note + CAPABILITY_MAP | Anti-amnesia |
| A7 | Output wajib 4-label + sanad + maqashid + masking + Indonesia | Epistemic integrity |
| A8 | Security audit pre-commit (grep owner/IP/password) | Privasi |
| A9 | Delegate ke subagent untuk task besar | Efisiensi context |
| A10 | Verifikasi sebelum klaim selesai | Trust but verify — cek endpoint live |
| A11 | Commit atomic + co-author line | Traceability |
| A12 | Decision log di docs/decisions/ atau note [DECISION] | ADR |

## Part B — SIDIX Self-Development (10 aturan)

| # | Aturan | Intent |
|---|---|---|
| B1 | Daily growth cycle 7-fase (SCAN→RISET→APPROVE→TRAIN→SHARE→REMEMBER→LOG) | Compounding learning |
| B2 | Whitelist domain pembelajaran | Fokus + maqashid |
| B3 | Blacklist (personal/copyright/hate/face) | Etika + legal |
| B4 | Validasi per-konten (sanad/tier/maqashid/overlap/masking/bahasa) | Kualitas corpus |
| B5 | Self-evaluation loop mingguan (vision_tracker + epistemic_validator) | Detect regressi |
| B6 | Auto-retrain LoRA tiap 7 hari / 500 pair, dengan rollback criteria | Safe continuous deployment |
| B7 | Self-evolving roadmap (image/vision/audio/DiLoCo/SPIN) | Capability parity |
| B8 | Guardrails self-modify (allowlist path, require approval, audit log) | Prevent runaway |
| B9 | Escalation kapan minta user (gap, regressi, strategic, resource) | Human-in-loop titik kritikal |
| B10 | Identity preservation (5 persona, 4 prinsip, masking) | Tidak drift |

## Keputusan desain (anti-revisit)

- **File ini LOCK per 2026-04-19** — edit via ADR di `docs/decisions/` dengan rationale.
- **DEVELOPMENT_RULES.md adalah SSoT** — kalau konflik dengan handoff lama, file ini menang.
- **CLAUDE.md merujuk ke DEVELOPMENT_RULES.md** — satu tempat aturan.
- **Memory `partner_rules.md`** diperbarui dengan pointer ke file repo (agar Claude sesi baru tahu mana yang up-to-date).

## Mengapa 2 audience digabung

Awalnya pertimbangan bikin 2 file terpisah (`AGENT_RULES.md` + `SIDIX_SELF_DEV.md`). Digabung karena:
1. Agent eksternal yang modify growth loop WAJIB paham self-dev protocol (mereka yang implement).
2. Satu file = lebih gampang dipelihara + dibaca sekali.
3. Overlap: audit pre-deploy, commit etiquette, epistemic check — sama untuk keduanya.

## Sanad

- User request: chat 2026-04-19 — "catat dan bikin rules untuk agent manapun kalo nerusin ngembangin SIDIX, termasuk untuk SIDIX sendiri."
- File pokok: `docs/DEVELOPMENT_RULES.md` (commit ini).
- Referensi: CLAUDE.md, SIDIX_CAPABILITY_MAP.md, HANDOFF_2026-04-19.md, INVENTORY_2026-04-19.md, note 157-159.
- Protocol growth loop: existing code `learn_agent.py`, `daily_growth.py`, `auto_lora.py`, `knowledge_gap_detector.py`, `vision_tracker.py`, `epistemic_validator.py`.

## Implementasi belum lengkap (follow-up)

Beberapa protocol di Part B butuh kode tambahan yang belum ada:

| Protocol | File yang perlu dibuat/dimodifikasi |
|---|---|
| B4 validasi pipeline | Extend `note_drafter.py` dengan maqashid + overlap check |
| B5 weekly audit auto | Cron `0 4 * * 0 curl /research/weekly-audit` + endpoint baru |
| B6 auto-retrain pipeline | `auto_lora.py` butuh swap + rollback logic, validation test set |
| B8 self-modify guardrail | `workspace_write` tool tambah allowlist path + audit log jsonl |
| B9 escalation ke user | Endpoint `/admin/notif` atau webhook; `docs/open_questions.md` append helper |

Flag sebagai **next-sprint backlog** untuk agent berikut yang pilih Plan C (sub-agent) atau plan khusus self-dev.
