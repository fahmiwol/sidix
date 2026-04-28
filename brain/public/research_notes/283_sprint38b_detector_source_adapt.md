# Note 283 — Sprint 38b: Detector Source Adapt (Tool Synthesis Fix)

**Sanad**: Sprint 38b compound Sprint 38 (tool_synthesis MVP) + Sprint 36 (reflect_day).  
**Tanggal**: 2026-04-29  
**Status**: SHIPPED ✅

---

## Apa

Sprint 38b memperbaiki root cause mengapa `tool_synthesis.detect_repeated_sequences()` selalu
return 0 sequences di VPS production.

**Root cause** (diagnose sebelum iter — feedback_diagnose_before_iter.md):

```
sidix_observations.jsonl  ←  ditulis oleh sidix_always_on.sh
Format field: {"kind": "git_activity" | "commit_seen" | "diff_stats" | ...}

tool_synthesis.py (Sprint 38)
  reads: e.get("action") or e.get("tool") or e.get("name")
  → SELALU "" karena field "kind" tidak pernah dicek
  → 0 events → 0 sequences detected → 0 proposals
```

`sidix_observations.jsonl` adalah **system observation log** (git activity, commit tracking),
bukan **ReAct tool execution log**. Tidak ada file yang log tool calls ReAct sebelum Sprint 38b.

---

## Mengapa

Tool Synthesis adalah **Pillar Pencipta** — SIDIX mendeteksi pola tool berulang → propose skill baru.
Tanpa detector yang berfungsi, Pencipta milestone tidak bisa jalan. Sprint 38 partial karena gap ini.

Sprint 38b menyelesaikan gap: buat source data yang benar, update detector untuk baca sumber itu.

---

## Bagaimana

### 1. Tambah REACT step logger di `agent_react.py`

```python
def _log_react_step_to_file(action_name, session_id, step_num, persona):
    """Append non-final REACT step ke react_steps.jsonl."""
    # Non-blocking, format: {ts, session_id, action, persona, step}
    entry = {"ts": ..., "session_id": ..., "action": action_name, ...}
    with open("/opt/sidix/.data/react_steps.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
```

Hook dipasang di dalam `run_react()` setelah setiap non-final `session.steps.append(react_step)`:

```python
session.steps.append(react_step)
_praxis.record_react_step(session_id, react_step)
_log_react_step_to_file(action_name, session_id, step_num, persona)  # Sprint 38b
```

Format `react_steps.jsonl`:
```json
{"ts":"2026-04-29T...", "session_id":"abc123", "action":"search_corpus", "persona":"UTZ", "step":0}
{"ts":"2026-04-29T...", "session_id":"abc123", "action":"web_search", "persona":"UTZ", "step":1}
```

### 2. Update `tool_synthesis.py` — primary/fallback source logic

Tambah `_load_tool_events()` helper:

```
Priority 1 → react_steps.jsonl  (field "action" = real tool names dari ReAct)
Priority 2 → sidix_observations.jsonl  (field "kind" → mapped via _KIND_TO_TOOL)
```

`_KIND_TO_TOOL` mapping:
```python
"commit_seen"  → "git_commit"
"git_activity" → "git_activity"
"diff_stats"   → "git_diff"
"self_progress"→ "progress_check"
...
```

Fallback berguna untuk masa transisi sebelum `react_steps.jsonl` terisi cukup data.

---

## Verifikasi Offline

```
Test primary source (react_steps.jsonl):
  _load_tool_events: 12 events  ✓
  detect_repeated_sequences: 1 sequence ('search_corpus', 'web_search', 'search_corpus') count=4  ✓
  propose_macro: skill_id=search_corpus_web_search_search_corpus conf=low  ✓

Test fallback (sidix_observations.jsonl kind field):
  fallback events: 15  ✓
  tool names: {'git_activity', 'git_commit'}  (kind→tool mapping OK)  ✓

Syntax check: ast.parse OK untuk tool_synthesis.py + agent_react.py  ✓
```

---

## Keterbatasan

- `react_steps.jsonl` baru mulai terisi setelah Sprint 38b deploy + VPS restart
- Minimum data untuk detect (min_count=3): butuh 3+ user sessions dengan tool sequence berulang
- `parallel_tools` (virtual action name untuk parallel execution) di-skip di logger — hanya log single action steps
- Data retensi `react_steps.jsonl` tidak ada rotation; perlu cron cleanup kalau file terlalu besar (defer)

---

## Compound Chain

```
Sprint 36 Reflection Cycle  →  lesson draft "Repeated Tool Sequences" section
Sprint 37 Hafidz Ledger     →  provenance trail per proposal
Sprint 38 Tool Synthesis MVP →  module + CLI shipped (detector 0 sequences gap)
Sprint 38b Detector Source Adapt →  THIS NOTE — fix detector → Pencipta milestone JALAN
Sprint 39 Quarantine + Promote →  next: sandbox execution + owner approve flow
```

---

**Pencipta milestone**: setelah 38b + data accumulate beberapa hari → detector detect sequence
→ SIDIX propose skill pertama lahir dari dirinya sendiri → quarantine (Sprint 39) → promote ke active.
