# SIDIX Pixel — Chrome Extension

> **Sprint 42 Phase 1 scaffold** · Tiranyx Lab · MIT License
>
> Spawn SIDIX dari mana saja terhubung internet via keyword `@sidix`.

## Concept

Type `@sidix` di Twitter/IG/FB/LinkedIn/blog/etc → context captured → sent to SIDIX backend → research note generated → cognitive multi-persona analysis.

Pattern: Manifest V3 service worker + content script + popup UI + per-domain opt-in.

## Files (Phase 1 scaffold)

```
extension/sidix-pixel/
├── manifest.json     ← V3 manifest, host permissions, content script matches
├── content.js        ← @sidix detection (live typing + page mention)
├── background.js     ← service worker, POST to endpoint, queue + notify
├── popup.html/.js    ← UI: status + manual capture + recent list
├── options.html/.js  ← settings: endpoint + token + whitelist
├── icons/            ← 16/48/128 png (TODO Phase 2)
└── README.md         ← this file
```

## Phase 1 status

✅ Scaffold complete:
- Manifest V3 schema valid
- Content script regex `(?:^|\s)@sidix\b/i`
- Background worker fetch + storage + notification
- Popup with toggle + manual capture + recent log
- Options page with endpoint/token/whitelist config

⏳ Phase 2 (next sprint window):
- Wire backend endpoint `/sidix/pixel/capture` di agent_serve.py
- Add icons/ (16/48/128 png) — design token Tiranyx
- Privacy policy URL (Chrome web store requirement)
- IndexedDB offline queue
- Smoke test + dogfood real Twitter/IG capture

## Local install (Chrome dev mode)

```
1. chrome://extensions
2. Toggle "Developer mode" on
3. "Load unpacked" → select extension/sidix-pixel/
4. Pin to toolbar
5. Open Options → set endpoint = https://ctrl.sidixlab.com/sidix/pixel/capture
6. Visit twitter.com, type "@sidix testing capture"
7. Notification: "SIDIX captured" (atau error dari endpoint stub)
```

## Privacy

- Default: opt-in per domain (8 whitelist defaults)
- ❌ Tidak capture password / credential field (sensitive_input_types check)
- ❌ Tidak capture domain di luar whitelist
- 🔒 Surrounding text capped 500 chars
- 🔒 Auth via X-Sidix-Pixel-Token header (optional Phase 1, required Phase 2)
- 🛑 Toggle off kapan saja dari popup

## Backend contract (Phase 2)

```http
POST /sidix/pixel/capture
Content-Type: application/json
X-Sidix-Pixel-Token: <token>

{
  "url": "https://twitter.com/user/status/...",
  "page_title": "...",
  "trigger_keyword": "@sidix",
  "surrounding_text": "...",
  "source": "live_typing" | "page_mention" | "popup_manual",
  "captured_at": "2026-04-29T...",
  "client_version": "0.1.0"
}
```

Response:

```json
{
  "ok": true,
  "note_id": 291,
  "note_path": "brain/public/research_notes/291_pixel_capture_...md",
  "synthesis_summary": "..."
}
```

## Future

- **Sprint 42b** — meta tag pixel embed (`<script src="cdn.tiranyx.co.id/sidix-pixel.js">`)
- **Sprint 43** — 5 Persona Discussion UI (Telegram bot first)
- **Sprint 45** — Persona-to-Innovation pipeline (capture → method/tool/penemuan)
- **Long term** — mobile companion (Tasker Android, Shortcuts iOS)

---

*Reference: docs/SPRINT_42_SIDIX_AS_PIXEL_PLAN.md, project_sidix_distribution_pixel_basirport.md.*
