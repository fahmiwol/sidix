# 105 — Project Archetype System untuk SIDIX: Cara Pakai dan Desain

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Task:** Track L (lanjutan) — bagaimana archetypes dipakai SIDIX  
**File terkait:** `apps/brain_qa/brain_qa/project_archetypes.py`  

---

## Apa Itu Project Archetype?

Archetype proyek = **template berulang** yang sudah terbukti dipakai di proyek nyata. Bukan boilerplate kosong — tapi knowledge dari proyek yang sudah pernah berjalan.

Analogi: seperti arsitek punya "tipe bangunan" (rumah tinggal, ruko, gedung kantor) — masing-masing punya pola struktur, material, dan langkah konstruksi yang sudah teruji.

---

## Desain Sistem

### Struktur ARCHETYPES dict

```python
ARCHETYPES = {
    "archetype_name": {
        "description": str,      # Penjelasan singkat
        "stack": list[str],      # Daftar teknologi
        "real_project": str,     # Proyek nyata yang menginspirasi
        "structure": dict,       # Direktori/file penting + fungsinya
        "setup_steps": list,     # Langkah setup berurutan
        "env_vars": list[str],   # Environment variables yang diperlukan
        "deploy": str,           # Cara deploy
    }
}
```

### Fungsi Publik

| Fungsi | Input | Output | Kegunaan |
|--------|-------|--------|----------|
| `list_archetypes()` | — | `list[str]` | Tampilkan semua pilihan |
| `get_archetype(name)` | nama archetype | `dict` | Detail lengkap |
| `suggest_archetype(desc)` | deskripsi proyek | nama archetype | Rekomendasi otomatis |
| `generate_project_plan(arch, name)` | archetype + nama proyek | `dict` | Rencana proyek + sprint |

---

## Cara SIDIX Menggunakan Archetypes

### Skenario 1: User bertanya tentang tech stack

**User:** "SIDIX, aku mau buat chatbot SaaS yang bisa konek ke WhatsApp"  
**SIDIX flow:**
```python
archetype = suggest_archetype("chatbot SaaS WhatsApp omnichannel")
# → "nestjs_nextjs_saas"
plan = generate_project_plan("nestjs_nextjs_saas", "MyChatbot")
# → dict dengan stack, setup_steps, sprint_plan
```

### Skenario 2: User minta generate project plan

**User:** "Buatkan rencana proyek untuk Shopee gateway API"  
**SIDIX flow:**
```python
archetype = suggest_archetype("shopee gateway oauth api")
# → "hono_edge_api"
plan = generate_project_plan("hono_edge_api", "ShopeeGateway")
```

### Skenario 3: User minta semua pilihan

**User:** "SIDIX, archetype apa saja yang kamu punya?"  
**SIDIX flow:**
```python
archetypes = list_archetypes()
# → ["nextjs_fullstack", "threejs_game_multiplayer", ...]
```

---

## Mekanisme Suggest (Keyword Scoring)

`suggest_archetype()` menggunakan **keyword scoring sederhana**:
1. Mapping keyword → archetype (lebih spesifik prioritas lebih tinggi)
2. Hitung score setiap archetype berdasarkan jumlah keyword yang match
3. Pilih archetype dengan score tertinggi
4. Default fallback: `vite_react_ts` (paling umum)

Ini **sengaja sederhana** agar:
- Tidak butuh LLM untuk fungsi dasar
- Bisa dijalankan offline
- Mudah di-extend dengan keyword baru

Upgrade di masa depan: embedding similarity (pakai model lokal) untuk matching yang lebih semantik.

---

## Cara Extend Archetypes

Tambah entry baru di `ARCHETYPES` dict dengan format yang sama:

```python
ARCHETYPES["django_rest_api"] = {
    "description": "REST API dengan Django + DRF + PostgreSQL",
    "stack": ["Django", "Django REST Framework", "PostgreSQL", "Celery"],
    "real_project": "Contoh proyek baru",
    "structure": {
        "myapp/": "Django app",
        "api/": "DRF endpoints",
        "settings/": "Environment-based settings",
    },
    "setup_steps": [
        "pip install django djangorestframework psycopg2-binary",
        "django-admin startproject config .",
        "python manage.py startapp myapp",
    ],
    "env_vars": ["DATABASE_URL", "SECRET_KEY", "DEBUG"],
    "deploy": "Gunicorn + Nginx",
}
```

---

## Integrasi ke Endpoint SIDIX (Roadmap)

Endpoint yang bisa ditambah ke `serve.py`:

```
GET  /archetypes            → list_archetypes()
GET  /archetypes/{name}     → get_archetype(name)
POST /archetypes/suggest    → suggest_archetype(description)
POST /archetypes/plan       → generate_project_plan(archetype, project_name)
```

---

## Keterbatasan

- Keyword matching manual — tidak semantik, bisa salah suggest untuk kasus ambiguous
- Sprint plan yang di-generate sangat generik (belum customized per use case)
- Tidak ada validasi bahwa setup_steps masih relevan (package versions berubah)
- Belum terintegrasi ke query SIDIX — masih standalone module

---

## Nilai Jangka Panjang

Setiap kali SIDIX membantu user membuat proyek baru dan proyek tersebut berhasil, archetype bisa di-update dengan learnings baru. Sistem ini bersifat **living knowledge** — makin banyak proyek nyata, makin kuat rekomendasinya.
