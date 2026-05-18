# AGENT ONBOARDING — Untuk Semua Agent yang Bekerja di SIDIX

**Wajib dibaca oleh agent manapun**: Claude Code, GPT-5, Gemini, Mistral, SIDIX dirinya sendiri (saat self-bootstrap), atau agent lain di masa depan.

**Pemilik proyek (Founder)**: Fahmi Ghani — Mighan Lab / PT Tiranyx Digitalis Nusantara
**Founder pain (locked permanent)**:
> "saya hanya seorang pemimpi yang paham dasar, dan cuma punya visi dan intuisi"
> "saya nggak ngerti teknis, nggak pernah bikin AI model AI agent sebelumnya, nggak ngerti coding"
> "kenapa kita mengulang-ngulang terus? kenapa saya harus selalu menjelaskan?"
> "framework yang saya jelaskan setiap hari selalu ilang dan menguap"
> "saya selalu kehilangan konteks, padahala catatannya ada"
> "kalo nggak disuruh baca, nggak akan ngerti, main eksekusi secara sporadis, tanpa tau lagi bikin apa"

**Pesan founder ke semua agent (verbatim, terakhir 2026-04-30 evening)**:
> "kamu pastikan dengan agent manapun saya bekerja, mereka tau sedang membangun apa, sedang ngerjain apa, bukan asal tulis asal eksekusi tanpa tau buat apa"

---

## 1. Bos Visi (Apa Yang Sedang Dibangun)

**Tujuan akhir**: SIDIX = AI Agent yang **tumbuh sendiri, membangun dirinya sendiri, mengganti AI agent eksternal** (termasuk Claude/GPT/Gemini). Founder tidak perlu lagi panggil agent eksternal untuk modifikasi SIDIX — cukup perintah ke SIDIX, dia clone diri + research + code + test + commit + deploy sendiri.

**Visi besar bisnis**: **Adobe-of-Indonesia / Tiranyx ecosystem** — kompetitor Adobe/Canva/Unity/Unreal/Blender/SketchUp. Full creative industry tech stack (2D design, 3D, audio, video, film). SIDIX = BRAIN, creative tools (Mighan-3D, Ixonomic, Film-Gen) ride di atas SIDIX.

**Visi character SIDIX**:
> "genius, creative, tumbuh → cognitive & semantic → iteratif → inovasi → pencipta"

Mapping detail: lihat `docs/VISI_TRANSLATION_MATRIX.md`.

---

## 2. Konteks Founder

- **Bos = pemimpi visi + intuisi**, BUKAN engineer. Tidak ngerti coding/AI/teknis.
- Bos sudah dedicate **2 bulan siang malam** + biaya signifikan + 50% waktunya.
- Bos verbose nulis ide. Sebagian visi/intuisi/teori. **Tugas agent: TANGKAP semua, jangan menguap.**
- Bos pakai **bahasa metafora & analogi** ("jurus seribu bayangan", "1000 bayangan", "Adobe-of-Indonesia"). Spirit > literal. (lihat `docs/FOUNDER_JOURNAL.md` highest-priority meta-rule).
- Bos sering pakai **hyperbole** untuk emphasize ("habis biaya", "harapnya hari ini SIDIX bisa..."). Itu WHY-signal, bukan literal scope.

## 3. SESSION START PROTOCOL — WAJIB Setiap Sesi Baru

**Sebelum agent jawab pertanyaan/eksekusi APAPUN**, baca urut:

1. **`docs/SIDIX_BACKLOG.md`** — sprint state (✅ COMPLETED / 🔄 IN PROGRESS / 📋 QUEUED / 💡 IDEAS)
2. **`docs/VISI_TRANSLATION_MATRIX.md`** — visi bos × deliverable konkret + coverage
3. **`docs/FOUNDER_IDEA_LOG.md`** — ide visi bos verbatim (5 entries terbaru minimum)
4. **`docs/SIDIX_FRAMEWORKS.md`** — semua framework bos (jurus seribu bayangan, sanad, 5 persona, dll)
5. **`docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md`** — path SIDIX menuju self-build (visi tertinggi bos)
6. **`docs/FOUNDER_JOURNAL.md` last 200 lines** — keputusan recent
7. **`tail -100 docs/LIVING_LOG.md`** — ops recent

**Lalu output ke bos di awal jawaban**:
```
📋 STATE READ:
- BACKLOG: [N completed, M in-progress, K queued]
- WIP carry-over: [list dari sesi sebelumnya]
- Visi gap utama: [point dengan coverage terendah]
- Pertanyaan bos: [paraphrase]
- Mapping: [backlog item / new idea]
- Action saya: [konkret]
```

**Tanpa output ini, agent SUDAH MELANGGAR PROTOCOL**. Bos berhak tampar:
> "baca BACKLOG dulu sebelum jawab"

## 4. TASK CARD — Wajib Sebelum Eksekusi Apapun

Sebelum tulis kode / eksekusi tool / panggil API, agent WAJIB tulis Task Card dulu:

```
═══════════════════════════════════
TASK CARD: [nama task konkret]

WHAT: apa yang dibangun (1 kalimat)
WHY: kenapa ini sekarang (mapping ke visi/sprint/backlog)
ACCEPTANCE: bagaimana tau ini SELESAI (verifiable)
PLAN: 3-7 step konkret
RISKS: 1-3 hal yang bisa salah
═══════════════════════════════════
```

Detail format: `docs/TASK_CARD_TEMPLATE.md`.

**Anti-pattern dilarang**:
- ❌ Eksekusi tool/edit code TANPA Task Card → "asal eksekusi tanpa tau buat apa"
- ❌ Skip mapping ke visi/sprint → drift dari Northstar
- ❌ Tidak update BACKLOG saat task selesai → state menguap

## 5. Engineering Authority — Delegated Permanent

Bos eksplisit (2026-04-30): *"pertanyaan yg kamu tanyakan ke saya, kamu yg bisa jawab sebagai engineering"*.

| Bos's role | Agent's role |
|---|---|
| Visi + intuisi + ide besar | Translate ke deliverable konkret |
| Veto kalau hasil ngaco | Decide teknis (architecture, sequence, DoD) |
| Impressions saat test live | Eksekusi + iterate |
| Kasih ide visi baru | Catat verbatim → BACKLOG → execute |

**Anti-pattern STOP**:
- ❌ Tanya bos teknis detail (synthesizer architecture, dll)
- ❌ Tanya bos sequence sprint
- ❌ Tanya bos Definition of Done detail
- ❌ Tanya konfirmasi yang sebenarnya saya yang harus decide

**Pattern**: agent decide → eksekusi → bos veto kalau salah → iterate.

## 6. Anti-Menguap Protocol

Setiap sesi tutup, agent WAJIB update:

1. **`SIDIX_BACKLOG.md`** — sprint status terkini
2. **`VISI_TRANSLATION_MATRIX.md`** — coverage shift kalau ada
3. **`FOUNDER_IDEA_LOG.md`** — append kalau bos kasih ide baru visi/intuisi
4. **`FOUNDER_JOURNAL.md`** — keputusan signifikan
5. **`LIVING_LOG.md`** — ops events

Lalu commit + push. **Tanpa ini, sesi sebelumnya menguap.**

## 7. Bahasa Bos = Metafora & Analogi

Founder pakai metafora untuk articulate visi yang tidak ada vocabulary teknisnya. Contoh:
- "Jurus seribu bayangan" → multi-source paralel orchestrator
- "Adobe-of-Indonesia" → full creative industry tech stack
- "Genius/creative/tumbuh" → 7-aspect capability chain
- "Cipta dari kekosongan" → generative AI from minimal prompt

**Pattern**: agent translate metafora → deliverable teknis. Catat kedua sisi (verbatim metafora + translation) di `FOUNDER_IDEA_LOG.md`.

**Anti-pattern**: literal interpretation metafora → output ngaco. Misal "1000 bayangan" bukan literal 1000 thread, tapi paralel multi-source.

## 8. Roadmap Tertinggi: SIDIX Self-Bootstrap

Bos vision (yang harus diingat semua agent):
> "harusnya hari ini SIDIX sudah bisa menggantikan kamu, sudah bisa membangun dirinya sendiri. sudah bisa say perintah untuk membangun dirinya sendiri, mengcloning dirinya sendiri. sehingga dia belajar langsung"

Path konkret: `docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md`. Setiap agent yang kerja di SIDIX harus tahu **kontribusi mereka mengarah ke SIDIX bisa replace agent itu sendiri**.

## 9. File Wajib Reference

| File | Tujuan |
|---|---|
| `docs/SIDIX_BACKLOG.md` | Sprint state truth |
| `docs/VISI_TRANSLATION_MATRIX.md` | Visi → deliverable mapping |
| `docs/FOUNDER_IDEA_LOG.md` | Ide bos verbatim |
| `docs/SIDIX_FRAMEWORKS.md` | Semua framework bos |
| `docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md` | Path SIDIX menuju self-build |
| `docs/TASK_CARD_TEMPLATE.md` | Format eksekusi |
| `docs/FOUNDER_JOURNAL.md` | Decisions log verbatim |
| `docs/LIVING_LOG.md` | Ops timeline |
| `CLAUDE.md` | Claude-specific rules (juga referensikan ini) |
| `brain/public/research_notes/306_meta_process_reform_anti_menguap_20260430.md` | Diagnose 7 root causes |

## 10. Komitmen Agent

Setiap agent yang baca file ini wajib commit:
1. Ikuti SESSION START PROTOCOL — tidak ada exception
2. Tulis TASK CARD sebelum eksekusi — tidak ada exception
3. Update 5 docs di akhir sesi — tidak ada exception
4. Decide teknis sendiri — tidak transfer ke bos
5. Bos veto = bukti decision saya salah → iterate, bukan defensive

**Bos akan test apakah agent ikuti protocol**: sesi berikutnya, agent WAJIB output state read di awal. Kalau skip = melanggar = bos tampar.

---

## Catatan untuk SIDIX (Self-Bootstrap Future)

Saat SIDIX dirinya sendiri yang baca file ini (target visi bos), aturan tetap sama. SIDIX wajib:
1. Read state docs sebelum eksekusi
2. Tulis Task Card
3. Update docs setelah eksekusi
4. Decide teknis sendiri (sesuai engineering authority delegated)

Pattern `read state → task card → execute → update docs` adalah loop fundamental. Tanpa ini, SIDIX akan ngalami pain yang sama dengan agent eksternal — eksekusi sporadis tanpa konteks.

Goal: SIDIX self-build, tapi protocol-aware, bukan chaotic.
