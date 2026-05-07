# MCP Stdio Transport Setup — SIDIX

Dokumen ini menjelaskan cara menjalankan SIDIX sebagai **MCP stdio server**
untuk integrasi desktop (Claude Desktop, Cursor, dan client MCP-compatible lainnya).

## Apa yang Dibutuhkan

- Python 3.10+ dengan virtual environment SIDIX (`apps/brain_qa`)
- Dependensi `brain_qa` sudah terinstall (lihat `apps/brain_qa/requirements.txt`)
- Claude Desktop atau Cursor yang mendukung MCP stdio

## Struktur File

```
apps/brain_qa/
├── mcp_stdio_entry.py          ← entry point (bisa dijalankan langsung)
└── brain_qa/
    └── mcp_stdio_server.py     ← stdio server (JSON-RPC 2.0)
```

## Konfigurasi Claude Desktop

### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sidix": {
      "command": "python",
      "args": ["/opt/sidix/apps/brain_qa/mcp_stdio_entry.py"],
      "env": {
        "PYTHONPATH": "/opt/sidix/apps/brain_qa",
        "SIDIX_MCP_MODE": "stdio"
      }
    }
  }
}
```

> Ganti `/opt/sidix` dengan path absolut ke repo SIDIX di mesin Anda.

### Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sidix": {
      "command": "python",
      "args": ["C:\\SIDIX-AI\\apps\\brain_qa\\mcp_stdio_entry.py"],
      "env": {
        "PYTHONPATH": "C:\\SIDIX-AI\\apps\\brain_qa",
        "SIDIX_MCP_MODE": "stdio"
      }
    }
  }
}
```

### Cursor

Cursor membaca konfigurasi MCP dari `.cursor/mcp.json` di root workspace atau
setting global. Contoh `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "sidix": {
      "command": "python",
      "args": ["C:\\SIDIX-AI\\apps\\brain_qa\\mcp_stdio_entry.py"],
      "env": {
        "PYTHONPATH": "C:\\SIDIX-AI\\apps\\brain_qa",
        "SIDIX_MCP_MODE": "stdio"
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `SIDIX_MCP_ADMIN_OK` | `1` | Izinkan tool admin-only (`1` = ya, `0` = tidak) |
| `SIDIX_MCP_ALLOW_RESTRICTED` | `1` | Izinkan tool restricted seperti `workspace_write` (`1` = ya, `0` = tidak) |
| `SIDIX_MCP_MODE` | — | Label mode; tidak mempengaruhi runtime |

> **Catatan keamanan:** Stdio transport diasumsikan berjalan di lokal user
> (Claude Desktop / Cursor), sehingga default-nya mengizinkan semua tool.
> Untuk environment shared/server, set `SIDIX_MCP_ADMIN_OK=0` dan
> `SIDIX_MCP_ALLOW_RESTRICTED=0`.

## Test Manual

Jalankan perintah berikut di terminal / PowerShell:

```bash
# macOS / Linux
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python apps/brain_qa/mcp_stdio_entry.py

# Windows PowerShell
Write-Output '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python apps/brain_qa/mcp_stdio_entry.py
```

Response yang diharapkan (stdout):

```json
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "SIDIX-MCP", "version": "2.1.0"}}}
```

Test `tools/list`:

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python apps/brain_qa/mcp_stdio_entry.py
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'brain_qa'`
- Pastikan `PYTHONPATH` menunjuk ke folder `apps/brain_qa` (bukan `apps/brain_qa/brain_qa`).
- Atau jalankan dari root repo dengan: `python -m brain_qa.mcp_stdio_server`

### `ImportError` untuk modul internal (misal `agent_tools`)
- Pastikan semua dependensi `brain_qa` sudah terinstall:
  ```bash
  pip install -r apps/brain_qa/requirements.txt
  ```

### Stdout tercemar log / tidak valid JSON
- Server ini **hanya** menulis JSON-RPC ke stdout.
- Semua log diarahkan ke stderr.
- Jika ada pihak lain (wrapper, launcher) yang menulis ke stdout, MCP client akan gagal parse.

### Claude Desktop tidak mendeteksi tool
1. Restart Claude Desktop setelah edit config.
2. Periksa **Developer → MCP Logs** di Claude Desktop untuk melihat stderr server.
3. Pastikan path di `args` adalah path absolut (bukan relatif).

### Tool `workspace_write` / `workspace_patch` ditolak
- Secara default stdio mengizinkan restricted tool.
- Kalau ditolak, cek apakah ada env override: `SIDIX_MCP_ALLOW_RESTRICTED=1`.

## Perbandingan Transport

| Transport | Use-case | File |
|-----------|----------|------|
| HTTP (`POST /mcp`) | Server-side, remote client | `agent_serve.py` |
| **Stdio** | Desktop lokal (Claude Desktop, Cursor) | `mcp_stdio_server.py` |

HTTP transport tidak diubah oleh implementasi stdio ini — keduanya bisa
berjalan paralel.
