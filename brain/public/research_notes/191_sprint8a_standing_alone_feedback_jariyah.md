# 191 — Sprint 8a: Standing Alone + Feedback → Jariyah (Local-only)

[FACT] Repositori SIDIX memiliki aturan mengikat “Standing Alone”: inference tidak boleh bergantung pada vendor AI API (lihat `docs/DEVELOPMENT_RULES.md` dan `CLAUDE.md`).

[FACT] Sprint 8a menuntut wiring end-to-end minimal untuk: Typo Bridge → Jiwa (Nafs/Hayat/Aql) → Feedback loop (👍/👎) → training pairs (Jariyah), sesuai kontrak dokumen `complete/13_ALGORITHMS.md`, `complete/05_MODULES.md`, `complete/04_FRAMEWORK.md`, `complete/12_INPUT_OUTPUT.md`.

## Apa yang diubah (high-level)

[FACT] Jalur cloud fallback (vendor API) di backend `apps/brain_qa` dinonaktifkan dan diganti router lokal:

- `multi_llm_router.py` diubah menjadi router **local-only** (Ollama → LoRA → Mock).
- `agent_react.py` menghapus fallback text synthesis ke provider cloud (sekarang hanya local).
- `multi_modal_router.py` disederhanakan menjadi **local-only interface** (vision/ASR/TTS belum diimplementasi).

[FACT] Feedback loop sekarang punya jalur persistence + hook ke Aql:

- Endpoint `POST /agent/feedback` menyimpan event ke JSONL (local) dan pada `thumbs_up` memicu capture training pair (non-blocking) via `jiwa.post_response(... user_feedback="thumbs_up")`.
- `jiwa/aql.py` menerima `user_feedback` dan bisa menyimpan training pair walau CQF rendah **jika** user `thumbs_up`.

## Kenapa desainnya seperti ini

[OPINION] “Standing alone” bukan cuma kebijakan; ini mengubah cara kita merancang fallback: bukan “kalau gagal, lempar ke cloud”, tapi “kalau capability belum tersedia lokal, kembalikan error yang jujur + instruksi setup yang aman”.

[OPINION] Feedback 👍 adalah sinyal kualitas yang lebih kuat daripada heuristik skor otomatis di fase awal. Karena itu, thumbs-up boleh “memaksa” capture training pair supaya pipeline Jariyah punya data nyata lebih cepat.

## Kontrak data minimal (Sprint 8a)

[FACT] Blueprint schema PostgreSQL untuk Branch System + feedback + training pairs disediakan di:

- `docs/schema/SIDIX_AGENCY_OS_CORE.sql`

## Batasan & follow-up

[UNKNOWN] Vision/ASR/TTS lokal belum terpasang; modul multi-modal saat ini hanya interface. Sprint 8b/8c perlu memasang pipeline lokal (contoh: Ollama vision multimodal, Whisper.cpp, Piper).

[SPECULATION] Jika volume feedback meningkat, persistence JSONL untuk feedback perlu diganti ke DB (`messages.user_feedback` + `training_pairs`) agar bisa dianalisis (drift detection, false negative).

## Sanad

- `docs/DEVELOPMENT_RULES.md` (Standing Alone rule + verifikasi sebelum klaim)
- `CLAUDE.md` (Identitas SIDIX + larangan vendor API untuk inference)
- Sprint plan `complete/13_ALGORITHMS.md`, `complete/05_MODULES.md`, `complete/04_FRAMEWORK.md`, `complete/12_INPUT_OUTPUT.md`

