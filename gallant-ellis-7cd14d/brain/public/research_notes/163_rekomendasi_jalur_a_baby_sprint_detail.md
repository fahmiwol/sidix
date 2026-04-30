# 163 — Rekomendasi Jalur A + Baby Sprint 1–3 Detail

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

Tanggal: 2026-04-19
Tag: [DECISION] jalur A terpilih; [PLAN] sprint detail; [LAUNCH] strategi v0.2

Konteks: user minta arahan — pilih Jalur A (prioritisasi 3 kemampuan) atau Jalur B (deep dive satu). Saya rekomendasi **Jalur A** dengan alasan konkret + detail sprint.

---

## Kenapa Jalur A

| Faktor | Jalur A (Prioritisasi) | Jalur B (Deep dive) |
|---|---|---|
| Solo founder + resource terbatas | ✅ lebih realistis | ❌ risiko tunnel vision |
| Butuh momentum + wow factor | ✅ 3 demo kombinatif | ❌ teoretis, lambat visible |
| Baby stage 80% done | ✅ tutup gap strategis | ⚠️ mungkin prematur |
| Launch incremental (v0.2) | ✅ 2 bulan ready | ❌ timeline tidak jelas |
| Feedback loop | ✅ banyak titik sentuh pengguna | ❌ satu titik |

**Verdict:** Jalur A → 3 kemampuan dengan urutan optimal (GraphRAG → Python wrap → Image gen Nusantara) → launch v0.2 di ~2 bulan.

---

## Sprint 1 (2026-04-20 → 2026-05-03) — GraphRAG + Sanad Ranking

### Kenapa ini duluan
- **No-GPU** — bisa dikerjakan sekarang tanpa setup infra.
- **Differensiator paling kuat** — transparansi epistemologis adalah keunggulan #1 SIDIX.
- **Foundation** untuk Sprint 3 — corpus yang ter-graph jadi basis prompt enhancer Nusantara.

### Tasks

**T1.1 Wire `brain_synthesizer.py` sebagai tool `concept_graph`**
- File: `apps/brain_qa/brain_qa/agent_tools.py`
- Tambah `_tool_concept_graph(args)` — `args.query` → panggil `brain_synthesizer.get_concept_graph()` → return node+edge list + sitasi
- Register di `TOOL_REGISTRY` permission `open`
- Test: "jelaskan relasi IHOS dan Maqashid" → graph traversal multi-hop

**T1.2 Sanad-based ranker untuk `search_corpus`**
- File: `apps/brain_qa/brain_qa/query.py` (atau adapter baru)
- Tag tiap dokumen di frontmatter dengan `sanad_tier: primer/ulama/peer_review/aggregator`
- Rank score = BM25 × sanad_weight (primer=1.5, ulama=1.3, peer=1.2, aggregator=1.0)
- Test: query yang hasilnya ambigu → urutkan primer di atas

**T1.3 Fix cron LearnAgent + index corpus server**
- File: `scripts/setup_learn_cron.sh`
- Baca nama env var token yang benar di `/opt/sidix/apps/brain_qa/.env`
- Setup cron `0 4 * * *` → `POST /learn/run {"domain":"all"}`
- Jalankan `python3 -m brain_qa index` di server → verify `corpus_doc_count > 100`

**T1.4 Endpoint `/concept_graph/query` + agent_serve wiring**
- Tambah endpoint admin untuk raw graph query (debug + future UI)
- Return JSON: `{nodes: [...], edges: [...], sources: [...]}`

### DoD Sprint 1
- `tools_available = 18` (+concept_graph)
- `corpus_doc_count > 100`
- Cron LearnAgent aktif (log tail di `/var/log/sidix_learn.log`)
- Smoke test: `POST /agent/chat {"question":"apa hubungan IHOS dengan maqashid dalam corpus?","persona":"FACH"}` → jawab pakai graph traversal dengan multi-source sanad
- Research note `164_sprint1_review.md`

### Blocker potensial
- `brain_synthesizer.py` mungkin perlu refactor untuk expose `get_concept_graph(query)` API. Audit dulu.
- Cron env var token key — dari memori sesi sebelumnya blocker B2, perlu cek `.env` server.

---

## Sprint 2 (2026-05-04 → 2026-05-17) — Python Executor Wrap (Math + Data)

### Kenapa kedua
- `code_sandbox` fondasi sudah ada → tinggal wrap untuk use-case spesifik.
- Utility tinggi — matematika + data analysis dibutuhkan lintas persona (FACH, HAYFAR, TOARD).
- Deps ringan (numpy/pandas/scipy/sympy/matplotlib) — `pip install` cukup.

### Tasks

**T2.1 Tool `math_solve`**
- Wrap SymPy untuk simbolik (turunan, integral, persamaan, simplify)
- Input: `expression` (str) + `operation` (str: diff/integrate/solve/simplify) + `variable` (opsional)
- Output: LaTeX + plain text + step-by-step (jika feasible)

**T2.2 Tool `data_analyze`**
- Input: `path` (CSV di workspace) + `question` (natural language)
- Pipeline: load pandas → inspect schema → SIDIX decide analisis (groupby, correlation, trend) → execute di sandbox → return summary + tabel teratas

**T2.3 Tool `plot_generate`**
- Matplotlib preset: bar/line/scatter/heatmap
- Save PNG ke `.data/generated_plots/` → return path
- Integrasi dengan `data_analyze` (optional auto-plot)

**T2.4 Frontend support file upload**
- `SIDIX_USER_UI/src/main.ts` — upload CSV/XLSX ke workspace
- Backend endpoint `/workspace/upload` dengan permission user quota
- Deteksi mime type, save ke `.data/sidix_workspace/user_<id>/`

### DoD Sprint 2
- `tools_available = 21` (+math_solve, data_analyze, plot_generate)
- Upload CSV → tanya "tren penjualan bulanan" → chart + narasi
- `POST /agent/chat` dengan persona HAYFAR test: "solve x^2 + 5x + 6 = 0 dan plot grafiknya"

---

## Sprint 3 (2026-05-18 → 2026-06-14, 4 minggu) — Image Gen + Nusantara Prompt Enhancer

### Kenapa terakhir
- Butuh setup GPU infra (paling makan waktu eksternal).
- Differensiator paling visible untuk launch demo.
- Dependency ke Sprint 1 (corpus ter-graph → lookup Nusantara context).

### Tasks

**T3.1 Pilih + setup GPU backend**

Opsi (pilih 1):
- **A. Kaggle Inference Endpoint** — gratis 30h/week, cukup untuk demo. Limit: per-batch, tidak real-time heavy.
- **B. VPS GPU sewa (RTX 3090/4090 atau A5000)** — kontrol penuh, biaya ~$100–300/bulan.
- **C. Partner GPU** — cari mitra yang punya idle GPU.
- **D. RunPod serverless GPU** — pay-per-use, bagus untuk MVP.

**Rekomendasi:** D (RunPod serverless) untuk fase awal → migrate ke B kalau traffic cukup. Biaya RunPod ~$0.5/jam A100 serverless, launch MVP mungkin $10–30/bulan untuk trial limit.

**T3.2 Deploy SDXL / FLUX.1**
- Pilihan: FLUX.1 schnell (cepat, lisensi Apache) atau SDXL base + refiner.
- Deploy via ComfyUI / Diffusers library + FastAPI wrapper di GPU endpoint.
- Endpoint `/generate` POST `{prompt, negative, width, height, seed}` → PNG base64.

**T3.3 `image_gen.py` module di backend SIDIX**
- File: `apps/brain_qa/brain_qa/image_gen.py`
- Function `generate_image(prompt, enhance_nusantara=True)` → call GPU endpoint.
- Cache hasil di `.data/generated_images/` dengan hash prompt.

**T3.4 Nusantara Prompt Enhancer (USP SIDIX)**
- Module: `apps/brain_qa/brain_qa/prompt_enhancer_nusantara.py`
- Input: prompt user (Indonesia atau English)
- Logic:
  1. Detect Nusantara entity (candi, kota, pakaian, makanan, dll.) via NER atau keyword dictionary
  2. Lookup corpus notes terkait → extract ornamen/gaya/konteks
  3. Inject context ke prompt (English, karena model dilatih English-dominant)
  4. Tambahkan style modifier (photorealistic, 85mm lens, golden hour, dll.)
- Output: enriched prompt
- Test set: 20 prompt Nusantara → compare enhanced vs raw → manual quality check

**T3.5 Tool `generate_image` di agent_tools**
- Permission `open` (tapi quota per user)
- Params: `prompt` (str), `style` (opsional: photorealistic/illustration/batik), `aspect` (1:1, 16:9, 9:16)
- Return path file + metadata (enhanced_prompt, seed, time_ms)

**T3.6 Frontend UI image display**
- Chat message bisa render image dari tool result (markdown ![](path))
- Gallery view sederhana `/gallery` page

### DoD Sprint 3
- `tools_available = 22` (+generate_image)
- Demo video: prompt "masjid di Sumatera Barat waktu Idul Fitri" → image coherent dengan rumah gadang background + pakaian Minang
- 20 prompt test pass quality threshold
- Launch-ready untuk v0.2

---

## Launch v0.2 (2026-06-15+)

**Kriteria launch:**
- 3 sprint DoD terpenuhi
- Regressi test vs v0.1: tidak ada penurunan kapabilitas existing
- Smoke test 50 Q&A random → maqashid_pass_rate > 0.85

**Assets launch:**
- Demo video 60 detik (image Nusantara showcase)
- Blog post: "SIDIX v0.2 — AI Nusantara yang bisa bikin gambar dengan sanad"
- Threads series 3 posting (hook/detail/cta)
- Twitter thread + LinkedIn post
- Update README GitHub + changelog

**Target metric v0.2:**
- 500 unique trial user / 30 hari
- 50 GitHub star
- 10 qualified feedback (via form / Threads DM)

---

## Rekomendasi lintas-sprint

1. **Jangan skip research note** per sprint — `164_sprint1_review.md`, `165_sprint2_review.md`, dst. Itu feedback loop untuk sprint berikut.
2. **Jangan abaikan weekly self-audit** — sprint 1 sekalian setup cron audit (B5 di DEVELOPMENT_RULES).
3. **Instrumentation dulu** — log tiap tool call, durasi, success rate. Data ini → identifikasi pain point.
4. **GPU resource hunt mulai Sprint 1** — jangan tunggu Sprint 3 baru cari. 1 bulan waktu cari partner/sewa.
5. **Simpan semua prompt + hasil image** untuk dataset training LoRA SIDIX berikutnya (growth loop Layer 3).

---

## Kalau user tanya lagi "kerjakan apa?"

Jawaban permanen:
> Lihat `docs/SIDIX_ROADMAP_2026.md` + `docs/NORTH_STAR.md`. Kalau Baby Sprint 1–3 belum selesai, kerjakan itu sesuai urutan. Kalau sudah, lanjut Sprint 4 (LoRA retrain manual pipeline).

---

## Sanad

- User chat 2026-04-19: pilih Jalur A, minta arahan.
- Referensi: `docs/NORTH_STAR.md` (file ini lahir bareng), note 161 (konsep), note 162 (framework).
- Tools existing: `agent_tools.py` commit ce3f7fe.
- File yang perlu dibuat sprint ini: `image_gen.py`, `prompt_enhancer_nusantara.py`, endpoints graph/upload.
