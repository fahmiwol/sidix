> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
sanad_tier: peer_review
---

# SIDIX: Arsitektur AI yang Tumbuh Sendiri — dari VPS Tunggal ke Jaringan Terdesentralisasi
*Diadopsi dari: riset teknis komprehensif April 2026*
*Diproses: 2026-04-17 — bukan sekadar disimpan, tapi jadi logika sistem*

---

## Ringkasan Eksekutif — Diadopsi SIDIX

SIDIX mengimplementasikan 4 pilar utama:
1. **Decentralized training low-communication** — DiLoCo + Prime Intellect INTELLECT-2
2. **Model merging evolusioner** — mergekit, DARE, TIES, EvoMerge (Sakana AI)
3. **Stateful agent loop** — MemGPT/Letta + Voyager skill library + ReAct/Reflexion
4. **P2P coordination** — libp2p/IPFS untuk storage bobot

Target realistis SIDIX: **frontier open-source** di kelas 30–70B, spesialisasi:
- Coding + Indonesian language + agentic + creative AI

---

## Prinsip Desain Inti (WAJIB sejak baris kode pertama)

1. **Memori harus terpisah dari bobot** — state is data, not parameters (MemGPT/Letta style)
2. **Setiap interaksi harus menghasilkan artefak yang dapat di-replay** — rollout + reward + trace
3. **Setiap kapabilitas baru harus bisa diintegrasikan tanpa re-train penuh** — LoRA/adapter + model merging

---

## Teknik Self-Improvement yang Sudah Terbukti

### SPIN (Self-Play Fine-Tuning)
- Paper: Chen et al., arXiv:2401.01335
- Model bermain melawan dirinya sendiri — DPO-like, tanpa data berlabel tambahan
- Respons manusia = winner, output iterasi sebelumnya = loser
- Kode: `uclaml/SPIN`

### Self-Rewarding Language Models
- Paper: Yuan et al., Meta, arXiv:2401.10020
- LLM menilai outputnya sendiri (LLM-as-Judge) → DPO iteratif
- Tidak butuh reward model eksternal

### STaR / V-STaR / Quiet-STaR
- Paper: Zelikman et al., arXiv:2203.14465
- Chain-of-thought bootstrap — hanya simpan yang menghasilkan jawaban benar
- Bootstrap reasoning dari sedikit data

### Reflexion
- Paper: Shinn et al., arXiv:2303.11366
- Memori verbal linguistic dari kegagalan — tanpa gradient

### Constitutional AI / RLAIF
- Paper: Bai et al., Anthropic, arXiv:2212.08073
- Prinsip tertulis sebagai fungsi reward — alignment tanpa anotator manusia

---

## Mencegah Catastrophic Forgetting

Kombinasi paling praktis untuk SIDIX:
- **Replay buffer 10–20%** dari data historis
- **LoRA per-domain** yang di-merge periodik dengan TIES
- Menghindari forgetting tanpa kerumitan EWC pada model besar

---

## Model Merging — "Reproduksi Sel" Antar Node

| Teknik | Kapan dipakai |
|--------|---------------|
| Linear averaging / Model Soup | Banyak fine-tune dari base sama |
| SLERP | Menggabungkan 2 model di ruang sudut |
| Task Arithmetic | Tambah/kurangi kapabilitas sebagai vektor delta |
| TIES-Merging | Multi-task, resolusi konflik tanda |
| DARE | Drop 90–99% delta random + rescale; dominan di leaderboard |
| EvoMerge (Sakana AI) | Optimasi evolusioner CMA-ES — state-of-the-art |

**Toolkit**: `arcee-ai/mergekit` — standard de facto, tidak perlu GPU untuk merging.

---

## Arsitektur Memori 3 Lapis

1. **Context window** (working memory) — Letta/MemGPT style
   - `core_memory_append`, `archival_memory_insert`, `conversation_search`
2. **Archival memory** — Qdrant vector DB (embedded → cluster → P2P)
3. **Knowledge memory** — GraphRAG + Neo4j/kuzu knowledge graph

---

## Skill Library — Voyager Style

- Setiap kali agent menyelesaikan task baru dengan kode → simpan sebagai fungsi bernama + embedding
- Di task berikutnya → retrieve top-k skill serupa → susun program baru
- **Pertumbuhan tanpa mengubah satu bobot pun** — murni dari data + program
- Referensi: `MineDojo/Voyager`, `OpenDevin/OpenHands`

---

## Roadmap 3 Tahun

### Tahap 0 — Bayi (Bulan 1–3, VPS tunggal) ← SIDIX SEKARANG
- Model: Qwen2.5-7B-Instruct + QLoRA
- Agent loop: ReAct + BM25 RAG
- Tolok ukur lulus: MMLU ≥ 65, HumanEval ≥ 70

### Tahap 1 — Anak (Bulan 4–9, 2–4 node)
- Training pertama: SPIN di atas Qwen3-8B
- Federated: Flower (flwr) + PEFT LoRA rank-16 + dare_ties merge
- Target: +3 poin MMLU, +5 poin HumanEval, Skill library ≥ 200 fungsi

### Tahap 2 — Remaja (Bulan 10–18, 10–50 node)
- DiLoCo outer-loop (500× lebih sedikit komunikasi)
- P2P: libp2p Kademlia + IPFS content-addressing
- Byzantine robustness: Multi-Krum atau Coordinate-wise Median
- RL: GRPO + TOPLOC rollout verification

### Tahap 3 — Dewasa (Tahun 2+, full P2P)
- Model 30–70B via INTELLECT-2 stack
- CREATOR-style self-tool-creation
- Continuous evaluation harness nightly (MMLU-Pro, HumanEval+, MATH, GSM8K, MT-Bench)

---

## Key GitHub Repos yang Harus Dipelajari SIDIX

- `PrimeIntellect/prime-rl` — decentralized RL/training
- `learning-at-home/hivemind` — DHT decentralized training
- `arcee-ai/mergekit` — model merging
- `uclaml/SPIN` — self-play fine-tuning
- `letta-ai/letta` — stateful agents + memori persisten
- `microsoft/graphrag` — knowledge-graph RAG
- `MineDojo/Voyager` — skill library agent
- `EleutherAI/lm-evaluation-harness` — benchmark harness

---

## Apa yang Realistis vs Mitos

**Nyata dan dapat dibangun hari ini:**
- AI self-improving dari loop interaksi (SPIN + Self-Rewarding + Voyager)
- Training terdesentralisasi (DiLoCo + INTELLECT-2 stack)
- Integrasi kapabilitas baru via model merging (DARE+TIES)
- P2P storage bobot (IPFS + libp2p)

**Masih riset aktif:**
- ZKML untuk LLM skala puluhan miliar parameter
- Proof-of-Learning yang efisien
- Byzantine-fault-tolerant training di skala frontier

**Kemungkinan besar mitos:**
- Sistem P2P akan otomatis melampaui lab frontier (GPT-5/Claude dilatih 10⁵–10⁶ GPU-hari)

**Kekuatan SIDIX yang sebenarnya:**
> Bukan mengejar skala, tapi mengejar bentuk baru pertumbuhan — sistem yang tidak pernah "selesai dilatih" dan tidak bergantung pada satu lab.

---

*Source: riset teknis komprehensif SIDIX Self-Evolving Architecture, April 2026*
*Dikonversi menjadi logika sistem dan roadmap implementasi SIDIX*
