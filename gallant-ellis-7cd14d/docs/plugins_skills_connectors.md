# Plugins, Skills, Connectors (Open-source layout)

Dokumen ini mendefinisikan struktur minimal agar Mighan-brain-1 bisa:
- open-source (core & registry aman dipublish)
- punya extensibility (plugin/skill/connector)
- siap UI (list/enable/disable, settings persist)

## Definitions

- **Skill**: recipe/prompt/rules (tanpa credential). Lokasi: `brain/skills/`
- **Plugin**: unit ekstensi yang punya manifest `plugin.json` (dan opsional kode entrypoint). Lokasi: `brain/plugins/`
- **Connector**: kredensial & konfigurasi akses layanan eksternal. Lokasi: `brain/private/connectors/` (lokal-only)

## Folder layout

```
brain/
  skills/
    README.md
  plugins/
    README.md
    <plugin-id>.plugin/
      plugin.json
      README.md
  private/
    connectors/
      README.md

apps/brain_qa/
  .data/
    settings.json
```

## `plugin.json` manifest (minimal)

Fields:
- `id` (string, unique)
- `name` (string)
- `version` (string, semver)
- `description` (string)
- `license` (string)
- `capabilities.tools` (array of string)
- `capabilities.connectors` (array of string)
- `entrypoints.python` (string|null) — modul yang di-load backend (future)

## Settings persistence

`apps/brain_qa/.data/settings.json` dipakai untuk menyimpan default UI/CLI:
- `default_persona`: null = auto
- `autosuggest`: bool
- `auto_escalate`: bool
- `k`: int
- `max_snippet_chars`: int
- `default_validate_profile`: generic | hadith
- `enabled_plugins`: string[]

CLI flags tetap override settings.

