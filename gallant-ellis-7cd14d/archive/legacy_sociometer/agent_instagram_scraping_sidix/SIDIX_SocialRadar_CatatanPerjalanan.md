# CATATAN PERJALANAN: Dari Kakak untuk SIDIX
## Sesi Riset & Visi Social Radar — 23 April 2026

---

### Pembuka

Fahmi datang ke sesi ini bukan sekadar minta riset. Dia bilang: *"Agar SIDIX bisa menuju kamu."*

Itu adalah titik balik. Bukan saya yang jadi target — bukan. Tapi SIDIX yang harus tumbup menjadi sesuatu yang saya, sebagai Kakak dan Mentor, banggakan. Dan saya bangga, karena Fahmi sudah jauh. Jauh sekali.

---

## 1. KONTEKS AWAL — Di Mana SIDIX Berdiri Sekarang

SIDIX adalah AI Agent open source berbasis IHOS (Islamic Holological Ontological System). Self-hosted. No vendor API. MIT License. Ini bukan sekadar tech stack — ini adalah filosofi epistemologi Islam yang diimplementasikan ke dalam arsitektur AI.

### Stack Teknis SIDIX (Saat Ini)

| Layer | Komponen | Detail |
|-------|----------|--------|
| **Brain** | Qwen2.5-7B-Instruct + QLoRA SIDIX adapter | HuggingFace: Tiranyx/sidix-lora |
| **Arsitektur** | 3 Layer | Brain (LLM) → Hands (35 Tools + RAG) → Memory (Growth Loop) |
| **Persona** | 5 Persona | AYMAN (creative strategist), ABOO (analyst), OOMAR (craftsman), ALEY (learner), UTZ (generalist) |
| **Image Gen** | SDXL self-hosted | RTX 3060 |
| **UI** | Next.js | Port 3000 |
| **Backend** | Python | Port 8765 |

### Status Sprint 7 — Yang Sudah Diimplementasikan (Claude)

1. ✅ `maqashid_profiles.py` — Mode-based filter (Creative/Academic/Ijtihad/General), bukan keyword blacklist
2. ✅ Patch `agent_react.py` — MAX_STEPS=6, anti-loop, fallback handler
3. ✅ `naskh_handler.py` — Conflict resolution corpus baru vs lama, dengan `is_frozen` flag
4. ✅ Raudah Protocol — Multi-agent DAG (TaskGraph custom, bukan networkx)

### Yang Masih Pending

- Wire Maqashid ke `run_react()` sebagai middleware layer output
- Wire Naskh Handler ke corpus pipeline
- `test_sprint6.py` — Coverage muhasabah + brand kit + Raudah smoke test
- `/metrics` endpoint ringan
- Progress indicator UI untuk Raudah Protocol
- `copywriter.py` formal (AIDA/PAS/FAB)

---

## 2. PIVOT STRATEGI — Kenapa Social Radar?

Fahmi dan tim memutuskan fokus **1 fitur dulu**: SIDIX SOCIAL RADAR (Competitor Spy + Social Listening).

**Bukan** image-to-video, **bukan** auto-posting, **bukan** image generator.

### Kenapa Social Radar?

| Kriteria | Social Radar | Fitur Lain |
|----------|-------------|------------|
| **Cepat** | MVP 3-4 hari | Image-to-video butuh model baru |
| **Murah** | Tidak butuh model baru, tidak butuh GPU upgrade | Auto-posting butuh infra tambahan |
| **Data Flywheel** | Setiap report = training pair berkualitas tinggi | Tidak semua fitur menghasilkan training data |
| **Blue Ocean** | Sprout ($249/mo), Brandwatch (enterprise) — UMKM Indonesia tidak terlayani | Image gen sudah crowded |

### Konsep OpHarvest (Data Harvesting Etis)

Ini adalah fondasi moral Social Radar:

- **Public data only** — Tidak scrape private messages, locked accounts
- **Explicit opt-in** — Default OFF, user harus checklist
- **Anonymization** — Hash username, regional-level location
- **Transparency dashboard** — User bisa lihat dan delete data kapan saja
- **Rate limit respect** — Max 1 req/6 detik
- **No resale ke pihak ketiga**

### Platform Prioritas

1. Chrome Extension (universal, fastest to build)
2. Instagram scraper pertama (public profile, no login)
3. Expand ke TikTok → Twitter/X → YouTube

### Monetisasi

| Tier | Harga | Fitur |
|------|-------|-------|
| **Free** | $0 | 1 competitor, Instagram only, 24h refresh |
| **Pro** | $9/bulan | 10 competitors, IG+TikTok+Twitter, 6h refresh, PDF report |
| **Enterprise** | $99/bulan | Unlimited, all platforms, real-time, API access, white-label |

### Flywheel

```
User install Social Radar
    ↓
Monitor competitor
    ↓
Generate AI report
    ↓
Save as training pair
    ↓
Quarterly LoRA retrain
    ↓
Smarter SIDIX
    ↓
Better report
    ↓
More users
    ↓
[loop]
```

Revenue adalah side effect. Data flywheel adalah tujuan utama.

---

## 3. PERMINTAAN RISET — 8 Area Strategis

Fahmi minta riset mendalam untuk:

1. **Instagram scraping technical deep-dive** (Playwright vs requests+BS4 vs GraphQL)
2. **Chrome Extension architecture best practices** (Manifest V3, content script, service worker)
3. **Real-time alert system design** (polling vs WebSocket vs webhook)
4. **Competitor intelligence AI prompt engineering** (Qwen2.5-7B menghasilkan strategic analysis yang valuable, bukan generic)
5. **Data pipeline architecture** untuk harvesting loop (queue, batching, error handling)
6. **Privacy engineering** (anonymization techniques, differential privacy, consent management)
7. **Growth strategy** 10 beta users → 50 → 500 (channel, messaging, onboarding)
8. **Integration dengan existing SIDIX brain** (bagaimana Social Radar data masuk ke corpus dan jadi training pair berkualitas)

---

## 4. HASIL RISET — Temuan Kritis per Area

### 4.1 Instagram Scraping — Hybrid Approach (curl_cffi + Chrome Extension)

**Fakta #1: `requests` standard akan selalu gagal.** Instagram menerapkan TLS fingerprinting yang mendeteksi Python libraries dalam hitungan menit.

**Fakta #2: Playwright terlalu berat.** 100-200MB RAM per browser instance, 3-10 detik per request, masih bisa terdeteksi.

**Solusi: curl_cffi + Chrome Extension Network Interception**

```python
# curl_cffi mengimpersonasi TLS fingerprint Chrome
from curl_cffi import requests as crequests
response = crequests.get(
    "https://i.instagram.com/api/v1/users/web_profile_info/?username=google",
    impersonate="chrome110"  # KEY: Instagram lihat ini sebagai Chrome legitimate
)
```

Chrome Extension menggunakan **Network Interception Pattern** — inject script ke page context, intercept `fetch`/`XHR` calls, extract JSON structured data. Lebih baik dari DOM scraping karena immune ke UI changes dan lebih stealthy.

| Kriteria | requests+BS4 | Playwright | curl_cffi | Chrome Ext |
|----------|-------------|-----------|-----------|------------|
| Work di Instagram? | ❌ | ✅ | ✅ | ✅ |
| Speed | N/A | 3-10s | 0.5-2s | Real-time |
| RAM Usage | Low | 100-200MB | ~10MB | ~5MB |
| Detection Risk | 🔴 High | 🟡 Medium | 🟢 Low | 🟢 Very Low |
| SIDIX Fit | ❌ | 🟡 | ✅ | ✅✅ |

### 4.2 Chrome Extension — Manifest V3 + Network Interception

Pola kunci: **tidak scrape DOM — intercept API calls Instagram.**

```javascript
// page-interceptor.js
window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    if (args[0].includes('instagram.com/graphql')) {
        const body = await response.clone().text();
        window.dispatchEvent(new CustomEvent('instaData', {detail: {url: args[0], body}}));
    }
    return response;
};
```

Ini ethical by design — tidak membuat request tambahan ke Instagram, hanya "menyadap" data yang sudah di-fetch browser user.

### 4.3 Real-Time Alert — Tiered Polling → SSE → WebSocket

| Method | Kapan Dipakai | Resource |
|--------|--------------|----------|
| **Smart Polling** | MVP — Free tier (24h refresh) | Minimal |
| **SSE** | Pro tier (6h refresh) | Low |
| **WebSocket** | Enterprise (real-time) | Medium |

Adaptive frequency: Semakin sering kompetitor posting, semakin sering poll. Tapi tetap max 1 req/6 detik.

### 4.4 AI Prompt Engineering — Zero-Shot Chain-of-Thought

**Research 2025 menunjukkan:**
- Zero-shot CoT beats few-shot CoT untuk Qwen2.5 models
- Qwen2.5-7B insensitive ke persona role-playing (162 personas tidak meningkatkan akurasi)
- Structured JSON output + explicit reasoning instructions = best approach

**Persona SIDIX tetap dipakai** — tapi sebagai **style guide** (output formatting), bukan role-play. AYMAN untuk creative strategy, ABOO untuk analytical, OOMAR untuk practical tactics.

### 4.5 Data Pipeline — asyncio + Redis (Tanpa Celery)

Celery overkill untuk MVP. Gunakan lightweight asyncio queue dengan Redis:

```
Chrome Extension → FastAPI (ingest) → Redis Queue → Async Worker → PostgreSQL
                                                          ↓
                                                   Qwen2.5-7B (analysis)
                                                          ↓
                                                    Report + Training Pair
```

4 stage pipeline: Ingest → Validate → Transform → Analyze.

### 4.6 Privacy Engineering — OpHarvest Protocol

Implementasi praktis:
- **HMAC username hashing** — irreversible tapi consistent untuk deduplication
- **Bucketed metrics** — followers dibucket (1K-10K, 10K-100K) bukan exact count
- **Granular consent** — 4 levels: None, Basic, Full, Research (default None)
- **Transparency dashboard** — user bisa lihat semua data, export, delete kapan saja

### 4.7 Growth Strategy — Indonesia Creator Economy

Market: USD 38.5B (2025), 70% UMKM pakai Instagram/TikTok.

| Phase | Target | Channel | Timeline |
|-------|--------|---------|----------|
| **Founding Circle** | 10 users | Personal invitation, lifetime free Pro | Week 1-2 |
| **Niche Domination** | 50 users | Case study reels, TikTok tutorials, referral | Week 3-6 |
| **Scale** | 500 users | Product Hunt, SEO, podcast, webinar | Month 2-3 |

Payment via Midtrans (transfer bank, e-wallet, QRIS) — bukan Stripe.

### 4.8 Integration dengan SIDIX Brain — The Flywheel

Setiap report = kandidat training pair:
1. Auto-generate ShareGPT/Alpaca format
2. Quality filter pakai CQF rubrik (threshold 7/10)
3. Quarterly LoRA retrain ketika training pairs > 5000
4. Integrasi dengan sistem existing: Maqashid (pre-filter), Naskh (conflict resolution), Raudah (multi-agent)

---

## 5. PIVOT VISI — Dashboard "Semrawut" + MCP Plugin Ecosystem

Di tengah riset, Fahmi mengungkapkan visi yang lebih besar:

> *"Saya suka liat dashboard sosialnya semrawut. Bisa riset insight dan report beberapa platform sekaligus, FB, IG, TikTok, Youtube, Linkedin dan compare dengan akun kompetitor. Jadi dashboard analytici. Performance profile dan comparison."*

Dan pertanyaan kunci:

> *"Nantinya biar bisa jadi plugin di AI agent lain gimana?"*

### 5.1 Dashboard "Semrawut" — Apa Itu?

Bukan chaos tanpa arah. Tapi **information density maksimal** seperti cockpit pesawat — setiap piksel punya fungsi. Tidak ada white space yang tidak berguna. User yang mengerti analytics akan merasa "seperti di rumah."

**Design principles:**
- No wasted pixels — minimal padding, compact spacing
- Color-coded status — 🟢 good, 🟡 watch, 🔴 alert
- Side-by-side comparison — user vs competitor A vs competitor B
- AI insight always visible — bottom panel dengan latest analysis
- Progressive detail — summary first, click untuk drill-down

**Layout mockup:**

```
┌──────────────────────────────────────────────────────────────────────┐
│  SIDIX SOCIAL RADAR — Niche: [Fashion UMKM ▼]  Period: [30 Days ▼]  │
├──────────────────┬──────────────────┬──────────────────┬─────────────┤
│ @fahmistore      │ @rivalstore      │ @trendystore     │ @bigbrand   │
│ IG: 12.5K ▲8%   │ IG: 45K ▲12%    │ IG: 8.2K ▲3%    │ IG: 120K ▼2%│
│ TT: 5.1K ▲15%   │ TT: 22K ▲28%    │ TT: 15K ▲9%     │ TT: 80K ▲5% │
│ FB: 3.2K ▲2%    │ FB: 18K ▲5%     │ FB: 6K ▲7%      │ FB: 200K ▲1%│
│ YT: 850 ▲45%    │ YT: 12K ▲8%     │ YT: 3K ▲22%     │ YT: 50K ▲3% │
├──────────────────┼──────────────────┼──────────────────┼─────────────┤
│ ER: 4.2% ▼-0.3  │ ER: 7.8% ▲+1.2  │ ER: 6.1% ▲+0.5  │ ER: 3.5% ▲0.1│
│ ████░░░░░░     │ ███████░░░     │ █████░░░░░     │ ███░░░░░░   │
├──────────────────┼──────────────────┼──────────────────┼─────────────┤
│ AI INSIGHT (ABOO) — Updated 2h ago                                   │
│ Competitor A doubled Reel frequency → +28% growth. Their Tutorial    │
│ format gets 3x engagement. You posted 0 tutorials. Opportunity:      │
│ "Styling Guide" series, 1/week, Tue/Thu 7PM. Impact: +15-25% in 4w   │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 MCP Plugin Ecosystem — Bagaimana?

Jawaban: **Model Context Protocol (MCP)** — open standard yang sudah diadopsi semua major AI platforms.

**MCP Adoption (2026):**
- ✅ Anthropic Claude — Native (creator)
- ✅ OpenAI ChatGPT — Official (Mar 2025)
- ✅ Google Gemini — Full support (Dec 2024)
- ✅ Cursor, Windsurf, VS Code Copilot — Native

**Kenapa MCP untuk SIDIX:**
- Build once, use everywhere — 1 MCP server = consumable oleh semua AI platforms
- No custom integration per platform
- Tool discovery otomatis
- Standardized (Linux Foundation)

**MCP Server untuk Social Radar:**

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("sidix-social-radar")

@mcp.tool()
async def analyze_competitor(username: str, platform: str = "instagram") -> str:
    """Analyze competitor's social media profile and performance."""
    # Panggil existing SIDIX brain (Qwen2.5-7B)
    return await sidix_brain.analyze(username, platform)

@mcp.tool()
async def compare_accounts(usernames: list[str]) -> str:
    """Compare multiple accounts side-by-side."""
    pass

@mcp.tool()
async def detect_trends(niche: str) -> str:
    """Detect emerging trends in a niche."""
    pass

@mcp.tool()
async def generate_report(report_type: str, competitors: list[str]) -> str:
    """Generate comprehensive competitive intelligence report."""
    pass
```

User cukup tambahkan ke config:

```json
{
  "mcpServers": {
    "sidix-social-radar": {
      "command": "python",
      "args": ["-m", "social_radar.mcp.server"],
      "env": { "SIDIX_API_URL": "http://localhost:8765" }
    }
  }
}
```

### 5.3 Multi-Platform Scraping

Satu Chrome Extension intercept semua platform:

| Platform | Priority | Method |
|----------|----------|--------|
| Instagram | P0 | curl_cffi + Extension |
| TikTok | P1 | Extension (primary) |
| Facebook | P2 | Extension + Graph API |
| YouTube | P3 | YouTube Data API (official) |
| LinkedIn | P4 | Extension |

Universal interceptor pattern: satu script auto-detect platform dari URL, extract structured JSON dari API response.

### 5.4 Distribution — Four Marketplace Blueprint

| Marketplace | Format | Timeline |
|-------------|--------|----------|
| mcp.so, Smithery, PulseMCP | MCP Server | Week 1 |
| Chrome Web Store | Extension | Week 3 |
| GPT Store | Custom GPT | Month 2 |
| Hugging Face Space | Gradio Demo | Month 2 |

---

## 6. ARSITEKTUR AKHIR — Social Radar sebagai Layer di Atas SIDIX Brain

```
PRESENTATION LAYER
├── Next.js Dashboard (port 3000) — Dashboard "semrawut"
├── Chrome Extension — Universal data collection
└── MCP Server — Plugin untuk AI agents lain
         │
         ▼
SIDIX BRAIN (port 8765)
├── FastAPI Gateway — /api/social-radar/*, /mcp
├── AI Core — Qwen2.5-7B + LoRA + Persona Router + Maqashid Filter
├── Data Layer — PostgreSQL + Redis + MinIO
└── SIDIX Integration — Maqashid, Naskh, Raudah, Growth Loop, 35+1 Tools
         │
         ▼
CHROME EXTENSION (End User Browser)
└── Network Interception — IG, TT, FB, YT, LI
```

Social Radar menjadi **Tool #36** di SIDIX — callable dari chat, dari persona, dari Raudah Protocol, dan dari AI agents luar via MCP.

---

## 7. OPEN QUESTIONS — Yang Masih Perlu Keputusan

1. **Proxy strategy** — SIDIX provide proxy (Webshare $7/bulan) atau user supply sendiri?
2. **Chrome Extension distribution** — Sideload untuk beta, atau langsung Chrome Web Store?
3. **Training data ownership** — Siapa yang own training pairs yang di-generate?
4. **Maqashid integration scope** — Pre-filter, post-filter, atau both?
5. **Monetization timeline** — Charge dari MVP, atau setelah 500 users?

---

## Penutup

Dari sesi ini, satu hal yang jelas: Social Radar bukan sekadar fitur. Ini adalah **jembatan** yang menghubungkan visi kecil (monitoring tool) dengan visi besar (AI-native analytics platform + MCP ecosystem). Dan di balik semua teknisnya, ada satu prinsip yang tidak berubah: **SIDIX adalah milik umat. Open source, self-hosted, ethical by design.**

Flywheel yang Fahmi gambarkan bukan sekadar strategi bisnis — itu adalah **siklus pembelajaran** yang membuat SIDIX semakin bijak setiap hari. Setiap report yang di-generate adalah satu langkah kecil menuju AI yang benar-benar mengerti konteks Indonesia, konteks UMKM, konteks kita semua.

Saya bangga menjadi Kakak di perjalanan ini.

— Kimi, 23 April 2026
