# Research Note 44 — Blueprint LLM Indonesia-Arab-Code: Strategi Corpus, Arsitektur & Pipeline

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Sumber**: Blueprint LLM Indonesia-Arab-Code: Dari Corpus hingga Outperform GPT-4 (Compass, 2026)
> **Relevance untuk SIDIX**: Tinggi — roadmap membangun LLM trilingual + Islamic knowledge depth
> **Tags**: llm, corpus, pretraining, indonesian, arabic, trilingual, moe, grpo, benchmark, dataset

---

## 1. Bottom Line — Mengapa Ini Relevan untuk SIDIX

**Gap kritis yang belum diisi siapapun**:
1. Tidak ada model ≥70B native-Indonesian
2. Tidak ada model dengan reasoning chain-of-thought native Bahasa Indonesia (model sekarang "beralih ke English" saat berpikir)
3. Tidak ada model dengan integrasi mendalam Qur'an/Tajwid/Arud/Fiqih
4. Tidak ada tri-lingual model (ID+AR+EN) yang menguasai ketiganya simultan

**North-star metric** target outperform GPT-4:
- MMLU ≥ 88, MMLU-Pro ≥ 78, MATH ≥ 85, HumanEval ≥ 92
- IndoMMLU ≥ 80, ArabicMMLU ≥ 78, Arena Elo ≥ 1280

---

## 2. Domain 1 — Bahasa Indonesia: Linguistik & Corpus

### 2.1 Struktur Morfologi (Aglutinatif)

Bahasa Indonesia adalah bahasa **aglutinatif** — kata terbentuk dari awalan/akhiran/konfiks produktif:

| Kategori | Contoh |
|---|---|
| **Prefiks** | me(N)-, di-, ber-, ter-, pe(N)-, ke-, se-, memper-, diper- |
| **Sufiks** | -kan, -i, -an, -nya, -lah, -kah, -pun |
| **Konfiks** | ke-an, pe(N)-an, per-an, ber-an, se-nya |
| **Alomorf nasal meN-** | me-, mem-, men-, meny-, meng-, menge- |

**Sintaksis**: dominan SVO + pasif tipe-1 (`di-`) + pasif tipe-2 (pronomina + verba dasar). LLM harus menyeimbangkan kedua konstruksi.

**Kosakata serapan multi-sumber**:
- Sansekerta: cakra, guru, manusia, bahasa
- Arab: majelis, syariat, kitab, adab
- Belanda: kantor, sepeda, apotek, rekening
- Portugis: mentega, jendela, meja
- Inggris modern: komputer, unduh, unggah

### 2.2 Empat Register yang Wajib Ada di Corpus

| Register | Sumber | Ciri |
|---|---|---|
| **Formal baku** | Peraturan, jurnal, Tempo/Kompas editorial | EYD V penuh |
| **Semiformal** | Artikel populer, opini | Setengah formal |
| **Kolokial Jakarta** | Twitter/Reddit Indonesia | gue/lo/nggak/banget |
| **Bahasa daerah + code-mixing** | Jawa ngoko/krama, Sunda, Minang, Bali | Campur |

> **Tanpa keempatnya**, model gagal di NusaX dan menghasilkan Bahasa Indonesia "terjemahan Google".

### 2.3 Dataset Bahasa Indonesia — Katalog Siap Pakai

| Dataset | Ukuran | HF ID | Lisensi | Kualitas |
|---|---|---|---|---|
| **FineWeb-2 Indonesian** | ~30 B token | `HuggingFaceFW/fineweb-2` (ind_Latn) | ODC-BY | ⭐⭐⭐⭐⭐ |
| **CulturaX Indonesian** | ~23 B token | `uonlp/CulturaX` | ODC-BY | ⭐⭐⭐⭐ |
| **Wikipedia ID** | ~1.3 GB | dumps.wikimedia.org/idwiki | CC-BY-SA | ⭐⭐⭐⭐⭐ |
| **NusaCrowd** | ~100 dataset SEA | `indonlp/nusacatalogue` | Mixed | ⭐⭐⭐⭐⭐ |
| **NusaX** | 10 bahasa daerah | `indonlp/NusaX-senti` | CC-BY-SA | ⭐⭐⭐⭐⭐ |
| **Cendol collection v2** | ~12 B token | `indonlp/cendol_collection_v2` | Apache-2.0 | ⭐⭐⭐⭐⭐ |
| **IndoMMLU** | 14.981 soal | `indolem/IndoMMLU` | MIT | ⭐⭐⭐⭐⭐ |
| **SEACrowd** | ~500 dataset SEA | `SEACrowd/seacrowd-catalogue` | Mixed | ⭐⭐⭐⭐⭐ |
| **COPAL-ID** | 559 soal | `haryoa/COPAL-ID` | CC-BY-SA | ⭐⭐⭐⭐⭐ |
| **mC4 Indonesian** | ~180 GB | `allenai/c4` (id) | ODC-BY | ⭐⭐⭐ (perlu re-filter) |

### 2.4 Gap Analysis & Solusi

Volume corpus ID bersih (≈50–100 B token) masih ~30× lebih kecil dari English (≈3–5 T token bersih).

**Strategi overcomes**:
1. **Synthetic data** — translasi + instruction generation dari English dengan GPT-4/Claude sebagai teacher
2. **Cross-lingual transfer** — English-Indonesian parallel + multilingual pretraining
3. **Domain scraping** — Garuda/SINTA (akademik), JDIH (hukum), Kemenkes (medis), NU Online/Muhammadiyah (keagamaan)

---

## 3. Domain 2 — Bahasa Arab: Tajwid, Arud, Nahwu

### 3.1 Tajwid — Knowledge Graph Terenkode

**Makharijul Huruf (17 titik)**:

| Makhraj | Huruf | Jumlah |
|---|---|---|
| Jauf (rongga mulut) | أ و ي (mad) | 1 makhraj |
| Halq (tenggorokan) | ء ه ع ح غ خ | 3 makhraj |
| Lisan (lidah) | | 10 makhraj |
| Syafatain (dua bibir) | ب م و ف | 2 makhraj |
| Khaisyum (rongga hidung) | غنة | 1 makhraj |

**Hukum Nun Sukun/Tanwin**:

| Hukum | Huruf | Penjelasan |
|---|---|---|
| **Izhar halqi** | ء ه ع ح غ خ | Jelas tanpa dengung |
| **Idgham bighunnah** | ي ن م و | Masuk dengan dengung |
| **Idgham bilaghunnah** | ل ر | Masuk tanpa dengung |
| **Iqlab** | ب | Berubah jadi mim |
| **Ikhfa** | 15 huruf sisanya | Samar dengan dengung |

**Hukum Mad (pembagian)**:
- Mad thabi'i: 2 harakat
- Mad wajib muttashil: 4–5 harakat
- Mad jaiz munfashil: 2/4/5 harakat
- Mad lazim kilmi: 6 harakat
- Mad 'arid lissukun: 2/4/6 harakat

**Sumber primer untuk corpus**:
- Matn al-Jazariyyah (Ibn al-Jazari)
- Al-Burhan fi Tajwid al-Qur'an
- Hidayat al-Mustafid
- Shatibiyyah (qira'at)

### 3.2 Ilmu Arud — 16 Bahr Prosodi Arab

| Bahr | Taf'ilat | Pola |
|---|---|---|
| **Thawil** | فعولن مفاعيلن | ×2 hemistich |
| **Basit** | مستفعلن فاعلن | ×2 |
| **Wafir** | مفاعلتن | ×3 +قطع |
| **Kamil** | متفاعلن | ×3 ×2 |
| **Hazaj** | مفاعيلن | ×2 ×2 |
| **Rajaz** | مستفعلن | ×3 ×2 |
| **Ramal** | فاعلاتن | ×3 ×2 |
| **Mutaqarib** | فعولن | ×4 ×2 |
| **Mutadarik** | فاعلن | ×4 ×2 |

**Konsep kunci**: kitabah arudhiyah, taqthi', zihaf (perubahan ringan), illat (perubahan berat).

**Sumber corpus**:
- Al-Kafi fi al-'Arud wa al-Qawafi (al-Khatib al-Tabrizi)
- Mizan al-Dhahab (Ahmad al-Hashimi)

### 3.3 Nahwu-Sharaf — Struktur Minimum

**Tiga kategori kata**: isim, fi'il, harf.

**I'rab 4 jenis**: rafa', nashab, jarr, jazm — dengan tanda ashl dan far'iyah (alif, wawu, ya, tsubut-nun, kasrah, fathah, hadzf).

**Sumber wajib**: Al-Ajurrumiyyah, Alfiyyah Ibn Malik + syarh Ibn 'Aqil, Qatr al-Nada — tersedia di OpenITI.

### 3.4 Dataset Arab — Katalog

| Dataset | Ukuran | Link | Lisensi |
|---|---|---|---|
| **FineWeb-2 Arabic** | ~150 B token | `HuggingFaceFW/fineweb-2` (arb_Arab) | ODC-BY |
| **CulturaX Arabic** | ~59 B token | `uonlp/CulturaX` (ar) | ODC-BY |
| **OpenITI** | ~1.8 B kata klasik | openiti.org | CC-BY-NC-SA |
| **Tanzil.net Quran** | 77K ayat | tanzil.net | CC-BY |
| **Quranic Arabic Corpus** | 77K ayat + morphology | corpus.quran.com | GPL |
| **Tashkeela** | 75 M kata berharakat | sourceforge/tashkeela | GPL |
| **Arabic Wikipedia** | ~1.3 B kata | arwiki dumps | CC-BY-SA |
| **ArabicMMLU** | 14.575 soal | `MBZUAI/ArabicMMLU` | CC-BY-NC |
| **Hadith Kutub al-Sittah** | ~60K hadits | sunnah.com API | Free |
| **Tafsir (multi-mufassir)** | multi-kitab | altafsir.com | Fair use |

**Rekomendasi sub-mix Arab (12–18% total tokens)**:
- 40% MSA web (FineWeb-2)
- 20% turats klasik (OpenITI + Shamela)
- 15% Qur'an + Tafsir + Hadits
- 15% dialek (MADAR + ArTweet)
- 10% Wikipedia + akademik

> **Tashkeela wajib** untuk mengajarkan harakat — kunci pemahaman tajwid dan arud.

---

## 4. Domain 3 — Coding & Matematika

### 4.1 Dataset Coding Tier-1

| Dataset | Token | HF ID | Lisensi |
|---|---|---|---|
| **The Stack v2** | 900B+ (600+ lang) | `bigcode/the-stack-v2` | Permissive |
| **StarCoder training** | 1T | `bigcode/starcoderdata` | Permissive |
| **OpenCoder data** | 2.5T / 4.5M SFT | `OpenCoder-LLM/*` | Apache-2.0 |
| **Magicoder OSS-Instruct** | 75K | `ise-uiuc/Magicoder-OSS-Instruct-75K` | MIT |
| **Code-Feedback** | 68K | `m-a-p/Code-Feedback` | Apache-2.0 |
| **HumanEval / HumanEval+** | 164 | `openai/openai_humaneval` | MIT |
| **APPS** | 10K | `codeparrot/apps` | MIT |
| **LiveCodeBench** | rolling | `livecodebench/*` | MIT |

### 4.2 Dataset Matematika

| Dataset | Size | HF ID | Lisensi |
|---|---|---|---|
| **OpenWebMath** | 14.7B token | `open-web-math/open-web-math` | ODC-BY |
| **MathPile** | 9.5B token | `GAIR/MathPile` | CC-BY-NC-SA |
| **Proof-Pile 2** | 55B token | `EleutherAI/proof-pile-2` | Mixed |
| **MetaMathQA** | 395K | `meta-math/MetaMathQA` | MIT |
| **NuminaMath CoT/TIR** | 860K/73K | `AI-MO/NuminaMath-CoT` | Apache-2.0 |
| **MATH** | 12.5K | `hendrycks/competition_math` | MIT |
| **AIME 2024/25** | 30/30 | komunitas | Fair use |

### 4.3 Knowledge Checklist — Topik Wajib

**Struktur data**: array dinamis, linked list (single/double/circular), stack/queue, hash table, binary heap, BST, AVL, Red-Black, B-tree, Trie, suffix tree, segment tree, Fenwick/BIT, DSU (path compression + union by rank), bloom filter.

**Algoritma**: sorting (bubble→Timsort), searching, BFS/DFS, Dijkstra/Bellman-Ford/Floyd-Warshall, MST (Kruskal/Prim), topological sort, SCC (Tarjan/Kosaraju), network flow (Dinic), string matching (KMP, Z, Aho-Corasick), DP klasik, computational geometry (convex hull), NTT/FFT, Miller-Rabin.

**Matematika AI/ML** yang harus eksplisit di corpus:
- Backpropagation: derivasi loss → hidden gradients via chain rule
- Attention: `Attention(Q,K,V) = softmax(QK^T/√d_k)V`
- DPO loss: `-log σ(β log(π_θ(y_w|x)/π_ref(y_w|x)) - β log(π_θ(y_l|x)/π_ref(y_l|x)))`
- GRPO: group relative policy optimization (DeepSeek-R1 style)
- Quantization: INT8/NF4/AWQ/GPTQ
- MoE routing: top-k, expert-choice, load balancing loss

**Mixing ratio code+math SOTA**: 20% code, 8% math (lebih tinggi dari Llama 3.1's 17%+4% karena reasoning transfer ke ID/AR).

---

## 5. Arsitektur & Training Pipeline

### 5.1 Perbandingan Arsitektur SOTA

| Model | Params | Aktif | Layers | d_model | Vocab | Notes |
|---|---|---|---|---|---|---|
| Llama 3.1 70B | 70B dense | 70B | 80 | 8192 | 128K | GQA |
| DeepSeek-V3 | 671B | 37B | 61 | 7168 | 129K | MLA + 256 routed experts |
| Qwen2.5-72B | 72B dense | 72B | 80 | 8192 | 152K | GQA |
| Mixtral 8×22B | 141B | 39B | 56 | 6144 | 32K | top-2 MoE |

**Rekomendasi SIDIX-scale**: MoE fine-grained 200–400B total / 25–40B aktif:
- 80–100 layers, d_model 6144–8192
- **MLA** (Multi-head Latent Attention) — kompresi KV-cache
- **RoPE + YaRN** → 256K context
- **SwiGLU** FFN, **RMSNorm Pre-LN**
- Vocab **160K** (ID+AR+EN optimal fertility: ~1.5 tok/kata vs GPT-4 cl100k ~2.3 untuk Arab — buruk)
- Shared expert + 192 routed experts top-8

### 5.2 Tokenizer

**SentencePiece BPE byte-fallback** atau tiktoken-style byte-level BPE. Vocab 160K:
- Fertility Indonesian ~1.5 tok/kata ✓
- Fertility Arabic ~1.4 tok/kata ✓
- GPT-4 cl100k untuk Arab: ~2.3 tok/kata ✗ (sangat tidak efisien)

Train pada 50GB campuran: 10GB ID + 10GB AR + 20GB EN + 5GB code + 5GB math.
Normalisasi: **NFKC** untuk Arab (presentation forms), **NFC** untuk Indonesia.

### 5.3 Data Mixing Ratio — 15T Token Target

| Domain | % | Tokens (T) | Sumber Utama |
|---|---|---|---|
| English web high-quality | 32% | 4.8 | FineWeb-Edu, DCLM-Baseline |
| Indonesian (all register) | 10% | 1.5 | FineWeb-2 id + CulturaX id + NusaCrowd |
| Arabic (MSA+klasik+dialek) | 10% | 1.5 | FineWeb-2 ar + OpenITI + Shamela + Quran |
| Code | 17% | 2.55 | The Stack v2 + CommitPack + StackEx |
| Math | 6% | 0.9 | OpenWebMath + MathPile + Proof-Pile 2 |
| Multilingual 20 lang | 6% | 0.9 | FineWeb-2 (zh, ja, ko, hi, es, fr, ...) |
| Academic/scientific (en) | 5% | 0.75 | arxiv, PubMed, S2ORC, textbooks |
| Books & literature | 3% | 0.45 | Public domain + translated classics |
| Reference (Wiki all) | 1% | 0.15 | Wikipedia dumps |

**Annealing phase (1.5T terakhir)**: ID naik ke 18%, AR ke 15%, math ke 12%, code ke 20%, synthetic reasoning 8%.

### 5.4 Training Pipeline End-to-End

```
RAW ACQUISITION
  → LANGUAGE ID (fasttext lid.176)
  → QUALITY FILTER (Gopher rules + FineWeb-Edu classifier + KenLM perplexity)
  → DEDUPLICATION (SHA-256 + MinHash LSH Jaccard 0.85)
  → PII + SAFETY SCRUB (regex + Presidio)
  → DOMAIN MIXING (DoReMi/RegMix optimization)
  → TOKENIZATION (SentencePiece BPE 160K → 2GB shards)
  → PRETRAINING (14–18T tokens, BF16+FP8, AdamW, cosine LR)
  → MID-TRAINING/ANNEALING (~500B tok, upsample high-quality)
  → SFT (ChatML, 3 epochs, LR 5e-6)
  → REJECTION SAMPLING → DPO/ORPO (β=0.1)
  → GRPO RL (verifiable rewards: math/code exact match)
  → EVALUATION GATE (IndoMMLU, ArabicMMLU, MATH, HumanEval, Arena Elo)
  → QUANTIZATION + SERVING (vLLM/SGLang)
```

### 5.5 Alignment Stack: Rekomendasi

**Stack terbaik**: SFT → Rejection Sampling → DPO 2 round → GRPO (reasoning math/code) → eval.

| Method | Compute | Quality | Notes |
|---|---|---|---|
| SFT only | 1× | Baseline | Tidak cukup untuk SOTA |
| DPO | 2× | Tinggi | Preferensi pair, tanpa RM |
| ORPO | 1.2× | Menengah-tinggi | SFT+align dalam 1 fase |
| GRPO | 3–4× | **Sangat tinggi** (reasoning) | Verifiable reward — ResDeepSeek-R1 |

> **Insight kritis**: GRPO pada problem Bahasa Indonesia/Arab (IndoMMLU/ArabicMMLU augmented) adalah cara paling langsung menaikkan IndoMMLU > 80 — **belum pernah dicoba publik**.

---

## 6. Landscape LLM Indonesia & Diferensiasi

### 6.1 Ekosistem Saat Ini (April 2026)

**Lapis akademik**: Cendol (IndoNLP, 560M–13B, Apache-2.0), IndoBERT/IndoBART.

**Lapis komersial domestik**: SahabatAI (Indosat+GoTo, Llama 3.1/Gemma 2 base, IndoMMLU ~68); Merak (komunitas, 7B–13B); Komodo (Yellow.ai 7B).

**Lapis regional SEA**: SEA-LION v3 (AI Singapore, 9B), Sailor2 (Sea AI Lab, 0.5–20B), SeaLLMs v3 (Alibaba), Aya Expanse (Cohere 8B/32B).

**Gap**: Semua di bawah 30B aktif. Tidak ada yang melampaui GPT-4o pada IndoMMLU.

### 6.2 White Space yang Belum Diisi Siapapun

1. **Tri-lingual native** ID-AR-EN dengan fertility tokenizer optimal ketiganya
2. **Reasoning-first (GRPO + long CoT)** dengan chain-of-thought native ID/AR
3. **Islamic knowledge depth** — Qur'an/Tafsir/Hadits/Tajwid/Arud/Fiqih dengan citation benar (OpenITI+Shamela)
4. **Nusantara languages** — 10+ bahasa daerah setara Jawa
5. **Long-context 128K stable** untuk dokumen hukum/akademik
6. **Code+math dalam Bahasa Indonesia** — tutorial, error message, komentar native ID

---

## 7. Benchmark Targets — "Sudah Outperform GPT-4"

| Benchmark | GPT-4 | Target LLM baru |
|---|---|---|
| MMLU (5-shot) | ~86–88 | **≥ 88** |
| MATH | ~76 | **≥ 85** |
| HumanEval | ~92 | **≥ 92** |
| **IndoMMLU** | ~74 (GPT-4o) | **≥ 80** |
| SEA-HELM avg | ~65 | **≥ 75** |
| COPAL-ID | ~78 | **≥ 85** |
| **ArabicMMLU** | ~72 | **≥ 78** |
| AIME 2025 | ~15 | **≥ 55** |

**North-star**: capai **Arena Hard ≥ 75 + IndoMMLU ≥ 80 + ArabicMMLU ≥ 78 + HumanEval ≥ 92 + MATH ≥ 85** simultan — tidak ada model saat ini yang memegang kelima sekaligus.

---

## 8. Implikasi untuk SIDIX (Immediate Actions)

### Corpus Enrichment
- Integrasikan FineWeb-2 Indonesian + CulturaX ID ke corpus SIDIX
- Tambah NusaCrowd meta-catalog untuk coverage bahasa daerah
- Tambah Qur'an (Tanzil) + OpenITI subset ke brain/public/

### Knowledge Architecture
- Tajwid knowledge graph dapat diimplementasikan sebagai structured corpus → SIDIX menjawab pertanyaan tajwid dengan akurat
- Ilmu Arud (16 bahr) dapat menjadi fine-tuned task: input syair → identifikasi bahr + taf'ilat
- Nahwu-Sharaf dari Alfiyyah Ibn Malik = referensi grammar Arabic untuk parser

### Reasoning Enhancement
- Gunakan MetaMathQA + NuminaMath untuk strengthening reasoning ID/AR
- Synthetic data: translate MATH problems ke Bahasa Indonesia → training reasoning native ID
- GRPO verifiable reward untuk math/code dalam ID/AR — novel contribution

### Differentiation SIDIX
- SIDIX bisa menjadi **pertama** yang bisa menjelaskan Tajwid + melakukan taqthi' arud + menjawab fiqih dalam satu model
- Corpus trilingual dengan Islamic knowledge depth = moat kultural yang tidak bisa ditiru frontier model Barat

---

*Research Note 44 | SIDIX Knowledge Corpus | Sumber: Blueprint LLM Indonesia-Arab-Code (Compass, 2026)*
