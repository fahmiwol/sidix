---
sanad_tier: primer
tags: [research, nusantara, prompt-enhancer, knowledge-base, differentiator]
date: 2026-04-19
---

# 172 — Nusantara Knowledge Base Design untuk Prompt Enhancer

## 1. Konsep

[FACT] Flow SIDIX untuk image gen yang membedakan dari GPT/Claude/Midjourney:

```
User prompt ("masjid demak subuh")
  ↓
Entity Recognition (extract "masjid demak" sebagai Nusantara entity)
  ↓
NUSANTARA_LEXICON lookup (ID: nusantara.masjid.demak)
  ↓
Prompt Enrichment:
  base: "Masjid Agung Demak at dawn"
  + visual_keywords: "tumpang roof four tiers, dark teak wood pillars, Arabic calligraphy medallion"
  + style_modifiers: "serene, golden hour light, 15th century Islamic Javanese architecture"
  + cultural_context: "oldest mosque in Java, founded 1479 CE"
  ↓
Kirim prompt enriched ke FLUX.1-schnell
  ↓
Output: gambar yang secara visual akurat untuk budaya Nusantara
```

[OPINION] Big tech tidak punya KB ini karena:
- Data cultural specific dari dinas kebudayaan + kitab klasik + buku specialty → tidak ter-scrape massal.
- Curated by native speaker + ahli cultural → butuh effort komunitas lokal yang di luar scope global AI.
- Ini adalah **differensiator struktural** SIDIX, bukan sekadar prompt template.

---

## 2. Schema Proposal

### 2.1 Struktur per-entry (JSON Schema)

```json
{
  "id": "nusantara.candi.borobudur",
  "canonical_name": "Borobudur",
  "category": "candi_buddhist",
  "subcategory": "mahayana_temple",

  "aliases": [
    "Borobudur",
    "Candi Borobudur",
    "Stupa Borobudur",
    "Barabudur"
  ],

  "location": {
    "country": "Indonesia",
    "province": "Jawa Tengah",
    "regency": "Magelang",
    "coordinates": [-7.6079, 110.2038]
  },

  "visual_keywords_en": [
    "bell-shape stupas",
    "Buddhist relief carvings",
    "Boddhisattva reliefs",
    "mandala layout",
    "nine stacked platforms",
    "central dome"
  ],

  "visual_keywords_id": [
    "stupa lonceng",
    "relief Buddha",
    "relief Boddhisattva",
    "tata mandala"
  ],

  "style_modifiers": [
    "ancient stone carving",
    "volcanic landscape",
    "misty morning",
    "golden hour light",
    "weathered andesite stone"
  ],

  "cultural_context": "9th century Mahayana Buddhist temple, built during Sailendra dynasty, UNESCO World Heritage 1991",

  "period": {
    "era": "Sailendra",
    "approximate_year_ce": 825
  },

  "sanad_tier": "peer_review",
  "sources": [
    {
      "type": "unesco",
      "url": "https://whc.unesco.org/en/list/592",
      "accessed": "2026-04-19"
    },
    {
      "type": "konservasi",
      "name": "Balai Konservasi Borobudur",
      "url": "https://borobudurpedia.id"
    }
  ],

  "sensitive": false,
  "requires_expert_review": false,

  "last_reviewed": "2026-04-19",
  "reviewed_by": "sidix_team"
}
```

### 2.2 Kategori utama (8 bucket)

1. **candi** — Borobudur, Prambanan, Penataran, Sukuh, Cetho, Mendut, Kalasan, dll.
2. **arsitektur_vernakular** — Joglo (Jawa), Rumah Gadang (Minang), Tongkonan (Toraja), Bale (Bali), Omo Sebua (Nias), dll.
3. **pakaian_tradisional** — Kebaya (Jawa/Bali), Baju Kurung, Ulos (Batak), Tenun Sumba, Pakaian Dayak, dll.
4. **tekstil** — Batik (Parang, Kawung, Mega Mendung, Truntum, Sidomukti), Tenun Ikat, Songket, Ulos.
5. **lansekap** — Sawah terasering Ubud/Tegalalang, Gunung Bromo, Danau Toba, Raja Ampat, Pantai Kuta, Hutan Kalimantan.
6. **alat_musik** — Gamelan, Angklung, Sasando, Kolintang, Kendang, Rebab, Suling, Gong.
7. **ornamen_keagamaan** — Masjid (Demak, Raya Medan, Istiqlal), Pura (Besakih, Ulun Danu, Tanah Lot), Vihara, Gereja Batak, Klenteng.
8. **kuliner_visual** — Rendang, Gudeg, Sate Padang, Nasi Tumpeng, Soto Betawi, Pempek, Rawon.

### 2.3 Phase 1 target: 50 entitas paling esensial

Distribusi:
- 10 candi utama
- 8 arsitektur vernakular
- 7 pakaian + tekstil tradisional
- 8 lansekap ikonik
- 5 alat musik
- 7 ornamen keagamaan
- 5 kuliner visual

---

## 3. Sumber Kurasi

| Tier | Sumber | Catatan |
|------|--------|---------|
| **primer** | Dinas Kebudayaan provinsi, Kemendikbud, Balai Konservasi tiap candi | Paling authoritative — data langsung dari custodian cultural |
| **primer** | Buku ahli: "Nusantara Heritage" (P. Koentjaraningrat), "Prehistoric Indonesia" (H.R. van Heekeren), "Candi Indonesia" (Soekmono) | Scholar lokal, reliable |
| **peer_review** | UNESCO World Heritage, BPS Cultural Statistics, Journal of Indonesian Culture | International peer-reviewed |
| **peer_review** | Wikipedia Indonesia + English (cross-check keduanya) | Bagus untuk baseline; **jangan jadi primary** |
| **aggregator** | Travel blogs (Lonely Planet, CultureTrip) | Hanya untuk verify visual description, bukan historical fact |
| **ulama** (keagamaan) | Rumah Zakat, KH Sahal Mahfudh fatwa archives, MUI untuk konteks Islamic heritage | Untuk masjid + ornamen Islamic |

[OPINION] Sensitivitas tinggi untuk entitas keagamaan — konsultasi ulama/pandita/pendeta lokal sebelum publikasi entry yang menyangkut ritus sakral.

---

## 4. Pipeline Kurasi

### Phase 1 (Sprint 3, 4 minggu) — Bootstrap 50 entitas

Workflow:
1. **Draft by SIDIX** — SIDIX generate entry dari corpus existing (research notes + web_search Wikipedia ID/EN + UNESCO).
2. **Human review** — founder + kontributor lokal cross-check visual keywords + cultural context.
3. **Sanad addition** — tambah URL sumber authoritative + tanggal akses.
4. **Commit ke `brain/public/nusantara_lexicon/<category>/<id>.json`**.
5. **Smoke test** — generate 3 image pakai prompt enhanced vs raw, panel lokal rate.

### Phase 2 (Sprint 4–6, setelah v0.2 launch) — Community contribution

- Endpoint `/nusantara/submit` (restricted, butuh approved contributor role).
- PR template GitHub `nusantara-entry-template.yml`.
- Review queue: 2 reviewer min approval sebelum merge.

### Phase 3 (Adolescent stage) — SIDIX autonomous expansion

- LearnAgent fetch sumber baru (UNESCO updates, dinas announcements).
- `knowledge_gap_detector` trigger research ketika user query entity yang belum ada di lexicon.
- User approve draft → masuk lexicon.

---

## 5. Integration dengan brain_synthesizer

**Rekomendasi: Buat lexicon TERPISAH, bukan extend CONCEPT_LEXICON IHOS.**

Alasan:
- CONCEPT_LEXICON IHOS fokus konsep epistemologis (Sanad, Maqasid, IHOS, Hafidz). Nusantara entities beda domain (cultural heritage) — mixing akan bloat dan susah reason.
- Schema berbeda: IHOS concepts punya relations (hierarchical), Nusantara entries punya visual_keywords + style (tidak hierarchical).
- File structure:
  ```
  brain/public/concept_lexicon.json        # IHOS existing
  brain/public/nusantara_lexicon/
    ├── index.json                         # ID → path mapping
    ├── candi/
    │   ├── borobudur.json
    │   └── prambanan.json
    ├── arsitektur_vernakular/
    ├── ...
  ```

### 5.1 Helper API di brain_qa

```python
# apps/brain_qa/brain_qa/nusantara.py (baru di Sprint 3)

def detect_nusantara_entities(prompt: str) -> list[dict]:
    """Match prompt against NUSANTARA_LEXICON aliases, return matched entries."""
    ...

def enrich_prompt(prompt: str, matches: list[dict]) -> str:
    """Append visual_keywords + style_modifiers + cultural_context to prompt."""
    ...
```

### 5.2 Integration point di image_gen.py

```python
def generate_image(raw_prompt: str, **kwargs) -> bytes:
    entities = detect_nusantara_entities(raw_prompt)
    if entities:
        prompt = enrich_prompt(raw_prompt, entities)
        citations = [{"type": "nusantara", "id": e["id"], "sources": e["sources"]}
                     for e in entities]
    else:
        prompt = raw_prompt
        citations = []
    image = call_flux(prompt, **kwargs)
    return image, citations  # SIDIX output include sanad chain per gambar
```

---

## 6. Privasi & Etika

- [FACT] **Tidak mengumpulkan face data** — entries tidak menyimpan foto wajah tokoh spesifik. Hanya description visual style.
- [OPINION] **Sensitive entities** (ritus sakral, tempat upacara) → flag `"requires_expert_review": true` dan **exclude dari auto-enrich** sampai review ulama/pandita.
- [FACT] **Attribution wajib** di setiap output image: metadata EXIF + caption include sanad chain.
- [OPINION] **Commercial use** gambar yang generate dari prompt enrich KB Nusantara harus explicit consent review oleh dinas kebudayaan relevan kalau publikasi komersial skala besar — ini masuk governance SIDIX, tidak otomatis.

---

## 7. Roadmap Mini Sprint 3 (khusus Nusantara KB)

| Week | Deliverable |
|------|-------------|
| 1 | Schema final + 10 entry seed candi + pipeline tooling |
| 2 | +20 entry (arsitektur + tekstil + lansekap) + nusantara.py helper |
| 3 | +20 entry (sisa 20) + integration dengan image_gen |
| 4 | Benchmark 10 prompt Nusantara enriched vs raw, panel rating, iterate |

---

## Sanad

- UNESCO World Heritage List Indonesia: https://whc.unesco.org/en/statesparties/id
- Kemendikbud Warisan Budaya: https://warisanbudaya.kemdikbud.go.id
- Balai Konservasi Borobudur: https://borobudurpedia.id
- Museum Nasional Indonesia: https://www.museumnasional.or.id
- BPS Cultural Statistics: https://www.bps.go.id
- Soekmono, R. "Candi: Fungsi dan Pengertiannya" (Pustaka Jaya, 1974)
- Koentjaraningrat. "Kebudayaan Jawa" (Balai Pustaka, 1984)
- van Heekeren, H.R. "The Stone Age of Indonesia" (M. Nijhoff, 1972)
- Akses referensi: 2025-Q4 sampai 2026-04-19

## Catatan Integrasi dengan Note Lain
- **Note 171** (FLUX.1-schnell) — Nusantara enricher paling cocok dipair dengan FLUX karena superior text rendering (kaligrafi) + compositional quality.
- **Note 170** (RunPod) — integrasi API call dari `image_gen.py` ke RunPod endpoint, lexicon lookup terjadi di SIDIX brain (CPU, instant).
- **Note 173** (deployment pattern) — referensi arsitektur wrapper yang akan load lexicon in-memory saat startup.
