# 102 — Pattern Plugin dari D:\skills & Claude Plugin Ecosystem

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** DOC  
**Tanggal:** 2026-04-18  
**Author:** Claude Sonnet 4.6 (agen SIDIX)

---

## Apa

Analisis pola arsitektur plugin Claude — bagaimana skill dan plugin dibangun, didaftarkan, dan dipanggil — serta pelajaran yang bisa diterapkan ke sistem `builtin_apps.py` SIDIX.

---

## Mengapa

SIDIX membangun kapabilitas built-in (bukan hanya instruksi Markdown seperti plugin Claude). Memahami pola Claude plugin membantu mendesain interface yang konsisten, mudah di-extend, dan mudah dipelajari oleh agen di masa depan.

---

## Bagaimana: Anatomi Plugin Claude

### 1. Struktur Direktori

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json       ← Manifest: nama, versi, deskripsi
├── skills/               ← Skill yang bisa dipanggil (atau commands/)
│   └── skill-name/
│       └── skill.md      ← Instruksi + contoh (format Markdown + YAML)
├── commands/             ← Slash commands (opsional)
│   └── command.md
├── agents/               ← Sub-agent spesialis (opsional)
│   └── agent-role.md
├── .mcp.json             ← Daftar MCP tool yang diperlukan (opsional)
├── CONNECTORS.md         ← Daftar integrasi eksternal yang bisa dipakai
├── README.md
└── LICENSE
```

### 2. Format `plugin.json`

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Deskripsi singkat",
  "skills": ["skill-name"],
  "commands": ["command-name"]
}
```

### 3. Format `skill.md` (YAML frontmatter + Markdown)

```markdown
---
name: skill-name
description: Trigger condition — kapan skill ini diaktifkan
argument-hint: "<argumen opsional>"
user-invocable: true   # apakah user bisa memanggilnya langsung
---

# Judul Skill

## Cara Kerja
[Penjelasan flow]

## Output Format
[Format output yang diharapkan]

## If Connectors Available
[Perilaku conditional jika MCP tool tersedia]
```

---

## Pola Arsitektur yang Ditemukan

### Pola 1: Skill Berbasis Trigger (Trigger-based Skill)

Skill tidak dipanggil dengan nama — dipicu oleh **konteks percakapan**. Claude membaca `description` frontmatter dan memutuskan kapan skill diaktifkan.

**Contoh (skill sql-queries):**
```yaml
description: Write correct, performant SQL across all major data warehouse dialects.
  Use when writing queries, optimizing slow SQL, translating between dialects...
user-invocable: false
```

**Implikasi untuk SIDIX:** `builtin_apps.py` menggunakan model berbeda — explicit `call_app("name", **kwargs)` — lebih deterministik, cocok untuk tool use dalam agent ReAct loop.

---

### Pola 2: Command dengan Argumen (Slash Command Pattern)

```markdown
---
name: debug
argument-hint: "<error message or problem description>"
---

## Usage
/debug $ARGUMENTS
```

**Mapping ke SIDIX:** `call_app("debug", description="TypeError: ...")` — parameter eksplisit menggantikan argumen string.

---

### Pola 3: Multi-Agent Plugin (Feature-Dev Pattern)

Plugin `feature-dev` menggunakan **3 sub-agent spesialis**:
- `code-architect.md` — Merancang solusi
- `code-explorer.md` — Membaca dan memahami codebase
- `code-reviewer.md` — Review kode yang dihasilkan

**Implikasi untuk SIDIX:** Model multi-agent ini bisa diadopsi di level orchestration (bukan builtin_apps), tapi builtin_apps harus single-function agar mudah di-test.

---

### Pola 4: Conditional Connector Pattern

```markdown
## If Connectors Available

If **~~monitoring** is connected:
- Pull logs, error rates, and metrics...

If **~~source control** is connected:
- Identify recent commits...
```

Skill berperilaku berbeda tergantung MCP tool yang aktif.

**Implikasi untuk SIDIX:** `builtin_apps.py` saat ini adalah pure-Python (tidak bergantung MCP). Di masa depan bisa ditambahkan fallback logic:
```python
def _web_search_handler(query, use_mcp=False, **kwargs):
    if use_mcp and _mcp_available("brave_search"):
        return _mcp_search(query)
    return _stub_response(query)
```

---

### Pola 5: Knowledge Work Domain Grouping

Plugin knowledge-work dikelompokkan per **domain profesional**, bukan per teknik:
- engineering, data, marketing, sales, legal, finance, HR, operations, product

**Mapping ke SIDIX:** `builtin_apps.py` menggunakan kategori teknis (math, text, islamic, utility). Untuk roadmap ke depan, bisa ditambah kategori domain:
- `fiqh` — zakat, hukum Islam, fatwa
- `quran` — tafsir, hafalan, tajwid
- `hadith` — pencarian hadits

---

### Pola 6: Self-Describing Registry

Semua plugin/skill **self-describing** — deskripsi, params, dan contoh embedded dalam file yang sama dengan implementasi.

**SIDIX sudah mengikuti ini** di `builtin_apps.py`:
```python
BUILTIN_APPS = {
    "calculator": {
        "description": "...",
        "handler": _calc_handler,
        "params": {"expression": "..."},
        "example": {"expression": "sqrt(144)"},
    }
}
```

---

## Perbandingan: Claude Plugin vs SIDIX builtin_apps

| Aspek | Claude Plugin | SIDIX builtin_apps |
|-------|--------------|-------------------|
| Format | Markdown + YAML | Python dict + function |
| Trigger | Contextual (LLM decides) | Explicit `call_app()` |
| Runtime | Claude model | Pure Python |
| Extensibility | Tambah file .md | Tambah entry di dict + handler |
| Testability | Sulit (perlu LLM) | Mudah (unit test biasa) |
| Dependency | Tidak ada | Python stdlib only |
| Offline | Ya (instruksi) | Ya (logika) |

---

## Keterbatasan Claude Plugin Pattern untuk SIDIX

1. **Tidak executable** — Skill adalah instruksi untuk LLM, bukan kode yang bisa dijalankan. SIDIX butuh kode nyata.
2. **Non-deterministic** — Trigger berbasis konteks bisa salah aktif. SIDIX butuh explicit dispatch.
3. **Tidak bisa di-unit-test** — Test skill Claude memerlukan LLM. SIDIX builtin_apps bisa di-test dengan `pytest`.
4. **Format tidak standar** — Setiap plugin punya variasi sendiri. SIDIX menggunakan dict registry yang konsisten.

---

## Rekomendasi untuk Roadmap SIDIX Plugin

1. **Phase 1 (sekarang):** `builtin_apps.py` — pure Python, no-dependency, 18 tools
2. **Phase 2:** `plugin_registry.py` — load plugin dari folder `apps/brain_qa/plugins/` (dynamic import)
3. **Phase 3:** MCP integration — jika tool MCP tersedia, gunakan sebagai backend tool
4. **Phase 4:** Skill YAML loader — baca skill.md dari folder dan convert ke tool spec
