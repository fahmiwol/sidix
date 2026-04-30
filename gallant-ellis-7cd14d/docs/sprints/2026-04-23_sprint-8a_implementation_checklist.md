# Sprint 8a — Implementation Checklist (Kontrak: 13/05/04/12)

Tujuan dokumen ini adalah menurunkan kontrak desain menjadi checklist implementasi **tanpa nambah scope**. Semua item di bawah **harus bisa ditelusuri** ke:

- `complete/13_ALGORITHMS.md` (alur `jiwa_orchestrate()` + Raudah DAG)
- `complete/05_MODULES.md` (spesifikasi modul + dependency contract)
- `complete/04_FRAMEWORK.md` (IHOS: Maqashid, Sanad, Naskh, Labels, Typo framework)
- `complete/12_INPUT_OUTPUT.md` (kontrak I/O + format respons)

## A. Intake & Normalisasi (Typo Bridge) — (04_FRAMEWORK + 05_MODULES + 13_ALGORITHMS)
- **A1. Toggle & observability**
  - [ ] Pastikan typo pipeline bisa di-enable/disable via env (default ON).
  - [ ] Simpan metadata normalisasi pada session/response: `question_normalized`, `script_hint`, `substitutions_applied`.
- **A2. Non-breaking behavior**
  - [ ] Jika pipeline error / file tidak ada → fallback ke teks asli, tidak boleh crash.

## B. Persona Selection (5 Persona Resmi) — (05_MODULES + 12_INPUT_OUTPUT)
- **B1. Allowed persona**
  - [ ] Persona hanya: `AYMAN`, `ABOO`, `OOMAR`, `ALEY`, `UTZ`.
  - [ ] Default persona: `UTZ` (simple).
- **B2. Persona I/O**
  - [ ] Validasi input persona di endpoint chat/generate.
  - [ ] Return persona terpakai pada response metadata.

## C. Branch System (Agency → Client) — (02_ERD + 05_MODULES + 12_INPUT_OUTPUT)
- **C1. Context propagation**
  - [ ] Tangkap `client_id` dari header (contoh: `x-client-id`) atau body request.
  - [ ] Simpan `client_id` pada session metadata untuk semua jalur: `/agent/chat`, `/ask`, websocket (jika ada).
- **C2. Data isolation contract**
  - [ ] Semua persistence yang menyentuh `conversations/messages/kg_nodes/training_pairs` harus menyertakan `client_id` (atau eksplisit global dengan `client_id NULL`).

## D. Jiwa Orchestrator Wiring (Nafs→Hayat→Aql) — (13_ALGORITHMS)
- **D1. Nafs routing (3-layer / blend profile)**
  - [ ] Route profile menentukan: `max_obs_blocks`, `system_hint`, `skip_corpus`, `topic`, `hayat_enabled`.
  - [ ] Tetap patuh pada `Maqashid` & epistemic labels pada output final.
- **D2. Hayat iteration (CQF loop)**
  - [ ] Iterasi hanya jika model lokal tersedia.
  - [ ] Batas iterasi & stop condition jelas (minim loop).
- **D3. Aql learning capture**
  - [ ] Capture bila \(CQF \ge 7.0\) **atau** user memberi `thumbs_up`.
  - [ ] Hindari PII pada payload training pair (redaksi/opt-in).

## E. Feedback Loop (👍/👎) → Training Pairs (Jariyah v3) — (11_LOGIC + 12_INPUT_OUTPUT + 05_MODULES)
- **E1. Endpoint feedback**
  - [ ] Endpoint menerima `(session_id, vote)` minimal.
  - [ ] Vote `up` memicu learning capture (non-blocking).
  - [ ] Vote `down` disimpan untuk analisa/drift (tidak otomatis jadi training pair).
- **E2. Reactor semantics (kontrak logic)**
  - [ ] `on_thumbs_up`: tambah sinyal kualitas, bisa auto-promote ke queue.
  - [ ] `on_thumbs_down`: simpan reason/correction bila ada, tandai untuk review.

## F. Epistemic Labels + Maqashid Filter — (04_FRAMEWORK + 13_ALGORITHMS + 12_INPUT_OUTPUT)
- **F1. Epistemic labels**
  - [ ] Output memuat label epistemik minimal: `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` atau padanan.
  - [ ] Metadata response memuat `epistemic_labels` (JSON array) bila kontrak mengharuskan.
- **F2. Maqashid mode gate**
  - [ ] Hard-block untuk intent berbahaya/prompt injection.
  - [ ] Status gate dikembalikan sebagai `maqashid_profile_status` + alasan ringkas.

## G. Sanad & Kutipan — (04_FRAMEWORK + 12_INPUT_OUTPUT)
- **G1. Sanad chain**
  - [ ] Untuk jawaban berbasis corpus/web allowlist: simpan citations structured.
  - [ ] Jangan mengarang sumber.

## H. Persistence Minimal (Schema Sprint 8a) — (02_ERD + 12_INPUT_OUTPUT)
- **H1. Schema blueprint**
  - [ ] Sediakan SQL blueprint untuk tabel minimal: `agencies`, `clients`, `conversations`, `messages`, `training_pairs`, `kg_nodes`, `kg_relationships`, `health_checks`, `audit_logs`.
- **H2. Migration strategy**
  - [ ] Tentukan “cara apply” (migration tool) sebagai task terpisah (tanpa hardcode secrets).

## I. Verification / Definition of Done — (13_ALGORITHMS + docs/DEVELOPMENT_RULES.md)
- [ ] Backend tidak memiliki jalur inference vendor API.
- [ ] `/health` tidak mengiklankan provider cloud.
- [ ] Feedback `up` menghasilkan entry training pair (minimal file-based queue).
- [ ] `client_id` tercatat di session export (branch context).
- [ ] Log perubahan di `docs/LIVING_LOG.md` + research note baru untuk keputusan penting.

