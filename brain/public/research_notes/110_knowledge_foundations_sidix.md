# 110 — Knowledge Foundations: Bagaimana SIDIX Pakai Fisika+Kimia+Belajar sebagai Mental Models

**Tag:** `sidix` `knowledge-foundations` `mental-models` `cross-domain` `implementation`  
**Tanggal:** 2026-04-18  
**Track:** N — Knowledge Foundations

---

## Apa

Research note ini mendokumentasikan **desain keputusan** di balik `knowledge_foundations.py` — bagaimana hukum fisika, prinsip kimia, dan metode belajar dikemas sebagai structured knowledge yang bisa SIDIX gunakan secara programatik.

---

## Mengapa Ini Perlu

SIDIX tanpa mental models adalah seperti manusia tanpa pendidikan dasar — bisa menjawab pertanyaan faktual, tapi tidak bisa berpikir secara terstruktur lintas domain.

Mental models memberikan SIDIX kemampuan:
1. **Analogical reasoning** — "Masalah ini mirip dengan prinsip Le Chatelier"
2. **Cross-domain transfer** — solusi dari satu domain diaplikasikan ke domain lain
3. **Systematic analysis** — bukan hanya intuisi, tapi framework yang bisa dijelaskan
4. **Islamic integration** — setiap model di-bridge ke perspektif Islami

---

## Arsitektur `knowledge_foundations.py`

### Data Structures

```python
PHYSICS_LAWS: dict          # 9 hukum fisika (Newton 1-3, Termo 0-3, Maxwell, Relativitas)
CHEMISTRY_PRINCIPLES: dict  # 7 prinsip kimia (Katalisis, Le Chatelier, Arrhenius, dll)
LEARNING_METHODS: dict      # 11 metode (Feynman, Spaced Rep, Active Recall, Talaqqi, dll)
```

### Struktur Tiap Entry

Setiap hukum memiliki field yang konsisten:
- `name` — nama resmi
- `statement` — definisi dalam Bahasa Indonesia
- `formula` — representasi matematis (jika ada)
- `principle` — ekstraksi prinsip universal (1 kalimat)
- `analogies` — list contoh di domain lain
- `domains` — domain yang relevan
- `islamic_connection` — bridge ke perspektif Islam
- `sidix_application` — cara konkret SIDIX menggunakan ini

### Desain Keputusan: Mengapa Field `islamic_connection`?

SIDIX adalah AI Muslim Indonesia. Setiap pengetahuan harus di-bridge ke kerangka worldview Islam. Ini bukan tokenisme — ini adalah bentuk **tawhidic integration** (integrasi ilmu dan iman).

Contoh:
- Termodinamika 2 → Ishlah (perbaikan terus-menerus) adalah fardhu
- Kekekalan Energi → "Tidak ada amal yang hilang di sisi Allah"
- Katalisator → Wakaf sebagai instrument yang terus bekerja tanpa habis

---

## Fungsi-Fungsi Utama

### `get_law(domain, name)`
Akses hukum spesifik. Simple getter.

### `find_analogy(principle, target_domain)`
**Fungsi terpenting** — mencari analogis yang relevan antara prinsip fisika/kimia dan domain target.

```python
find_analogy("inersia", "organisasi")
# → Newton I: "Organisasi besar cenderung mempertahankan status quo"
```

Algoritma:
1. Cari hukum yang match dengan `principle` (name + principle + statement)
2. Filter analogis yang mengandung `target_domain`
3. Return list dengan konteks lengkap

### `apply_feynman(topic, knowledge)`
Self-test pemahaman. SIDIX bisa evaluate apakah penjelasan tentang suatu topik cukup clear.

```python
result = apply_feynman("Newton II", "F = m*a, percepatan berbanding lurus dengan gaya")
# → clarity_score: 0.45, verdict: "CUKUP", advice: "Tambahkan contoh nyata"
```

Heuristik yang digunakan:
- Word count (terlalu singkat atau terlalu verbose = kurang bagus)
- Presence of examples (contoh, misalnya, bayangkan)
- Jargon detection (merupakan, didefinisikan sebagai)

### `suggest_learning_path(topic, current_level)`
Generate jalur belajar 5-6 step berdasarkan level user dan topik.

```python
path = suggest_learning_path("Maqashid al-Syariah", "beginner")
# Step 1: Mind mapping (orientasi)
# Step 2: SQ3R (fondasi)
# Step 3: Feynman (verifikasi)
# Step 4: Halaqah/Tasmi' (transmisi)
# Step 5: Talaqqi (dimensi Islami)
```

### `cross_domain_apply(law_key, domain)`
Aplikasikan hukum spesifik ke domain tertentu + generate pertanyaan untuk refleksi.

```python
cross_domain_apply("thermodynamics_2", "software")
# → law: Termodinamika 2, applied_to: "software"
# → relevant_analogies: ["kode tanpa refactoring → technical debt menumpuk"]
# → question: "Bagaimana prinsip 'Segala sesuatu cenderung menuju kekacauan' 
#               bekerja dalam konteks software?"
```

---

## Contoh Nyata: SIDIX Menganalisis Startup Problem

```
User: "Startup saya stuck, sudah 2 tahun di market tapi tidak berkembang"

SIDIX internal process:
1. find_analogy("inersia", "business") 
   → Newton I: "Bisnis established sulit berubah tanpa tekanan eksternal"
   
2. cross_domain_apply("thermodynamics_2", "organizational")
   → "Tanpa maintenance aktif, organisasi naturally decay"
   
3. find_analogy("keseimbangan", "business")
   → Le Chatelier: "Sistem akan cari equilibrium baru setelah intervensi"
   
SIDIX output:
"Startup Anda mengalami 'inersia bisnis' (Newton I). Untuk bergerak butuh 
'gaya eksternal' — bisa berupa investor baru, pivot produk, atau kompetitor 
yang memaksa inovasi. Namun perhatikan juga 'entropi organisasi' (Termodinamika 2): 
pastikan ada sistem maintenance (culture, meeting rituals, OKR) yang aktif melawan 
kekacauan alamiah..."
```

---

## Integrasi dengan Modul Lain

```python
# Di problem_solver.py
from .knowledge_foundations import find_analogy

# Saat menganalisis masalah, SIDIX mencari analogi ilmiah
analogies = find_analogy(problem_type, target_domain)
result["scientific_analogies"] = analogies[:3]
```

---

## Keterbatasan Desain

1. **Heuristik apply_feynman sangat simpel** — dalam produksi, butuh LLM yang evaluate penjelasan
2. **Analogi tidak exhaustive** — hanya mencakup 2-5 analogi per hukum
3. **`find_analogy` berbasis keyword** — bukan semantic search, bisa miss analogis yang semantically close tapi lexically berbeda
4. **Tidak ada weighting** antara hukum yang lebih/kurang applicable

---

## Next Steps

- [ ] Augment `find_analogy` dengan embedding-based search
- [ ] Expand `PHYSICS_LAWS` dengan Quantum Mechanics + Statistical Mechanics
- [ ] Add `BIOLOGY_PRINCIPLES` (natural selection, homeostasis, membranes)
- [ ] Integrate ke `agent_react.py` agar ReAct agent bisa spontan gunakan mental models
- [ ] Self-test SIDIX dengan `apply_feynman` setiap menerima topik baru

---

## Referensi

- Research note 107: Hukum Fisika sebagai Fondasi Berpikir
- Research note 108: Kimia sebagai Framework Analisis
- Research note 109: Metode Belajar Efektif
- Research note 16: Decision Engine + Maqashid
- Charlie Munger, *Poor Charlie's Almanack* — Latticework of Mental Models
