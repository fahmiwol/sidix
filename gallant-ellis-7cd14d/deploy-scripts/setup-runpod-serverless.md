# RunPod Serverless Setup — Hybrid GPU untuk SIDIX 2.0

> Budget $30/mo, idle = $0, pay per request. Cocok untuk early beta (10–100 user).

## Konsep Hybrid

```
┌──────────────────────────────┐         ┌──────────────────────────┐
│  Hostinger VPS (CPU)         │         │  RunPod Serverless (GPU) │
│  - sidix-brain (router/RAG)  │  HTTPS  │  - vLLM worker           │
│  - sidix-ui                  │ ──────▶ │  - qwen2.5:7b atau 14b   │
│  - corpus, web_search        │ ◀────── │  - auto-stop saat idle   │
│  TETAP — $0 extra            │         │  ~$0.005/request         │
└──────────────────────────────┘         └──────────────────────────┘
```

## Math Budget $30/mo

| Setup | Cost/req | Req/$30 | Req/hari |
|---|---|---|---|
| qwen2.5:7b @ RTX 4090 Serverless | ~$0.004 | ~7,500 | ~250 |
| qwen2.5:14b @ RTX 4090 Serverless | ~$0.008 | ~3,750 | ~125 |
| qwen2.5:32b @ A100 Serverless | ~$0.025 | ~1,200 | ~40 |

**Rekomendasi awal**: qwen2.5:7b @ RTX 4090. Reasoning quality jauh lebih baik dari CPU 7b (latency 8-15s vs 60-180s) dan tetap muat budget.

---

## Setup Steps

### 1. Buat akun RunPod
1. Sign up di https://runpod.io
2. Top up wallet $30 (Stripe, crypto, atau invoice)
3. Generate API key: Settings → API Keys → Create

### 2. Deploy Serverless Endpoint
1. Console → **Serverless** → **New Endpoint**
2. **Template**: pilih `vllm-worker` (atau `Worker vLLM`)
3. **GPU**: RTX 4090 24GB (cheapest yang reliable untuk 7b/14b)
4. **Container Configuration**:
   - Image: `runpod/worker-vllm:stable-cuda12.1.0` (atau versi terbaru)
   - Container Disk: 20 GB
5. **Environment Variables**:
   ```
   MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
   MAX_MODEL_LEN=8192
   DTYPE=auto
   GPU_MEMORY_UTILIZATION=0.9
   ```
6. **Worker Configuration**:
   - Active Workers: **0** (no idle cost — penting!)
   - Max Workers: 2
   - Idle Timeout: 30 detik
   - Request Timeout: 180 detik
   - Flash Boot: ON (kurangi cold start)
7. Deploy → catat **Endpoint ID** (format: `xxxxxx-xxxx-xxxx`)

### 3. Konfigurasi Hostinger VPS

```bash
# SSH ke VPS Hostinger
ssh root@72.62.125.6
cd /opt/sidix

# Tambah env vars ke .env
cat >> .env << 'EOF'

# ── RunPod Serverless Hybrid (Pivot 2026-04-26) ──
SIDIX_LLM_BACKEND=runpod_serverless
RUNPOD_API_KEY=rpa_YOUR_API_KEY_HERE
RUNPOD_ENDPOINT_ID=YOUR_ENDPOINT_ID_HERE
RUNPOD_MODEL=Qwen/Qwen2.5-7B-Instruct
RUNPOD_TIMEOUT=180
EOF

# Restart sidix-brain (PM2 akan source .env via start_brain.sh)
pm2 restart sidix-brain --update-env
```

### 4. Verifikasi

```bash
# Healthcheck RunPod connectivity
curl -X POST -H "Authorization: Bearer $RUNPOD_API_KEY" \
  https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/health

# Test SIDIX dengan complex query (harusnya fast sekarang)
curl -X POST https://ctrl.sidixlab.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"jelaskan algoritma PageRank dengan analogi","persona":"ALEY"}'
```

---

## Wiring di SIDIX (sudah tersedia)

File `apps/brain_qa/brain_qa/runpod_serverless.py` sudah include:

- `runpod_available()` — healthcheck
- `runpod_generate()` — direct call
- `hybrid_generate()` — smart router: RunPod first, fallback Ollama lokal

Untuk aktifkan, edit `agent_react.py` line ~858 (Coba Ollama generative section):

```python
# SEBELUM:
from .ollama_llm import ollama_available, ollama_generate
if ollama_available():
    text, mode = ollama_generate(...)

# SESUDAH (hybrid):
from .runpod_serverless import hybrid_generate
text, mode = hybrid_generate(prompt, system=..., corpus_context=...)
if mode == "runpod" or mode == "ollama":
    return (text, all_citations, 0.85, "fakta")
```

(Atau lebih elegant: ubah `ollama_llm.py:ollama_generate` jadi delegate ke `hybrid_generate`. KIMI/SHARED territory — perlu koordinasi.)

---

## Monitoring & Cost Control

### Check spending harian
```bash
curl -H "Authorization: Bearer $RUNPOD_API_KEY" \
  https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/requests \
  | jq '[.requests[] | select(.status=="COMPLETED")] | length'
```

### Set hard cap (kalau ramai)
RunPod Console → Endpoint → Limits → Max Requests/Day = 200

### Cold start mitigation
- **Active Workers: 1** kalau traffic lebih konsisten ($0.34/hr × 24 × 30 = $245/mo, bukan untuk $30 budget)
- **Flash Boot ON** — recommended (cold start ~5s instead of 15s)
- **Always warm worker** alternative: schedule wake-up tiap 25 detik via cron

### Auto-shutdown jika budget habis
Set webhook RunPod → notify saat $25 spent → otomatis disable endpoint.

---

## Rollback Plan

Kalau RunPod down atau budget habis:

```bash
ssh root@72.62.125.6
sed -i 's/SIDIX_LLM_BACKEND=runpod_serverless/SIDIX_LLM_BACKEND=local/' /opt/sidix/.env
pm2 restart sidix-brain --update-env
```

`hybrid_generate()` otomatis fallback ke Ollama CPU lokal (qwen2.5:7b yang sudah ada di Ollama VPS).

---

## Alternatif Provider

| Provider | RTX 4090 Serverless | Cold start | Notes |
|---|---|---|---|
| **RunPod** | $0.00026/sec | ~5-15s | Best ekosistem, banyak templates |
| **Modal** | $0.00029/sec | ~5-10s | Python-native, decorator API |
| **Replicate** | $0.000725/sec | ~10-30s | Mahal tapi mudah pakai |
| **Lambda Labs** | on-demand only | N/A | Tidak ada serverless |
| **Vast.ai** | community pool | ~30s | Cheapest tapi reliability vary |

**RunPod menang untuk SIDIX** karena: serverless mature, persistent volume option, simpel auth.

---

## Next-step kalau berhasil + traffic naik

1. **Active Workers = 1** (~$245/mo) saat traffic > 500/day → eliminasi cold start
2. **Multi-region** kalau user di luar Indonesia
3. **Model upgrade**: qwen2.5:14b atau qwen2.5-coder:32b (lebih cerdas tapi 2-3× cost)
4. **LoRA hosted**: upload `sidix-lora-adapter` ke RunPod volume → bias output ke gaya SIDIX
