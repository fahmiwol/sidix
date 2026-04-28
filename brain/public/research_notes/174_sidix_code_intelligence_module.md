> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
sanad_tier: primer
---

# 174 — SIDIX Code Intelligence Module: SIDIX Bisa Ngoding

Tanggal: 2026-04-21
Tag: [IMPL] code_intelligence.py selesai; [DECISION] arsitektur tool-augmented coding; [FACT] 30 tool aktif; [TEST] smoke test passed

Sumber: sesi implementasi 2026-04-21 + research_notes/162_framework_brain_hands_memory.md

---

## 1. Konteks: Mengapa SIDIX Perlu "Bisa Ngoding"

Target sesi ini: SIDIX bisa **ngoding, memahami program, menyusun untuk dirinya sendiri** —
setara kemampuan coding Opus/Sonnet.

Miskonsepsi yang harus dihindari: "SIDIX perlu model coding 100B+ parameter".
Fakta: **Opus/Sonnet juga tidak satu model tunggal**. Mereka adalah:
- LLM otak yang reasoning
- Tool `code interpreter` yang run Python
- Tool `computer use` yang baca file
- Konteks panjang yang hold seluruh codebase

**SIDIX bisa replikasi ini** dengan Qwen2.5-7B-LoRA + tool stack lengkap.
Ini pendekatan Brain + Hands (lihat note 162).

---

## 2. Tools Baru yang Dibangun (Sprint 2026-04-21)

### 2.1 `code_analyze` (via `code_intelligence.py`)
**Apa**: Analisis statik kode Python melalui AST (Abstract Syntax Tree).
**Input**: `code` (str) + `filename` (opsional) + `verbose` (bool)
**Output**: List fungsi, kelas, import, kompleksitas cyclomatic, ringkasan

**Contoh output**:
```
# Analisis Kode: agent_tools.py
- Baris: 2043
- Syntax: OK
- Kompleksitas total: 187

## Fungsi (89)
  L34: def _log_tool_call(tool_name, args, result_summary, approved, session_id, step)  [cx=2]
  L68: def _tool_search_corpus(args)  [cx=3]
  ...
```

**Kenapa penting**: LLM bisa "melihat" struktur kode sebelum mengeditnya.
Tanpa ini, LLM harus baca 2000 baris mentah untuk tahu ada fungsi apa saja.
Dengan `code_analyze`, satu tool call → struktur lengkap → LLM bisa targeted edit.

**Keterbatasan**: Statik only — tidak bisa detect runtime behavior, side effects,
atau bug logic (untuk itu butuh `code_sandbox`).

### 2.2 `code_validate` 
**Apa**: Compile-check Python tanpa menjalankan.
**Input**: `code` (str)
**Output**: `"Syntax OK"` atau `"SyntaxError baris N: ..."`

**Kenapa penting**: Sebelum `workspace_write`, selalu validate dulu.
Flow optimal: LLM generate kode → `code_validate` → jika OK → `workspace_write` → `code_sandbox` test.

### 2.3 `project_map`
**Apa**: Tree struktur folder (seperti perintah `tree` Linux).
**Input**: `path` (opsional, default workspace root) + `depth` (1-5)
**Output**: ASCII tree

**Kenapa penting**: LLM tidak punya "mata" untuk lihat file system.
Dengan `project_map`, SIDIX bisa orientasi: "file apa yang ada? di folder mana?"
sebelum baca/tulis. Ini replikasi kemampuan `ls -la` / Glob di Claude Code.

**Path resolution**: Relative path dicoba urutan: workspace → repo root → cwd.

### 2.4 `self_inspect`
**Apa**: Meta-tool — SIDIX melihat dirinya sendiri.
**Input**: `target` ("tools" | "modules" | "all")
**Output**:
- `tools`: daftar 30 tool + params + permission + deskripsi singkat
- `modules`: daftar 102 modul brain_qa + jumlah baris masing-masing

**Kenapa penting**: Ini fondasi **self-composition** — SIDIX tahu:
- "Saya punya tool apa saja?" → tidak perlu tanya user, inspect langsung
- "Modul mana yang relevan untuk task ini?" → bisa baca modulnya via `workspace_read`
- "Saya sudah bisa apa? Apa yang belum?" → capability gap awareness

**Contoh use case**:
```
User: "Buat tool baru untuk convert markdown ke HTML"
SIDIX: 
  1. self_inspect → lihat tool yang ada (apakah sudah ada md→html?)
  2. project_map → orientasi struktur
  3. search_corpus → cari referensi/contoh
  4. code_sandbox → test prototype
  5. code_validate → validasi sintaks
  6. workspace_write → tulis tool draft
```

### 2.5 Upgrade `code_sandbox`
**Perubahan**:
- Timeout: 10s → 30s (bisa di-override hingga 60s via param `timeout`)
- Max output: 4KB → 8KB
- Forbidden list: diperketat ke `os.system(`, `subprocess.run(`, `subprocess.Popen(`
  (allow `os.path`, `os.getcwd`, `os.environ` — dibutuhkan untuk analisis)

---

## 3. Arsitektur `code_intelligence.py`

```
code_intelligence.py
  ├── analyze_code(source, filename) → CodeAnalysis
  │     ├── AST parse + walk
  │     ├── FunctionInfo (nama, args, is_async, docstring, decorators, complexity)
  │     ├── ClassInfo (nama, bases, methods, docstring)
  │     ├── imports list
  │     └── format_analysis_text() → human-readable
  ├── validate_python(source) → {ok, error, line}
  ├── extract_dependencies(source) → list[str]
  ├── get_project_map(root, depth) → str tree
  ├── summarize_module_file(path) → str
  ├── get_self_modules() → list[{name, path, size_lines}]
  └── get_self_tools_summary() → list[dict] via list_available_tools()
```

Semua fungsi **murni statik** — tidak ada network call, tidak ada subprocess.
Aman, cepat, deterministik.

---

## 4. Peta Kemampuan Coding SIDIX (Post Sprint)

| Kemampuan | Tool | Status |
|---|---|---|
| Jalankan Python snippet | `code_sandbox` | ✅ upgraded |
| Analisis kode statik | `code_analyze` | ✅ baru |
| Validasi sintaks | `code_validate` | ✅ baru |
| Tulis file ke workspace | `workspace_write` | ✅ ada |
| Baca file workspace | `workspace_read` | ✅ ada |
| Lihat struktur folder | `project_map` | ✅ baru |
| Introspeksi diri | `self_inspect` | ✅ baru |
| Belajar dari GitHub/Reddit | `programming_learner.py` | ✅ ada (non-tool) |
| Routing ke Qwen-Coder | Multi-LLM router | 🚧 Sprint berikutnya |
| Math solve (SymPy) | `math_solve` | 🚧 Sprint berikutnya |
| Data analysis (pandas) | `data_analyze` | 🚧 Sprint berikutnya |

---

## 5. Self-Composition Flow (Fondasi)

**"SIDIX bisa menyusun kode untuk dirinya sendiri"** — artinya:

```
LLM otak (Qwen+LoRA)
  → self_inspect: "Saya butuh tool X tapi belum ada"
  → project_map + workspace_read: "Pola tool yang ada seperti ini"
  → code_sandbox: "Test prototipe tool X"
  → code_validate: "Pastikan syntax OK"
  → workspace_write: "Simpan draft tool X ke agent_workspace/draft_tools/"
  → Lapor ke user: "Saya tulis draft tool, minta review + register"
```

Ini berbeda dari "model menulis kode sekali jadi" — ini **iterative self-improvement loop**
yang terinspirasi Voyager (note 36) + curriculum engine (note 43).

---

## 6. Keterbatasan & Next Steps

### Keterbatasan saat ini:
- `code_analyze` hanya Python (belum TypeScript/JS/Go)
- `code_sandbox` masih subprocess biasa — bukan Docker/namespace isolation
- `self_inspect` list tool statis — tidak bisa hot-reload jika tool baru ditambah
- Tool baru belum bisa auto-register ke TOOL_REGISTRY (masih manual + restart)

### Sprint berikutnya:
1. **`math_solve`** — SymPy wrapper (integral, turunan, persamaan)
2. **`data_analyze`** — pandas + matplotlib basic stats
3. **`code_route_qwen_coder`** — route complex coding ke Qwen2.5-Coder-7B specialist
4. **Hot-reload tools** — workspace draft → runtime register tanpa restart server

---

## 7. Test Results (2026-04-21)

```
# Import test
from apps.brain_qa.brain_qa.code_intelligence import analyze_code, validate_python, get_project_map
→ OK

# code_analyze smoke test
analyze_code("def add(x,y): return x+y", "math.py")
→ OK, 1 fungsi, complexity 0

# code_validate smoke test
validate_python("x = 1 +") → {ok: False, error: "invalid syntax", line: 1}
validate_python("x = 1 + 2") → {ok: True}

# self_inspect tools
_tool_self_inspect({'target': 'tools'})
→ 30 tools terdaftar (naik dari 17 sebelum sprint series ini)

# project_map
_tool_project_map({'path': 'apps/brain_qa/brain_qa', 'depth': 2})
→ tree ASCII 102 modul

# self_inspect modules
→ 102 modul brain_qa terdeteksi
```

**Total tool count: 30** (naik dari 17 pre-sprint, +4 hari ini)
