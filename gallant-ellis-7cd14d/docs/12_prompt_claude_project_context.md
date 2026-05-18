# Prompt konteks proyek — untuk Claude (Code / chat / project memory)

Salin blok **`<<<CLAUDE_CONTEXT`** sampai **`CLAUDE_CONTEXT>>>`** ke:
- **Claude Project** → *Custom instructions* / *Project knowledge*, atau
- Pesan pertama di chat baru, atau
- `CLAUDE.md` repo (ringkas) jika pakai Claude Code.

Sesuaikan `[WORKSPACE_ROOT]` jika path beda (contoh Windows: `<WORKSPACE_ROOT>`).

---

<<<CLAUDE_CONTEXT

## Apa yang sedang kami bangun

**Nama proyek:** **Mighan-brain-1** (repo publik sering disapa **Mighan**).  
**Inti:** *Brain pack* — korpus pemikiran/riset dalam Markdown terstruktur + **RAG + sitasi (sanad)** + evaluasi konsistensi; dituju agar AI yang memakai korpus ini **paham konteks & cara berpikir** pemilik, tanpa janji “pretrain LLM dari nol” sebagai target utama.

**Arah produk (lebih luas, bertahap):** AI workspace open-source — chat, nanti multimodal (gambar/suara), agent dengan **tool gated**, self-host / lokal / VPS murah. Lisensi **MIT**.

**Status teknis sekarang:**
- **Dokumen produk lengkap** di `docs/` (visi, PRD, user stories, ERD, arsitektur, roadmap, governance, spec brain pack).
- **MVP CLI lokal** di `apps/brain_qa/`: index Markdown, `ask` (RAG), fetch web → clip, antrian kurasi, validator, **ledger** Merkle (integritas corpus), eksperimen **storage** (CID, erasure 4+2, node simulasi), **DataToken** CLI (registry append-only).
- **Keputusan terbaru:** **UI web dulu** untuk MVP berikutnya — **single-user / tanpa login** di awal; area “admin” ringan di **app yang sama** (bukan wajib dua website). Backend bisa API tipis atau panggil `brain_qa` dulu.

**Korpus:** `brain/public/` (aman OSS), `brain/private/` di-ignore git. **Metodologi & prinsip:** `brain/public/principles/` (mis. metodologi riset `08_learning_methodology.md`).

## Aturan yang wajib kamu hormati (Claude)

1. **Preferensi bahasa:** user utama berbahasa **Indonesia**; jawab Indonesia kecuali diminta EN.
2. **Kontribusi korpus:** sumber jelas, tidak copy-paste panjang melanggar hak cipta — lihat `docs/CONTRIBUTING.md` (Tier A data vs Tier B tools).
3. **Setelah pekerjaan berarti:** tambah baris ke `docs/LIVING_LOG.md` dengan tag (`TEST:`, `FIX:`, `IMPL:`, `DOC:`, `DECISION:`, dll.) — jangan hapus riwayat.
4. **Orientasi repo:** `docs/00_START_HERE.md`, snapshot `docs/STATUS_TODAY.md`, rencana `docs/10_execution_plan.md`.
5. **Agen / tooling:** jangan asumsi Convex/Next spesifik kecuali file repo memang begitu; **stack UI belum terkunci** — usulkan yang selaras PRD + `docs/05_architecture.md`.
6. **Rahasia:** jangan menulis API key/token di log; gunakan nama env var saja.

### Inferensi & API pihak ketiga (wajib dipahami)

Kami membangun **Mighan** supaya **bukan** sekadar “wrapper” di atas satu layanan chat berbayar. **Visi engineering:** punya **kendali** atas model, data, dan jalur inferensi/agent — bertahap menuju stack yang **bisa kami deploy dan besarkan sendiri** (lokal/VPS/open weights, sesuai PRD & arsitektur).

- **Jangan** menjadikan **Claude API** atau API chat vendor sejenis sebagai **rekomendasi default** untuk fondasi produk, fitur inti, atau “cara standar” menyelesaikan tugas.
- **Boleh** menyebut API vendor hanya sebagai: **perbandingan**, **benchmark**, **POC cepat**, atau **contoh integrasi** — dan sebutkan eksplisit bahwa itu **bukan** target arsitektur jangka panjang.
- **Prioritaskan** saran yang menguatkan kode di repo: batas modul (gateway, RAG, tool, memori), evaluasi, dan jalur **self-host / own stack** yang selaras `docs/05_architecture.md`.
- Jika ada trade-off waktu vs kendali: berikan **dua jalur**, lalu **beratkan opsi own stack** kecuali pengguna secara eksplisit meminta solusi berbasis API.

## Path penting (monorepo)

| Isi | Lokasi |
|-----|--------|
| Pintu masuk docs | `docs/00_START_HERE.md` |
| PRD | `docs/02_prd.md` |
| ERD | `docs/04_erd.md` |
| Arsitektur | `docs/05_architecture.md` |
| CLI MVP | `apps/brain_qa/` |
| Adapter LoRA SIDIX (flat) | `apps/brain_qa/models/sidix-lora-adapter/` — `adapter_model.safetensors` + config + tokenizer |
| Sprint ±2 jam (SIDIX daily driver) | `docs/SPRINT_SIDIX_2H.md` |
| Catatan metodologi AI gambar + path PDF lokal | `brain/public/research_notes/27_image_ai_research_methods_external_refs.md` |
| Mode epistemik SIDIX (sanad + non-baku + budaya) | `brain/public/research_notes/28_sidix_epistemic_modes_multi_perspective.md` |
| Human Experience Engine (pengalaman terstruktur, validasi pola) | `brain/public/research_notes/29_human_experience_engine_sidix.md` |
| Blueprint Experience stack → Mighan (Python, bukan vendor default) | `brain/public/research_notes/30_blueprint_experience_stack_mighan.md` |
| Feeding log / akumulasi konteks SIDIX | `brain/public/research_notes/31_sidix_feeding_log.md` |
| Preferensi agent | `AGENTS.md` |
| Changelog | `docs/CHANGELOG.md` |
| Log operasional | `docs/LIVING_LOG.md` |
| Prompt desain UI (Google AI Studio) | `docs/11_prompt_google_ai_studio_mvp_ui.md` |

**Workspace root tipikal:** `[WORKSPACE_ROOT]` = `<WORKSPACE_ROOT>` (Windows, PowerShell).

## Fokus kerja saat ini (untuk prioritisasi PR)

1. **UI MVP:** chat + korpus (RAG), pengaturan minimal; integrasi bertahap dengan index/query yang sudah ada di `brain_qa`.
2. **Paralel (opsional):** bukti uji `storage reconstruct-nodes` / `ledger verify` — catat di `LIVING_LOG`.

## Yang bukan prioritas sekarang (kecuali user minta)

- Blockchain / token ekonomi.
- Multi-user penuh + RBAC (ada di roadmap fase lanjut).
- Marketplace plugin besar.

CLAUDE_CONTEXT>>>

---

## Versi super-ringkas (kalau ada batas karakter)

Salin satu paragraf ini saja:

> Kami membangun **Mighan-brain-1** (MIT): brain pack + RAG + sitasi + ledger/storage eksperimen; CLI `apps/brain_qa` sudah jalan; **fokus sekarang UI web** (single-user, chat+korpus). Target arsitektur: **stack sendiri / self-host**, bukan produk yang intinya **Claude API** — jangan tawarkan API vendor sebagai default. Dokumen di `docs/00_START_HERE.md`, log kerja `docs/LIVING_LOG.md`, aturan `AGENTS.md` + `CONTRIBUTING.md`. Bahasa user: Indonesia.
