# Sprint 7b — SIDIX Socio Bot MCP: Arsitektur Plugin AI Multi-Platform

> Captured via SIDIX MCP - 2026-04-23

## Apa

SIDIX Socio Bot MCP adalah plugin yang menghubungkan Claude/GPT/Cursor/Kimi/Codex ke
kapabilitas Social Intelligence SIDIX. Lewat satu MCP server (`sidix-socio-mcp`), AI agent
eksternal bisa scan profil Instagram/Threads/X/YouTube, analisis engagement, banding akun,
kirim/terima WhatsApp, dan baca data dari Chrome Extension Social Radar.

## Komponen Sistem

```
Claude/GPT/Cursor/Kimi
        │  MCP (stdio)
        ▼
apps/sidix-mcp/src/index.js       ← MCP server (4 core + 9 social tools)
        │  HTTP
        ├── http://localhost:8765  ← SIDIX brain_qa backend (FastAPI)
        │     └── /social/radar/scan  ← analisis ER + sentiment + tier
        ├── http://localhost:7788  ← Extension Bridge (Express)
        │     └── /push-scan, /last-scan
        └── http://localhost:7789  ← WA Bridge (Express + Baileys)
              └── /send, /inbox, /status

Chrome Extension (Social Radar)
        │  DOM scraping
        ├── extractSocialMetadataFromPage() — meta description + JSON-LD
        ├── POST https://ctrl.sidixlab.com/social/radar/scan → analisis
        └── POST http://localhost:7788/push-scan → MCP bisa baca
```

## 9 Social Tools MCP

| Tool | Fungsi |
|------|--------|
| `scan_instagram_profile` | Scan IG via backend radar |
| `scan_threads_profile` | Scan Threads |
| `scan_youtube_channel` | Scan YouTube |
| `scan_twitter_profile` | Scan X/Twitter |
| `analyze_social` | Analisis mendalam 1 URL |
| `compare_social_accounts` | Banding 2+ akun |
| `social_post_threads` | Post otomatis ke Threads |
| `wa_send` | Kirim pesan WA via bridge |
| `wa_receive` | Baca inbox WA terbaru |

## Bridge Pattern

**Extension Bridge (port 7788)**:
- Chrome Extension POST `/push-scan` setelah setiap scan
- MCP tool `scan_instagram_profile` bisa polling `/last-scan` (TTL 5 menit)
- Fallback: MCP langsung call backend `/social/radar/scan` dengan URL

**WA Bridge (port 7789 — Baileys)**:
- Pertama kali: tampilkan QR di terminal, scan dengan HP
- Auth disimpan di `.wa_auth/` (gitignored)
- MCP tool `wa_send` POST ke `/send { jid, message }`
- MCP tool `wa_receive` GET `/inbox` (ring buffer 50 pesan)

## Cara Pakai (Claude Desktop)

Copy `apps/sidix-mcp/claude_desktop_config.json` ke
`%APPDATA%/Claude/claude_desktop_config.json`, lalu:

```bash
# Terminal 1: Extension Bridge
cd apps/sidix-extension-bridge && npm install && npm start

# Terminal 2: WA Bridge (opsional)
cd apps/sidix-wa-bridge && npm install && npm start
# Scan QR code di terminal

# Terminal 3: SIDIX brain backend (biasanya sudah jalan di port 8765)
```

## DOM Scraping Strategy (Chrome Extension)

Instagram tidak expose API publik, jadi kita scrape:
1. `<meta name="description">` — "1.2K followers, 56 following, 78 posts - Name (@handle)"
2. `<script type="application/ld+json">` — interactionStatistic untuk follower count
3. `parseShortCount()` — normalize "1.2K" → 1200, "3.4M" → 3400000

Limit: Instagram kadang tidak include meta description untuk profil private atau
jika halaman belum fully loaded. Fallback ke JSON-LD jika ada.

## Keterbatasan

- WA bridge perlu scan QR ulang jika session expire (biasanya 14-30 hari)
- Extension bridge hanya jalan di lokal (localhost:7788) — tidak bisa dari VPS
- Untuk produksi MCP di cloud: deploy bridge dengan ngrok atau reverse proxy
- Instagram rate limit: jangan scan 1 akun lebih dari 5x per 5 menit

## Format Radar Response

```json
{
  "metrics": {
    "engagement_rate": 3.45,
    "sentiment": 0.72,
    "tier": "emerging"
  },
  "advice": "Konten performing baik, tingkatkan frekuensi posting"
}
```

Tier: `micro` (<10K followers) | `emerging` (10K-100K) | `leader` (>100K)
