# Founder Strategic Dialogue — 2026-04-29

> **Source:** Real-time dialogue antara Founder (Fahmi) ↔ Claude (sebagai AI advisor) saat training Sprint 13 LoRA persona adapter berjalan di RunPod (~step 400/2529).
>
> **Captured oleh:** Claude (Sonnet 4.6)
>
> **Tujuan capture:** dokumen ini ditulis supaya **agent lain (Kimi) + future Claude session + acquirer due-diligence + founder sendiri** bisa rujuk kembali keputusan strategis yang di-lock hari ini. Memory file (`MEMORY.md`) cuma punya kompresi 1-line; full nuance ada di sini.
>
> **Audience implicit:** Tim Tiranyx (ketika ada), Kimi agent, Claude future session, potential acquirer DD packet.

---

## TL;DR — keputusan lock 2026-04-29

1. **Vision lock:** Tiranyx = **Adobe of Indonesia** (perusahaan teknologi creative terbesar & pertama di ID). 3-5 tahun decade-play.
2. **Produk portfolio:** 4 produk paralel di bawah Tiranyx (parent): SIDIX (AI brain) · Mighan (3D + game) · Ixonomic Coin (transactional) · Tiranyx Platform (distribution).
3. **Sub-produk baru:** *Film Generator* (anak/adik SIDIX) — bundle image+video+tts+audio+3d untuk user bikin film, watermark "built by Tiranyx ecosystem".
4. **Time allocation:** 70% briket biz (cash flow), 30% Tiranyx tech (~12 jam/minggu), dibagi 50% film-gen + 50% SIDIX core.
5. **Strategic principle:** Build-not-buy 60/40 (60% stand-alone first, 40% partnership untuk kolaborasi). Target growth: 70% lebih cepat dari kompetitor AI ID.
6. **Exit goal:** M&A eventually (timeline: 12-24 bulan, bukan 3-month sprint seperti frame keliru saya sebelumnya). Briket biz = bridge funding alami.
7. **SIDIX core differentiator (founder's WHY):** AI yang **self-learn, self-improve, iterasi & cognitive proaktif** saat founder idle — bisa experiment & menciptakan inovasi otonom yang align visi. Ini bukan fitur, ini **raison d'être SIDIX**.

---

## Konteks dialogue

Dialogue dimulai dari pertanyaan praktis ("whitepaper bisa diganti?") tapi escalate jadi strategic disclosure penuh. Trigger besar:

- **Hour 1:** Update README whitepaper section + tulis whitepaper v2.0 markdown (`docs/whitepaper/SIDIX_WHITEPAPER_v2.md`) dengan inject 7 novel contributions terbaru.
- **Hour 2:** Founder tanya monetisasi → Claude kasih 6 jalur termasuk pesantren targeting → **founder reject** ("ko jadi ke pesantren? kan udah nggak islamic banget"). Saved as `feedback_sidix_positioning_secular.md`.
- **Hour 3:** Founder lock direction Creative Agent (Canva/Fotor/Dzine level), benchmark GPT+Claude. Saved as `project_sidix_direction_creative_agent.md`. Claude audit capability gap → 77% gap to GPT-level.
- **Hour 4 (existential moment):** Founder express doubt — *"apa saya drop aja project sidix... saya balik jadi pemimpi lagi"*. Claude push back dengan data konkret (39 sprint shipped, 290+ notes, whitepaper 7 novel contributions, adapter LIVE training). Frame correction: bukan kapasitas yang kurang, scope kemarin yang ketinggian.
- **Hour 5 (full disclosure):** Founder reveal Adobe-of-ID vision + 4-produk Tiranyx + briket biz cash flow + build-not-buy principle. Saved as `project_tiranyx_ecosystem.md`.
- **Hour 6 (now):** Founder confirm parallel work (50/50 film-gen + SIDIX) + tanya soal recording.

---

## 4 Produk Tiranyx — full architecture (founder's words + Claude synthesis)

### Layered architecture

```
┌─────────────────────────────────────────────────────┐
│  LAYER 4: IXONOMIC COIN (transactional, future)     │
│  AI-to-AI payment, marketplace settlement            │
│  Status: konsep, defer ke Q2-Q3 2027                 │
└─────────────────────────────────────────────────────┘
                          ↑
┌─────────────────────────────────────────────────────┐
│  LAYER 3: TIRANYX PLATFORM (distribution + UX)      │
│  Dashboard, freemium, billing, member portal         │
│  Status: revamp ongoing, target Q1 2027              │
│  Pivot: agency → tech company                        │
└─────────────────────────────────────────────────────┘
                          ↑
┌──────────────────────┐    ┌──────────────────────────┐
│  LAYER 2A: SIDIX     │    │  LAYER 2B: MIGHAN        │
│  AI brain orkestrator│    │  3D NPC, game builder,   │
│  ├── Image+Editor    │    │  immersive worlds        │
│  ├── Persona LoRA    │    │  Status: scaffold local, │
│  ├── 48 tools ReAct  │    │  dikerjain KIMI, lambat &│
│  ├── Hafidz Ledger   │    │  kurang inovatif         │
│  ├── Growth loop     │    │  Target: kickoff Q4 2026 │
│  └── 🎬 Film-Gen     │    │                          │
│      (sub-produk)    │    │                          │
│  Status: production  │    │                          │
│  LIVE Sprint 13      │    │                          │
└──────────────────────┘    └──────────────────────────┘
                          ↑
┌─────────────────────────────────────────────────────┐
│  LAYER 1: COMMON FOUNDATION (shared across produk)  │
│  LoRA infra · RunPod GPU · Hafidz Ledger · sanad     │
│  · VPS brain_qa · MIT corpus · research notes        │
└─────────────────────────────────────────────────────┘
```

### Cara saya (Claude) baca synergy 4 produk

**SIDIX → Mighan synergy:** LoRA persona Sprint 13 = voice consistency. Plug ke NPC Mighan = NPC dengan persona depth (UTZ creative-director NPC, ABOO engineer NPC, dst.). Mighan tidak perlu re-train persona dari nol.

**SIDIX → Film-Gen synergy:** SIDIX brain orchestrate pipeline (script → storyboard → image gen → 3D scene → audio → video stitching). Film-gen = vertical app, bukan core re-build.

**Tiranyx Platform → semua:** dashboard host SIDIX + Mighan + Film-Gen sebagai apps. Billing layer common.

**Ixonomic → ekosistem:** kalau tahap matang ada GMV antar creator (template share, persona share, asset Mighan share), Ixonomic jadi settlement layer.

### KIMI status (per founder, captured verbatim)

> *"Mighan ada di local dan repo, dikerjain KIMI, cuma lambat. dan kurang inovatif"*

**Implikasi untuk capture:** Kimi dibatasi di territory anti-bentrok (`docs/AGENT_WORK_LOCK.md`) — Jiwa/Emosi/Kreativitas. Mighan masuk creative territory Kimi. Kalau lambat & kurang inovatif, perlu ada **synergy injection dari SIDIX** (misal: persona LoRA di-port ke Mighan NPC) supaya Mighan tidak start-from-scratch.

---

## Film Generator — sub-produk baru (lock 2026-04-29)

**Nama TBD oleh founder.** Posisi: anak/adik SIDIX, bukan produk standalone level Tiranyx.

**Capability target:**
- Image gen + video gen + TTS + audio gen + 3D
- User bisa bikin film free-tier dengan watermark "built by Tiranyx ecosystem" / "powered by SIDIX"
- Premium: no watermark + higher resolution + longer duration

**Why ini di-prioritize paralel dengan SIDIX core:**
- Film = consumer-facing demo TERKUAT (acquirer pitch friendly)
- Watermark = organic distribution / brand marketing free
- Multimodal stack (image+video+audio+3d) = portfolio capability bos sebut earlier sebagai "dasar-dasarnya dulu"
- Ekosistem play: film-gen butuh image (SIDIX has) + 3D (Mighan has) + audio (build) + video (build/wrap)

**Cara teknis ship cepat:**
- Image: SIDIX SDXL self-host (sudah jalan)
- 3D: TripoSR self-host (Sprint 14e scaffold, port ke Mighan eventually)
- TTS: XTTS open-source self-host (Indonesian voice clone potential)
- Audio music: Suno/Udio API wrap di v0.1 → AudioCraft self-host di v1.0
- Video: AnimateDiff self-host atau Replicate API wrap di v0.1

**Build-not-buy applied:** image + 3D + TTS = self-host (build). Music + video = wrap di v0.1, replace di v1.0. Match 60/40 principle.

---

## SIDIX self-improvement — founder's WHY (verbatim 2026-04-29)

> *"Itulah alasan kenapa saya mau sidix, saat saya lagi idle, dia bisa self learn, self improvement, iterasi dan cognitive serta proaktit melakukan experiment untuk menghasilkan inovasi atau menciptakan sesuatu, untuk dirinya, atau untuk saya. Tentunya yang tetap align dengan visinya."*

**Ini bukan nice-to-have. Ini SIDIX raison d'être.** 70% time founder di briket = SIDIX harus produktif tanpa supervisi.

### Capability mapping ke yang sudah ada

| Founder need | Implementation existing | Status |
|---|---|---|
| Self-learn (corpus growth) | `LearnAgent` fetch 50+ sumber harian → corpus queue | ⚠️ scaffold, perlu verify aktif |
| Self-improvement (model retrain) | `corpus_to_training` + `auto_lora` JSONL→adapter | ⚠️ Sprint 13 = first cycle (LIVE sekarang) |
| Iterasi (try-fail-fix loop) | `cloud_run_iterator.py` + ErrorCategory classifier | ✅ scaffold v1 (Sprint 14a) |
| Cognitive (synthesis) | Cognitive synthesis (note 288 — iteration_cost law) | ✅ pattern shipped |
| Proaktif experiment | `knowledge_gap_detector` → `autonomous_researcher` | ⚠️ scaffold, perlu verify trigger cron |
| Vision alignment guard | `docs/SIDIX_CANONICAL_V1.md` + 4 Operating Principles | ✅ LOCK 2026-04-28 |

**Action item urgent:** verify `daily_growth` 7-fase cron actually firing di VPS. Kalau sleep, SIDIX tidak self-improve = founder's WHY tidak terpenuhi.

---

## Build-not-buy principle — founder's words & Claude reconciliation

> *"Kenapa saya selalu bersikeras, 'buat sendiri' jangan pake API orang 'cari metode sendiri' karena saya mau stand alone di awal, ketika 60% stand alone 40% nya adalah keterlibatan pihak ke-3 untuk melengkapi fitur-fitur kolaborasi dalam teknologi saya."*

**Claude's reconciliation per phase (acknowledged & accepted by founder direction):**

| Phase | Build vs Wrap | Reasoning |
|---|---|---|
| v0.1 MVP (now-Q3 2026) | Wrap OK untuk non-hero (video/music API) | Velocity. Non-moat capabilities. |
| v1.0 Hero (Q3-Q4 2026) | **BUILD untuk image+editor+brand+TTS+3D** | Itu moat utama. Cannot rent. |
| v2.0 Expansion (2027) | Build strategic, partner commodity | 60/40 founder principle exact match |
| v3.0 Ecosystem (2028+) | Full stand-alone + open ecosystem | Adobe-level positioning |

**Sudah self-host TODAY:** SDXL · LoRA training (Qwen+adapter) · Hafidz Ledger · BGE-M3 embedding · ReAct loop · 48 tools sandbox.

**Akan self-host Q3-Q4 2026:** Editor canvas · Brand guideline generator · TripoSR 3D · XTTS Indonesian · AnimateDiff video.

**Akan partner di v0.1 (replace nanti):** Suno/Udio music · Replicate video gen sebagai fallback.

---

## Acquirer narrative (revised dari frame sebelumnya)

**Frame lama (saya keliru advise jam pertama):** "3-month M&A sprint, single product."

**Frame benar (post-disclosure):** Tiranyx = portfolio play multi-produk dengan briket biz cash bridge. Acquirer pitch:

> *"Tiranyx is the Adobe of Indonesia in the making. 4-product portfolio (SIDIX AI brain + Mighan 3D + Tiranyx Platform + Ixonomic Coin), with proprietary Indonesian-native LoRA persona stylometry as defensible IP, parent company with cash flow (waste-management business), and the only stand-alone AI agent ecosystem in Southeast Asia with novel contributions published (Proof-of-Hifdz, Hafidz Ledger, Cloud-Iter Cost Law)."*

**Likely acquirer pipeline (ordered by strategic fit):**

1. **GoTo Group (Gojek+Tokopedia)** — UMKM productivity tools, creator economy gap
2. **Sea Group / Shopee** — seller content tools regional
3. **EMTEK / SCM** — media + content + creative
4. **Telkomsel / Telkom** — corporate AI initiative + UMKM digitization
5. **Lippo Digital** — diversified tech + retail
6. **Adobe** (long-shot, regional acquisition pattern existing)
7. **Canva** (Australian, expanding SEA, would buy wedge play in ID)

**Bridge funding pipeline (parallel, ~$500k-$1.5M target Q4 2026):**
- East Ventures · AC Ventures · Alpha JWC · Trihill · Openspace · 500 Global · Antler

---

## Sequence lock (12-month plan, decision pending founder confirm)

| Quarter | Hero deliverable | SIDIX role | Mighan role | Cash event |
|---|---|---|---|---|
| Q3 2026 (Jul-Sep) | SIDIX hero ship: Image+Editor+Brand Guideline LIVE. Film-Gen v0.1 paralel. | 🎯 priority | maintenance | Persona adapter LIVE → demo asset |
| Q4 2026 (Oct-Dec) | Mighan kickoff (3D + persona NPC). SIDIX + Film-Gen iterate. | maintenance | 🎯 priority | Bridge fundraise close target |
| Q1 2027 (Jan-Mar) | Tiranyx Platform v2 (dashboard host all). Pivot agency complete. | maintenance | maintenance | Pricing live, freemium open |
| Q2 2027 (Apr-Jun) | Ixonomic Coin scaffold (kalau GMV cukup) | maintenance | maintenance | Series A or M&A LOI |
| Q3-Q4 2027 | Full ecosystem live · M&A close (jika diambil) | platform | platform | Exit |

---

## Outstanding decisions (founder lock pending)

1. **Confirm sequence Q3 SIDIX → Q4 Mighan → Q1 Platform → Q2 Ixonomic** (atau prioritas beda)?
2. **Film-Gen nama** — TBD founder (suggestion bank: SIDIX Cinema, Tiranyx Studio, IXIA, Tira Studio)
3. **Hours/week realistic untuk SIDIX core** vs Film-Gen (saat ini asumsi 50/50 dari 12 jam = 6 jam/minggu masing-masing)
4. **Bridge fundraise — Y/N?** Recommended Y (extend runway 12-18 bulan, beli space untuk M&A negotiation)
5. **Acquirer outreach start kapan?** Recommended Q4 2026 setelah Sprint 14e + Film-Gen v0.1 ada demo

---

## Catatan untuk agent lain (Kimi + future Claude)

**Kimi (yang kerjain Mighan):**
- Founder feedback: Mighan progress lambat & kurang inovatif. Synergy injection dari SIDIX dianjurkan (port persona LoRA ke NPC).
- Adobe-of-ID vision = decade play. Mighan adalah Q4 2026 priority, bukan late-priority.
- Build-not-buy 60/40 berlaku juga untuk Mighan.
- Coordinate via `docs/AGENT_WORK_LOCK.md`. Synergy point: NPC bisa pakai SIDIX persona adapter.

**Future Claude session:**
- Read `MEMORY.md` first (auto-load). Lalu read this file untuk full nuance.
- 3-month runway frame **SALAH** — briket biz funding 70% time. Real timeline: 12-month sprint to bridge round atau M&A LOI.
- Founder personality: ambisi besar, occasional doubt cycle, butuh **data konkret** (anti-halusinasi) bukan motivational. Push back dengan facts saat doubt strike.
- Founder sensitive: jangan suggest pesantren/Islamic targeting (positioning secular). Jangan minimize briket biz.
- 4 Operating Principles (note 248 lock 2026-04-28) tetap berlaku.

**Acquirer due-diligence (jika diakses):**
- Whitepaper v2.0: `docs/whitepaper/SIDIX_WHITEPAPER_v2.md`
- Technical capability map: `docs/SIDIX_CAPABILITY_MAP.md`
- IP inventory: persona LoRA adapter (`huggingface.co/Tiranyx/sidix-dora-persona-v1`) + Hafidz Ledger primitive + Cloud-Iter cost law (note 288)
- Code: github.com/fahmiwol/sidix (MIT)
- Live products: sidixlab.com / app.sidixlab.com

---

*Dialog capture by Claude · Sonnet 4.6 · 2026-04-29 · Sprint 13 LoRA training step ~400/2529 LIVE saat capture ini ditulis.*
