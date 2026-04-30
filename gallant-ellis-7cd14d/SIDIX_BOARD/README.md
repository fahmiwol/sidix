# SIDIX Command Board

> Single-page web app yang aggregate semua interaction surface SIDIX. Akses dari HP atau PC. **NO Telegram dependency** — board dibangun sendiri pakai infra Tiranyx.

**Status:** Sprint 43 PIVOT (replaced Telegram-bot-only approach 2026-04-29) · Phase 1 scaffold LIVE

---

## Mengapa board sendiri (bukan Telegram)?

Founder reasoning (2026-04-29):
> *"buatkan 1 url chat board, buka lewat telegram bukan WA tapi chat tools baru, yang sudah terinstall dan terimplementasi itu semua. pake url apapun. ada tutorial, ada approval yang dipelajari sidix, usulan atau perintah, jadi sy bisa akses lewat hp atau lewat pc."*

**Why this is better than Telegram-only:**

| Aspect | Telegram Bot | SIDIX Board |
|---|---|---|
| Dependency | Telegram API + token + @BotFather setup | Static HTML, zero external deps |
| HP access | Telegram app | Mobile browser (PWA support) |
| PC access | Telegram desktop | Any browser |
| Approval queue UX | Inline buttons (limited UI) | Full dashboard with diff view |
| Task queue UX | Slash commands | Form input + filter |
| Synthesizer UX | File upload via WTF flow | Native paste + select session |
| Tutorial | Static doc | Interactive in-context |
| Branding | Telegram chrome | Full Tiranyx branding |
| Privacy | Per-user Telegram settings | Self-hosted, no 3rd party |
| Plugin/extend | Limited bot API | Full HTML/JS/CSS |

**Verdict:** Board jauh lebih flexible + brand-aligned + zero dependency. Telegram bot scaffold (Sprint 43 Phase 1 telegram_persona_bot.py) di-keep sebagai **fallback notification channel** (e.g. push notif kalau approval queue ada item baru saat board ditutup), TAPI bukan primary UI.

---

## 6 Panels

| Panel | Function | Phase 1 status |
|---|---|---|
| 💬 **Chat 5 Persona** | Single + Council mode (all 5 paralel) | Stub responses |
| ✅ **Approval Queue** | Sprint 40 autonomous_developer PR review | Mock 2 items |
| 📋 **Task Queue** | Add task + persona research fanout | Mock 3 items + add form |
| 📸 **Pixel Captures** | Sprint 42 Chrome ext capture log | Mock 2 captures |
| 🧠 **Synthesizer** | Conversation Synthesizer + 12 sesi list | List sessions + paste form |
| 📖 **Tutorial** | In-context guide | 8 step walkthrough |

---

## 4 Cara Akses (pilih sesuai use case)

### A. Local file (paling cepat untuk test)
```bash
# Buka di browser:
file:///C:/SIDIX-AI/pedantic-banach-c8232d/SIDIX_BOARD/index.html
```
Atau drag-drop `index.html` ke browser.

### B. Subdomain `ctrl.sidixlab.com/chatbos` (production)
Setup nginx di VPS:
```nginx
server {
    listen 80;
    server_name ctrl.sidixlab.com/chatbos;
    root /opt/sidix/SIDIX_BOARD;
    index index.html;

    location /api/ {
        proxy_pass http://localhost:8765/;
        proxy_set_header Host $host;
    }
}
```
Plus DNS A record `ctrl.sidixlab.com/chatbos → VPS_IP`. Phase 2 deploy.

### C. Subpath `app.sidixlab.com/board/`
Reuse existing nginx, alias subpath:
```nginx
location /board/ {
    alias /opt/sidix/SIDIX_BOARD/;
    index index.html;
}
```

### D. Mobile PWA (HP install)
1. Buka URL board di Chrome HP
2. Menu (⋮) → "Tambahkan ke Layar Utama"
3. Board jadi app icon native di HP
4. Mobile-responsive layout otomatis (tabs scroll horizontal di < 768px)

Phase 2: tambah `manifest.json` + service worker untuk full PWA (offline support, push notif).

---

## Phase 2 wiring (yang akan dikerjakan)

| Panel | API endpoint to wire |
|---|---|
| Chat 5 Persona | `POST /agent/chat?persona=X` (existing) |
| Council mode | `POST /agent/council` (existing) |
| Approval Queue | `GET /autonomous_dev/queue` + `POST /autonomous_dev/approve|reject` (Sprint 40) |
| Task Queue | `GET/POST /autonomous_dev/queue` (Sprint 40) |
| Pixel Captures | `GET /sidix/pixel/captures` (Sprint 42 add Phase 2) |
| Synthesizer | `POST /sidix/synthesize_conversation` (Sprint 41 endpoint Phase 2) |
| API status | `GET /health` (existing) |

Auth: `X-Sidix-Board-Token` header, generate dari env atau dashboard settings.

---

## Build / Deploy

**Phase 1 (now):** Static HTML, no build. Just `index.html`.
**Phase 2 (later):** Add bundler (Vite optional), service worker, manifest.json, real API wire.
**Phase 3 (production):** Deploy ke ctrl.sidixlab.com/chatbos via nginx + Let's Encrypt SSL.

---

## Browser support

- ✅ Chrome 120+ (primary target)
- ✅ Edge 120+
- ✅ Brave (chromium)
- ✅ Firefox 120+ (mostly works)
- ✅ Safari 17+ (mostly works)
- ✅ Mobile Chrome (Android)
- ✅ Mobile Safari (iOS)

Tested rendering: Phase 1 verified via Claude Code Launch preview panel.

---

## File structure

```
SIDIX_BOARD/
├── index.html      ← single-file SPA (611 lines, ~25 KB)
├── README.md       ← this file
└── (future)
    ├── manifest.json    (PWA Phase 2)
    ├── sw.js            (service worker Phase 2)
    └── api/             (proxy / auth helpers Phase 2)
```

---

## Reference

- `docs/SPRINT_43_PERSONA_DISCUSSION_PLAN.md` — original Telegram-bot plan (now superseded by board)
- `docs/SPRINT_42_SIDIX_AS_PIXEL_PLAN.md` — Chrome extension yang feed pixel captures panel
- `docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md` — autonomous_developer yang feed approval queue
- `apps/brain_qa/brain_qa/conversation_synthesizer.py` — engine for synthesizer panel
- `apps/brain_qa/brain_qa/claude_sessions.py` — discovery for sessions list

---

*Built by Claude · Sonnet 4.6 · 2026-04-29 · Tiranyx Lab · MIT License*
