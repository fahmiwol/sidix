# Note 284 — Sprint 39: Quarantine + Promote Flow (Pencipta Lifecycle)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Sanad**: Sprint 39 compound Sprint 38b (reactor_steps.jsonl) + Sprint 37 (Hafidz Ledger) + Sprint 38 (tool_synthesis MVP).  
**Tanggal**: 2026-04-29  
**Status**: SHIPPED ✅

---

## Apa

Sprint 39 menyelesaikan **lifecycle management** untuk Pencipta milestone:

```
[Sprint 38]                   [Sprint 39]
tool_synthesis.py        →    quarantine_manager.py
  detect_repeated_sequences       list_quarantine()
  propose_macro              →    auto_test_skill()
  write_proposal_to_quarantine    promote_skill()
                                  reject_skill()
skills/quarantine/*.yaml  →  skills/active/*.yaml  |  skills/rejected/*.yaml
                                  active/index.json
                                  hafidz_ledger.jsonl  (sanad-as-governance)
```

Sebelum Sprint 39, skills yang dipropose oleh Tool Synthesis hanya "numpuk"
di quarantine/ tanpa bisa di-review, di-approve, atau di-promote ke production.
Sprint 39 menutup gap itu.

---

## Mengapa

**Voyager pattern (NeurIPS 2023)**: skill library harus tumbuh dari experience —
generate → verify → promote → execute. Tanpa promote flow, "Pencipta" milestone
tidak bisa tuntas. SIDIX harus bisa memproduksi dan mengaktifkan skill-nya sendiri.

**Sanad-as-governance (note 276)**: setiap promoted skill punya `isnad_chain`
yang traceable ke parent proposal → detector cycle → react_steps.jsonl source.
Ini bukan sekedar "skill baru" — ini **knowledge dengan provenance chain**.

---

## Bagaimana

### quarantine_manager.py — 5 fungsi utama

```python
list_quarantine()     # scan quarantine/*.yaml → SkillInfo list dengan age_days
auto_test_skill(id)   # structural checks: YAML parseable + fields + TOOL_REGISTRY
promote_skill(id, owner_note, force)  # age_check → auto_test → copy → index → hafidz
reject_skill(id, reason)              # copy → rejected/ + hafidz entry + cleanup
list_active()         # scan active/*.yaml → SkillInfo list
```

### YAML parser (no PyYAML dep)

Manual parser untuk format minimal yang ditulis `tool_synthesis.py`:
- Key-value: `key: value`
- List: `key:\n  - item1\n  - item2`
- Handles integer auto-cast untuk `frequency`

Konsisten dengan `tool_synthesis.py` approach (lean, no extra dep).

### Auto-test MVP scope

Sprint 39 auto-test = **structural validation only**:
1. YAML parseable
2. Required fields ada: `skill_id`, `composed_from`, `trigger_pattern`
3. Setiap tool dalam `composed_from` exist di `TOOL_REGISTRY`

NOT sandbox execution (Sprint 38c defer) — belum ada execution runtime.
Structural check cukup untuk quarantine gate.

### Age gate

`QUARANTINE_MIN_DAYS = 7` — minimum 7 hari di quarantine sebelum promote.
`force=True` override untuk owner testing.

Alasan 7 hari: cukup waktu observe apakah sequence yang sama muncul lagi
(validasi dari usage pattern), tanpa blockt growth terlalu lama.

### Hafidz Ledger isnad chain (sanad-as-governance)

```python
# promote_skill → _write_promote_to_hafidz
write_entry(
    content_id=f"skill-active-{skill_id}",
    content_type="skill_active",
    isnad_chain=[f"skill-proposal-{skill_id}"],  # ← traceable ke parent
    tabayyun_quality_gate=True,  # auto_test passed
    ...
)

# reject_skill → hafidz entry
write_entry(
    content_id=f"skill-rejected-{skill_id}",
    content_type="skill_rejected",
    isnad_chain=[f"skill-proposal-{skill_id}"],  # ← traceable ke parent
    owner_verdict="rejected",
    ...
)
```

Chain traceability:
```
skill-active-X → skill-proposal-X → (hafidz entry dari Sprint 38)
                                   → react_steps.jsonl (Sprint 38b)
```

### CLI subcommands (__main__.py)

```bash
python -m brain_qa quarantine_review       # list all quarantine dengan age + auto-test
python -m brain_qa promote_skill --skill-id X [--force] [--owner-note "..."]
python -m brain_qa reject_skill --skill-id X [--reason "..."]
```

### Admin API endpoints (agent_serve.py)

```
GET  /admin/skills/quarantine     # list proposals (admin-gated)
POST /admin/skills/promote        # body: {skill_id, owner_note?, force?}
POST /admin/skills/reject         # body: {skill_id, reason?}
GET  /admin/skills/active         # list promoted skills
```

Semua di-gate `_admin_ok(request)` — butuh `X-Admin-Token` header.

---

## Active Index

`active/index.json` — maintained by `_update_active_index()`:

```json
[
  {
    "skill_id": "search_corpus_web_search_search_corpus",
    "composed_from": ["search_corpus", "web_search", "search_corpus"],
    "trigger_pattern": "search_corpus then web_search then search_corpus",
    "frequency": 4,
    "confidence": "low",
    "promoted_at": "2026-04-29T..."
  }
]
```

Index ini akan jadi input untuk **dispatch router** — Sprint 40+ bisa query index
untuk route query ke macro yang sesuai, bukan hardcode tool calls.

---

## Compound Chain

```
Sprint 36 Reflection Cycle  →  lesson draft "Repeated Tool Sequences"
Sprint 37 Hafidz Ledger     →  provenance trail per proposal
Sprint 38 Tool Synthesis MVP →  module + CLI (detector gap)
Sprint 38b Detector Source  →  react_steps.jsonl primary source
Sprint 39 Quarantine + Promote  →  THIS NOTE — lifecycle complete
Sprint 40+ Telegram / dispatch  →  next: owner notify + macro dispatch
```

---

## Keterbatasan

- `auto_test` = structural only; belum sandbox execution (Sprint 38c)
- `promote_skill` butuh manual owner call (CLI atau API); belum Telegram push (Sprint 40)
- `active/index.json` belum di-query oleh `agent_react.py` dispatch (Sprint 40+)
- Skill yang di-promote belum otomatis "execute" — hanya tersimpan, perlu wire ke tool dispatch

---

## Pencipta Milestone Progress

```
[✅] Tool Synthesis detector  →  react_steps.jsonl primary (Sprint 38b)
[✅] Proposal generation      →  quarantine/*.yaml (Sprint 38)
[✅] Lifecycle management     →  promote/reject/active (Sprint 39)
[⏳] Data accumulation        →  min 3 sessions react sequence → propose
[⏳] Macro dispatch           →  active skills → tool router (Sprint 40+)
[⏳] Telegram owner notify    →  Sprint 40
```

SIDIX sekarang bisa: **mendeteksi pola → propose skill → quarantine → approve → aktif**.
Yang tersisa: data accumulate + wire dispatch + Telegram notification.
