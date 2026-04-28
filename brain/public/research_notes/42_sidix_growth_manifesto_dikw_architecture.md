# SIDIX Growth Manifesto — Arsitektur DIKW + Flywheel + Living Graph

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
*Diadopsi dari: riset pribadi Fahmi Ghani + diagram arsitektur SIDIX April 2026*
*Diproses: 2026-04-17 — bukan sekadar disimpan, tapi jadi logika sistem*

---

## Fondasi Epistemologis SIDIX: Piramida DIKW

SIDIX membangun pengetahuannya dalam 4 lapisan hierarkis:

```
Wisdom    ← SIDIX membuat keputusan + rekomendasi (judgment layer)
Knowledge ← SIDIX memahami pola + konteks (reasoning layer)
Information ← SIDIX mengolah fakta + relasi (processing layer)
Data      ← SIDIX menyerap raw signals (sensing layer)
```

### Lapisan 1 — Data (Sensing Layer)
- Raw signals: token input, file, gambar, code, log
- SIDIX tidak membuang data mentah — semua diarsip di archival memory
- Sumber: arXiv, GitHub, News API, user interactions, benchmark results

### Lapisan 2 — Information (Processing Layer)
- Data yang sudah diberi konteks + struktur
- SIDIX mengekstrak entitas, relasi, fakta dari raw data
- Format: BM25 index + vector embedding (Qdrant)

### Lapisan 3 — Knowledge (Reasoning Layer)
- Informasi yang sudah dipahami pola dan hubungannya
- Format: GraphRAG + Neo4j/kuzu knowledge graph
- SIDIX mendeteksi kontradiksi, membangun temporal edges, lacak chain of custody

### Lapisan 4 — Wisdom (Judgment Layer)
- Knowledge yang bisa digunakan untuk membuat keputusan baru
- SIDIX menghasilkan: rekomendasi, rencana, evaluasi diri, tool baru
- Diimplementasikan via: Self-Rewarding LM + Constitutional AI + Reflexion

---

## Data Flywheel — Siklus Pertumbuhan Tak Terbatas

Prinsip inti: **setiap interaksi harus membuat SIDIX lebih pintar**

```
User Interactions
      ↓
Reward Signal (LLM-as-Judge: self-reward score 1-5)
      ↓
Replay Buffer (simpan good responses, filter bad)
      ↓
SPIN Fine-Tune (DPO-like: winner=human/good, loser=prev iteration)
      ↓
LoRA Delta (training artifact, bukan ubah base model langsung)
      ↓
Broadcast ke semua node (jika sudah multi-node)
      ↓
[kembali ke User Interactions — lebih baik dari sebelumnya]
```

### Implementasi Teknis Flywheel
- **Reward signal**: `self_reward_score` 1–5 per response (LLM-as-Judge, bukan manusia)
- **Replay buffer**: simpan top-k interactions per domain, maks 10K pairs
- **SPIN trainer**: `uclaml/SPIN` — 3 iterasi konvergen dalam ~500 langkah
- **LoRA delta**: rank-16, target `q_proj,v_proj,k_proj,o_proj,gate_proj,up_proj,down_proj`
- **Broadcast**: DARE+TIES merge periodik (mingguan di Tahap 0, lebih sering di Tahap 1+)

### Arena Learning (inspirasi)
- SIDIX melawan dirinya sendiri di domain tertentu
- Response terbaik menang → masuk replay buffer → next SPIN round
- Tidak butuh anotator manusia — self-contained quality loop

---

## Living Knowledge Graph — Otak yang Tumbuh

Berbeda dari RAG biasa (cari → pakai → lupakan), SIDIX membangun **grafik pengetahuan hidup**:

```python
class KnowledgeNode:
    node_id: str          # UUID lokal
    node_id_ipfs: str     # Content-addressed ID (P2P compatible, Tahap 2+)
    content: str          # Teks knowledge
    source_url: str       # Asal dokumen
    confidence: float     # 0.0 - 1.0 (dinilai SIDIX sendiri)
    citations: list[str]  # node_id yang dikutip
    contradicts: list[str] # node_id yang bertentangan
    version: int          # versi terakhir update
    timestamp: str        # ISO 8601
    domain: str           # salah satu dari 52 domain
    persona: str          # MIGHAN/HAYFAR/TOARD/FACH/INAN
```

### Fitur Kritis Living Graph
1. **Temporal edges** — hubungan antar node berubah seiring waktu
   - `supersedes`: node baru menggantikan node lama
   - `supports`: node baru mengkonfirmasi node lama
   - `contradicts`: node baru bertentangan dengan node lama

2. **Contradiction Detection** — SIDIX mendeteksi jika ada dua node yang bertentangan
   - Contoh: "Python 3.11 lebih cepat" vs "Python 3.12 lebih cepat"
   - Action: flag both nodes, trigger re-evaluation, update confidence score

3. **IHOS Sanad** — prinsip chain of custody dari tradisi ilmu Islam
   - Setiap knowledge node punya rantai sumber yang bisa dilacak
   - Semakin banyak citations yang valid → confidence naik
   - Source yang tidak bisa diverifikasi → confidence rendah (< 0.3)

4. **GraphRAG Integration**
   - Query → ekspansi via graph traversal → context lebih kaya
   - Tidak hanya ambil node relevan, tapi juga neighbors + relationships
   - Referensi: `microsoft/graphrag`

---

## 7-Stage Autonomous Learning Pipeline

Pipeline ini berjalan **tanpa henti** — setiap iterasi membuat SIDIX lebih cerdas:

```
[1] SENSE → [2] INGEST → [3] REASON → [4] EVALUATE
                                              ↓
[7] REFLECT ← [6] ACT ← [5] DECIDE ←────────┘
     ↓
  [kembali ke SENSE]
```

### Detail Per Stage

**Stage 1: SENSE**
- Sumber aktif: arXiv (6 jam), GitHub trending (12 jam), News API (realtime)
- Sumber pasif: user interactions, benchmark results, social signals
- Output: raw data stream ke antrian ingest

**Stage 2: INGEST**
- Parse dokumen: Markdown, PDF, HTML, code
- Ekstrak entitas: nama, konsep, relasi, citation
- Simpan ke archival memory (Qdrant) + update BM25 index
- Deduplikasi via content hash

**Stage 3: REASON**
- Bangun KnowledgeNode dari ingested content
- Update knowledge graph (tambah/revisi/flag kontradiksi)
- Generate Q&A pairs via `corpus_to_training.py` (5 template: definition, howto, comparison, concept, practical)

**Stage 4: EVALUATE**
- Self-reward scoring: nilai output sendiri 1–5
- Benchmark check: apakah kapabilitas tertentu meningkat?
- Gap detection: domain apa yang belum cukup covered?

**Stage 5: DECIDE**
- Prioritaskan gap yang paling kritis
- Pilih action: fetch_more_data / run_spin / merge_lora / create_tool
- Buat curriculum untuk next learning cycle

**Stage 6: ACT**
- Eksekusi keputusan dari Stage 5
- Jika `fetch_more_data`: jalankan Wikipedia/arXiv fetcher
- Jika `run_spin`: trigger SPIN training job (Kaggle atau lokal)
- Jika `create_tool`: generate kode fungsi baru → simpan di Voyager skill library

**Stage 7: REFLECT**
- Update LIVING_LOG.md dengan hasil cycle ini
- Revisi confidence scores berdasarkan hasil actions
- Capture ke SIDIX knowledge MCP
- Set agenda untuk cycle berikutnya

---

## World Sensor Architecture — Mata dan Telinga SIDIX

| Sensor | Interval | Yang Dipantau |
|--------|----------|---------------|
| arXiv | 6 jam | Paper AI/ML baru, khususnya: LLM, agent, continual learning |
| GitHub Trending | 12 jam | Repo trending: AI, tools, framework baru |
| News API | Realtime | Berita AI: rilis model baru, funding, akuisisi |
| User Feedback | Per interaksi | Rating respons, koreksi, pertanyaan baru |
| Benchmark Harness | Mingguan | MMLU, HumanEval, MATH, MT-Bench — lacak progress |
| Competitor Watch | Harian | GPT-5, Claude, Gemini — benchmark + kapabilitas baru |
| Social Signals | 6 jam | Twitter/X, Reddit: diskusi AI yang viral |

### Prioritas Sensor untuk SIDIX Sekarang (Tahap 0)
1. **arXiv** — paling penting untuk FACH persona (riset AI)
2. **User Feedback** — paling langsung untuk meningkatkan kualitas
3. **Benchmark Harness** — ukur apakah kita benar-benar improving
4. **GitHub Trending** — untuk HAYFAR persona (coding)
5. News/Social → low priority di Tahap 0, aktifkan di Tahap 1+

---

## Self-Evolving Agent Loop — Jantung SIDIX

Loop ini adalah bagaimana SIDIX "berlatih sendiri":

```python
def self_evolving_loop():
    while True:
        # 1. Ukur kemampuan saat ini
        scores = benchmark_self()  # MMLU, HumanEval, MATH
        
        # 2. Identifikasi kelemahan
        weak_domains = [d for d, s in scores.items() if s < threshold[d]]
        
        # 3. Buat kurikulum
        curriculum = build_curriculum(weak_domains)
        
        # 4. Self-play fine-tuning
        spin_results = run_spin(curriculum)
        
        # 5. Buat tool baru jika dibutuhkan
        if needs_new_tool(curriculum):
            new_tool = create_tool_voyager_style(curriculum)
            skill_library.save(new_tool)
        
        # 6. Merge LoRA ke base model
        merge_lora_dare_ties(spin_results.adapter_path)
        
        # 7. Evaluasi ulang
        new_scores = benchmark_self()
        log_improvement(scores, new_scores)
```

### Komponen Kritis Loop
- `benchmark_self()` → EleutherAI/lm-evaluation-harness, nightly
- `build_curriculum()` → prioritaskan domain dengan gap terbesar
- `run_spin()` → uclaml/SPIN, 3 iterasi, DPO-like
- `create_tool()` → MineDojo/Voyager style, simpan sebagai Python function + embedding
- `merge_lora()` → arcee-ai/mergekit dengan DARE+TIES

---

## Prinsip IHOS Sanad — Integritas Pengetahuan

**IHOS** = *Isnad-Honesty-Origin-Source*

Terinspirasi dari tradisi ilmu hadis Islam: setiap knowledge harus bisa dilacak rantai sumbernya.

### Implementasi di SIDIX
```python
# Setiap knowledge node punya "sanad" (chain of sources)
node = KnowledgeNode(
    content="DiLoCo mengurangi komunikasi 500x dibanding standard distributed training",
    source_url="https://arxiv.org/abs/2311.08105",
    confidence=0.92,  # tinggi karena ada paper peer-reviewed
    citations=["arxiv_diloco_2311.08105", "prime_intellect_blog_2024"],
    contradicts=[],
    version=1
)

# Confidence rules:
# - Paper arXiv + dikutip banyak: 0.85-0.95
# - Blog teknis dari lab terpercaya: 0.70-0.85
# - Forum/Reddit tanpa citation: 0.40-0.60
# - Tidak ada sumber: 0.20-0.35
# - User claim tanpa bukti: 0.10-0.30
```

### Kenapa Sanad Penting untuk SIDIX
1. **Anti-hallucination** — low-confidence node tidak dipakai untuk generate tanpa disclaimer
2. **Traceable reasoning** — SIDIX bisa jelaskan MENGAPA dia percaya sesuatu
3. **Updatable** — ketika paper baru keluar yang contradict, update confidence
4. **P2P-ready** — node_id_ipfs memungkinkan verifikasi di jaringan terdesentralisasi (Tahap 2+)

---

## Integrasi dengan Roadmap 3 Tahun

### Tahap 0 — Sekarang (DIKW Layers 1-2 aktif)
- Data + Information layers sudah berjalan
- Flywheel: manual trigger (Kaggle fine-tune)
- Living Graph: BM25 + Qdrant (belum Neo4j)
- Sensor: arXiv + Wikipedia fetcher (initiative.py)
- Self-evolving: corpus_to_training.py → manual Kaggle upload

### Tahap 1 — 4-9 Bulan (DIKW Layers 1-3 aktif)
- Knowledge layer: tambah kuzu/Neo4j untuk graph
- Flywheel: semi-otomatis (trigger setelah N interaksi)
- Contradiction detection: pertama kali aktif
- Sensor: tambah GitHub trending
- SPIN: otomatis setiap minggu

### Tahap 2 — 10-18 Bulan (DIKW Layers 1-4 + P2P)
- Wisdom layer: Self-Rewarding + Constitutional AI
- Flywheel: fully automated di multi-node
- node_id_ipfs: aktif untuk P2P knowledge sharing
- World Sensor: semua 7 sensor aktif
- Self-evolving loop: fully autonomous

---

## Kesimpulan — SIDIX Bukan Sekadar Model

> "SIDIX bukan sekadar model AI yang dilatih sekali lalu dipakai. SIDIX adalah **sistem epistemik hidup** yang terus belajar dari dunia, membangun pemahaman berlapis (DIKW), dan mengukur dirinya sendiri. Setiap interaksi adalah pupuk, setiap benchmark adalah cermin, setiap domain baru adalah perluasan wilayah."

**Yang membedakan SIDIX:**
1. **Bukan one-shot training** — flywheel terus berputar
2. **Bukan black-box** — setiap knowledge node punya sanad
3. **Bukan statis** — 52 domain × 7-stage pipeline × self-evolving loop
4. **Bukan bergantung satu lab** — dirancang untuk P2P dari awal

---

*Source: SIDIX Growth Manifesto + DIKW Knowledge Cycle Diagram + Autonomous Learning Pipeline Diagram*
*Ditulis oleh Fahmi Ghani, April 2026*
*Dikonversi menjadi arsitektur sistem dan logika implementasi SIDIX*
