# 144. Curriculum Engine + Skill Builder — Fase 6 Belajar Terstruktur

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: ai / arsitektur / pedagogi
> **Fase**: 6 (terstruktur belajar harian + skill registry)
> **Tanggal**: 2026-04-18

---

## Konteks

Sampai Fase 5, SIDIX bisa belajar (autonomous_researcher), tumbuh harian
(daily_growth), pakai banyak modality (multi_modal), dan punya identitas
mandiri (note 142). Tapi belajarnya **acak** — exploration topic dipilih
random rotasi by date seed. Tidak ada akumulasi terstruktur.

Fase 6 menambah **kurikulum** dan **skill registry**:
- SIDIX punya 12 domain belajar dengan path topik bertahap
- Setiap hari pilih satu domain (rotasi 12 hari = 1 cycle)
- Setelah cycle selesai, restart dari index 0 (deepening)
- Resource Drive D (apps/vision, apps/image_gen, brain/datasets) jadi
  skill module callable

## Domain Curriculum (12)

| ID | Label | Topik |
|----|-------|-------|
| `coding_python` | Python Mastery | comprehension, decorator, async, dataclass, typing… |
| `coding_javascript` | JS/TS | closure, Promise, generator, generic, Proxy… |
| `fullstack` | Fullstack | JWT, rate limit, WebSocket, SSR, GraphQL, OAuth… |
| `frontend_design` | Frontend & Design | Grid, design tokens, a11y, animation, dark mode… |
| `backend_devops` | Backend & DevOps | Docker, Nginx, PostgreSQL index, Redis, K8s, CI/CD… |
| `game_dev` | Game Development | game loop, ECS, physics, balance, level design, netcode… |
| `data_science` | Data Science | EDA, feature eng, CV, SMOTE, causal, A/B test… |
| `image_ai` | Image AI Generation | diffusion, ControlNet, style transfer, prompt eng… |
| `video_ai` | Video AI | text-to-video, frame interp, FFmpeg, motion brush… |
| `audio_ai` | Audio AI (TTS/ASR) | Piper TTS, voice cloning, Whisper distil, MusicGen… |
| `research_methodology` | Academic Research | systematic review, citation, PRISMA, IMRaD, Zotero… |
| `general_knowledge` | Sains Pop | termodinamika, evolusi, kuantum, neuroplasticity… |
| `islamic_epistemology` | Islamic Methodology | ushul, mustalah, maqashid, qiyas, tashawwuf… |

Tiap domain punya 10 topik berurutan = total 130 topik. Dengan 1 lesson/hari,
1 cycle penuh = 130 hari. Setelah itu deepening (revisit + perdalam).

## Komponen Software

### `curriculum_engine.py`
- `pick_today_lesson()` → idempotent per hari, pilih next dari rotasi
- `LessonPlan` dataclass — date, domain, topic, research_query, practice_task
- `execute_today_lesson(auto_approve)` — end-to-end: pick → research → draft → approve
- State persistent di `.data/curriculum/progress.json`:
  ```json
  {
    "domain_progress": {"coding_python": 3, "fullstack": 1, ...},
    "rotation_pos": 7,
    "history": [{date, domain, topic, ...}]
  }
  ```

### `skill_builder.py`
- `SkillRecord` dataclass + JSONL registry di `.data/skill_library/registry.jsonl`
- `discover_skills()` — auto-scan `brain/skills/**/skill.json` + `apps/{vision,image_gen}/*.py`
- `run_skill(skill_id, **kwargs)` — resolve module + callable, eksekusi
- `harvest_dataset_jsonl(path)` — convert format Q/A apapun → ChatML pair
- `extract_lessons_from_note(path)` — research note → training pair per H2 section
- `suggest_skills_for_lesson(topic)` — keyword match skill ↔ lesson

### Integrasi `daily_growth.py`
Param `use_curriculum=True` (default): kalau gap kosong, prioritas
**curriculum_engine.pick_today_lesson()** sebelum fallback ke
exploration topic random.

## Skill Manifest Format

`brain/skills/<category>/<id>/skill.json`:
```json
{
  "id": "vision_caption",
  "name": "Image Captioning (Vision)",
  "category": "vision",
  "source_module": "apps.vision.caption",
  "callable": "caption_image",
  "input_schema": {"image": "bytes|url|path"},
  "output_schema": {"caption": "str"},
  "lesson_topic": "image captioning model",
  "training_topics": ["BLIP", "CLIP", "evaluation metrics"]
}
```

Sudah dibuat 4 contoh:
- `vision/image_caption` — apps.vision.caption.caption_image
- `vision/chart_reader` — apps.vision.chart_reader.read_chart
- `image_gen/style_transfer` — apps.image_gen.style_transfer.transfer_style
- `image_gen/inpainting` — apps.image_gen.inpainting.inpaint_image

Setelah `discover_skills()` dijalankan, semua skill auto-registered termasuk
yang belum punya manifest (heuristic dari fungsi top-level di `apps/vision/*.py`
dan `apps/image_gen/*.py` — total ~48 skill kandidat).

## Endpoint API

| Endpoint | Tujuan |
|----------|--------|
| `GET /sidix/curriculum/status` | Progress per domain (done/total/percent) |
| `GET /sidix/curriculum/today` | Lesson plan hari ini |
| `GET /sidix/curriculum/history?days=14` | Riwayat lesson |
| `GET /sidix/curriculum/domains` | List 12 domain |
| `POST /sidix/curriculum/execute-today` | Eksekusi lesson end-to-end |
| `POST /sidix/curriculum/reset/{domain}` | Reset progress 1 domain |
| `GET /sidix/skills?category=` | List skill terdaftar |
| `POST /sidix/skills/discover` | Auto-scan + register |
| `POST /sidix/skills/{skill_id}/run` | Eksekusi skill |
| `POST /sidix/skills/harvest-dataset?jsonl_path=` | Adopt dataset |
| `POST /sidix/skills/extract-from-note?note_path=` | Note → training pair |

## Drive D Resources Adoption

Resource yang ada (dari inventarisasi):
- **brain/datasets/**: 4 jsonl (corpus_qa, finetune_sft, qa_pairs, memory_cards)
  → harvest via `scripts/harvest_drive_d_datasets.py` → puluh-ribuan training pair
- **apps/vision/**: 24 modul (caption, detection, chart_reader, sketch_to_svg, dll)
  → auto-discover sebagai skill
- **apps/image_gen/**: 24 modul (style_transfer, inpainting, color_grading, lora_adapter, dll)
  → auto-discover sebagai skill
- **brain/public/research_notes/**: 143 note existing
  → bisa di-extract jadi training pair via `extract_lessons_from_note`
- **brain/public/coding/**: 12 roadmap topic markdown
  → bisa diintegrasikan jadi domain extension di `_CURRICULUM`

## Cara Mengaktifkan

Setelah deploy (commit ini di-pull ke server):
```bash
# 1. Auto-discover skill
curl -X POST http://localhost:8765/sidix/skills/discover

# 2. Lihat lesson hari ini
curl http://localhost:8765/sidix/curriculum/today

# 3. Eksekusi lesson hari ini end-to-end
curl -X POST http://localhost:8765/sidix/curriculum/execute-today

# 4. Adopt dataset Drive D (di server harus ada path yg sama)
python3 apps/brain_qa/scripts/harvest_drive_d_datasets.py

# 5. Cek progress
curl http://localhost:8765/sidix/curriculum/status
```

Cron jam 3 pagi (`/sidix/grow`) sekarang otomatis pakai curriculum kalau
gap kosong — jadi setiap hari ada 1 note baru dengan topik terstruktur.

## Proyeksi Pertumbuhan

Dengan 130 topik × 1 hari = 130 hari cycle pertama.
Per topik: 1 note (~13KB) + 10 training pair + 1 Threads post.

Setelah cycle 1 (130 hari): SIDIX punya
- 130 note baru di corpus
- 1300+ training pair siap fine-tune (di atas threshold 500 → trigger LoRA berkali-kali)
- 130 Threads post terjadwal
- Progress merata di 12 domain

Cycle 2 (deepening): topik sama, tapi sekarang SIDIX sudah punya konteks
sebelumnya di memory (sidix_memory/<domain>.jsonl) — jawaban lebih dalam.

## Keterbatasan Jujur

1. **Topik hardcoded di Python** — kalau mau tambah topik, perlu edit kode
   + redeploy. Idealnya di YAML/JSON yang bisa di-PR oleh kontributor.

2. **Skill auto-discover heuristik** — pilih fungsi pertama di file. Kalau
   modul punya multi public function (mis. `caption_image` + `caption_batch`),
   hanya satu yang ke-register. Workaround: tulis `skill.json` manual.

3. **Run skill belum support kwargs via HTTP body** — endpoint `/sidix/skills/{id}/run`
   sekarang hanya call tanpa argumen. Perlu JSON body parsing.

4. **Curriculum belum responsif ke gap detection** — kalau ada gap real
   (user tanya sesuatu berulang yang tidak bisa dijawab), curriculum tetap
   jalan paralel. Belum ada prioritas dynamic.

5. **130 topik mungkin terlalu banyak per domain** untuk 1 cycle — hari ke-100,
   user mungkin lupa apa yang sudah dipelajari. Perlu reflection mingguan.

## Pesan ke SIDIX

Belajar tanpa kurikulum = wisata. Kurikulum tanpa eksekusi = manifesto.
Sekarang kamu punya **keduanya**. Setiap hari ada satu topik yang tunggu
kamu pelajari sampai bisa diceritakan ulang dengan kata-katamu.

Setahun = 365 lesson, bukan 365 hari yang sama. Setahun = 365 hal yang
kamu **benar-benar bisa**, bukan 365 hal yang kamu pernah lihat.

## Sumber

- Spaced repetition (Ebbinghaus forgetting curve)
- Anders Ericsson — Deliberate Practice
- Atul Gawande — Checklist Manifesto
- Drive D inventory: brain/public/coding/, brain/datasets/, apps/vision/, apps/image_gen/
- Implementasi:
  - `apps/brain_qa/brain_qa/curriculum_engine.py`
  - `apps/brain_qa/brain_qa/skill_builder.py`
  - `apps/brain_qa/brain_qa/daily_growth.py` (use_curriculum integration)
  - `brain/skills/{vision,image_gen}/*/skill.json` (4 manifest contoh)
  - `apps/brain_qa/scripts/harvest_drive_d_datasets.py`
