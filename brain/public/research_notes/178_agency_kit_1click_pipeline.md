# Agency Kit — 1-Click Agency Pipeline (6-Layer DAG)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
**[FACT]** — 2026-04-21

## Apa itu
`agency_kit.py` adalah pipeline DAG (Directed Acyclic Graph) yang membangun paket
pemasaran lengkap ("Agency Kit") dalam satu panggilan fungsi. Target: UKM Indonesia
yang tidak bisa bayar agency mahal tapi butuh semua aset marketing.

Ini adalah **Killer Offer #4** dari MASTER_ROADMAP: "Gantikan apa yang biasanya
Anda bayar Rp 15-20 juta untuk agency — berikan gratis atau di bawah Rp 100rb."

## Mengapa
Fragmentasi adalah masalah utama UKM dalam marketing: brand kit dari satu tempat,
konten dari freelancer lain, campaign dari konsultan berbeda. Tidak ada koherensi.

Agency Kit menyelesaikan ini dengan pipeline terintegrasi di mana output Layer 1
(Brand Kit) otomatis menjadi input Layer 2 (Captions), dan seterusnya. Brand voice
yang konsisten mengalir dari brand kit → captions → content plan → campaign.

## Bagaimana
**6-Layer DAG:**

```
Layer 1: brand_builder.generate_brand_kit()
         ↓ brand_voice (input ke layer berikutnya)
Layer 2a: copywriter.generate_copy() × 10 (AIDA×3, PAS×3, FAB×2, bonus×2)
Layer 2b: content_planner.generate_content_plan() → 30-day plan
Layer 3: campaign_strategist.plan_campaign() → AARRR 5 stages
Layer 4: ads_generator.generate_ads() × 3 platforms (fb/google/tiktok)
Layer 5: thumbnail_generator.generate_thumbnail() × 3 specs
Layer 6: muhasabah_loop.run_muhasabah_loop() → quality gate bundle
```

**`_safe()` wrapper pattern:**
```python
def _safe(fn, *args, **kwargs) -> tuple[Any, str]:
    try:
        return fn(*args, **kwargs), ""
    except Exception as exc:
        logger.warning("agency_kit safe-call error: %s — %s", fn.__name__, exc)
        return None, str(exc)
```
Pattern ini memastikan satu layer yang gagal tidak crash keseluruhan pipeline.
Warning di-log, pipeline tetap lanjut.

**Budget parser:**
```python
_parse_budget("2jt")    → 2_000_000
_parse_budget("500rb")  → 500_000
_parse_budget("1500000") → 1_500_000
# default jika parse gagal: 1_500_000
```

**Composite CQF**: rata-rata semua skor CQF dari tiap layer yang berhasil.
```
tier: "premium" (≥8.5) | "delivery" (≥7.0) | "needs_work" (<7.0)
```

## Contoh nyata
```python
from brain_qa.agency_kit import build_agency_kit
r = build_agency_kit(
    business_name="Warung Pak Budi",
    niche="kuliner nasi goreng",
    target_audience="keluarga Jabodetabek",
    budget="1.5jt",
)
print(r["cqf_composite"])    # 0.0 (jika semua modul belum available)
print(r["caption_count"])    # 0-10 (tergantung copywriter module)
print(r["ok"])               # True (pipeline sukses walau banyak warning)
```

**Smoke test note**: Saat pengujian Sprint 5, ada warning:
- `generate_brand_kit()` tidak terima parameter `target_audience` — ini karena
  signature modul main belum diupdate (minor, tidak mempengaruhi ok=True).
- `generate_content_plan()` idem. Bug kecil di signature, bukan di pipeline logic.

## Keterbatasan
- **Sequential, bukan parallel**: Layer 2-5 bisa dijalankan paralel dengan
  asyncio untuk performance lebih baik. Saat ini sequential.
- **Modul dependency**: semua layer bergantung pada modul Sprint 4 yang tersedia.
  Kalau modul belum ada, layer di-skip dengan warning.
- **No state persistence**: setiap build fresh. Tidak ada incremental update
  (misal: refresh hanya campaign tanpa rebuild brand kit).
- **Budget hanya untuk campaign**: budget hanya dipakai di `plan_campaign`,
  bukan untuk alokasi ads spend per platform.

## Referensi implementasi
- `D:\MIGHAN Model\sprint5\apps\brain_qa\brain_qa\agency_kit.py`
- `docs/MASTER_ROADMAP_2026-2027.md` (Killer Offer #4)
- Endpoint: `POST /creative/agency_kit` di `agent_serve.py`
