# 103 — SIDIX builtin_apps.py: Daftar, Cara Pakai, dan Cara Extend

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** IMPL  
**Tanggal:** 2026-04-18  
**Author:** Claude Sonnet 4.6 (agen SIDIX)

---

## Apa

`builtin_apps.py` adalah modul Python yang mendaftarkan 18 kapabilitas built-in SIDIX sebagai tool yang bisa dipanggil oleh agent, user, atau modul lain — tanpa API eksternal (kecuali Wikipedia yang menggunakan API publik gratis).

**Path:** `D:\MIGHAN Model\apps\brain_qa\brain_qa\builtin_apps.py`

---

## Mengapa

SIDIX dibangun sebagai AI platform mandiri (own-stack). Tool eksternal seperti WolframAlpha, OpenAI tools, atau Google APIs:
1. Memiliki biaya per request
2. Memerlukan koneksi internet
3. Tidak terkontrol privasi datanya
4. Tidak bisa dimodifikasi sesuai kebutuhan Islam

`builtin_apps.py` menyediakan **baseline tools** yang berjalan 100% lokal, deterministik, dan bisa diperluas tanpa dependensi vendor.

---

## Daftar Lengkap 18 Builtin Apps

### Kategori: math (4 tools)

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `calculator` | Hitung ekspresi matematika (eval aman) | `expression` |
| `statistics` | Statistik deskriptif dari list angka | `data`, `mode` |
| `equation_solver` | Selesaikan persamaan kuadrat | `a`, `b`, `c` |
| `unit_converter` | Konversi panjang/berat/volume/suhu | `value`, `from_unit`, `to_unit` |

### Kategori: datetime (1 tool)

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `datetime_tool` | Waktu sekarang, konversi Hijriah, selisih hari | `mode`, `date_str` |

### Kategori: text (3 tools)

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `text_tools` | Wordcount, uppercase, slug, dll | `text`, `operation` |
| `base64` | Encode/decode Base64 | `text`, `operation` |
| `hash_generator` | Hash MD5/SHA256/SHA512 | `text`, `algorithm` |

### Kategori: data (2 tools)

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `json_formatter` | Format/validasi/minify JSON | `json_str`, `operation` |
| `csv_parser` | Parse CSV menjadi struktur data | `csv_text`, `delimiter` |

### Kategori: utility (2 tools)

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `uuid_generator` | Generate UUID v4/v1 | `count`, `version` |
| `password_generator` | Password acak + entropi | `length`, `include_symbols` |

### Kategori: web (2 tools)

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `web_search` | Stub pencarian — mengembalikan URL DuckDuckGo | `query` |
| `wikipedia` | Ringkasan Wikipedia via API publik | `topic`, `lang` |

### Kategori: islamic (4 tools) ← PRIORITAS SIDIX

| App | Fungsi | Parameter Utama |
|-----|--------|----------------|
| `prayer_times` | Waktu shalat — algoritma astronomi pure Python | `latitude`, `longitude`, `method` |
| `zakat_calculator` | Zakat maal, fitrah, perdagangan, pertanian | `asset_type`, `total_assets` |
| `qiblat` | Arah kiblat + jarak ke Mekkah (Great Circle) | `latitude`, `longitude` |
| `asmaul_husna` | Cari 99 Nama Allah per nomor/keyword | `number`, `query` |

---

## Cara Pakai

### Import

```python
from brain_qa.builtin_apps import (
    list_apps,
    call_app,
    search_apps,
    get_app_categories,
    get_app_info,
    BUILTIN_APPS,
)
```

### `list_apps()` — Tampilkan semua app

```python
apps = list_apps()
# Returns: [{"name": "calculator", "description": "...", "category": "math", ...}, ...]
print(f"Total builtin apps: {len(apps)}")
```

### `call_app(name, **kwargs)` — Panggil satu app

```python
# Kalkulator
result = call_app("calculator", expression="(3.14159 * 6**2)")
print(result)
# {"ok": True, "result": 113.0972..., "note": "Ekspresi: (3.14159 * 6**2)"}

# Konversi suhu
result = call_app("unit_converter", value=100, from_unit="C", to_unit="F")
print(result["result"])  # 212.0

# Waktu shalat Jakarta
result = call_app("prayer_times", latitude=-6.2088, longitude=106.8456, method="MWL")
for waktu, jam in result["result"]["waktu_shalat"].items():
    print(f"{waktu}: {jam}")

# Zakat maal 100 juta
result = call_app("zakat_calculator",
    asset_type="maal",
    total_assets=100_000_000,
    gold_price_per_gram=1_200_000
)
print(result["result"]["jumlah_zakat"])  # Rp 2,500,000

# Arah kiblat dari Surabaya
result = call_app("qiblat", latitude=-7.2575, longitude=112.7521)
print(result["result"]["arah_kiblat"]["derajat_dari_utara"])  # ~295°

# Asmaul Husna nomor 99
result = call_app("asmaul_husna", number=99)
print(result["result"])  # {"nomor": 99, "arab": "الصَّبُورُ", "latin": "As-Shabur", ...}

# Konversi tanggal ke Hijriah
result = call_app("datetime_tool", mode="hijri_approx", date_str="2026-04-18")
print(result["result"]["hijri_formatted"])  # "20 Syawal 1447 H"
```

### `search_apps(query)` — Cari app

```python
matches = search_apps("zakat")
# Returns: [{"name": "zakat_calculator", "relevance": 3, ...}]

matches = search_apps("hash")
# Returns: [{"name": "hash_generator", ...}]
```

### `get_app_categories()` — Kelompokkan per kategori

```python
cats = get_app_categories()
for category, apps in cats.items():
    print(f"\n{category.upper()} ({len(apps)} apps):")
    for app in apps:
        print(f"  - {app['name']}: {app['description'][:60]}")
```

### `get_app_info(name)` — Detail satu app

```python
info = get_app_info("prayer_times")
print(info["result"]["params"])
print(info["result"]["example"])
```

---

## Format Response

Semua handler mengembalikan `dict` dengan format standar:

```python
# Sukses
{"ok": True, "result": <data>, "note": "<opsional>"}

# Error
{"ok": False, "error": "<pesan error>"}
```

---

## Cara Extend (Tambah App Baru)

### 1. Tulis handler function

```python
def _nama_handler(param1: str = "", param2: float = None, **kwargs) -> AppResult:
    """
    Deskripsi handler.

    Args:
        param1: penjelasan
        param2: penjelasan
    """
    if not param1:
        return _err("param1 wajib diisi.")

    # Logika
    hasil = do_something(param1, param2)
    return _ok(hasil)
```

**Aturan wajib handler:**
- Selalu gunakan `**kwargs` — agar tidak error jika ada parameter ekstra
- Gunakan `_ok()` dan `_err()` — format response konsisten
- Tangkap semua exception — jangan biarkan app crash
- Default parameter aman (biasanya `= None` atau `= ""`)

### 2. Daftarkan ke BUILTIN_APPS

```python
BUILTIN_APPS["nama_app"] = {
    "description": "Deskripsi singkat yang jelas — kapan dipakai",
    "handler": _nama_handler,
    "category": "math",  # atau: text, datetime, data, web, islamic, utility
    "params": {
        "param1": "penjelasan parameter",
        "param2": "penjelasan parameter (opsional)",
    },
    "example": {"param1": "contoh_nilai", "param2": 42},
}
```

### 3. Test handler

```python
# Quick test
from brain_qa.builtin_apps import call_app

result = call_app("nama_app", param1="test_value")
assert result["ok"] is True
print(result["result"])
```

---

## Implementasi Teknis: Detail Per App

### `prayer_times` — Algoritma Waktu Shalat

Menggunakan formula astronomi murni (tidak ada API):
1. **Julian Day Number** → posisi bumi dalam orbit
2. **Solar declination** → deklinasi matahari pada hari itu
3. **Equation of Time** → koreksi orbit elips bumi
4. **Hour Angle** → sudut sinar matahari per waktu shalat
5. **Transit (Dzuhur)** → ketika matahari tepat di meridian

Metode yang didukung:
- **MWL** (Muslim World League): Fajr 18°, Isha 17° — standar Asia/Eropa
- **ISNA**: Fajr 15°, Isha 15° — Amerika Utara
- **Egypt**: Fajr 19.5°, Isha 17.5°
- **Makkah**: Fajr 18.5°, Isha 90 menit setelah Maghrib
- **Karachi**: Fajr 18°, Isha 18°
- **UOIF**: Fajr 12°, Isha 12° — Eropa (UOIF)

### `zakat_calculator` — Fikih Zakat

Implementasi berdasarkan fiqh madzab Syafi'i (mayoritas Indonesia):

| Jenis | Nisab | Kadar | Haul |
|-------|-------|-------|------|
| Maal | 85g emas | 2.5% | 1 tahun |
| Perdagangan | 85g emas | 2.5% | 1 tahun |
| Fitrah | - | 2.5 kg beras | Sebelum shalat Id |
| Pertanian (tadah hujan) | 653 kg | 10% | Setiap panen |
| Pertanian (irigasi) | 653 kg | 5% | Setiap panen |

### `qiblat` — Formula Great Circle

```
bearing = atan2(
    sin(Δlon) * cos(lat_makkah),
    cos(lat_anda) * sin(lat_makkah) - sin(lat_anda) * cos(lat_makkah) * cos(Δlon)
)
```

Haversine formula untuk jarak:
```
a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
d = 2R * arcsin(√a)
```

### `datetime_tool` (mode hijri_approx)

Menggunakan algoritma Khalid Shaukat yang disederhanakan — konversi via Julian Day Number. Akurasi ±1 hari (bergantung timezone dan lokasi untuk penentuan awal bulan ru'yah).

---

## Rencana Pengembangan (Roadmap)

### Phase 2 — Tools Tambahan
- `quran_search` — Cari ayat Al-Quran (corpus lokal)
- `hadith_search` — Cari hadits (corpus lokal)
- `tajwid_checker` — Cek aturan tajwid
- `arabic_transliteration` — Transliterasi Arab-Latin
- `number_to_words_id` — Angka ke kata Indonesia (untuk dokumen)

### Phase 3 — Integration
- `weather_stub` — Stub cuaca dengan BMKG API (publik, gratis)
- `currency_converter` — Kurs dari Bank Indonesia API (publik)
- `gold_price` — Harga emas dari sumber lokal

### Phase 4 — AI-Enhanced Tools
- `text_summarizer` — Ringkasan teks via brain_qa local LLM
- `translation_hint` — Terjemahan sederhana (Indonesia ↔ Arab ↔ Inggris)

---

## Catatan Penting

1. **Tidak ada vendor AI API** — Semua tools menggunakan Python stdlib + algoritma lokal
2. **`_calc_handler` aman** — Menggunakan `eval()` dengan whitelist fungsi, bukan eval sembarangan
3. **`prayer_times` adalah aproksimasi** — Cukup untuk kebutuhan umum. Untuk jadwal masjid resmi, gunakan data Kemenag RI
4. **`zakat_calculator` adalah panduan** — Selalu konfirmasi dengan ahli fiqh/Baznas untuk jumlah yang signifikan
5. **Wikipedia tool** — Memerlukan koneksi internet; satu-satunya tool yang membutuhkan jaringan (selain web_search stub)

---

## Dependensi

**Zero external dependencies** — semua menggunakan Python stdlib:
- `math` — kalkulasi matematika dan astronomi
- `statistics` — statistik deskriptif
- `hashlib` — kriptografi
- `base64` — encoding
- `json` — format JSON
- `csv` — parse CSV
- `uuid` — generate UUID
- `secrets` — password generator (cryptographically secure)
- `urllib.request` — Wikipedia API call
- `datetime` — tanggal dan waktu
- `re` — regex
