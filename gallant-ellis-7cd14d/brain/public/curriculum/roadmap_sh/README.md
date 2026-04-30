# roadmap.sh curriculum snapshot

Folder ini menyimpan **snapshot** data roadmap publik dari `roadmap.sh` untuk dipakai sebagai:

- kurikulum terstruktur (graph nodes/edges)
- checklist skill untuk latihan/evaluasi SIDIX
- corpus tambahan untuk RAG (bila diindeks)

## Sumber data

Unduh via endpoint publik:

- `https://roadmap.sh/api/v1-official-roadmap/<slug>`

Contoh slug:

- `backend`
- `python`
- `sql`
- `system-design`
- `devops`

## Cara update

Jalankan:

```bash
python scripts/download_roadmap_sh_official_roadmaps.py
```

Output:

- JSON: `brain/public/curriculum/roadmap_sh/roadmaps/<slug>.json`
- Checklist: `brain/public/curriculum/roadmap_sh/checklists/<slug>.md`

