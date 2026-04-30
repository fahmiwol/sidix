# SIDIX Socio Bot MCP — Install di semua platform

SIDIX MCP menghubungkan **meja-arsip** (app desktop), **bengkel-pena** (IDE), **sarang-tamu** (host percakapan ber-MCP), **paviliun obrolan** (aksi terbuka), dan **sangkar naskah** (CLI cepat) — metafora untuk klien ber-MCP pada umumnya — ke otak SIDIX (13 tools: 4 inti + 9 social intelligence). Perintah konkret di bawah memakai path/flag **sesuai CLI masing-masing host** (lihat dokumentasi upstream untuk nama tepat).

---

## 13 Tools yang Tersedia

| Tool | Fungsi |
|---|---|
| `sidix_query` | Tanya ke SIDIX (RAG + generative, 5 persona) |
| `sidix_capture` | Simpan knowledge baru ke corpus |
| `sidix_learn_session` | Rekam ringkasan sesi kerja |
| `sidix_status` | Cek health + corpus size |
| `scan_instagram_profile` | ER + sentiment + tier profil IG publik |
| `scan_threads_profile` | Analisis profil Threads |
| `scan_youtube_channel` | Engagement rate YouTube channel |
| `scan_twitter_profile` | Analisis X/Twitter |
| `analyze_social` | Deep analysis dari URL social media |
| `compare_social_accounts` | Banding 2–5 akun lintas platform |
| `social_post_threads` | Auto-post ke Threads |
| `wa_send` | Kirim pesan WhatsApp via WA Bridge |
| `wa_receive` | Baca inbox WA (ring buffer 50 pesan) |

---

## Prasyarat

```bash
node --version   # >= 18
git clone https://github.com/fahmiwol/sidix.git
cd sidix/apps/sidix-mcp && npm install
```

---

## 1. One-Click via Smithery (Direkomendasikan)

[![Install via Smithery](https://smithery.ai/badge/sidix-socio-mcp)](https://smithery.ai/server/sidix-socio-mcp)

```bash
# Install otomatis (flag --client mengikuti Smithery / host; contoh umum)
npx @smithery/cli install sidix-socio-mcp --client claude
npx @smithery/cli install sidix-socio-mcp --client cursor
npx @smithery/cli install sidix-socio-mcp --client kimi
```

---

## 2. Claude Desktop (Manual)

Config file:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sidix": {
      "command": "node",
      "args": ["/path/to/sidix/apps/sidix-mcp/src/index.js"],
      "env": {
        "SIDIX_URL": "http://localhost:8765",
        "SIDIX_CORPUS": "/path/to/sidix/brain/public",
        "SIDIX_IG_EXTENSION_BRIDGE_URL": "http://localhost:7788",
        "SIDIX_WA_BRIDGE_URL": "http://localhost:7789"
      }
    }
  }
}
```

Copy siap pakai (Windows): `apps/sidix-mcp/claude_desktop_config.json`

**Restart aplikasi desktop** → SIDIX muncul di panel tool (🔨).

---

## 3. Meja-arsip — CLI agen

```bash
# Tambah global (perintah mengikuti CLI host)
claude mcp add sidix node /path/to/sidix/apps/sidix-mcp/src/index.js \
  --env SIDIX_URL=http://localhost:8765 \
  --env SIDIX_CORPUS=/path/to/sidix/brain/public

# Atau project-level — buat .claude/mcp.json
```

---

## 4. Cursor

**Cara 1 — Via Smithery:**
```bash
npx @smithery/cli install sidix-socio-mcp --client cursor
```

**Cara 2 — Manual:**
Buka Cursor Settings → Features → MCP → Add Server:
- Name: `sidix`
- Command: `node /path/to/sidix/apps/sidix-mcp/src/index.js`
- Env: `SIDIX_URL=https://ctrl.sidixlab.com`

Atau buat `.cursor/mcp.json` (copy dari `apps/sidix-mcp/configs/cursor_mcp.json`).

Tambahkan ke `.cursorrules`:
```
Setelah setiap implementasi fitur atau fix bug penting:
panggil sidix_capture untuk merekam pengetahuan baru ke SIDIX corpus.
```

---

## 5. Sarang-tamu — host orbit (folder `.kimi/`)

Host percakapan ini memakai berkas MCP serupa; contoh `/.kimi/mcp.json`:
```json
{
  "mcpServers": {
    "sidix": {
      "command": "node",
      "args": ["/path/to/sidix/apps/sidix-mcp/src/index.js"],
      "env": {
        "SIDIX_URL": "https://ctrl.sidixlab.com",
        "SIDIX_IG_EXTENSION_BRIDGE_URL": "http://localhost:7788"
      }
    }
  }
}
```

Copy dari `apps/sidix-mcp/configs/kimi_mcp.json`.

---

## 6. Paviliun obrolan — aksi terbuka (OpenAPI)

Host yang memakai **GPT Actions** / OpenAPI publik. Backend contoh: `https://ctrl.sidixlab.com`.

1. Buka penyusun GPT kustom → Actions → Import OpenAPI
2. Upload atau paste URL: `https://raw.githubusercontent.com/fahmiwol/sidix/main/apps/sidix-mcp/openapi.yaml`
3. Atau upload file: `apps/sidix-mcp/openapi.yaml`
4. Set Authentication: None (public API)
5. Simpan → aksi dapat memanggil `sidix_query`, `social_radar_scan`, dll.

---

## 7. Sangkar naskah — CLI cepat (contoh `config.toml`)

```toml
# ~/.codex/config.toml
[[mcp_servers]]
name = "sidix"
command = "node"
args = ["/path/to/sidix/apps/sidix-mcp/src/index.js"]

[mcp_servers.env]
SIDIX_URL = "https://ctrl.sidixlab.com"
```

---

## 8. Bridge Servers (Opsional)

Untuk mengaktifkan `wa_send`/`wa_receive` dan Social Radar real-time:

```bash
# Extension Bridge (port 7788) — relay Chrome Extension → MCP
cd apps/sidix-extension-bridge && npm install && npm start

# WA Bridge (port 7789) — WhatsApp Web via Baileys
cd apps/sidix-wa-bridge && npm install && npm start
# → Scan QR code di terminal dengan HP kamu
```

---

## Tips Penggunaan

### Tanya SIDIX (dari meja-arsip, bengkel-pena, atau paviliun obrolan)
```
Panggil sidix_query:
question: "Cara optimasi engagement Instagram untuk UMKM Indonesia?"
persona: "UTZ"
```

### Scan kompetitor
```
Panggil scan_instagram_profile:
url: "https://www.instagram.com/[username]/"
```

### Rekam sesi kerja (panggil di akhir sesi)
```
Panggil sidix_learn_session:
project: "Nama Proyek"
summary: "Apa yang dikerjakan hari ini..."
decisions: "Pilih X karena..."
errors: "Bug Y → fix dengan..."
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Cannot find module` | `cd apps/sidix-mcp && npm install` |
| `SIDIX offline` | Pastikan backend jalan: `python3 -m brain_qa serve` |
| Tool tidak muncul | Restart aplikasi setelah edit config |
| WA: QR expired | Hapus `.wa_auth/` dan restart WA bridge |
| Scan IG: 0 followers | Buka profil di browser dulu, lalu scan lagi |
