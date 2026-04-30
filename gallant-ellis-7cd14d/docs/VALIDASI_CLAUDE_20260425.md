# ✅ VALIDASI & TEST CHECKLIST — Claude

> **Tanggal:** 2026-04-25  
> **Dari:** Kimi (Jiwa+Otak sprint)  
> **Untuk:** Claude (Deploy + Review + Validasi)  
> **Commit terakhir:** `d5a2895` — FIX: Filter error observations + Compact persona for 1.5B model  

---

## 📋 DAFTAR PERUBAHAN (Hari Ini — Semua Sudah di `main`)

### 1. Backend — `apps/brain_qa/brain_qa/agent_react.py`
- **Greeting fallback persona-aware** — 5 persona, tidak lagi hardcoded formal
- **Filter error observation blocks** — skip error text masuk ke corpus_context
  - Error markers: `gagal`, `timeout`, `tidak ada hasil`, `failed`, `connection`
  - Mencegah model 1.5B generate "aku sedang mengalami masalah..." dari error message

### 2. Backend — `apps/brain_qa/brain_qa/cot_system_prompts.py`
- **Persona descriptions compact** — dari ~300 token → ~80-100 token per persona
  - Essence only: siapa + cara kerja + kata ganti
  - Untuk model 1.5B yang overwhelmed dengan prompt panjang

### 3. Frontend — `SIDIX_USER_UI/src/main.ts`
- **Thinking indicator** — "Sedang berpikir..." persist sampai token pertama
- **Stream bubble hidden** — muncul setelah token pertama datang
- **Hide confidence/feedback** — tidak render "Keyakinan: tinggi" + 👍👎 untuk v2.0 agent mode

### 4. Deploy — `docs/HANDOFF_KIMI_TO_CLAUDE_20260425.md`
- Dokumen handoff komprehensif (sudah ada di repo)

---

## 🚀 DEPLOY CHECKLIST (Wajib Dikerjakan Claude)

### Step 1: Pull & Restart Backend
```bash
ssh root@72.62.125.6
cd /opt/sidix
git pull origin main
pm2 restart sidix-brain
```

### Step 2: Rebuild UI
```bash
cd /opt/sidix/SIDIX_USER_UI
npm install
npm run build
pm2 restart sidix-ui
```

### Step 3: Sync Landing Page
```bash
cd /opt/sidix
rsync -av --delete SIDIX_LANDING/ /www/wwwroot/sidixlab.com/
# atau kalau rsync tidak ada:
# cp -r SIDIX_LANDING/* /www/wwwroot/sidixlab.com/
```

---

## 🧪 TEST CASES (Jalankan Satu per Satu, Catat Hasil)

### Test 1 — Health Check
```bash
curl -s http://72.62.125.6:8765/health | python3 -m json.tool
```
| Field | Expected |
|-------|----------|
| status | "ok" |
| model_ready | true |
| tools_available | 48 |
| corpus_doc_count | 1182 |

**Catatan hasil:** _______________

---

### Test 2 — Greeting Persona-Aware (Fallback LLM Off)
```bash
curl -s -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"halo","persona":"AYMAN","strict_mode":false}'
```
| Expected | Actual |
|----------|--------|
| Tidak ada "[EXPLORATORY]" | |
| Tidak ada "Berdasarkan referensi" | |
| Tone hangat/empatik (bukan formal) | |
| Tidak ada "Keyakinan: tinggi" di UI | |

**Catatan hasil:** _______________

---

### Test 3 — Factual Query + Web Search
```bash
curl -s -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"siapa presiden indonesia sekarang","persona":"AYMAN","strict_mode":false}'
```
| Expected | Actual |
|----------|--------|
| BUKAN "aku sedang mengalami masalah..." | |
| BUKAN "Halo! Bagaimana saya bisa membantu Anda?" | |
| Jawaban mengandung nama presiden (Prabowo Subianto) ATAU penjelasan bahwa data tidak tersedia | |
| Tidak ada [EXPLORATORY] tag untuk factual query | |

**Catatan hasil:** _______________

---

### Test 4 — Web Search Tool (Direct Test)
```bash
ssh root@72.62.125.6
cd /opt/sidix && source .venv/bin/activate
python3 -c "
from brain_qa.agent_tools import _tool_web_search
r = _tool_web_search({'query': 'presiden indonesia 2024', 'max_results': 3})
print('success:', r.success)
print('error:', r.error)
print('output:', r.output[:500] if r.output else 'NO OUTPUT')
print('citations:', len(r.citations or []))
"
```
| Expected | Actual |
|----------|--------|
| success = True | |
| Output mengandung hasil search (judul, URL, snippet) | |
| Tidak ada error timeout/connection | |

**Catatan hasil:** _______________

> **Kalau web_search GAGAL:**
> - Cek koneksi internet VPS: `curl -I https://html.duckduckgo.com`
> - Kalau blocked → tambah proxy atau ganti ke search engine lain (Bing API, SerpAPI)
> - Kalau timeout → tambah retry logic atau reduce timeout

---

### Test 5 — Persona Compact (Tone Check)
```bash
# Test AYMAN — harusnya hangat
curl -s -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"gimana cara jelasin coding ke anak kecil?","persona":"AYMAN","strict_mode":false}' | head -c 300

# Test ABOO — harusnya nyelekit/casual
curl -s -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"gimana cara jelasin coding ke anak kecil?","persona":"ABOO","strict_mode":false}' | head -c 300

# Test UTZ — harusnya playful/visual
curl -s -X POST http://72.62.125.6:8765/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"gimana cara jelasin coding ke anak kecil?","persona":"UTZ","strict_mode":false}' | head -c 300
```
| Persona | Expected Tone | Actual Tone |
|---------|---------------|-------------|
| AYMAN | Hangat, analogi sederhana, nanya balik | |
| ABOO | Nyelekit, praktis, "gue", cepat | |
| UTZ | Playful, visual, metafora, "aku" | |

**Catatan hasil:** _______________

---

### Test 6 — Frontend UI (Browser)
Buka `https://app.sidixlab.com` dan test:

| Check | Expected | Actual |
|-------|----------|--------|
| Footer | "SIDIX v2.0 · Autonomous AI Agent · Self-hosted · Free" | |
| Thinking indicator | "Sedang berpikir..." muncul saat loading | |
| No confidence | Tidak ada "Keyakinan: tinggi" di response casual | |
| No feedback buttons | Tidak ada 👍👎 di response casual | |
| Stream bubble | Muncul setelah token pertama (bukan langsung) | |

**Screenshot:** [attach screenshot]

---

### Test 7 — Landing Page
Buka `https://sidixlab.com` dan test:

| Check | Expected | Actual |
|-------|----------|--------|
| Title | "SIDIX 2.0 — Autonomous AI Agent" | |
| Hero subtitle | "Not a chatbot. An AI Agent with initiative..." | |
| Badge | v2.0 | |
| Changelog | v2.0 PIVOT entry ada | |

**Screenshot:** [attach screenshot]

---

## 🔴 KNOWN ISSUES (Masih Terbuka)

| # | Issue | Severity | Owner | Catatan |
|---|-------|----------|-------|---------|
| 1 | **Model 1.5B masih lemah untuk persona following** | 🔴 HIGH | Otak | Kalau Test 5 gagal → perlu upgrade ke 7B minimum |
| 2 | **Web search reliability** | 🔴 HIGH | Otak | Kalau Test 4 gagal → fix network/proxy/search engine |
| 3 | **Response ngelantur untuk prompt kompleks** | 🟡 MED | Jiwa+Otak | Model 1.5B limit → simplify prompt further atau upgrade |
| 4 | **Backend timeout occasional** | 🟡 MED | Otak | Streaming endpoint bisa bantu, tapi frontend belum pakai |
| 5 | **TypeScript pre-existing errors** | 🟢 LOW | Otak | `api.ts` quota, `main.ts` conversationId — non-blocking |

---

## 🎯 DECISION POINTS (Untuk User/Claude)

### A. Model Upgrade (Rekomendasi)
| Model | Size | RAM Needed | Persona Following | Factual Accuracy | Speed (CPU) |
|-------|------|------------|-------------------|------------------|-------------|
| qwen2.5:1.5b | 1 GB | 2-3 GB | ⭐⭐ Lemah | ⭐⭐ Lemah | ✅ Cepat |
| qwen2.5:7b | 4.1 GB | 6-8 GB | ⭐⭐⭐⭐ Baik | ⭐⭐⭐⭐ Baik | ⚠️ Lambat |
| qwen2.5:14b | 8.5 GB | 12-16 GB | ⭐⭐⭐⭐⭐ Kuat | ⭐⭐⭐⭐⭐ Kuat | ❌ Sangat lambat CPU |

**Rekomendasi:** Upgrade VPS ke GPU instance (RTX 3090/4090 atau A100) untuk qwen2.5:7b/14b. Kalau budget terbatas, tetap 1.5b + prompt engineering + web search.

### B. Web Search Fallback
Kalau DuckDuckGo blocked, opsi:
1. Bing Search API (free tier: 1000 query/bulan)
2. SerpAPI (free tier: 100 search/bulan)
3. Google Custom Search API (free tier: 100 query/hari)
4. Brave Search API (free tier: 2000 query/bulan)

---

## 📝 CATATAN TAMBAHAN

- **Anti-bentrok override:** User meminta Kimi mengerjakan semua (Jiwa + Otak). Claude fokus deploy + validasi.
- **Persona compact** mungkin terlalu ringkas untuk model besar (7B+). Kalau upgrade model, pertimbangkan balik ke persona full.
- **Filter error obs** aman untuk semua model size — mencegah parrot error message.
- **UI rebuild wajib** — perubahan frontend tidak aktif sampai `npm run build` dijalankan di VPS.

---

*Dokumen ini dibuat oleh Kimi untuk memudahkan Claude melakukan deploy dan validasi. Isi checklist dan catat hasil di bagian "Actual".*
