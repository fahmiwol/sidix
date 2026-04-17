# SIDIX MCP — Install di Semua Platform

SIDIX MCP Server menghubungkan AI agent (Claude, Cursor, Codex, dll) ke SIDIX brain_qa.
Sekali dipasang → SIDIX hadir di semua sesi, semua proyek.

## Tools yang tersedia setelah install

| Tool | Fungsi |
|---|---|
| `sidix_query` | Tanya ke SIDIX |
| `sidix_capture` | Rekam pengetahuan baru ke corpus |
| `sidix_learn_session` | Rekam ringkasan sesi kerja |
| `sidix_status` | Cek SIDIX online + jumlah dokumen |

---

## Prasyarat

```bash
# Node.js 18+
node --version  # harus >= 18

# Clone repo SIDIX (kalau belum)
git clone https://github.com/fahmiwol/sidix.git
cd sidix/apps/sidix-mcp
npm install
```

---

## 1. Claude Desktop

**Config file:**
- Windows: `C:\Users\[USER]\AppData\Roaming\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Tambahkan:**
```json
{
  "mcpServers": {
    "sidix": {
      "command": "node",
      "args": ["/path/to/sidix/apps/sidix-mcp/src/index.js"],
      "env": {
        "SIDIX_URL": "http://localhost:8765",
        "SIDIX_CORPUS": "/path/to/sidix/brain/public"
      }
    }
  }
}
```

**Restart Claude Desktop** → SIDIX muncul di tool panel (🔨 icon).

---

## 2. Claude Code (CLI)

**Project level** — buat `.claude/mcp.json` di root project:
```json
{
  "mcpServers": {
    "sidix": {
      "command": "node",
      "args": ["/path/to/sidix/apps/sidix-mcp/src/index.js"],
      "env": {
        "SIDIX_URL": "http://localhost:8765",
        "SIDIX_CORPUS": "/path/to/sidix/brain/public"
      }
    }
  }
}
```

**Global** — tambahkan via Claude Code settings:
```bash
claude mcp add sidix node /path/to/sidix/apps/sidix-mcp/src/index.js \
  --env SIDIX_URL=http://localhost:8765 \
  --env SIDIX_CORPUS=/path/to/sidix/brain/public
```

---

## 3. Cursor

**Project level** — buat `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "sidix": {
      "command": "node",
      "args": ["/path/to/sidix/apps/sidix-mcp/src/index.js"],
      "env": {
        "SIDIX_URL": "http://localhost:8765",
        "SIDIX_CORPUS": "/path/to/sidix/brain/public"
      }
    }
  }
}
```

**Global** — buka Cursor Settings → Features → MCP → Add Server:
- Name: `sidix`
- Command: `node /path/to/sidix/apps/sidix-mcp/src/index.js`
- Env: `SIDIX_URL=http://localhost:8765`

Tambahkan juga di `.cursorrules` agar Cursor otomatis mengajar SIDIX:
```
Setiap kali mengimplementasikan fitur, fix bug, atau membuat keputusan arsitektur:
panggil tool sidix_capture dengan topik dan penjelasan apa yang baru dikerjakan.
Ini agar SIDIX belajar dari setiap sesi kerja di Cursor.
```

---

## 4. Codex (OpenAI CLI)

Codex CLI mendukung MCP via config:

**`~/.codex/config.toml`:**
```toml
[[mcp_servers]]
name = "sidix"
command = "node"
args = ["/path/to/sidix/apps/sidix-mcp/src/index.js"]

[mcp_servers.env]
SIDIX_URL = "http://localhost:8765"
SIDIX_CORPUS = "/path/to/sidix/brain/public"
```

---

## 5. Antigravity

**`antigravity.config.json`** di root project:
```json
{
  "plugins": {
    "sidix": {
      "type": "mcp",
      "command": "node",
      "args": ["/path/to/sidix/apps/sidix-mcp/src/index.js"],
      "env": {
        "SIDIX_URL": "http://localhost:8765",
        "SIDIX_CORPUS": "/path/to/sidix/brain/public"
      }
    }
  }
}
```

---

## Cara Pakai Setelah Install

### Tanya ke SIDIX
```
Panggil sidix_query dengan pertanyaan:
"Bagaimana cara setup RLS di Supabase untuk user anonim?"
```

### Rekam pengetahuan baru
```
Panggil sidix_capture:
- topic: "inline edit pattern di PHP"
- content: "Untuk inline edit tanpa framework: ..."
```

### Rekam sesi kerja (panggil di akhir sesi)
```
Panggil sidix_learn_session:
- project: "CRM Nutrisius"
- summary: "Implementasi inline edit di tabel leads..."
- decisions: "Pilih fetch POST ke save_inline.php..."
- errors: "CORS error saat fetch → fix dengan header di PHP"
```

### Cek status
```
Panggil sidix_status
→ SIDIX Online | 523 dokumen | Tools: 14
```

---

## Kontribusi ke SIDIX

Kalau kamu pakai SIDIX dan menemukan pengetahuan baru:

1. **Cara paling mudah:** panggil `sidix_capture` dari tool AI apapun
2. **Cara manual:** buat file di `brain/public/research_notes/[N]_[topik].md`
3. **Cara developer:** jalankan `python tools/sidix-learn.ps1 "topik"` di terminal

Semua kontribusi knowledge diterima via Pull Request ke repo ini.
Format lengkap: lihat [`CLAUDE.md`](../../CLAUDE.md).

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Cannot find module` | `cd apps/sidix-mcp && npm install` |
| `SIDIX Offline` | Pastikan `python3 -m brain_qa serve` berjalan di port 8765 |
| Tool tidak muncul di Claude | Restart aplikasi setelah edit config |
| `ENOENT: no such file` | Cek path di config — gunakan path absolut |
