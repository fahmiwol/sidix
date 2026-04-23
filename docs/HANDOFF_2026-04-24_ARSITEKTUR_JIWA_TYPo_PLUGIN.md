# Handoff — Arsitektur Jiwa, Typo Multibahasa, Plugin Jembatan (2026-04-24)

## Narasi singkat (status sesi terputus)

Sesi sebelumnya terhenti karena **batas kuota API** saat membangun tiga sistem sekaligus. Yang **sudah ada di disk** sebelum putus (atau ditambah paralel):

- Folder korpus/arsitektur di `brain/`: **`nafs/`**, **`aql/`**, **`qalb/`** berisi modul Python mandiri (`response_orchestrator.py`, `learning_loop.py`, `healing_system.py`) — ini **implementasi referensi** di pohon `brain/`, selaras konsep 7 pilar di `brain/public/research_notes/189_arsitektur_jiwa_7_pilar_sidix.md`.
- **Runtime yang terpasang ke agen** berada di **`apps/brain_qa/brain_qa/jiwa/`** (`JiwaOrchestrator`, `NafsRouter`, hook Aql/Hayat/Qalb) — lihat **`brain/public/research_notes/190_jiwa_implementasi_7_pilar_wiring.md`**.
- Folder **`kimi-plugin/`** di root awalnya kosong — sesi ini diisi **stub + README** (tanpa kunci API, tanpa vendor wajib).
- **`brain/typo/`** sebelumnya belum ada — sesi ini menambah **`MULTILINGUAL_TYPO_FRAMEWORK.md`** + **`pipeline.py`** (kerangka universal, tanpa layanan eksternal).

**Risiko duplikasi konsep:** ada dua lapisan kode Jiwa — `brain/nafs|aql|qalb` (dokumentasi + modul bebas) vs `brain_qa/jiwa` (terintegrasi FastAPI). Agen berikutnya harus memutuskan: **mengarahkan impor** dari satu sumber saja atau **menyatukan** implementasi.

## Prioritas lanjutan (urutan)

1. ~~**Wire `brain/typo/pipeline.py`**~~ **Selesai (2026-04-24):** `apps/brain_qa/brain_qa/typo_bridge.py` + awal `run_react` (setelah gate keamanan). Nonaktif: `SIDIX_TYPO_PIPELINE=0`.
2. **Lengkapi pilar `brain/ruh`, `hayat`, `ilm`, `hikmah`** di pohon `brain/` hanya jika ingin mirror kode; kalau tidak, cukup README delegasi (sudah sesuai catatan di `JiwaOrchestrator`).
3. **Plugin `kimi-plugin/`**: implementasi nyata = HTTP ke endpoint **self-hosted** yang Anda kontrol; jangan commit URL/token.
4. **Uji regresi:** `pytest` + smoke chat satu putaran setelah menyambung typo pipeline.

## File dokumen baru (sesi ini)

| File | Fungsi |
|------|--------|
| `docs/PRD_ARSITEKTUR_JIWA_MULTILINGUAL_TYPO_ASSISTANT_PLUGIN.md` | PRD internal (ID + ringkasan EN) |
| `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md` | Spesifikasi typo-resilience universal |
| `brain/jiwa/README.md` | Peta folder + taut ke `brain_qa.jiwa` |
| `brain/ruh|hayat|ilm|hikmah/README.md` | Delegasi ke modul yang sudah ada |
| `kimi-plugin/README.md` + `bridge.py` | Kontrak plugin opsional |
| `kimi-plugin/manifest.json` + `sidix_skill.yaml` | Manifest + skill (MCP default off) |
| `brain/typo/TYPO_RESILIENT_FRAMEWORK.md` | 4-layer typo Indonesia |
| `docs/KIMI_INTEGRATION_GUIDE.md`, `docs/BRIEF_SIDIX_SocioMeter.md` | Integrasi + brief master |
| `brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md` | Blueprint pilar Jiwa (korpus) |
| `docs/MAPPING_FRAMEWORK_TO_REPO.md` | Peta impor `Framework_bahasa_plugin_update` → path git + status spec vs kode |
| `docs/sociometer/` | Paket dokumen SocioMeter (PRD, ERD, strategi, …) |

## Aturan tetap proyek

- Standing alone: **tanpa API vendor** sebagai dependensi wajib.
- Terminologi: Maqashid, Naskh, Raudah, Sanad, Muhasabah, Jariyah, Tafsir.
- Persona: **AYMAN, ABOO, OOMAR, ALEY, UTZ**.
- Penjelasan dokumen: **Bahasa Indonesia**; kode: **Bahasa Inggris**.
- Artefak publik: hindari nama pribadi, merek asisten, atau jejak vendor (selaras `AGENTS.md`).

---

_Agen berikutnya: baca PRD + `MULTILINGUAL_TYPO_FRAMEWORK.md` lalu lanjutkan wiring dan uji._
