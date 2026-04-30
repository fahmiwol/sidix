# Task bundle untuk Antigravity — Research Sprint 3 prep + Plan B/C exploration

**Agent:** Antigravity (Google IDE agent).
**Branch:** `antigravity/sprint-3/research-<topik>`.
**Mode:** read-only research + markdown output. **Jangan edit kode backend** — output research saja.
**Prasyarat baca (wajib 10 menit):**
- [CLAUDE.md](../../CLAUDE.md) — identitas SIDIX 3-layer + UI LOCK + prinsip standing-alone.
- [docs/NORTH_STAR.md](../NORTH_STAR.md) — tujuan akhir + release strategy.
- [docs/DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md) — Part A agent rules.
- [docs/MULTI_AGENT_WORKFLOW.md](../MULTI_AGENT_WORKFLOW.md) — koordinasi.
- [docs/SIDIX_ROADMAP_2026.md](../SIDIX_ROADMAP_2026.md) — 4 stage, terutama Baby & Child stage.
- [brain/public/research_notes/161](../../brain/public/research_notes/161_ai_llm_generative_claude_dan_differensiasi_sidix.md), [162](../../brain/public/research_notes/162_framework_brain_hands_memory_peta_kemampuan_sidix.md), [163](../../brain/public/research_notes/163_rekomendasi_jalur_a_baby_sprint_detail.md).

**Prinsip non-negosiasi:**
- Output berupa **research note markdown** di `brain/public/research_notes/NNN_topik.md` dengan 4-label epistemik + sanad chain.
- Tidak pakai API vendor AI untuk research (pakai search publik / paper open access).
- Semua rekomendasi harus **standing-alone compatible**: open weight model, self-hostable, tidak depend vendor proprietary.
- Bahasa Indonesia untuk narasi, English OK untuk istilah teknis.

---

## 🎯 Task R1 — GPU Provider Comparison untuk SIDIX Sprint 3

### Tujuan
Hasil akhir: rekomendasi GPU provider konkret untuk self-host SDXL/FLUX + Qwen2.5-VL di Sprint 3, dengan cost-analysis + limitasi + setup step.

### Deliverable
File: `brain/public/research_notes/170_gpu_provider_comparison_2026.md` (nomor 170+ supaya tidak tabrakan dengan Cursor di 164/165).

### Struktur yang harus ada

```markdown
# 170 — GPU Provider Comparison untuk SIDIX Sprint 3

## 1. Kebutuhan SIDIX
- [FACT] SDXL minimum VRAM: 8 GB (optimal 12–16 GB)
- [FACT] FLUX.1 schnell: ~24 GB optimal, bisa <16 GB dengan quantization
- [FACT] Qwen2.5-VL-7B: ~16 GB 4-bit quant
- Workload pattern: user-triggered (bukan 24/7 training)

## 2. Kandidat provider (min 5)
Bandingkan minimum:
1. RunPod serverless GPU (A100, A5000, RTX 4090, L40)
2. Vast.ai marketplace
3. Kaggle free tier (T4, P100) + Inference Endpoint
4. Lambda Labs (A100 on-demand)
5. CoreWeave (A100/H100)
6. Google Cloud Run GPU (jika relevan)
7. VPS GPU sewa lokal Indonesia (kalau ada — Biznet, Indobiz, dll.)

Untuk tiap provider, kumpulkan:
- Harga per jam (A100, A5000, RTX 4090)
- Minimum commitment (serverless vs reserved)
- Cold start time
- Billing granularity (per-detik, per-menit)
- Region (latency ke Asia)
- Compliance (GDPR, Indonesia data residency)
- Community feedback (reddit r/MachineLearning, reddit r/LocalLLaMA)

## 3. Rekomendasi untuk tiap fase
- Baby Sprint 3 (MVP image gen): provider paling murah untuk low-traffic
- Child multi-model (SDXL + VLM + Qwen-Coder): mix strategy
- Adolescent self-evolving (retraining): cost-efficient

## 4. Setup step konkret untuk Top 1 pilihan
- Registrasi
- Deploy container / endpoint
- API integration ke SIDIX brain (referensi: `apps/brain_qa/brain_qa/image_gen.py` yang akan dibuat)
- Monitoring + cost alert

## 5. Risiko + mitigasi
- Vendor lock-in → mitigasi: containerize, portable
- Biaya membengkak → budget cap + quota
- Region down → multi-provider fallback

## 6. Keputusan
Rekomendasi Top 1 dengan alasan. Alternatif Top 2.

Sanad: daftar URL + tanggal akses tiap referensi.
```

### Acceptance
- Minimal 5 provider dibandingkan
- Harga 2026-04-19 (cek live saat riset, bukan cached old pricing)
- Rekomendasi konkret, bukan "depends"
- Sanad lengkap

---

## 🎯 Task R2 — SDXL vs FLUX.1 vs Alternatif untuk Image Gen SIDIX

### Tujuan
Pilih 1 model image gen yang paling cocok untuk SIDIX (quality + license + VRAM + kecepatan).

### Deliverable
`brain/public/research_notes/171_image_model_comparison_sdxl_flux_alternatif.md`

### Struktur

```markdown
# 171 — Image Model Comparison: SDXL, FLUX.1, Alternatif

## 1. Requirement SIDIX
- Standing alone: open weight, self-hostable
- Quality: coheren untuk prompt kompleks Nusantara (contoh: "masjid Agung Demak subuh dengan kaligrafi")
- Performance: <30 detik per image di A100
- License: permissive untuk komersial eventual
- Integration: ComfyUI atau Diffusers lib

## 2. Model kandidat
1. Stable Diffusion XL base + refiner
2. SDXL Turbo (cepat tapi kualitas lebih rendah)
3. FLUX.1 dev (non-komersial license)
4. FLUX.1 schnell (Apache 2.0, komersial OK)
5. Pixart-Σ
6. Stable Cascade
7. AuraFlow
8. Hunyuan-DiT
9. PlaygroundAI Playground-v3 (jika open)

Untuk tiap:
- [FACT] Lisensi exact (text quote dengan URL sumber)
- [FACT] VRAM minimum + optimal
- [FACT] Quality benchmark (dari HELM, Arena, paper citations)
- [OPINION] Kemampuan prompt complex multi-subject
- Speed: image/s di A100/4090
- Prompt adherence (apakah paham prompt panjang / concept compositional)
- Community tooling (ComfyUI node, LoRA ecosystem)

## 3. Test case Nusantara (propose, bukan eksekusi)
Daftar 10 prompt Nusantara untuk benchmark post-selection:
- Masjid Agung Demak waktu subuh
- Relief Borobudur dengan cahaya matahari pagi
- Pasar Beringharjo Yogyakarta pagi
- Batik Parang dengan motif emas
- Rumah gadang Sumatra Barat
- (5 lagi)

## 4. Rekomendasi
Top 1 dengan alasan + setup approx.

Sanad: URL arxiv, huggingface, blog posts, tanggal akses.
```

---

## 🎯 Task R3 — Nusantara Knowledge Base Design untuk Prompt Enhancer

### Tujuan
Desain schema knowledge base + strategi kurasi untuk prompt enhancer Nusantara (differensiator SIDIX).

### Deliverable
`brain/public/research_notes/172_nusantara_knowledge_base_design_prompt_enhancer.md`

### Struktur

```markdown
# 172 — Nusantara Knowledge Base Design untuk Prompt Enhancer

## 1. Konsep
SIDIX menerima prompt user → deteksi entitas Nusantara → lookup KB → enrich prompt
sebelum kirim ke model diffusion. Differensiator: big tech tidak punya KB ini.

## 2. Schema proposal
Tabel atau struktur JSON per kategori:
- Candi (Borobudur, Prambanan, Penataran, dll.) — ornamen, relief, lokasi, sejarah visual.
- Pakaian daerah (Bali, Minang, Batak, Dayak, ...) — style, warna, aksesori.
- Lansekap (sawah terasering, pantai Anyer, hutan Kalimantan, ...) — flora, langit, pencahayaan.
- Arsitektur (joglo, rumah gadang, tongkonan, ...) — material, atap, proporsi.
- Batik & tenun (Parang, Kawung, Mega Mendung, songket, ulos, ...) — motif, warna.
- Kuliner visual (rendang, gudeg, sate padang, ...) — penyajian, warna.
- Alat musik (gamelan, angklung, sasando, ...) — bentuk, konteks.
- Ornamen keagamaan (masjid, pura, gereja Batak, vihara, ...) — elemen distinctif.

Setiap entry:
```
{
  "id": "nusantara.candi.borobudur",
  "canonical_name": "Borobudur",
  "aliases": ["Borobudur", "Candi Borobudur", "Stupa Borobudur"],
  "category": "candi_buddhist",
  "location": "Magelang, Central Java, Indonesia",
  "visual_keywords_en": [
    "bell-shape stupas", "Buddhist relief carvings", "Boddhisattva reliefs",
    "mandala layout", "volcanic landscape", "misty morning"
  ],
  "style_modifiers": ["ancient", "serene", "golden hour light"],
  "cultural_context": "9th century Mahayana Buddhist temple",
  "sanad_tier": "peer_review",
  "sources": ["UNESCO", "Balai Konservasi Borobudur"]
}
```

## 3. Sumber kurasi
- UNESCO World Heritage (tier: peer_review)
- Dinas Kebudayaan provinsi (tier: primer)
- Wikipedia ID + EN (tier: peer_review, cross-check)
- Buku: "Nusantara Heritage" (propose list)
- arXiv cultural AI papers

## 4. Pipeline kurasi
- Phase 1 (Sprint 3): 50 entitas paling umum.
- Phase 2: community contribution.
- Phase 3: SIDIX sendiri generate draft dari corpus, user approve.

## 5. Integration dengan brain_synthesizer
Extend CONCEPT_LEXICON dengan Nusantara concepts atau buat lexicon terpisah?
Rekomendasi: terpisah (`NUSANTARA_LEXICON`) supaya tidak bloat IHOS concepts.

## 6. Privasi + etika
- Tidak mengumpulkan face data.
- Sensitif cultural: konsultasi ahli untuk entity yang sakral.

Sanad: daftar referensi.
```

---

## 🎯 Task R4 — Deployment pattern image gen (ComfyUI vs Diffusers wrapper)

### Tujuan
Pilih cara deploy model image gen yang paling maintainable untuk SIDIX.

### Deliverable
`brain/public/research_notes/173_image_gen_deployment_pattern.md`

### Bandingkan
- ComfyUI + workflow JSON
- Diffusers library (pipeline sederhana)
- Custom FastAPI + transformers
- Replicate Cog (gratis local mode)

Kriteria: maintenance, LoRA support, memory efficiency, observability, community support.

---

## 📝 Output format aturan

Setiap research note:
- 4-label epistemik di setiap klaim non-obvious.
- Sanad chain di akhir (URL + tanggal akses + lisensi jika applicable).
- Bahasa Indonesia untuk narasi, English OK istilah teknis.
- Table comparison > prose untuk data komparasi.
- Rekomendasi konkret di akhir (bukan "tergantung").

## 📞 Handoff ke Claude

Setelah research note selesai:
1. Commit ke branch `antigravity/sprint-3/research-<topik>`.
2. Open PR ke `main` dengan body link ke task file ini.
3. Append entry di `docs/LIVING_LOG.md` dengan tag `[NOTE]` + ringkasan 1 kalimat.
4. Tulis report di `docs/agent_tasks/reports/RESEARCH_<topik>_report_antigravity.md`.

Claude akan review konsistensi dengan North Star + standing-alone principle, lalu merge.

## 🚫 Apa yang Antigravity TIDAK kerjakan di sprint ini

- ❌ Touch kode backend (`apps/brain_qa/`).
- ❌ Touch frontend (`SIDIX_USER_UI/`).
- ❌ Edit dokumen governance (CLAUDE.md, NORTH_STAR, RULES, ROADMAP).
- ❌ Deploy ke server.
- ❌ Setup infrastruktur langsung.

Research-only, output markdown. Implementasi oleh Claude + Cursor berdasar hasil research.

## 📞 Komunikasi

- Stuck? Tulis di `docs/open_questions.md` tag `@claude` atau `@user`.
- Research butuh data dari codebase? Read-only OK, jangan modify.
- Hasil ambigu / dua rekomendasi seimbang? Tulis keduanya + minta user decide.

---

## Signature
Task file dibuat: 2026-04-19 oleh Claude sebagai koordinator.
Review: setelah 4 research note selesai → Claude rangkum ke ADR untuk Sprint 3 execution.
