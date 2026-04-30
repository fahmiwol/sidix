# brain/jiwa — Peta Arsitektur Jiwa (korpus)

Folder ini adalah **jangkar dokumentasi** untuk tujuh pilar Jiwa di pohon `brain/`.

**Blueprint panjang (tabel pilar + fungsi):** lihat `ARSITEKTUR_JIWA_SIDIX.md` di folder ini (impor dari paket *framework*; selaraskan dengan runtime di `brain_qa` bila ada perbedaan nama file).

## Sumber kebenaran runtime

Implementasi yang dipakai **FastAPI / `agent_react`** berada di:

- `apps/brain_qa/brain_qa/jiwa/` — `JiwaOrchestrator`, `NafsRouter`, hook Aql, Hayat, Qalb.

Baca wiring: `brain/public/research_notes/190_jiwa_implementasi_7_pilar_wiring.md`.

## Modul referensi di `brain/`

| Pilar | Folder | Catatan |
|-------|--------|---------|
| Nafs | `brain/nafs/` | Respons berlapis (topik + persona) |
| Aql | `brain/aql/` | Jariyah / loop pembelajaran |
| Qalb | `brain/qalb/` | Pemantauan kesehatan / syifa |
| Ruh | `brain/ruh/` | README delegasi |
| Hayat | `brain/hayat/` | README delegasi (refine di `brain_qa.jiwa`) |
| Ilm | `brain/ilm/` | README delegasi (`learn_agent`) |
| Hikmah | `brain/hikmah/` | README delegasi (training stack) |

**Typo multibahasa:** `brain/typo/`.

Tindakan lanjut yang disarankan: satukan atau arahkan impor agar tidak ada dua versi logika yang divergen tanpa tes.
