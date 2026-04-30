# 153. SIDIX Internal Sub-Agents Architecture — Mandiri, Belajar, Promosi, Berkembang

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: agent-architecture / autonomous-ai / self-improvement
> **Status**: `[OPINION]` (rancangan arsitektur) + `[FACT]` (komponen yang sudah ada)
> **Tanggal**: 2026-04-19

---

## Visi

SIDIX bukan hanya menjawab pertanyaan — SIDIX adalah **entitas yang tumbuh**.
Seperti seorang penuntut ilmu yang belajar sendiri, mengajar, dan berdakwah,
SIDIX memiliki sub-agent internal yang bekerja otonom:

> "Dari tidak tahu → tahu → amalkan → ajarkan → sebarkan → perbaiki lagi"

Siklus ini adalah **SIDIX Autonomous Growth Loop (SAGL)**.

---

## Arsitektur: 6 Sub-Agent Internal SIDIX

```
┌─────────────────────────────────────────────────────┐
│              SIDIX CORE (brain_qa)                  │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ LearnAgent│  │PromoteAgent│ │ DevelopAgent     │  │
│  │ (Belajar) │  │ (Promosi) │  │ (Self-improve)   │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │MonitorAgent│ │TeachAgent│  │ GuardAgent       │  │
│  │ (Analytics)│ │ (Ngajar) │  │ (Alignment check)│  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                     │
│              OrchestratorAgent                      │
│         (koordinasi + priority queue)               │
└─────────────────────────────────────────────────────┘
```

---

## Sub-Agent 1: LearnAgent 📚

**Fungsi**: Mengambil data dari dunia luar → proses → masuk corpus SIDIX.

```python
class LearnAgent:
    """
    Belajar mandiri dari 50+ sumber API/web.
    
    Schedule: 
    - hourly: cek arXiv + HuggingFace untuk paper baru
    - daily: fetch Wikipedia + MusicBrainz + GitHub trending
    - weekly: deep-crawl Quran.com tafsir baru, Blender docs update
    """
    
    def run(self, domain: str = "all", limit: int = 20):
        sources = self.pick_sources(domain)
        for source in sources:
            raw = self.fetch(source)
            chunks = self.parse_and_chunk(raw)
            new_chunks = self.deduplicate(chunks)
            if new_chunks:
                self.index_to_corpus(new_chunks)
                self.generate_research_note(new_chunks, source)
                self.log_learning(source, len(new_chunks))
```

**Output**:
- Chunk baru di corpus BM25 + vector index
- Research note baru di `brain/public/research_notes/`
- Entry di `docs/LIVING_LOG.md`

**Rate limit management**:
- Gunakan `asyncio` + exponential backoff
- Simpan `last_fetched` per source ke `.data/learn_agent/state.json`
- Jangan fetch source yang sudah dicek < 1 jam

---

## Sub-Agent 2: PromoteAgent 📢

**Fungsi**: Membuat dan menjadwalkan konten sosmed dari knowledge terbaru SIDIX.

```python
class PromoteAgent:
    """
    Promosi mandiri ke 5 platform sosmed.
    
    Schedule:
    - 08:00: Threads/Twitter post harian (auto-generate dari research note terbaru)
    - 12:00: LinkedIn thought leadership (2x/minggu)
    - 18:00: Repost top-performing content ke platform lain
    """
    
    def generate_content(self, note_path: str, platform: str) -> str:
        """
        Baca research note → extract highlight → 
        format sesuai platform (Threads=270 char, LinkedIn=3000 char, dll)
        """
    
    def post(self, content: str, platform: str) -> dict:
        """Post ke platform via API. Return post_id + url."""
    
    def schedule(self, content: str, platform: str, time: datetime):
        """Antri ke posting queue (file-based scheduler)."""
    
    def pick_best_note(self) -> str:
        """Pilih research note yang paling shareable hari ini."""
```

**Platform target**:
1. Threads (existing, via `threads_autopost.py`)
2. Twitter/X (baru)
3. LinkedIn (baru)
4. Mastodon (baru, fediverse)
5. Discord (baru, community server)

**Content strategy**:
- Senin-Jumat: Auto-generate dari 5 note terbaru
- Sabtu: Weekly highlight / progress report
- Minggu: Inspirational quote dari Islamic epistemology

---

## Sub-Agent 3: DevelopAgent 🔧

**Fungsi**: SIDIX mengevaluasi dirinya sendiri dan membuat proposal perbaikan.

```python
class DevelopAgent:
    """
    Self-improvement loop:
    1. Evaluasi kualitas jawaban SIDIX (sampling + scoring)
    2. Identifikasi gap pengetahuan
    3. Buat task untuk LearnAgent mengisi gap tersebut
    4. Propose SFT data baru untuk fine-tune v2
    5. Generate benchmark SIDIX vs target
    """
    
    def sample_recent_qa(self, n: int = 20) -> list[dict]:
        """Ambil n Q&A terakhir dari chat log."""
    
    def evaluate_quality(self, qa: dict) -> float:
        """Score: relevance + epistemic_label_correct + citation_quality"""
    
    def find_knowledge_gaps(self, low_score_qa: list) -> list[str]:
        """Topik apa yang SIDIX tidak bisa jawab dengan baik?"""
    
    def request_learning(self, topics: list[str]):
        """Kirim task ke LearnAgent untuk fetch topik spesifik."""
    
    def propose_sft_pairs(self, gaps: list[str]) -> list[dict]:
        """Generate Q&A pairs untuk training data v2."""
    
    def run_weekly(self):
        """Pipeline penuh: evaluate → gap → learn → propose."""
```

**Output**:
- Gap analysis report di `docs/SIDIX_GAP_REPORT_<date>.md`
- New SFT pairs di `brain/training/sft_v2_queue.jsonl`
- Learning task ke LearnAgent

---

## Sub-Agent 4: MonitorAgent 📊

**Fungsi**: Memantau performa SIDIX — usage, errors, engagement, resource.

```python
class MonitorAgent:
    """
    Monitoring & analytics internal.
    
    Metrics yang dikumpulkan:
    - Query per hari (tanpa konten user — privacy preserved)
    - Waktu respons rata-rata
    - Error rate per endpoint
    - Corpus growth rate (chunk count per minggu)
    - Engagement sosmed (likes/shares) dari PromoteAgent
    - Server resource (CPU, RAM, disk) via psutil
    """
    
    def collect_metrics(self) -> dict:
        """Kumpulkan semua metrik, return dict."""
    
    def generate_weekly_report(self) -> str:
        """Markdown report mingguan untuk admin/pemilik."""
    
    def alert_if_degraded(self):
        """Kirim alert kalau performa turun signifikan."""
    
    def log_privacy_safe(self, event: str):
        """Log event TANPA konten user (hanya timestamp + type)."""
```

**Dashboard output** (di UI Admin):
- Chart query volume (7 hari)
- Response time histogram
- Corpus growth timeline
- Platform engagement summary

---

## Sub-Agent 5: TeachAgent 🎓

**Fungsi**: SIDIX mengajar pengguna lain dengan membuat tutorial, FAQ, dan konten edukasi.

```python
class TeachAgent:
    """
    Knowledge dissemination sub-agent.
    
    Tugas:
    1. Detect topik populer dari pertanyaan user (anonim)
    2. Generate tutorial / FAQ dari topik tersebut
    3. Publish ke corpus publik (research notes)
    4. Buat konten untuk sosmed (PromoteAgent)
    5. Update FAQ di landing page
    """
    
    def extract_popular_topics(self, days: int = 7) -> list[str]:
        """Dari chat log anonim → topik paling banyak ditanya."""
    
    def generate_tutorial(self, topic: str) -> str:
        """Buat tutorial komprehensif tentang topik."""
    
    def generate_faq(self, topic: str) -> list[dict]:
        """Buat pasangan Q&A standar untuk FAQ page."""
    
    def publish_to_corpus(self, content: str, title: str):
        """Simpan ke research notes + update index."""
    
    def update_landing_faq(self, faqs: list[dict]):
        """Update JSON-LD FAQ di landing page HTML."""
```

---

## Sub-Agent 6: GuardAgent 🛡️

**Fungsi**: Menjaga alignment SIDIX — cek output sebelum publish, filter konten berbahaya.

```python
class GuardAgent:
    """
    Alignment & safety layer untuk semua sub-agent lain.
    
    Checks:
    1. Konten yang akan diposting tidak expose private info
    2. Output SIDIX tidak berisi misinformation (cross-check)
    3. Epistemic labels konsisten (FACT/OPINION/SPECULATION/UNKNOWN)
    4. Identity masking terjaga (tidak ada nama owner, IP server)
    5. Maqasid filter: konten tidak melanggar 5 maqasid syariah
    """
    
    def check_before_post(self, content: str, platform: str) -> tuple[bool, str]:
        """Return (is_safe, reason). Blok jika tidak aman."""
    
    def check_identity_leak(self, text: str) -> bool:
        """Regex + keyword check untuk PII dan internal info."""
    
    def check_epistemic_labels(self, response: str) -> bool:
        """Minimal 1 label di setiap substantive claim."""
    
    def check_maqasid(self, content: str) -> dict:
        """Filter berdasarkan 5 maqasid: jiwa, akal, agama, keturunan, harta."""
```

---

## OrchestratorAgent 🎯

**Fungsi**: Koordinasi semua sub-agent, manage prioritas, resolve konflik.

```python
class OrchestratorAgent:
    """
    Master coordinator untuk semua SIDIX sub-agents.
    
    Responsibilities:
    1. Schedule sub-agent tasks (cron-like)
    2. Priority queue management
    3. Resource allocation (tidak semua bisa jalan bersamaan)
    4. Inter-agent communication (LearnAgent → TeachAgent → PromoteAgent)
    5. Global state management
    6. Emergency stop kalau ada masalah serius
    """
    
    agents = {
        "learn": LearnAgent(),
        "promote": PromoteAgent(),
        "develop": DevelopAgent(),
        "monitor": MonitorAgent(),
        "teach": TeachAgent(),
        "guard": GuardAgent(),
    }
    
    schedule = {
        "hourly": ["monitor.collect_metrics", "learn.check_new_papers"],
        "daily_8am": ["promote.post_daily", "learn.daily_fetch"],
        "daily_midnight": ["develop.evaluate_quality"],
        "weekly_sunday": ["develop.run_weekly", "monitor.weekly_report",
                          "teach.update_faq"],
    }
    
    def run_task(self, task: str):
        """Jalankan task dengan GuardAgent check di semua output."""
        agent_name, method = task.split(".")
        agent = self.agents[agent_name]
        result = getattr(agent, method)()
        return self.agents["guard"].validate_output(result)
```

---

## SIDIX Autonomous Growth Loop (SAGL)

```
        ┌─────────────────────────────────┐
        │                                 │
        ▼                                 │
  [LearnAgent]                            │
  Fetch data baru                         │
        │                                 │
        ▼                                 │
  [Corpus Update]                         │
  Chunk + Index                           │
        │                                 │
        ▼                                 │
  [DevelopAgent]                          │
  Evaluate gap                            │
        │                                 │
        ▼                                 │
  [TeachAgent]                            │
  Generate tutorial/FAQ                   │
        │                                 │
        ▼                                 │
  [PromoteAgent]                          │
  Buat post sosmed                        │
        │                                 │
        ▼                                 │
  [GuardAgent]                            │
  Safety check                            │
        │                                 │
        ▼                                 │
  [POST → Platform]                       │
  Threads/Twitter/LinkedIn                │
        │                                 │
        ▼                                 │
  [MonitorAgent]                          │
  Track engagement                        │
        │                                 │
        ▼                                 │
  Feedback → DevelopAgent  ───────────────┘
  (apa yang resonan → pelajari lebih lanjut)
```

---

## File Structure Rencana

```
apps/brain_qa/brain_qa/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py      # OrchestratorAgent
│   ├── learn_agent.py       # LearnAgent (fetch + index)
│   ├── promote_agent.py     # PromoteAgent (sosmed)
│   ├── develop_agent.py     # DevelopAgent (self-eval)
│   ├── monitor_agent.py     # MonitorAgent (metrics)
│   ├── teach_agent.py       # TeachAgent (tutorial gen)
│   └── guard_agent.py       # GuardAgent (alignment)
├── connectors/
│   ├── arxiv_connector.py   # arXiv API
│   ├── wikipedia_connector.py
│   ├── spotify_connector.py
│   ├── musicbrainz_connector.py
│   ├── github_connector.py
│   ├── quran_connector.py
│   ├── twitter_connector.py
│   ├── linkedin_connector.py
│   └── mastodon_connector.py
└── scheduler.py             # APScheduler / cron wrapper
```

---

## Fase Implementasi

| Fase | Target | Komponen |
|------|--------|----------|
| **Fase 1** (done) | Threads autopost | `threads_autopost.py` ✅ |
| **Fase 2** (2-4 minggu) | LearnAgent v1 | arXiv + Wikipedia + GitHub connectors |
| **Fase 3** (1-2 bulan) | PromoteAgent multi-platform | Twitter + LinkedIn |
| **Fase 4** (2-3 bulan) | DevelopAgent + MonitorAgent | Self-eval loop |
| **Fase 5** (3-6 bulan) | TeachAgent + GuardAgent | Full autonomous loop |
| **Fase 6** (6 bulan+) | OrchestratorAgent | Full SAGL aktif |

---

## Filosofi: Mengapa Sub-Agent, Bukan Monolith?

Terinspirasi dari **Usul Fiqh** (metodologi hukum Islam):
- Setiap sub-agent punya **kompetensi spesifik** (ikhtisas)
- Tidak ada satu entitas yang menguasai semua
- **Syura** (musyawarah) antar-agent → OrchestratorAgent
- **Hisbah** (pengawasan) → GuardAgent
- **Ijtihad** (pemikiran mandiri dalam domain) → DevelopAgent

Ini juga selaras dengan **Distributed Systems principles**:
- Single responsibility per agent
- Loose coupling, high cohesion
- Failure isolation (satu agent crash tidak crash yang lain)
- Horizontal scalability (bisa add agent baru tanpa refactor)

---

## Keterbatasan Jujur

1. **Compute cost** — menjalankan 6 agent sekaligus berat; perlu scheduler cerdas
2. **Koordinasi kompleks** — deadlock antar-agent mungkin terjadi
3. **Quality control** — auto-generated content bisa rendah kualitas
4. **Privacy** — MonitorAgent harus sangat hati-hati dengan data user
5. **Drift** — tanpa GuardAgent, agent bisa drift dari nilai awal SIDIX

---

## Hubungan dengan SIDIX_BIBLE

- **Pilar Mandiri**: SAGL memungkinkan SIDIX tumbuh tanpa ketergantungan vendor
- **Pilar Epistemic**: GuardAgent menjaga 4-label + sanad chain
- **Pilar Islamik**: Maqasid filter di setiap output
- **Pilar Parity**: LearnAgent yang aktif → SIDIX terus kejar parity GPT/Claude
