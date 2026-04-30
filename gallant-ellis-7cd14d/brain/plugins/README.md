# Plugins (local registry)

Folder ini adalah **registry lokal** untuk plugin (open-source friendly).

- **Tujuan**: menambah kemampuan (tools/connectors/datasets/UI panel) tanpa mengotori core `brain_qa`.
- **Model**: plugin = folder + `plugin.json` (manifest) + kode entrypoint (opsional).

Struktur contoh:

```
brain/plugins/
  example.plugin/
    plugin.json
    README.md
```

Catatan:
- Plugin boleh open-source, tetapi **credential konektor tidak boleh** disimpan di repo.
- Credential disimpan di `brain/private/connectors/` (lokal) atau `.env` (lokal).

