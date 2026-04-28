# 206 — CoT Engine + Branch Gating (Sprint 10)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Sanad tier**: internal-impl  
**Epistemic label**: [FACT] (implementasi langsung di codebase)  
**Tanggal**: 2026-04-25  
**Referensi**: Note 200 (roadmap frontier), Note 201 (Constitutional AI), Note 198 (Tiranyx Agency OS)

---

## 1. Apa

Dua komponen baru yang di-wire ke ReAct loop SIDIX pada Sprint 10:

**A. CoT Engine** (`brain_qa/cot_engine.py`)  
Chain-of-Thought adaptif: mendeteksi kompleksitas query → inject scaffold penalaran ke dalam sesi sebelum loop dimulai. Seperti memberikan "mode berpikir" yang tepat kepada agent sebelum ia menjawab.

**B. Branch Gating** (`branch_manager.py` → `agent_react.py`)  
Multi-tenant access control yang akhirnya di-wire: setiap kombinasi `(agency_id, client_id)` punya `tool_whitelist` dan `corpus_filter`. Sebelumnya ada tapi tidak dipanggil — Sprint 10 men-wire-nya ke dalam ACT step.

---

## 2. Mengapa

### Mengapa CoT?
LLM yang lebih kecil (7B, 3B) cenderung langsung ke kesimpulan tanpa penalaran bertahap. CoT scaffolding memaksa model mengikuti struktur berpikir yang eksplisit → jawaban lebih akurat, lebih terverifikasi.

Riset menunjukkan (Wei et al., 2022; Google PaLM): CoT meningkatkan akurasi 2-4× pada task multi-step vs direct answer. Untuk SIDIX dengan model 7B, perbedaannya signifikan.

### Mengapa per-persona?
Tiap persona SIDIX punya epistemologi berbeda:
- **UTZ** (pengajar): berpikir bertahap, dari fondasi ke detail
- **AYMAN** (developer): requirement → arsitektur → implementasi → edge case
- **ABOO** (kreatif): esensi → brainstorm → pilih → polish
- **OOMAR** (fikih): dalil primer → perbedaan ulama → kesimpulan dengan label epistemic
- **ALEY** (konselor): validasi emosi → kebutuhan inti → respons empatik

### Mengapa Branch Gating baru di-wire sekarang?
Sudah ada sejak Sprint 8d (Tiranyx) tapi tidak pernah dipanggil di execution path. Gap antara "fitur ada di file" vs "fitur terpanggil saat runtime" — audit Sprint 10 menemukannya.

---

## 3. Bagaimana

### CoT Engine — Complexity Classifier

```python
def classify_complexity(question: str) -> str:  # "high" | "medium" | "low"
```

Tiga level via regex matching:
- **low**: greeting patterns + panjang < 40 char
- **high**: kata kunci multi-step (bandingkan, implementa*, analisis, debug, rancang, math expressions)
- **medium**: default — definisi, penjelasan, contoh, pertanyaan hukum

### CoT Pre-step Injection

```python
# Di run_react(), sebelum for loop:
_cot_scaffold = get_cot_scaffold(working_question, persona)
if _cot_scaffold:
    _pre_step_cot = ReActStep(
        step=-3,
        thought=f"[CoT] Kompleksitas={_cot_complexity}.",
        action_name="cot_scaffold",
        observation=_cot_scaffold,
    )
    session.steps.insert(0, _pre_step_cot)
```

Scaffold masuk sebagai pre-step (step -3, sebelum experience -2 dan skill -1). Saat `_compose_final_answer` membaca history, ia melihat instruksi penalaran di awal → output mengikuti struktur tersebut.

### Branch Gating — Tool Whitelist

```python
# Di ACT step, sebelum call_tool():
if _bm is not None and (_agency_id or _client_id):
    if not _bm.is_tool_allowed(_agency_id, _client_id, action_name):
        result = ToolResult(success=False, error=f"Tool '{action_name}' tidak diizinkan...")
        observation = f"[BLOCKED] {result.error}"
        session.steps.append(react_step)
        continue  # skip ke step berikutnya
```

Jika agency/client default kosong → skip gate (backward compatible dengan user biasa).

### Corpus Filter Injection

```python
# Sebelum call_tool():
_effective_args = dict(action_args)
if _corpus_filter and action_name in ("search_corpus", "graph_search"):
    _effective_args.setdefault("_corpus_filter", _corpus_filter)
```

Di dalam `_tool_search_corpus()`: fetch `k*3` results, filter yang `source_path` mengandung tag dari `corpus_filter`, kembalikan `k` terbaik. Fallback graceful: jika filter terlalu ketat dan hasil kosong, tetap kembalikan data asli.

---

## 4. Contoh Nyata

### Skenario: Tiranyx branch AYMAN (developer)

```json
// Branch config:
{
  "agency_id": "tiranyx",
  "client_id": "ayman",
  "tool_whitelist": ["search_corpus", "graph_search", "code_sandbox", "shell_run", "git_status"],
  "corpus_filter": ["software", "coding", "programming"]
}
```

User tanya: *"Implementasikan binary search tree dalam Python"*

1. `classify_complexity()` → **high**
2. `get_cot_scaffold("...", "AYMAN")` → scaffold engineering 4-langkah
3. Pre-step -3 inject scaffold
4. Step 0: planner plan `search_corpus(query="binary search tree python")`
5. `is_tool_allowed("tiranyx", "ayman", "search_corpus")` → **True**
6. `_corpus_filter = ["software", "coding", "programming"]` → diinjek ke args
7. `_tool_search_corpus` fetch hasil lalu filter ke dokumen coding saja
8. Step berikutnya: `code_sandbox` → allowed (ada di whitelist)
9. Jika agent coba `web_search` → **BLOCKED** (tidak di whitelist)

### Skenario: Tiranyx branch ABOO (konten)

```json
{
  "tool_whitelist": ["search_corpus", "generate_content_plan", "social_radar"],
  "corpus_filter": ["marketing", "content", "copywriting"]
}
```

Agent tidak bisa panggil `code_sandbox` atau `shell_run` → keamanan terjaga.

---

## 5. Keterbatasan

### CoT Engine
- **Rule-based**: classifier tidak memahami semantik, hanya pattern match. Query ambigu bisa salah klasifikasi.
- **Scaffold statis**: 5 persona × 3 level = 15 template. Tidak adaptif dari feedback user.
- **Impact terbatas tanpa LLM inference**: saat ini SIDIX rule-based planner tidak "membaca" scaffold — compose_final_answer perlu ditingkatkan agar benar-benar mengikuti scaffold.
- **TODO**: Saat LLM Qwen2.5 aktif, scaffold harus masuk ke `<system>` token bukan hanya history step.

### Branch Gating
- **In-memory**: BranchManager singleton di-reload setiap restart. Persistensi ke `data/branches.json` sudah ada, tapi tidak sync ke VPS kecuali manual sync.
- **Corpus filter by source_path**: filter berdasarkan substring dari path file, bukan metadata tag yang kaya. Tagging system yang lebih baik diperlukan.
- **Tidak ada audit log per-block**: saat tool diblokir, log masuk ke Python logger tapi tidak ke audit JSONL. TODO: tambahkan ke `_log_tool_call`.

---

## 6. Rencana Pengembangan

| Phase | Action |
|-------|--------|
| Sprint 11 | Expose `agency_id` di ChatResponse → frontend bisa tahu branch aktif |
| Sprint 12 | Audit log tiap tool block ke `agent_audit.jsonl` |
| Phase 1 LLM | Inject CoT scaffold ke `<system>` token Qwen2.5 saat inference aktif |
| Phase 2 | Adaptive CoT: belajar dari Jariyah pairs (DPO) mana scaffold yang efektif |
| Phase 3 | Corpus tagging system: setiap dokumen punya `tags[]` metadata → filter lebih presisi |

---

*Catatan implementasi: SIDIX Sprint 10, 2026-04-25. Total tools setelah sprint: 45.*
