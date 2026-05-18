# 113 — Decentralized Data dengan Recall Memory SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** `decentralized` `memory` `fragment` `recall` `hafidz` `dikw` `merkle`  
**Tanggal:** 2026-04-18  
**Track:** O — Core AI Capabilities

---

## Apa

`decentralized_data.py` adalah sistem penyimpanan data terdistribusi terstruktur untuk SIDIX. Data tidak disimpan monolitik, tapi dipecah menjadi **fragment-fragment independen** yang:
- Bisa disimpan tersebar
- Bisa di-query secara semantik
- Bisa di-assemble kembali menjadi pengetahuan koheren
- Terverifikasi integritasnya via content hash

---

## Mengapa Decentralized?

### Problem dengan Monolitik Storage

Bayangkan SIDIX menyimpan seluruh corpus-nya dalam satu file besar:
- Sulit di-query secara selektif
- Update satu bagian → harus baca seluruh file
- Tidak ada granularitas — tidak bisa tahu "mana bagian yang sering diakses?"
- Jika corrupt → semua hilang

### Solusi: Fragment-Based Storage

Terinspirasi dari:

1. **Hafidz Framework** (Research note 22): Para hafidz Al-Quran adalah "node" dalam distributed network. Jika satu hafidz hilang, ribuan lain menyimpan kopian yang sama. Knowledge tidak pernah hilang.

2. **Erasure Coding**: Data dipecah menjadi N fragment, hanya butuh K < N fragment untuk merekonstruksi. Ini dipakai di RAID, cloud storage (AWS, Google).

3. **Merkle Tree**: Setiap fragment punya content hash. Assembly dari fragment-fragment menghasilkan root hash yang bisa diverifikasi.

4. **DIKW Pyramid**: Fragment diklasifikasikan berdasarkan level epistemic (Data → Information → Knowledge → Wisdom).

---

## Arsitektur

### Storage Layout

```
.data/decentralized/
├── index.json               ← Master index semua fragment
└── fragments/
    ├── frag_abc123def456.json
    ├── frag_789xyz012ghi.json
    └── ...
```

### Fragment Structure

```python
@dataclass
class Fragment:
    fragment_id: str      # "frag_" + SHA256[:16] dari content
    content: str          # Konten teks aktual
    tags: list[str]       # Tags untuk indexing
    source: str           # Asal: URL, file path, "manual"
    dikw_level: str       # "data" | "information" | "knowledge" | "wisdom"
    created_at: str       # ISO timestamp
    accessed_at: str      # Terakhir diakses
    access_count: int     # Berapa kali diakses
    content_hash: str     # SHA256 penuh untuk integrity check
    metadata: dict        # Extra: author, date, dsb
```

### Content-Addressable

Fragment ID = `frag_` + SHA256(content)[:16]

Ini berarti:
- **Otomatis deduplicate** — simpan konten yang sama dua kali? ID sama, tidak disimpan dua kali
- **Integrity verifiable** — kapan saja bisa cek apakah content berubah
- **Distributed-friendly** — dua node yang simpan fragment yang sama akan setuju pada ID

---

## DIKW Pyramid dalam Fragment Classification

```
Wisdom    ← Insight lintas domain, kesimpulan tinggi level
Knowledge ← Konsep, penjelasan, "mengapa"
Information ← Fakta, data yang dicontekstualisasikan
Data      ← Raw data, angka, quotes tanpa konteks
```

Pada saat `recall()`, fragment dengan level `knowledge` dan `wisdom` mendapat bonus score karena lebih informatif untuk reasoning.

---

## Recall System

### Algoritma

```python
def recall(self, query: str, top_k: int = 5) -> list[dict]:
    query_terms = self._tokenize(query)  # Remove stopwords, lowercase
    
    for fragment in all_fragments:
        keyword_rel = fragment.keyword_score(query_terms)  # BM25-simplified
        tag_bonus = min(0.3, tag_matches * 0.1)           # Tag exact match bonus
        dikw_bonus = dikw_weight[fragment.dikw_level]     # Knowledge > Information
        
        total = min(1.0, keyword_rel + tag_bonus + dikw_bonus)
        if total >= 0.1:  # MIN_RELEVANCE_THRESHOLD
            results.append({"fragment": fragment, "relevance": total})
    
    return sorted(results, key=lambda x: x["relevance"], reverse=True)[:top_k]
```

**BM25-simplified** dalam `keyword_score()`:
- Term frequency dalam content: +0.5 per hit
- Exact match dalam tags: +1.5 per hit  
- Normalisasi dengan log(word_count) — tidak bias ke teks panjang

---

## Assembly

```python
def assemble(self, fragment_ids: list, separator="\n\n---\n\n") -> str:
    """Rekonstruksi pengetahuan dari fragment-fragment."""
    parts = []
    for fid in fragment_ids:
        fragment = load(fid)
        header = f"[{fragment.dikw_level.upper()} | {fragment.source}]"
        parts.append(f"{header}\n{fragment.content}")
    return separator.join(parts)
```

**Contoh output assembly:**

```
[KNOWLEDGE | research_notes/107_fisika.md]
Hukum Newton I (Inersia): benda diam tetap diam kecuali ada gaya luar.
Dalam bisnis: perusahaan established sulit berubah tanpa disrupsi.

---

[INFORMATION | quran_tafsir.json]
"Sesungguhnya Allah tidak akan mengubah keadaan suatu kaum..."
(QS Ar-Ra'd: 11)

---

[KNOWLEDGE | experience_engine.db]
Kasus: Startup X yang stuck 2 tahun — berhasil pivot setelah investor baru masuk.
```

---

## Memory Map

```python
memory_map = store.get_memory_map()
# {
#   "total_fragments": 847,
#   "dikw_distribution": {"data": 120, "information": 412, "knowledge": 298, "wisdom": 17},
#   "top_tags": [{"tag": "quran", "count": 156}, {"tag": "hadits", "count": 134}, ...],
#   "most_accessed": [...],
#   "integrity_check": {"checked": 10, "intact": 10, "integrity_rate": 1.0}
# }
```

---

## Integrity Check (Merkle-inspired)

```python
def _verify_integrity(self, fragments: list) -> dict:
    for fragment in fragments:
        expected = hashlib.sha256(fragment.content.encode()).hexdigest()
        if expected != fragment.content_hash:
            corrupted.append(fragment.fragment_id)
```

Jika content berubah (disk corruption, manual edit yang tidak sengaja) → terdeteksi.

Dalam distributed deployment: setiap node bisa cross-check hash dengan node lain.

---

## Chunking untuk Teks Panjang

```python
fragment_ids = store.store_text_chunked(
    text=long_document,
    source="docs/quran_tafsir.md",
    base_tags=["quran", "tafsir", "ibnu_katsir"],
    chunk_size=500,    # ~500 karakter per chunk
    overlap=50         # 50 karakter overlap untuk konteks
)
# → ["frag_abc", "frag_def", "frag_ghi", ...]
```

**Mengapa overlap?** Agar kalimat yang terpotong di batas chunk tetap ada konteksnya di kedua chunk. Ini mencegah recall yang salah karena kalimat terpotong.

---

## Prune — Satu-Satunya Cara Hapus

```python
removed = store.prune(min_relevance=0.3)
```

Prune menggunakan composite score:
```python
composite = access_score * 0.6 + size_score * 0.4
```

Filosofinya: **fragment yang tidak pernah diakses DAN pendek** → kemungkinan tidak berguna. Tapi fragment yang panjang meski jarang diakses tetap disimpan (mungkin reference penting).

---

## Contoh Nyata: SIDIX Menyimpan & Recall

### Store

```python
store = DecentralizedData()

# Simpan riset note baru
fid = store.store_fragment(
    content="Hukum Newton I: benda diam tetap diam kecuali ada gaya luar...",
    tags=["fisika", "newton", "mental-model", "inersia"],
    source="research_notes/107",
    dikw_level="knowledge"
)

# Simpan teks panjang (buku)
ids = store.store_text_chunked(
    text=open("ihya_ulumuddin.txt").read(),
    source="al-ghazali/ihya",
    base_tags=["ghazali", "ihya", "sufisme", "akhlak"],
    chunk_size=400
)
```

### Recall

```python
results = store.recall("bagaimana mengubah kebiasaan buruk?", top_k=5)
# Fragment 1: relevance 0.72 — Newton I (inersia kebiasaan)
# Fragment 2: relevance 0.65 — Ihya Ulumuddin tentang riyadhah
# Fragment 3: relevance 0.54 — Pengalaman user sebelumnya tentang kebiasaan

# Assemble
knowledge = store.assemble([r["fragment_id"] for r in results])
# → Assembled text dari 5 fragment paling relevan
```

---

## Integrasi dengan Modul Lain

```python
# Di problem_solver.py — recall masalah serupa
similar = decentralized_store.recall(problem, top_k=3)

# Di permanent_learning.py — simpan hasil self-play ke memory
store.store_fragment(
    content=f"Self-play result: skill '{skill}' meningkat {delta} setelah challenge edge_case",
    tags=["self-play", skill, "learning-event"],
    source="permanent_learning",
    dikw_level="information"
)
```

---

## Keterbatasan

1. **Keyword-based recall** — tidak semantic, bisa miss sinonim dan paraphrase
2. **Single-node storage** — fragment di `.data/decentralized/`, belum benar-benar distributed
3. **No embedding index** — tidak ada vector search, hanya BM25-simplified
4. **JSON files** — tidak scalable untuk > 100k fragments
5. **Assembly naif** — tidak ada re-ranking atau coherence check setelah assembly

---

## Next Steps

- [ ] Tambahkan embedding-based recall (menggunakan model lokal)
- [ ] Migrate storage ke SQLite untuk performa lebih baik
- [ ] Implement replication: sync fragment ke Supabase untuk true distribution
- [ ] Tambahkan `assemble_with_coherence()` yang re-rank fragments setelah assembly
- [ ] REST endpoint: `POST /memory/store`, `GET /memory/recall`, `GET /memory/map`

---

## Referensi

- Research note 22: Hafidz Framework — Distributed Knowledge Architecture
- Research note 23: Data Token + Storage Ops MVP
- DIKW Pyramid: Rowley (2007) — "The wisdom hierarchy: representations of the DIKW hierarchy"
- Merkle, *A Digital Signature Based on a Conventional Encryption Function* (1988)
- BM25: Robertson & Spärck Jones (1976) — Term weighting for information retrieval
