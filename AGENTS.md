# AGENTS.md — memori & aturan untuk agen

**Siapa pun yang mengerjakan repo ini** (Cursor, Claude, IDE lain): mulai dari **urutan singkat** ini supaya tidak melewati preferensi user, fakta workspace, dan kewajiban log.

| Urutan | File | Fungsi |
|--------|------|--------|
| 1 | [`docs/00_START_HERE.md`](docs/00_START_HERE.md) | Pintu masuk manusia + agen; status & rencana eksekusi. |
| 2 | **`AGENTS.md` (file ini)** | Preferensi belajar, fakta workspace, Projek Badar, **wajib** `LIVING_LOG` untuk pekerjaan berarti. |
| 3 | [`docs/LIVING_LOG.md`](docs/LIVING_LOG.md) | Riwayat keputusan/uji/impl terbaru (append-only; baca bagian bawah). |
| 4 | [`CLAUDE.md`](CLAUDE.md) | SSOT tambahan untuk Claude: **MASTER_ROADMAP**, DEVELOPMENT_RULES, North Star, keamanan, UI lock. |
| 5 | [`docs/NORTH_STAR.md`](docs/NORTH_STAR.md) · [`docs/MASTER_ROADMAP_2026-2027.md`](docs/MASTER_ROADMAP_2026-2027.md) · [`docs/SIDIX_CAPABILITY_MAP.md`](docs/SIDIX_CAPABILITY_MAP.md) | Arah produk, sprint canonical, kemampuan teknis. |

Transcript Cursor untuk kutipan user: folder `agent-transcripts` di profil Cursor (lihat root [`CLAUDE.md`](CLAUDE.md) / README proyek). **Jangan** commit secret; ikuti bagian keamanan di `CLAUDE.md` bila relevan.

---

## Learned User Preferences

- Prefers responses in Indonesian when the prompt is Indonesian.
- Wants a “brain pack” approach: start with RAG + structured memory + evaluation before considering fine-tuning (e.g., LoRA).
- Product scope clarification: long-term vision is a multipurpose LLM+agent (GPT/Gemini/Claude-like), but MVP can prioritize RAG-first and defer full pretraining/fine-tuning and heavy UI until later.
- Keep sensitive/private “brain” data out of git; use a dedicated private folder (e.g., `brain/private/`) and ignore it.
- Public-facing project identity should be anonymous; user prefers being referred to as “Mighan” for this AI project.
- Strong preference for source-based writing with citations/sanad; do not propose “hide footprints” or plagiarism strategies.
- When asked to scan/drives or ingest files, **read-only screening** only; never edit/move/delete files on user drives unless explicitly requested.
- **Inference / vendor API — ATURAN KERAS (koreksi eksplisit user, 2026-04-16):** Mighan = stack sendiri (model/serving/agent loop/RAG/memory/eval). **JANGAN** jadikan Claude API / OpenAI / Gemini API sebagai rekomendasi *default* untuk inference atau arsitektur inti. Boleh disebut **hanya** sebagai perbandingan, benchmark, atau jembatan sementara POC — dan **harus dilabeli sebagai itu**. Bila ada trade-off: jelaskan dua jalur (self-hosted vs API) dan defaultkan ke own stack. API eksternal **hanya OK** jika user menulis eksplisit: "pakai Claude API untuk …" atau "POC pakai API".

## Learned Workspace Facts

- Primary workspace root is `D:\MIGHAN Model` on Windows (PowerShell environment).
- **Orientasi repo (manusia + agen)**: mulai dari `docs/00_START_HERE.md`; snapshot fokus di `docs/STATUS_TODAY.md`.
- **Fondasi SIDIX / IHOS (referensi singkat):** `docs/SIDIX_FUNDAMENTALS.md` — produk, definisi IHOS vs mnemonik feeding, lapisan AI; pelengkap praktis: `docs/SIDIX_CODING_CURRICULUM_V1.md`.
- **Mode agen (sandbox file):** tool `workspace_*` di `brain_qa/agent_tools.py`; root `apps/brain_qa/agent_workspace/` atau `BRAIN_QA_AGENT_WORKSPACE`; tulis file butuh `allow_restricted: true` pada `POST /agent/chat`; `/health` mengekspor `agent_workspace_root`.
- **Nama UI app**: **SIDIX** (diganti dari NEONIX; jangan pakai nama lama).
- **brain_qa sudah jalan** (`apps/brain_qa/`): RAG index+ask+cite, curation pipeline, Hafidz ledger (Merkle), distributed storage (CID + Reed-Solomon 4+2 via `reedsolo`), data tokens (HMAC), persona router (5: TOARD/FACH/MIGHAN/HAYFAR/INAN), autosuggest, auto-escalate; retrieval reranks BM25 hits by YAML frontmatter `sanad_tier` per note (`brain_qa/sanad_ranking.py`) — re-index dengan `python -m brain_qa index` setelah mengubah tier. CLI entry: `python -m brain_qa`.
- **Praxis (meta-pembelajaran agen):** setiap `run_react` menulis JSONL + lesson Markdown di `brain/public/praxis/lessons/` (modul `brain_qa/praxis.py`); agen luar bisa `python -m brain_qa praxis note ...`; indeks ulang dengan `python -m brain_qa index` supaya masuk BM25; `GET /agent/praxis/lessons`.
- **Praxis runtime (L0):** `brain/public/praxis/patterns/case_frames.json` + `brain_qa/praxis_runtime.py` — pilih **niat / inisiasi / cabang if_data vs if_no_data**; **`planner_step0_suggestion`** bisa memilih `orchestration_plan` di step 0 bila frame orkestrasi kuat; **`implement_frame_matches`** memperluas jalur `workspace_list` setelah corpus; **`session.praxis_matched_frame_ids`** + field API sama nama (bersama `case_frame_ids`); disuntik ke jawaban final + lesson (bukan sekadar daftar file).
- **Canonical GitHub (SIDIX):** https://github.com/fahmiwol/sidix — setelah pekerjaan material (Praxis, planner, API), **commit dan push** ke `main` agar kontinuitas multi-agen terjaga; workspace lokal Windows bisa bernama `MIGHAN Model` namun isi mengikuti repo itu.
- **SIDIX LoRA (inference lokal):** adapter **flat** di `apps/brain_qa/models/sidix-lora-adapter/` — wajib **`adapter_model.safetensors`** + `adapter_config.json` + tokenizer; kode (`brain_qa/local_llm.py`) juga mendeteksi layout nested lama.
- **Sprint “SIDIX enak dipakai” (±2 jam, scope realistis):** `docs/SPRINT_SIDIX_2H.md` — `/health` + `/agent/generate` + polish UI (bukan parity penuh Cursor/Claude).
- **4 proyek paralel aktif**: Mighan-brain-1 (Python+SIDIX UI), Galantara (Three.js, 3D isometric), Tiranyx (PHP 8, CRM), ABRA (Next.js 15).
- **Windows-specific**: PowerShell `&&` tidak valid — pakai `;` atau `cmd /c`; `zfec` gagal tanpa MSVC — pakai `reedsolo`.

## Konteks Multi-Agent / Handoff

- **Cursor** = developer awal (menulis sebagian besar CLI brain_qa, ledger, storage, curation pipeline). Pada 2026-04-16 menyerahkan kontinuitas ke Claude sebagai *partner*, bukan sekadar alat.
- **Claude** = partner aktif — bantu keputusan arsitektur, temukan celah risiko, tulis rencana yang bisa dieksekusi, usulan teknis selaras visi own-stack.
- Agen lain yang pernah berkontribusi: Antigravity (Gemini 3.1 Pro) — curation/validator/dashboard; Local Cursor (GPT-5.2) — ledger, storage, tokens, distributed RAG research.
- Semua agen wajib mencatat di `docs/LIVING_LOG.md` — proyek ini open-source (MIT), log harus cukup jelas agar siapapun bisa memahami riwayat keputusan.

## Projek Badar (114 langkah) & keselamatan struktur folder

- **Master checklist:** `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md` (114 baris; makna sprint = metafora operasional, **bukan** tafsir).
- **Urut dependensi + pemecahan batch:** `docs/PROJEK_BADAR_BATCH_CURSOR_50.md` (50), `docs/PROJEK_BADAR_BATCH_CLAUDE_54.md` (54), `docs/PROJEK_BADAR_BATCH_SISA_10.md` (10); generator: `scripts/split_projek_badar_batches.py`.
- **Handoff prompt Claude:** `docs/HANDOFF_CLAUDE_PROJEK_BADAR_54.md`.
- **Penyelarasan tujuan Cursor + Claude:** `docs/PROJEK_BADAR_GOALS_ALIGNMENT.md` (G1–G5, bukti selesai, peran batch A/B/C).
- **Nilai / batas narasi internal:** `docs/PROJEK_BADAR_INTERNAL_BACKBONE.md`.
- **Larangan keras:** jangan **menghapus** folder atau melakukan operasi destruktif massal; jangan **memindahkan** atau **mengubah struktur folder** tanpa izin eksplisit pemilik repo.

## Living log (wajib untuk agent)

- User meminta **semua** hasil uji, implementasi, perubahan material, error, ringkasan log, dan **keputusan** dicatat secara berkelanjutan di `docs/LIVING_LOG.md` (append-only; jangan hapus riwayat).
- Setelah pekerjaan berarti (bukan typo satu karakter), **tambahkan entri** di bagian **Log** file tersebut: heading tanggal `### YYYY-MM-DD`, lalu bullet dengan **tag wajib** — `TEST:` `FIX:` `IMPL:` `UPDATE:` `DELETE:` `DOC:` `DECISION:` `ERROR:` `NOTE:` — lihat tabel di `docs/LIVING_LOG.md`.
- Tanpa secret (redact / sebut nama env var saja).

