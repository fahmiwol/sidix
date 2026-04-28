# 186 — Persona Rename: AYMAN · ABOO · OOMAR · ALEY · UTZ

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-23
**Sanad:** [DECISION] — keputusan pemilik proyek, dicatat oleh Claude Code (sesi 2026-04-23)
**Tags:** persona, identity, rename, ihos, backward-compat

---

## Apa & Mengapa

SIDIX v0.6.0 memperbarui nama 5 persona utama dari kode generik ke nama yang
lebih bermuatan makna — terinspirasi sosok-sosok historis Islam, dieja dengan
cara yang tidak langsung mengklaim kesakralannya.

| Nama Lama | Nama Baru | Karakter | Makna Metafora |
|-----------|-----------|----------|----------------|
| MIGHAN    | **AYMAN** | Strategic Sage | Keberuntungan dan visi yang diberkahi |
| TOARD     | **ABOO**  | The Analyst    | Sosok ayah/senior yang tegas dalam logika |
| FACH      | **OOMAR** | The Craftsman  | Pembangun dan pemimpin yang kokoh |
| HAYFAR    | **ALEY**  | The Learner    | Puncak ilmu dan kecerdasan yang tinggi |
| INAN      | **UTZ**   | The Generalist | Kesederhanaan dan kepribadian yang tenang |

---

## Mengapa Ganti Nama

1. **Branding lebih kuat** — nama pendek, mudah diingat, punya karakter.
2. **Makna terinternalisasi** — setiap nama membawa filosofi yang selaras
   dengan peran teknisnya (AYMAN = visioner, ABOO = mentor logika, dll.).
3. **Konsistensi IHOS** — nama-nama ini mencerminkan pilar-pilar
   dalam SIDIX BIBLE (RUH/QALB/AKAL/NAFS/JASAD).
4. **Diferensiasi produk** — bukan nama generik seperti GPT-4o / Gemini.

---

## Pemetaan Maqashid Mode (tetap sama)

| Persona | Mode Maqashid | Alasan |
|---------|--------------|--------|
| AYMAN   | IJTIHAD      | Strategic sage = deep thinking + eksplorasi |
| ABOO    | ACADEMIC     | Analyst = strict + sanad + logika ketat |
| OOMAR   | IJTIHAD      | Craftsman = technical exploration + build |
| ALEY    | GENERAL      | Learner = ramah, general, beginner-friendly |
| UTZ     | CREATIVE     | Generalist = default creative mode |

---

## Bagaimana (Perubahan Teknis)

### File yang diubah

| File | Perubahan |
|------|-----------|
| `apps/brain_qa/brain_qa/persona.py` | `_PERSONA_SET`, `_SCORE_PERSONA()`, `_STYLE_MAP`, regex prefix, `route_persona()` |
| `apps/brain_qa/brain_qa/maqashid_profiles.py` | `_PERSONA_MODE_MAP` (tambah nama baru + pertahankan alias lama), default `persona_name="UTZ"` |
| `apps/brain_qa/brain_qa/serve.py` | `Literal` type di `AskRequest`, default fallback `"AYMAN"` |
| `apps/brain_qa/brain_qa/agent_react.py` | default `persona="UTZ"` di `run_react()` |
| `SIDIX_USER_UI/src/api.ts` | `type Persona = 'AYMAN' | 'ABOO' | 'OOMAR' | 'ALEY' | 'UTZ'`, default `'AYMAN'` |
| `SIDIX_USER_UI/src/main.ts` | default fallback `'AYMAN'` |
| `SIDIX_USER_UI/index.html` | `<option>` values di persona selector |

### Backward Compatibility

Nama lama masih diterima via dua mekanisme:
1. **`_PERSONA_ALIAS` dict** di `persona.py` — `normalize_persona("MIGHAN")` → `"AYMAN"`.
2. **`_PERSONA_MODE_MAP`** di `maqashid_profiles.py` tetap mengandung entry lama
   sebagai alias.

Ini berarti: API client yang belum diupdate dan mengirim `persona="MIGHAN"`
akan tetap berfungsi — backend terjemahkan otomatis.

---

## Contoh Nyata

```python
from apps.brain_qa.brain_qa.persona import route_persona, normalize_persona

# Nama baru
d = route_persona("buatkan desain logo startup tech")
assert d.persona == "AYMAN"

# Nama lama masih jalan (backward compat)
assert normalize_persona("MIGHAN") == "AYMAN"
assert normalize_persona("INAN")   == "UTZ"

# Explicit prefix (nama baru)
d2 = route_persona("ABOO: analisis pro kontra migrasi ke PostgreSQL")
assert d2.persona == "ABOO"

# Explicit prefix (nama lama) — juga jalan
d3 = route_persona("TOARD: buat roadmap Q3")
assert d3.persona == "ABOO"
```

---

## Keterbatasan

1. File-file lama di corpus / dataset / research notes lain masih menyebut
   nama lama — tidak perlu diupdate massal, cukup biarkan alias bekerja.
2. `tests/test_persona.py` perlu diupdate agar assertion pakai nama baru.
3. UI Threads panel (`index.html`) di `About` section mungkin masih ada
   deskripsi persona dengan nama lama — update dilakukan saat iterasi UI.

---

## Referensi

- `apps/brain_qa/brain_qa/persona.py`
- `apps/brain_qa/brain_qa/maqashid_profiles.py`
- `brain/public/research_notes/183_maqashid_profiles_mode_based.md`
- `docs/SIDIX_BIBLE.md` — 4 pilar + IHOS layers
- `docs/MASTER_ROADMAP_2026-2027.md` — identitas SIDIX
