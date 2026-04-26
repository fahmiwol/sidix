# SIDIX North Star + Release Strategy (LOCK 2026-04-19, UPDATED 2026-04-26)

**Tujuan file ini:** mengunci tujuan akhir SIDIX dan strategi rilis incremental supaya **tidak kesana-kemari**. Semua keputusan teknis harus mengarah ke North Star di bawah.

Siapa pun yang ragu pilih plan: buka file ini.

---

## 🔒 UPDATE 2026-04-26 — DIRECTION LOCK Aktif

Setelah 4 pivot sepanjang Apr 2026, user explicit minta lock direction final.
Lihat **[`DIRECTION_LOCK_20260426.md`](DIRECTION_LOCK_20260426.md)** untuk lock IMMUTABLE.

**Quick reference**:
- **Tagline**: *"Autonomous AI Agent — Thinks, Learns & Creates"*
- **Direction**: AI Agent yang **BEBAS dan TUMBUH**
- **4-Pilar**: Memory + Multi-Agent + Continuous Learning + Proactive
- **5 Persona LOCKED**: UTZ / ABOO / OOMAR / ALEY / AYMAN
- **License**: MIT, self-hosted, no vendor LLM API

North Star di bawah (LOCK 2026-04-19) **konsisten** dengan DIRECTION_LOCK
2026-04-26 — lock 04-26 = elaborasi tactical, bukan pivot direction.

---

## 🌟 NORTH STAR — SIDIX v1.0 (target Q4 2026)

**SIDIX adalah AI agent standing-alone Nusantara-Islam-native yang multimodal, epistemically honest, self-hosted, dan bisa dimiliki komunitas.**

Operasional (kalimat kontrak):

> Pengguna bisa buka SIDIX → tanya apa saja (teks/gambar upload/suara) → SIDIX jawab dengan sanad + 4-label + bisa bikin gambar bergaya Nusantara + bisa coding + bisa bicara — **semua lewat model + tool self-hosted SIDIX, tidak pakai API vendor AI manapun**.

**3 keunggulan struktural (tidak bisa ditiru big tech):**
1. **Transparansi epistemologis** — 4-label wajib + sanad chain + maqashid scoring.
2. **Kedaulatan data** — own model (Qwen+LoRA) + own corpus + own infra.
3. **Spesialisasi kultural** — Nusantara + Islam native (bukan multilingual translate).

**Yang BUKAN target:** kalah parameter vs GPT-5/Claude Opus 5 → tidak kejar skala. Menang di karakter + integrity.

---

## 🚦 Rekomendasi tegas: JALUR A (prioritisasi, bukan deep dive)

**Kenapa A, bukan B:**
- Kamu solo founder dengan resource terbatas — butuh **momentum + wow factor**, bukan sprint riset teoritis.
- Baby stage 80% selesai — sisanya 3 kapabilitas strategis bisa dieksekusi 2 bulan.
- 3 kapabilitas kombinatif memberi **demo launch-ready**, bukan potongan fitur terisolasi.

## 🎯 3 Kapabilitas Baby Sprint (urutan sudah saya putuskan)

Urutan ini optimal karena **tiap sprint bangun di atas sebelumnya**:

### Sprint 1 (2 minggu) — GraphRAG + Sanad Ranking
**Kenapa ini duluan:** differensiator epistemologis paling kuat + no-GPU + foundation untuk sprint berikutnya (corpus jadi tulang punggung image prompt enhancer).

**Deliverable:**
- Tool baru `concept_graph` — wire `brain_synthesizer.py` + `knowledge_graph_query.py`
- Sanad-based ranker di `search_corpus` (prioritas: sumber primer > ulama > peer-reviewed > aggregator)
- Cron LearnAgent harian aktif (fix env var token)
- Index corpus di server → `corpus_doc_count > 100`

**DoD:** user tanya "hubungan maqashid dengan IHOS di note mana?" → SIDIX jawab multi-hop dengan traversal graph + sanad ranking, bukan BM25 polos.

### Sprint 2 (2 minggu) — Python Executor Wrap (Math + Data)
**Kenapa kedua:** `code_sandbox` sudah ada — tinggal wrap untuk use-case matematika + data. Utility tinggi, deps ringan (numpy/pandas/scipy/sympy).

**Deliverable:**
- Tool `math_solve` — wrap SymPy untuk simbolik (turunan, integral, persamaan)
- Tool `data_analyze` — pandas + matplotlib preset (user upload CSV → SIDIX analyze + plot)
- Tool `plot_generate` — matplotlib → PNG ke workspace
- Integrasi ke `workspace_read` untuk file upload

**DoD:** user upload CSV transaksi → SIDIX analyze pola + generate chart + summary naratif. User tanya "hitung ROI proyek X" → SIDIX tulis+execute kode.

### Sprint 3 (3–4 minggu) — Image Gen + Nusantara Prompt Enhancer
**Kenapa terakhir:** butuh GPU setup (paling makan waktu infra). Differensiator paling visible untuk launch demo.

**Deliverable:**
- Setup SDXL/FLUX self-host (pilihan: Kaggle Inference API / VPS GPU sewa / partner A100)
- `image_gen.py` module + tool `generate_image`
- **Nusantara prompt enhancer** — module yang enrich prompt dengan lookup ke corpus Nusantara (relief candi, batik, ornamen, pakaian daerah, lansekap) sebelum kirim ke SDXL
- Storage `.data/generated_images/` dengan retention 30 hari

**DoD:** prompt "astronaut di Borobudur" → SIDIX parse → lookup corpus Nusantara → enrich (stupa bell-shape, relief Boddhisattva, Merapi background, golden hour) → SDXL → coherent image 30s. Demo ke publik siap.

**Total:** ~2 bulan = **v0.2 launch-ready**.

---

## 📦 Release Strategy Incremental (rilis sedikit demi sedikit)

Tidak perlu tunggu "semua sempurna". Rilis setiap milestone tercapai, dapat feedback, iterate.

| Version | Target | Highlight launch ("wow factor") | Durasi cum. | Status |
|---|---|---|---|---|
| **v0.1** | Baby minimum | "SIDIX bisa jawab dengan sanad + 4-label epistemik" | sekarang | ✅ **LIVE** (chatboard + 17 tool + model ready) |
| **v0.2** | Baby sprint 1–3 | "SIDIX bikin gambar Nusantara + jawab grafik relasi konsep + analisis data" | +2 bulan | 🎯 target 2026-06-19 |
| **v0.3** | Baby complete | "SIDIX ingat konteks minggu lalu + skill library mulai tumbuh" | +1.5 bulan | target 2026-08-01 |
| **v0.5** | Child partial | "SIDIX bicara bahasa Indonesia + pakai suara kamu + coding agent self-host" | +2 bulan | target 2026-10-01 |
| **v0.8** | Child + video | "SIDIX bikin video ringan TikTok-style (story+image+narasi+stitch)" | +1 bulan | target 2026-11-01 |
| **v1.0** | Child complete — **PUBLIC BETA** | "SIDIX multimodal parity GPT-4V Nusantara, open source MIT, self-hostable" | +1 bulan | target 2026-12-01 |
| **v2.0** | Adolescent | "SIDIX self-evolving — belajar tanpa manusia, retrain mandiri" | +6 bulan | target 2027-Q2 |
| **v3.0** | Adult | "SIDIX Hafidz Network — federated contributors, DiLoCo" | +12 bulan | target 2028-Q1 |

**Prinsip rilis:**
1. Setiap versi punya **1 wow factor utama** — komunikasi publik fokus ke sana, bukan list fitur.
2. Versi minor (v0.x) = **internal + early users**. v1.0 = public beta. v2.0 = production.
3. Tiap rilis: changelog + demo video + research note + blog post.
4. Feedback loop: instrumentasi pemakaian → identifikasi pain → iterasi di sprint berikut.

---

## 🎬 Cara launching "sedikit demi sedikit"

**v0.1 (sudah LIVE):** `app.sidixlab.com` dengan chatboard. **Tidak perlu menunggu.** Sudah bisa di-announce:
- Blog post: "Memperkenalkan SIDIX — AI agent Nusantara dengan sanad"
- Threads series: hook (pain) → detail (3 keunggulan) → CTA (coba chat)
- GitHub star campaign (pasang badge open source MIT)

**v0.2 (target Juni 2026):** launch event "Bikin gambar bergaya Nusantara":
- Video demo 60 detik: prompt "masjid Agung Demak pagi Ramadhan" → SDXL dengan enhancer → hasil coherent Nusantara
- Posting: X thread, Threads, LinkedIn, Medium, YouTube short
- Target: 500 user trial, 50 GitHub star

**v0.3–v0.8:** rilis bulanan dengan 1 fitur besar per bulan. Bangun community di Discord/Threads.

**v1.0 (Desember 2026):** public beta launch — Product Hunt / TechCrunch / ID startup media. Target: 5000 trial, 500 GitHub star, 3 mitra awal.

**v2.0 (2027 Q2):** paper publikasi + konferensi akademik (IHOS + SIDIX sebagai contoh epistemologi-grounded AI).

---

## 🔐 Lock — apa yang TIDAK berubah

Untuk menghindari kesana-kemari, lock berikut **tidak boleh diubah tanpa ADR + approval user**:

1. **North Star di atas** — redefinisi butuh justifikasi kuat.
2. **3 keunggulan struktural** (transparansi epistemologis + kedaulatan + kultural) — ini core identity.
3. **Standing alone** — tidak pakai vendor AI API untuk inference.
4. **Urutan Sprint 1–3 di atas** — GraphRAG → Python wrap → Image gen.
5. **UI chatboard** — lihat `CLAUDE.md` section "UI LOCK".
6. **Arsitektur Brain+Hands+Memory** — detail di note 162.

## ✅ Apa yang BOLEH berubah

- Timeline (geser jika blocker resource).
- Pilihan model spesialis (SDXL vs FLUX vs Pixart — cari yang feasible).
- Urutan sub-task dalam sprint.
- Sprint berikutnya setelah v0.2 (dievaluasi dari feedback v0.2).

---

## 🧭 Pertanyaan kamu di masa depan — panduan jawab cepat

| Kamu nanya… | Jawaban cepat |
|---|---|
| "Sekarang kerjakan apa?" | Buka `docs/SIDIX_ROADMAP_2026.md`, pilih sprint paling bawah yang belum done. |
| "Apakah ini sesuai visi?" | Cek: (a) standing-alone? (b) advance 1 dari 3 keunggulan struktural? (c) arah ke v1.0 Child stage? Kalau semua ya, lanjut. |
| "Pakai model X boleh?" | Cek: (a) open weight? (b) bisa self-host? Kalau ya, boleh. API vendor = no. |
| "Urutan mana dulu?" | GraphRAG → Python wrap → Image gen (untuk Baby). Setelah Baby: voice → coding → video → v1.0. |
| "Ini fitur baru worth?" | Cek dampak ke wow factor rilis berikutnya. Kalau tidak ada kontribusi langsung, masuk backlog. |

---

## 📁 File terkait

- `CLAUDE.md` — aturan permanen + UI LOCK + IDENTITAS SIDIX
- `docs/DEVELOPMENT_RULES.md` — aturan mengikat agent + self-dev
- `docs/SIDIX_ROADMAP_2026.md` — 4 stage × sprint plan detail
- `docs/SIDIX_CAPABILITY_MAP.md` — SSoT kapabilitas current
- `docs/01_vision_mission.md` — visi + Brain/Hands/Memory
- `docs/02_prd.md` — PRD + peta 10 kemampuan
- `brain/public/research_notes/161_*.md` — konsep AI/LLM + 8 differensiator
- `brain/public/research_notes/162_*.md` — framework Brain+Hands+Memory
- `brain/public/research_notes/163_*.md` — rekomendasi jalur A + sprint detail (next file)

---

## Signature

File ini LOCK per 2026-04-19. Review tiap akhir quarter. Perubahan wajib via ADR di `docs/decisions/`.
