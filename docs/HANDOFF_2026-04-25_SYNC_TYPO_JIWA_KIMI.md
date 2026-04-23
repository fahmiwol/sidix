# Handoff — Sinkron Typo + Jiwa (korpus) + Kimi + dokumen (2026-04-25)

## Untuk agen berikutnya

1. **Cek commit terbaru di `main`** — berisi kode `typo_bridge`, perubahan `run_react`, paket `brain/typo/*`, modul referensi pilar, `kimi-plugin/`, dan dokumen BRIEF/KIMI/PRD.
2. **Satu sumber kebenaran Jiwa:** runtime tetap `apps/brain_qa/brain_qa/jiwa/`; `brain/nafs|aql|qalb` + README pilar = korpus/referensi — jangan menggandakan logika tanpa tes.
3. **Typo:** spesifikasi besar di `MULTILINGUAL_TYPO_FRAMEWORK.md` / `TYPO_RESILIENT_FRAMEWORK.md`; kode MVP di `pipeline.py`. Lanjutkan `locales/*.json` dan modul sesuai spec bila diperlukan.
4. **Kimi:** `manifest.json` + `sidix_skill.yaml` — MCP default off; isi URL/perintah setelah deploy self-hosted.
5. **Tidak ikut commit (sengaja):** folder `Framework_bahasa_plugin_update/`, `Agent_Instagram Scraping SIDIX/`, `Arsitektur jiwa dan Plugin/`, skrip VPS ad-hoc — rapikan atau `.gitignore` terpisah.

## Untuk maintainer (baca cepat)

- **Versi changelog repo:** `v0.7.4-dev` (lihat `CHANGELOG.md`).
- **Landing `SIDIX_USER_UI`:** patch **v1.0.4** (narasi rilis singkat di About).
- **Uji:** dari `apps/brain_qa`, `python -m pytest tests/ -q` — target hijau sebelum deploy.

## Eksternal (rilis ringkas — boleh dipakai di catatan publik)

**SIDIX v0.7.4-dev / UI v1.0.4:** Pipelines typo multibahasa tersambung ke agen ReAct (dapat dimatikan dengan `SIDIX_TYPO_PIPELINE=0`). Dokumentasi typo (Indonesia + universal), pilar Jiwa di `brain/`, integrasi Kimi (manifest + skill), serta BRIEF/PRD/KIMI guide masuk repositori. Tanpa kunci API pihak ketiga di paket ini; deploy self-hosted tetap menjadi tanggung jawab operator.

---

_Pembaruan ini melengkapi sinkronisasi git setelah pemetaan dokumen (`MAPPING_FRAMEWORK_TO_REPO.md`)._

**Catatan lanjutan (2026-04-23):** di `MAPPING_FRAMEWORK_TO_REPO.md`, baris “rilis sinkron” memakai rujukan `git log` pada `main`, bukan SHA tunggal, supaya tetap akurat setelah commit dokumen kecil beruntun.
