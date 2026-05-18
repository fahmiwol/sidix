# SIDIX Coding Curriculum v1 (roadmap.sh → checklist → latihan)

Lihat juga ringkasan fondasi produk/AI: `docs/SIDIX_FUNDAMENTALS.md`.

**Mulai belajar sekarang (CLI):** dari root repo jalankan `python apps/brain_qa/scripts/run_curriculum_learn_now.py` — menampilkan roadmap berikutnya, taut referensi, dan cuplikan korpus terkait fondasi.

Tujuan dokumen ini: menyediakan jalur “praktis dan bisa diuji” agar SIDIX makin jago coding.

## Sumber kurikulum (data)

Snapshot roadmap dari `roadmap.sh` di:

- `brain/public/curriculum/roadmap_sh/roadmaps/*.json`
- `brain/public/curriculum/roadmap_sh/checklists/*.md`

Update dengan:

```bash
python scripts/download_roadmap_sh_official_roadmaps.py
```

## Roadmap yang dipakai (v1)

- **Backend** (`backend`)
- **Python** (`python`)
- **SQL** (`sql`)
- **System Design** (`system-design`)
- **DevOps** (`devops`)

## Cara pakai (paling minimal tapi efektif)

1. Pilih 1 roadmap untuk 1 sprint (mis. `python`).
2. Ambil **10–20 item** teratas dari checklist.
3. Untuk tiap item, buat 2 artefak:
   - **Latihan implementasi** (coding task kecil)
   - **Rubrik evaluasi** (harus lulus test / golden)

## Template latihan (copy-paste)

Untuk tiap item checklist:

- **Skill**: `<nama>`
- **Prompt**: “Implementasikan …”
- **Constraints**: input/output, kompleksitas target, edge cases
- **Tests**: unit tests + minimal 1 property/edge test
- **Rubrik**: correctness, readability, time/space, error handling

## Catatan

Checklist dari roadmap adalah “peta”; kemampuan SIDIX meningkat jika peta itu diubah menjadi:

- kumpulan problem yang bisa dieksekusi
- feedback loop (lulus/gagal) yang otomatis

