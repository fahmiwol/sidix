# RISET: SIDIX-SocioMeter
## Laporan Riset Teknologi & Pasar

**Versi:** 1.0 | **Status:** FINAL | **Klasifikasi:** Research Document

---

## 1. TEKNOLOGI

### MCP (Model Context Protocol)
- Standar terbuka (Linux Foundation), diadopsi ekosistem host AI besar
- FastMCP: banyak server MCP memakai Python SDK
- Transport: stdio (lokal), streamable-http (produksi), SSE (real-time)
- Auto-discovery: agen memuat daftar tools tanpa konfigurasi manual berlebihan

### Chrome Extension MV3
- Wajib untuk Chrome Web Store (MV2 deprecated 2024)
- Service worker (tidak persisten) → pakai `chrome.alarms`
- IndexedDB untuk offline buffer (50MB+)
- Content script di `document_end` untuk SPA compatibility

### Instagram Scraping 2026
- 5-layer defense: IP check, TLS fingerprint, rate limit, behavioral, doc_id rotation
- `curl_cffi`: impersonate Chrome TLS → low detection risk
- Network interception (Chrome Ext): paling ethical, tidak extra request

### Qwen2.5-7B Fine-Tuning
- QLoRA: r=16, alpha=32, 3 epochs optimal untuk 7B
- Flash Attention v2: -40-50% memory usage
- 4-bit NF4: 7B muat di 8GB VRAM
- Multi-agent reasoning: +6.8 points dengan 7B model

### Generative AI Tren 2026
1. Multimodal + Agentic systems
2. Domain-specific models (smaller, specialized)
3. Synthetic data generation
4. Embedded governance
5. Edge deployment

---

## 2. PASAR

### Indonesia Creator Economy
- USD 38.5B (2025) → USD 112.7B (2031), CAGR 19.7%
- 70% UMKM menggunakan Instagram/TikTok untuk marketing
- Incumbent global: SaaS analitik sosial tier atas (ratusan USD/bulan) — UMKM sering tidak terlayani

### Competitive Landscape
| Tool | Harga | Self-Host | AI-Native | Indonesia | Open Source |
|------|-------|-----------|-----------|-----------|-------------|
| Incumbent A (SaaS global) | ~$249/mo | No | Basic | No | No |
| Incumbent B (SaaS global) | ~$199/mo | No | Basic | No | No |
| Incumbent C (enterprise listening) | Enterprise | No | Yes | No | No |
| **SIDIX** | **Free/$9/$99** | **Yes** | **Yes** | **Yes** | **Yes** |

### TAM/SAM/SOM
- TAM: 7 juta UMKM digital Indonesia
- SAM: 1.4 juta butuh AI tool
- SOM: 14,000 (1% conversion)

---

## 3. TOP 5 INSIGHT

1. **MCP = game changer** — 1 implementation = access ke banyak host mitra
2. **Chrome Ext network interception** = paling ethical + scalable untuk data collection
3. **Qwen2.5-7B + QLoRA** sudah cukup powerful untuk semua P0-P1 use cases
4. **Indonesia = blue ocean** — puluhan juta UMKM, tidak ada tool AI lokal yang affordable merata
5. **Self-training loop (Jariyah)** = ultimate differentiator — semakin banyak user = semakin pintar

---

## 4. REKOMENDASI TEKNIS

| Keputusan | Pilihan | Alasan |
|-----------|---------|--------|
| MCP transport | streamable-http + stdio | Scalable + compatible |
| Scraping method | Chrome Ext + curl_cffi | Ethical + stealthy |
| Queue system | asyncio + Redis | Lightweight, self-hosted |
| AI prompting | Zero-shot CoT | Optimal untuk Qwen2.5-7B |
| Retrain trigger | 5,000 pairs OR quarterly | Balance quality vs frequency |
| Pricing | Free / $9 / $99 | Accessible + sustainable |
