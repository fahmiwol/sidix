# RISET SIDIX-SocioMeter: Laporan Riset Teknologi & Pasar

**Versi:** 1.0  
**Status:** FINAL  
**Klasifikasi:** Research Document — Technology & Market Analysis

---

## 1. RISET TEKNOLOGI

### 1.1 Model Context Protocol (MCP)

**Status:** Open standard (Linux Foundation), diadopsi semua platform AI utama  
**SDK:** Python (FastMCP), TypeScript, Go, .NET, Java, Rust  
**Transport:** stdio, streamable-http, SSE  

**Temuan Kunci:**
- FastMCP adalah standard framework untuk Python — 70% MCP servers menggunakannya
- Transport `streamable-http` adalah rekomendasi untuk production (stateless, scalable)
- Auto-discovery: AI agents bisa list tools + descriptions tanpa konfigurasi manual
- Type hints Python otomatis menjadi JSON schema untuk tool definitions

**Rekomendasi SIDIX:**
- Gunakan FastMCP (Python SDK) untuk MCP server
- Support 2 transport: `stdio` (Claude Desktop) dan `streamable-http` (web-based)
- Desain tool signatures dengan type hints yang jelas
- Dokumentasi otomatis dari docstrings

### 1.2 Chrome Extension Manifest V3

**Status:** Wajib untuk Chrome Web Store (MV2 deprecated 2024)  
**API:** Service worker (background), content scripts, side panel, offscreen  

**Temuan Kunci:**
- Service worker tidak persisten — gunakan `chrome.alarms` untuk periodic tasks
- Offscreen documents untuk DOM manipulation (MV3 membatasi background)
- `chrome.storage` API untuk local persistence (IndexedDB untuk large data)
- Content script isolation: `world: "ISOLATED"` (default) atau `"MAIN"` (page context)

**Rekomendasi SIDIX:**
- Manifest V3 dengan service worker
- Content script di `document_end` untuk SPA compatibility
- Offscreen document untuk heavy processing
- IndexedDB untuk offline buffer (50MB+ capacity)
- `chrome.alarms` untuk 5-minute sync interval

### 1.3 Instagram Scraping 2026

**Status:** Instagram menggunakan 5-layer anti-scraping  
**Metode:** GraphQL API (primary), HTML scraping (fallback)  

**Temuan Kunci:**
- Layer 1: IP quality check → residential proxy rotation
- Layer 2: TLS fingerprinting → `curl_cffi` untuk impersonate Chrome
- Layer 3: Rate limiting (200 req/hour/IP) → random delays + proxy rotation
- Layer 4: Behavioral detection → human-like browsing patterns
- Layer 5: `doc_id` rotation (2-4 minggu) → auto-discovery mechanism

**Rekomendasi SIDIX:**
- **Primary:** Chrome Extension network interception (tidak membuat request baru)
- **Fallback:** `curl_cffi` dengan proxy rotation
- **Utility:** Playwright untuk `doc_id` auto-discovery (weekly)
- Rate limit: max 1 req/6 detik (10 req/menit)

### 1.4 Qwen2.5-7B Fine-Tuning

**Status:** Base model + QLoRA adapter, HuggingFace: Tiranyx/sidix-lora  
**Hardware:** RTX 3060 12GB (sufficient untuk 7B inference + LoRA training)  

**Temuan Kunci:**
- QLoRA: r=8-16, alpha=16-32, 3 epochs optimal untuk 7B model
- Flash Attention v2: reduce memory usage 40-50%
- 4-bit quantization (NF4): model 7B muat di 8GB VRAM
- Multi-agent reasoning: +6.8 points performance dengan 7B model

**Rekomendasi SIDIX:**
- QLoRA config: r=16, alpha=32, lr=1e-4, 3 epochs
- Flash Attention v2 wajib
- Quarterly retrain trigger: corpus > 5,000 pairs
- A/B test: win_rate > 55% untuk deploy

### 1.5 Generative AI Landscape 2026

**Tren Utama:**
1. **Multimodal + Agentic systems** — text + vision + audio + action
2. **Domain-specific models** — smaller, specialized, outperform general LLMs
3. **Synthetic data generation** — training data dari AI untuk AI
4. **Embedded governance** — compliance built-in, bukan afterthought
5. **Edge deployment** — on-device inference, reduced latency

**Relevansi untuk SIDIX:**
- SIDIX sudah on the right track: domain-specific (Islamic epistemology), self-hosted
- Growth loop (Jariyah) adalah implementasi synthetic data generation
- Maqashid + Naskh adalah governance framework built-in
- Edge deployment: Qwen2.5-0.5B-7B series mendukung on-device

---

## 2. RISET PASAR

### 2.1 Indonesia Creator Economy

**Market Size:** USD 38.5B (2025) → USD 112.7B (2031), CAGR 19.7%  
**UMKM Digital:** 70% menggunakan Instagram/TikTok untuk marketing  
**Pain Point:** Tools existing (Sprout Social $249/mo, Hootsuite $199/mo) terlalu mahal untuk UMKM  

### 2.2 Competitive Landscape

| Tool | Harga | Self-Hosted | AI-Native | Indonesia | Open Source |
|------|-------|-------------|-----------|-----------|-------------|
| Sprout Social | $249/mo | No | Basic | No | No |
| Hootsuite | $199/mo | No | Basic | No | No |
| Brandwatch | Enterprise | No | Yes | No | No |
| Buffer | $6/mo | No | No | No | No |
| **SIDIX-SocioMeter** | **Free/$9/$99** | **Yes** | **Yes** | **Yes** | **Yes** |

### 2.3 Blue Ocean Opportunity

SIDIX-SocioMeter mengisi gap yang tidak terlayani:
- **UMKM Indonesia:** Butuh tool murah + berbahasa Indonesia + mengerti konteks lokal
- **Privacy-conscious users:** Tidak mau data mereka training model orang lain
- **Self-hosted advocates:** Tidak mau vendor lock-in
- **AI developers:** Butuh MCP tools yang bisa di-embed ke aplikasi mereka
- **Islamic content creators:** Butuh AI yang mengerti etika dan epistemologi Islam

### 2.4 TAM/SAM/SOM

| Metrik | Nilai | Tahun |
|--------|-------|-------|
| TAM (Total Addressable Market) | 70 juta UMKM Indonesia × 10% digital = 7 juta | 2025 |
| SAM (Serviceable Addressable) | 7 juta × 20% butuh AI tool = 1.4 juta | 2026 |
| SOM (Serviceable Obtainable) | 1.4 juta × 1% conversion = 14,000 | 2027 |

---

## 3. RISET KEBUTUHAN USER

### 3.1 User Persona

**Persona 1: UMKM Creator (40% user base)**
- Usia: 25-40 tahun
- Skill: Basic social media, tidak technical
- Kebutuhan: Competitor analysis, content creation, branding sederhana
- Pain point: Tidak tahu strategi konten yang works, tidak punya budget untuk agency
- Platform: Instagram + TikTok utama

**Persona 2: Digital Marketer (30% user base)**
- Usia: 28-45 tahun
- Skill: Intermediate marketing, somewhat technical
- Kebutuhan: Multi-platform monitoring, reporting, campaign optimization
- Pain point: Manual reporting memakan waktu, tools mahal
- Platform: Instagram, TikTok, Facebook, LinkedIn

**Persona 3: Developer/AI Enthusiast (20% user base)**
- Usia: 22-35 tahun
- Skill: Technical, familiar dengan AI tools
- Kebutuhan: MCP integration, code generation, self-hosted AI
- Pain point: Tidak ada tool AI yang self-hosted + open source + berkualitas
- Platform: Semua, via MCP

**Persona 4: Enterprise (10% user base)**
- Usia: 30-50 tahun (decision maker)
- Skill: Strategic, compliance-focused
- Kebutuhan: White-label, on-premise, custom integration, compliance
- Pain point: Data privacy concerns, vendor lock-in
- Platform: Semua, via API

### 3.2 Feature Priority berdasarkan User Research

| Fitur | UMKM | Marketer | Developer | Enterprise | Priority |
|-------|------|----------|-----------|------------|----------|
| Competitor Analysis | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | P0 |
| Content Creation | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | P0 |
| Chrome Extension | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐ | P0 |
| MCP Integration | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | P0 |
| Multi-platform | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | P1 |
| Dashboard Analytics | ⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | P1 |
| Video Generation | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | P2 |
| Code Generation | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | P2 |
| 3D Generation | ⭐ | ⭐ | ⭐⭐ | ⭐⭐ | P3 |
| White-label | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | P3 |

---

## 4. RISET TEKNIS DETAIL

### 4.1 curl_cffi vs Playwright vs requests

| Kriteria | requests+BS4 | Playwright | curl_cffi | Chrome Ext |
|----------|-------------|-----------|-----------|------------|
| Instagram works | ❌ | ✅ | ✅ | ✅ |
| Speed | N/A | 3-10s | 0.5-2s | Real-time |
| RAM usage | Low | 100-200MB | ~10MB | ~5MB |
| Detection risk | 🔴 High | 🟡 Medium | 🟢 Low | 🟢 Very Low |
| SPA support | ❌ | ✅ Full | ✅ API | ✅ API |
| Maintenance | Low | 🔴 High | 🟡 Medium | 🟡 Medium |
| SIDIX fit | ❌ | 🟡 | ✅ | ✅✅ |

**Verdict:** Chrome Extension (primary) + curl_cffi (fallback)

### 4.2 Polling vs SSE vs WebSocket

| Kriteria | Polling | SSE | WebSocket |
|----------|---------|-----|-----------|
| Complexity | Low | Medium | High |
| Real-time | 30-60s delay | Near real-time | Real-time |
| Resource | Minimal | Low | Medium |
| Best for | MVP Free tier | Pro tier | Enterprise |
| Fallback | — | Yes (degrade to polling) | Yes (degrade to SSE) |

**Verdict:** Smart polling (MVP) → SSE (Pro) → WebSocket (Enterprise)

### 4.3 Zero-Shot vs Few-Shot Prompting (Qwen2.5-7B)

| Kriteria | Few-Shot | Zero-Shot CoT |
|----------|----------|---------------|
| Qwen2.5-7B accuracy | Baseline | +5-10% |
| Token usage | High (examples) | Low |
| Maintenance | High (update examples) | Low |
| Research result | Baseline | Equals or beats few-shot |

**Verdict:** Zero-shot CoT dengan explicit reasoning instructions

### 4.4 Asyncio vs Celery untuk Queue

| Kriteria | asyncio + Redis | Celery |
|----------|-----------------|--------|
| Complexity | Low | Medium |
| Dependencies | Minimal (redis-py) | Celery + broker |
| Features | Basic queue | Advanced (retries, chords, etc) |
| SIDIX fit | ✅ MVP | Overkill untuk scale awal |

**Verdict:** asyncio + Redis untuk MVP, upgrade ke Celery jika > 10 workers

---

## 5. KESIMPULAN & REKOMENDASI

### 5.1 Top 5 Insight

1. **MCP adalah game-changer** — 1 implementation = access ke semua AI platforms. Invest di awal.
2. **Chrome Extension network interception** adalah approach paling ethical dan scalable untuk data collection. Tidak membuat request tambahan ke platform.
3. **Qwen2.5-7B + QLoRA** sudah cukup powerful untuk semua use case P0-P1. Upgrade ke 14B/72B hanya jika necessary.
4. **Indonesia market adalah blue ocean** — 70 juta UMKM, 70% pakai social media, tidak ada tool AI lokal yang affordable.
5. **Self-training loop (Jariyah)** adalah differentiator utama — setiap interaksi memperkuat sistem, membuat SIDIX semakin pintar seiring waktu.

### 5.2 Rekomendasi Teknis

| Keputusan | Pilihan | Alasan |
|-----------|---------|--------|
| MCP transport | streamable-http + stdio | Scalable + compatible |
| Scraping method | Chrome Ext + curl_cffi | Ethical + stealthy |
| Queue system | asyncio + Redis | Lightweight, self-hosted |
| AI prompting | Zero-shot CoT | Optimal untuk Qwen2.5-7B |
| Retrain trigger | 5,000 pairs OR quarterly | Balance quality vs frequency |
| Pricing | Free/$9/$99 | Accessible + sustainable |
