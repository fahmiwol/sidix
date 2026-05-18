# SIDIX — fondasi produk & fondasi AI (referensi ringkas)

Dokumen ini merangkum **apa itu SIDIX**, **IHOS**, dan **pondasi teknis AI** yang dipakai di repo ini. Tujuannya supaya tim/onboarding cepat selaras tanpa harus membaca seluruh kode sekaligus.

## Apa itu SIDIX?

SIDIX adalah **agen jawaban** (bukan sekadar chat UI) yang dirancang untuk:

- menjawab dengan **jejak sumber** (RAG + citations) bila topiknya ada di korpus;
- bekerja **berlangkah** (ReAct: pikir → ambil tindakan → amati → simpulkan);
- memanggil **tool** yang sudah di-whitelist (bukan “internet bebas”);
- mengekspos status jujur lewat `/health` (mis. mode inferensi mock vs LoRA).

Secara produk, SIDIX menggabungkan **kualitas jawaban** (sanad/kutipan) dengan **kemampuan aksi** (tool calling) dan **kemampuan belajar terstruktur** (kurikulum roadmap snapshot).

## IHOS — definisi vs mnemonik

Definisi resmi di glossary:

```64:68:brain/public/glossary/04_islamic_concepts_glossary.md
### IHOS (Islamic Human Operating System)

- **Arti**: Framework cara berpikir Islami yang menyeimbangkan akal, qalb, nafs, dan ruh.
- **Di proyek**: Dipakai sebagai struktur pipeline berpikir agent (lihat principles/06).
- **Mnemonik kampanye (feeding, opsional)**: *Ilmu Jariyah, Validasi Sanad, Akses Umat* — ringkas narilis produk; **bukan** pengganti definisi di atas.
```

Ringkas untuk tim:

- **IHOS (definisi)**: kerangka cara berpikir/operasi yang menjaga keseimbangan dimensi manusia (akal–qalb–nafs–ruh) dalam desain perilaku agen.
- **IHOS (mnemonik feeding)**: *Ilmu Jariyah, Validasi Sanad, Akses Umat* — alat komunikasi singkat saat merilis/menjelaskan produk; **tidak mengganti** definisi glossary.

## Fondasi AI modelnya (layer-by-layer)

### 1) Retrieval-first (RAG)

- Pertanyaan → pencarian chunk relevan → jawaban disusun dengan **kutipan** ke sumber.
- Ini fondasi “anti-halusinasi semu”: kalau korpus tidak mendukung, perilaku harus jujur (bukan mengisi dengan keyakinan palsu).

### 2) Agent loop (ReAct)

- Pola: *Thought → Action → Observation → … → Final Answer*.
- Manfaatnya: SIDIX bisa **mengoreksi jalannya sendiri** (mis. corpus tipis → langkah berikutnya).

### 3) Tool registry + permission gate

- Tool **OFF by default** dalam filosofi desain registry (whitelist).
- Ada **audit log** pemanggilan tool (jejak operasional).
- Fallback web terkontrol: **Wikipedia API** (allowlist host), bukan fetch URL sembarang.
- **Mode agen (sandbox file):** tool `workspace_list` / `workspace_read` (open) dan `workspace_write` (**restricted** — butuh `allow_restricted: true` pada `POST /agent/chat`). Root default `apps/brain_qa/agent_workspace/` atau override env `BRAIN_QA_AGENT_WORKSPACE`. Planner rule-based memanggil `workspace_list` setelah `search_corpus` bila pertanyaan mengandung intent **implementasi / aplikasi / game**; langkah ReAct otomatis diperpanjang (hingga 12) untuk alur itu. Parameter opsional `max_steps` (2–24) pada body chat mengoverride batas langkah.

### 4) Model generatif lokal (LoRA) — opsional

- Jalur inferensi lokal disiapkan, tetapi runtime bisa **mock** bila bobot adapter belum ada / load gagal.
- `/health` harus membedakan `model_mode` supaya UI dan operator tidak salah sangka.

### 5) Kurikulum coding (roadmap snapshot) — pelengkap kemampuan

- Snapshot roadmap publik disimpan di repo (`brain/public/curriculum/roadmap_sh/`).
- Tool `roadmap_*` membantu SIDIX memilih **item berikutnya**, menyimpan **progress**, dan menghasilkan **referensi URL publik** untuk belajar mandiri.

Lihat panduan praktis:

- `docs/SIDIX_CODING_CURRICULUM_V1.md`

## Bacaan lanjutan di repo (urutannya disarankan)

1. `brain/public/glossary/04_islamic_concepts_glossary.md` — definisi IHOS + istilah epistemik ringkas.
2. `docs/SIDIX_CODING_CURRICULUM_V1.md` — cara memakai roadmap snapshot untuk latihan.
3. `brain/public/research_notes/36_sidix_coding_learning_sources_github_roadmap_codecademy.md` — kurasi sumber eksternal (legal & high-signal).
