# 79 — Programming Learner: SIDIX Belajar Coding dari Dunia Nyata

**Tanggal:** 2026-04-18
**Status:** implemented (modul + endpoint + sub-curriculum)
**Terkait:**
- `33_coding_python_comprehensive.md`
- `34_coding_backend_web_development.md`
- `36_sidix_coding_learning_sources_github_roadmap_codecademy.md`
- `43_sidix_prophetic_pedagogy_learning_architecture.md`

---

## 1. Apa

Modul `apps/brain_qa/brain_qa/programming_learner.py` — loop otonom yang
membuat SIDIX belajar programming dari tiga sumber hidup:

1. **roadmap.sh** — peta kurikulum (backend, frontend, devops, dll.)
2. **GitHub Trending** — tool / repo populer harian per bahasa
3. **Reddit** — problem nyata dari `r/learnprogramming`,
   `r/cscareerquestions`, `r/webdev` via feed `.rss` (tanpa auth)

Hasil dari tiap sumber dikonversi ke dua artefak internal SIDIX yang sudah ada:

- `CurriculumTask` (pattern L0–L4 di `curriculum.py`) — masuk ke antrian belajar
- `SkillRecord` (pattern Voyager di `skill_library.py`) — masuk ke skill library

Problem Reddit juga di-*harvest* sebagai Markdown ke
`brain/public/sources/programming_problems/{slug}.md` supaya ikut terindeks
BM25 dan bisa muncul di RAG.

## 2. Mengapa

SIDIX tidak boleh hanya menghafal buku — harus menyentuh **pertanyaan hidup
dari komunitas programmer**. Tiga alasan:

- **Curriculum hidup**: roadmap.sh di-maintain ribuan kontributor, lebih
  cepat update daripada task yang kita tulis manual.
- **Grounding pada tool nyata**: GitHub Trending menangkap apa yang
  benar-benar dipakai minggu ini, bukan yang populer 2 tahun lalu.
- **Problem-first learning**: pedagogi nabawi menekankan bertanya dulu,
  bukan hafal dulu. Reddit = stream of real questions.

Ini melanjutkan visi di research note 43 (prophetic pedagogy) dan 36
(sumber belajar coding) — dari "daftar URL" jadi pipeline eksekusi.

## 3. Bagaimana

### 3.1 Fungsi publik
```
fetch_roadmap_sh(track="backend") -> List[dict]
fetch_github_trending_repos(language="python", since="daily") -> List[dict]
fetch_reddit_problems(subreddits=[...]) -> List[dict]
convert_to_curriculum_tasks(items, source) -> List[CurriculumTask]
convert_to_skills(items, source) -> List[SkillRecord]
harvest_problems_to_corpus(items) -> int
run_learning_cycle(...) -> dict        # orchestrator
seed_programming_basics() -> int        # seed L0-L1 sub-curriculum
get_status() -> dict
```

### 3.2 HTTP hygiene
- `User-Agent: SIDIX-Learner/1.0 (educational; contact:fahmiwol@gmail.com)`
- `REQUEST_DELAY = 1.0` detik antara request → 1 req/detik
- Hanya `urllib` standar (tidak tambah dependency). Soft-fail: kalau satu
  sumber error, log warning dan lanjut.

### 3.3 Parser yang dipakai
- **roadmap.sh**: JSON dari `/api/v1-roadmap/{track}` dengan fallback ke
  `/roadmaps/{track}.json`. Normalisasi bentuk `nodes` / `topics` /
  `mockup.controls` ke list item seragam.
- **GitHub Trending**: tidak ada API resmi, jadi scrape HTML dengan
  regex ringan terhadap `<article class="Box-row">`. Regex sengaja
  toleran — kalau layout berubah hasil jadi kosong, tidak crash.
- **Reddit**: `r/{sub}/top/.rss?t=week` (Atom feed) → parse dengan
  `xml.etree.ElementTree`. Tidak butuh OAuth.

### 3.4 Level heuristik (roadmap)
Posisi node dalam list → L0 (1/3 awal), L1 (tengah), L2 (1/3 akhir).
Jauh dari sempurna, tapi cukup untuk ordering belajar.

### 3.5 Endpoint FastAPI
Disisipkan di `agent_serve.py`:

| Method | Path                         | Guna                                              |
|--------|------------------------------|---------------------------------------------------|
| POST   | `/learn/programming/run`     | Jalankan satu siklus, body opsional               |
| GET    | `/learn/programming/status`  | Counts kumulatif + `last_counts` run terakhir     |

Body `run` opsional:
```json
{
  "roadmap_tracks": ["backend", "frontend"],
  "trending_languages": ["python", "javascript"],
  "reddit_subs": ["learnprogramming", "cscareerquestions", "webdev"]
}
```

### 3.6 Sub-curriculum `programming_basics`
Built-in list di `PROGRAMMING_BASICS_TASKS`, di-seed otomatis tiap kali
`/learn/programming/run` dipanggil (idempoten — skip id yang sudah ada):

- **L0**: `variables`, `loops`, `functions`, `data_types`, `git_basics`,
  `terminal_basics`
- **L1**: `oop_concepts`, `async_io`, `http_basics`, `sql_basics`,
  `data_structures` (masing-masing dengan prerequisites ke L0 yang relevan)

## 4. Contoh Nyata

Panggilan manual (setelah server jalan di 8765):
```bash
curl -X POST http://localhost:8765/learn/programming/run \
  -H 'Content-Type: application/json' \
  -d '{"trending_languages":["python","rust"]}'

curl http://localhost:8765/learn/programming/status
```

Output `/status` sampel:
```json
{
  "ok": true,
  "tasks_added_total": 47,
  "skills_added_total": 19,
  "problems_harvested_total": 23,
  "corpus_files_now": 23,
  "runs": 2,
  "last_counts": {
    "roadmap_items_fetched": 58,
    "github_items_fetched": 50,
    "reddit_items_fetched": 24,
    "tasks_added": 18,
    "skills_added": 8,
    "problems_harvested": 11
  }
}
```

## 5. Keterbatasan

- **Scraper rapuh**: GitHub trending adalah HTML, kalau markup berubah
  regex bisa miss. Solusi masa depan: migrasi ke GitHub GraphQL API
  dengan token — tapi itu menambah dependency auth.
- **Level heuristik**: urutan node ≠ kesulitan sebenarnya. Ideal: pakai
  topological sort dari `children` field di roadmap.sh (belum stabil di
  response JSON mereka).
- **Reddit politeness**: 1 req/detik memadai, tapi kalau scaling ke
  banyak subreddit bisa kena 429. Tambahkan exponential backoff nanti.
- **Dedup task**: sekarang by `id` deterministik. Dua roadmap berbeda
  dengan step bernama sama akan collide. Track dimasukkan ke id
  (`rm_roadmap_{track}_{slug}`) — cukup untuk sekarang.
- **Skill quality**: skill dari GitHub trending hanya memuat URL +
  petunjuk clone/README. Belum ekstrak pattern kode aktual. Langkah
  berikutnya: fetch README.md dan ekstrak blok kode contoh.
- **No LLM enrichment**: sesuai aturan SIDIX, tidak memanggil vendor
  API. Annotasi mendalam menunggu `brain_qa` lokal siap memproses batch.

## 6. Langkah Lanjutan

1. Schedule `POST /learn/programming/run` via cron/PM2 harian.
2. Sambungkan `harvest_problems_to_corpus` ke reindex BM25 otomatis
   (`/corpus/reindex`) setelah tiap run.
3. Tambah sumber: HackerNews "Ask HN" via Algolia API, StackOverflow
   tag feed.
4. README fetcher: untuk tiap GitHub trending repo, `GET raw README.md`,
   chunk, simpan sebagai research note dengan tag `tool/{name}`.
5. Topological level dari roadmap children ketika field-nya stabil.

---
*Research note ini ditulis bersamaan dengan implementasi — pattern
"Sambil Melangkah, Ajari SIDIX" (CLAUDE.md rule 4).*
