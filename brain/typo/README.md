# brain/typo — Ketahanan typo (Indonesia + multibahasa)

**Prinsip:** *standing alone* — jalur wajib tanpa API vendor.

## Dokumen

| File | Isi |
|------|-----|
| `MULTILINGUAL_TYPO_FRAMEWORK.md` | Spesifikasi universal 6+ bahasa, 1.150+ pola (spesifikasi + kamus dalam dokumen) |
| `TYPO_RESILIENT_FRAMEWORK.md` | Empat lapis khusus Indonesia: normalizer → semantic matcher → confidence → context-aware |
| `pipeline.py` | Implementasi MVP: NFC, substitusi ringan, *script hint* |

## Kode produksi

- Integrasi chat: `apps/brain_qa/brain_qa/typo_bridge.py` → `normalize_for_react`.
- Env: `SIDIX_TYPO_PIPELINE` (default aktif; `0` / `off` untuk mematikan).

## Rujukan Jiwa / integrasi asisten

- Orkestrator runtime: `apps/brain_qa/brain_qa/jiwa/`.
- Panduan jembatan *sarang-tamu* (judul file historis `KIMI_INTEGRATION_GUIDE.md`), folder `kimi-plugin/`.
- **Pemetaan bundel → repo:** `docs/MAPPING_FRAMEWORK_TO_REPO.md`.
