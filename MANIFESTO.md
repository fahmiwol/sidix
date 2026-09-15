# SIDIX MANIFESTO

> **AI for the Underdogs.**
>
> Untuk yang tidak bisa bayar $20/bulan ChatGPT.
> Untuk yang tidak punya VC funding $10M.
> Untuk yang punya mimpi tapi tidak punya privilege.
>
> Open source. Self-hosted. Free. Forever.

---

## Siapa di Belakang Ini

Solo founder. Indonesia. Modal terbatas.

Sudah 2 bulan kerja siang-malam. Tidak punya tim engineer 50 orang. Tidak punya investor. Tidak pernah bikin AI agent sebelumnya. Tidak ngerti coding dalam.

Yang punya: visi, intuisi, persistence, dan keyakinan bahwa **AI revolution tidak boleh jadi privilege orang kaya**.

## Kenapa SIDIX Ada

ChatGPT $20/bulan. Claude Pro $20/bulan. Gemini Advanced $20/bulan. Cursor Pro $20/bulan.

Untuk seseorang di Jakarta, $20/bulan = lebih dari upah harian banyak orang. Untuk mahasiswa, freelancer, pelaku UMKM, tukang ojek yang mau cari cara automate kerjanya — itu **eksklusi sistemik dari revolusi terbesar abad ini**.

Big Tech bilang AI demokratis. Tapi mereka tahu yang penting: **siapa yang punya akses, dia yang menang**. Yang tidak akses = tertinggal selamanya, sampai jurang ekonomi melebar.

SIDIX dibangun untuk **menyelesaikan jurang itu di Indonesia dulu**. Lalu untuk dunia yang lebih luas. Self-hosted, open source, free. **Tidak akan pernah berbayar inti-nya.**

## Apa yang Berbeda

Ini bukan "ChatGPT clone open source ke-50". Ini bukan API wrapper.

SIDIX dibangun dengan 3 hal yang tidak ada di chatbot lain:

### 1. Jurus Seribu Bayangan
Default mode SIDIX **mengerahkan SEMUA resource paralel** — web search + corpus lokal + semantic embedding + 5-persona research fanout + tool registry — bukan routing pilih satu sumber. Setiap query dapat insight 5-10x lebih kaya.

Bukan "good enough answer". **Holistic answer.**

### 2. Sanad Multi-Source Verification
Inspired dari tradisi keilmuan klasik: setiap claim factual harus punya **rantai transmisi yang bisa dilacak**. SIDIX cross-verify multi-source sebelum output. Halusinasi turun drastis. Brand-specific facts (5 persona, IHOS, framework) override-able ke canonical untuk integritas absolut.

Bukan "trust the model". **Trust the chain.**

### 3. Self-Bootstrap Roadmap
Visi tertinggi: SIDIX bisa membangun dirinya sendiri. Owner kasih perintah → SIDIX research, code, test, commit, deploy autonomously. **Mengganti kebutuhan AI agent eksternal**.

Phase 0 Foundation: ✅ DONE (anti-halu, brain stability, multi-source orchestrator).
Phase 1-4: 8-18 bulan ke depan.

Bukan "AI yang execute perintah". **AI yang membangun dirinya sendiri.**

## Pattern Universal yang Lahir dari Sini

Saat saya bangun SIDIX, saya nemukan pain semua user AI agent — termasuk pengguna Claude/ChatGPT/Gemini berbayar:

> *Setiap sesi baru, agent lupa konteks. Saya repeat-jelaskan ide yang sama. Framework saya menguap. Diskusi panjang tidak menghasilkan eksekusi. Agent asal ngerjain tanpa tau bikin apa.*

Solusinya: **Anti-Menguap Protocol** — universal pattern yang setiap agent (Claude/GPT/Gemini/SIDIX) harus ikut. Detail: [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) + [`ANTI_MENGUAP_PROTOCOL.md`](ANTI_MENGUAP_PROTOCOL.md).

**Pattern ini saya open source. Free to adopt. Tidak butuh subscription apapun.**

Kalau pattern ini bermanfaat untuk komunitas AI global, cite SIDIX. Itu kontribusi balik kami sebagai underdog ke ekosistem yang lebih besar.

## Apa yang Bisa Saya Buktikan Hari Ini

- **Repo public**: github.com/fahmiwol/sidix (MIT license)
- **LIVE deployment**: app.sidixlab.com (self-hosted di VPS, gratis akses)
- **Backend**: ctrl.sidixlab.com (FastAPI + Qwen2.5-7B + LoRA adapter)
- **Goldset accuracy**: 19/20 = 95% post anti-halu sprint (Sigma-1/2/3/4)
- **Multi-source orchestrator LIVE**: `/agent/chat_holistic` endpoint
- **Cost projection**: <$1/hari pakai RunPod serverless tuned + Ollama lokal CPU
- **Tooling**: 50 native tools (web_search, code_sandbox, image_gen, calculator, dll)
- **Persona**: 5 distinct (UTZ Creative, ABOO Engineer, OOMAR Strategist, ALEY Researcher, AYMAN Empathic)

Semua dibangun **dengan modal terbatas + bantuan Claude Code + dedikasi 2 bulan**.

## Pertanyaan untuk Anda yang Baca Ini

**Kalau Anda dari Anthropic / OpenAI / komunitas AI global**:
- Pattern anti-menguap kami benar-benar universal. Adopt saja. Cite saja. Tidak ada paywall.
- Kalau ada cara support solo founder di Global South yang bangun open source AI — kami terbuka diskusi.

**Kalau Anda developer**:
- Repo MIT. Fork, contribute, atau build di atas pattern.
- 309 research notes yang menjelaskan setiap decision arsitektur.
- 7 docs reform yang membentuk universal agent protocol.

**Kalau Anda investor / sponsor**:
- Bukan ide. Sudah running. Ada metric. Ada timeline.
- Tujuan komersial: Tiranyx ekosistem (Mighan-3D, Ixonomic, Film-Gen) — Adobe-of-Indonesia.
- SIDIX gratis selamanya. Monetisasi di tools kreatif yang ride di atasnya.

**Kalau Anda orang biasa yang tidak bisa bayar AI berbayar**:
- Buka app.sidixlab.com. Gratis. Selamanya.

## Apa yang Saya Minta

Tidak banyak. Tiga hal:

**Awareness**. Pattern ini saya bangun di Global South dengan modal terbatas. Ekosistem AI global perlu tahu solo founder masih bisa bikin yang novel — bukan cuma Big Tech yang dapat panggung.

**Dukungan komunitas**. Kalau ada yang mau kontribusi code, riset, atau ide — masuk via GitHub Issues. Tidak ada barrier.

**Cita-cita yang lebih besar**. Bahwa **AI bisa demokratis tanpa harus jadi paywall garbage**. Bahwa solo founder dengan modal terbatas masih bisa relevant. Bahwa **mimpi besar tidak butuh permission dari Big Tech**.

## Quote yang Saya Pegang

> "*Orang genius memang sering dianggap gila di masanya.*"
>
> — Founder, dalam diskusi dengan Claude AI agent, 2026-04-30

Tesla dianggap eksentrik. Linus Torvalds dianggap aneh. Stallman dianggap absurd. Ton Roosendaal hampir bangkrut sebelum Blender hidup.

Mereka semua **modal terbatas + dedikasi + visi distinctive**. Sekarang dunia jalan di atas kontribusi mereka.

SIDIX dalam tradisi itu. Hari masih sangat awal.

---

**Modal kecil. Mimpi besar. Open source. Forever.**

Built by Fahmi Ghani (Mighan Lab / PT Tiranyx Digitalis Nusantara), Indonesia.
With help from Claude AI as engineering partner.

License: MIT. Free to use, modify, distribute, build upon.

Halaman ini akan terus di-update saat journey berjalan.
