# 93 — Conceptual Generalizer: Dari Contoh ke Prinsip Universal

**Tanggal:** 2026-04-18  
**Tag:** IMPL, DOC, DECISION  
**Audiens:** Tim internal SIDIX

---

## Masalah yang Diselesaikan

Manusia bisa belajar dari satu contoh dan langsung paham konsepnya:
- Diajarkan `1+1=2` → langsung paham `200+300=500`, `a+b=c`
- Diajarkan "api panas" → paham semua benda panas berbahaya bila disentuh
- Diajarkan "jual beli ada harga" → paham semua transaksi punya nilai tukar

AI tradisional: butuh ribuan contoh per konsep.  
SIDIX seharusnya: **1 contoh → pahami prinsipnya → generalisasi ke semua kasus**.

---

## Arsitektur Conceptual Generalizer

### Pipeline Utama

```
Input: Contoh spesifik
   ↓
[1. Extract Pattern]
   Identifikasi variabel, operator, relasi
   ↓
[2. Abstract Principle]
   Pisahkan nilai konkret dari struktur abstrak
   ↓
[3. Generalize]
   Gantikan nilai dengan variabel
   Temukan batas validitas
   ↓
[4. Analogize]
   Cari domain lain dengan pola serupa
   ↓
[5. Store Skill]
   Simpan ke skill_library sebagai prinsip reusable
```

### Contoh Konkret

**Input:** `1 + 1 = 2`

**Extract Pattern:**
```python
pattern = {
  "operation": "addition",
  "type": "arithmetic",
  "variables": ["a", "b", "result"],
  "relation": "a + b = result"
}
```

**Abstract Principle:**
```
Prinsip: Penjumlahan adalah operasi yang menggabungkan dua nilai
         menjadi nilai yang lebih besar (untuk bilangan positif)
Rumus: ∀a,b ∈ ℝ: a + b = a + b (komutativitas, asosiatif)
Batas: berlaku untuk semua bilangan riil
```

**Analogize:**
- Fisika: `v = v₀ + at` (kecepatan awal + tambahan = kecepatan akhir)
- Kimia: `reaktan₁ + reaktan₂ → produk` (kombinasi menghasilkan sesuatu baru)
- Fiqih: `pokok + riba = haram` (penjumlahan dengan elemen haram = haram)
- Sosial: `upaya + waktu = hasil` (effort + time = outcome)

---

## Implementasi: `conceptual_generalizer.py`

### Fungsi Utama

```python
def extract_principle(example: str, domain: str = "general") -> dict:
    """
    Dari satu contoh, ekstrak prinsip abstrak.
    
    Args:
        example: "1+1=2" atau "api panas bahaya" atau "jual beli ada harga"
        domain: math / physics / social / islam / general
    
    Returns:
        {
          "principle": str,       # prinsip abstrak
          "formula": str,         # jika ada rumus
          "variables": list,      # variabel yang terlibat
          "bounds": str,          # batas validitas
          "analogies": list,      # domain lain yang serupa
          "confidence": float     # 0.0-1.0
        }
    """
```

```python
def generalize(example: str, new_input: dict) -> str:
    """
    Terapkan prinsip yang dipelajari ke input baru.
    
    Contoh:
      generalize("1+1=2", {"a": 200, "b": 300}) → "500"
      generalize("api panas", {"benda": "kompor"}) → "kompor panas, hati-hati"
    """
```

```python
def find_cross_domain_analogy(principle: str, target_domain: str) -> str:
    """
    Temukan analogi prinsip di domain lain.
    Berguna untuk transfer learning antar domain.
    """
```

---

## Metode Generalisasi

### 1. Structural Abstraction
Pisahkan **nilai** dari **struktur**:
- `1 + 1 = 2` → `a + b = a+b` (nilai → variabel)
- `Nabi saw jujur` → `pemimpin ideal = jujur` (contoh → aturan)

### 2. Boundary Detection
Temukan kapan prinsip TIDAK berlaku:
- `a + b = a+b` berlaku untuk bilangan riil, TIDAK untuk string (meski Python bisa)
- `api panas` berlaku untuk api fisik, TIDAK untuk kiasan "api semangat"

### 3. Cross-Domain Transfer
Prinsip yang sama muncul di banyak domain:
```
Konservasi Energi (fisika) ≈ Keseimbangan Neraca (akuntansi) ≈ 
Keadilan Distributif (fiqih) ≈ Conservation of Information (komputasi)
```
Ini adalah **isomorfisme struktural** — pola yang sama, domain berbeda.

### 4. Hierarchical Abstraction
Dari konkret ke abstrak (piramid):
```
Level 0: 1+1=2 (contoh spesifik)
Level 1: penjumlahan bilangan (konsep)
Level 2: operasi binary (abstrak)
Level 3: relasi matematis (sangat abstrak)
Level 4: kombinasi entitas (universal)
```

---

## Koneksi dengan Islam

### Qiyas (Analogi Hukum)
Ini persis cara fiqih bekerja:
- **Asal:** Khamr haram karena memabukkan
- **Far'** (cabang baru): Narkoba — apakah haram?
- **'Illah** (alasan): memabukkan = menghalangi akal
- **Hukum:** Narkoba haram (karena 'illah sama)

Conceptual Generalizer adalah **mesin qiyas digital**.

### Ta'lil (Penelusuran Illat)
Setiap prinsip punya **'illah** (sebab efektif):
- Bukan "api itu panas" tapi "api panas KARENA oksidasi eksotermik"
- Ketika tahu 'illah-nya, bisa generalisasi ke semua proses eksotermik

---

## Integrasi dengan SIDIX

### Trigger Otomatis
Saat user memberi contoh, SIDIX otomatis:
1. Deteksi pola "X = Y", "jika A maka B", "A adalah B"
2. Jalankan `extract_principle()`
3. Simpan ke skill_library sebagai prinsip reusable
4. Log ke experience_engine sebagai CSDOR

### ReAct Integration
```python
tools = [
    Tool("generalize_concept", generalize, 
         "Terapkan prinsip yang sudah dipelajari ke kasus baru"),
    Tool("find_analogy", find_cross_domain_analogy,
         "Cari analogi di domain lain untuk prinsip ini"),
]
```

### Skill yang Dihasilkan
Setiap prinsip yang berhasil diabstraksi → skill baru:
```
skill: "apply_addition_principle"
skill: "apply_conservation_principle"  
skill: "apply_cause_effect_reasoning"
skill: "apply_qiyas_to_new_case"
```

---

## Keterbatasan

1. **Overgeneralization:** Bisa terlalu lebar — "semua X adalah Y" padahal tidak
   - Fix: Boundary detection + confidence scoring
2. **Domain confusion:** Analogi lintas domain bisa menyesatkan
   - Fix: Explicit domain tagging + validation step
3. **Shallow abstraction:** Hanya mengganti variabel tanpa paham struktur dalam
   - Fix: Hierarchical abstraction + knowledge graph linkage
4. **Tanpa ground truth:** Bagaimana tahu generalisasi benar?
   - Fix: Validasi dengan corpus BM25 + feedback loop

---

## Filosofi: Belajar Seperti Manusia

> "Manusia yang sudah bisa jalan, tidak akan lupa cara jalan.
>  Malah dia berkembang: bisa jalan → bisa lari → bisa menari"

Conceptual Generalizer adalah fondasi **permanent learning**:
- Prinsip yang sudah dipelajari → tidak terhapus
- Prinsip lama + pengalaman baru → prinsip yang lebih kaya
- Bukan hafalan, tapi **pemahaman** — itulah yang kekal
