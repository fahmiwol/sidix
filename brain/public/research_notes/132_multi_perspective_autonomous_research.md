# 132. Multi-Perspective Autonomous Research — Ruang Diskusi Jutaan Kepala

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> **Domain**: ai / epistemologi  
> **Fase**: 3 (self-learning roadmap, lanjutan dari note 131)  
> **Tanggal**: 2026-04-18

---

## Prinsip Dasar

SIDIX bukan oracle yang memuntahkan satu jawaban monolit. Dia dirancang seperti
**ruang diskusi jutaan kepala manusia** — banyak cara berpikir, banyak sudut,
tidak baku, tidak saklek. Tapi diskusi itu tetap memiliki disiplin: **kreatif,
inovatif, visioner, kritis, programatik, sistematis, logis, realistis — dan
selalu RELEVAN dengan topik utama**.

Inilah yang membedakan SIDIX dari model LLM biasa: jawaban apa pun yang keluar
sudah melewati *multi-lens synthesis*, bukan satu sudut pandang generic.

## Mengapa Multi-Perspective?

1. **Anti jawaban generic**. LLM tunggal cenderung safe/average. Lima lensa
   berbeda memaksa menggali angle yang jarang terpikir.
2. **Robust terhadap framing bias**. Kalau satu POV keliru, POV lain menjadi
   koreksi silang — mirip peer review mini dalam satu query.
3. **Menyerupai cara kerja manusia riset**. Kita tidak mendengar satu orang
   saja; kita dengarkan skeptis, praktisi, visioner, lalu sintesiskan.
4. **Output lebih kaya untuk LoRA fine-tuning**. Data training SIDIX nantinya
   memiliki diversity yang terstruktur, bukan sampling acak.

## Lima Lensa Wajib

| Lensa | Pertanyaan Kunci | Peran |
|-------|------------------|-------|
| **Kritis** | "Apa asumsi tersembunyi? Bukti apa?" | Skeptis sehat, uji klaim |
| **Kreatif** | "Analogi tak terduga? Koneksi lintas disiplin?" | Bebas konvensi, tetap relevan |
| **Sistematis** | "Komponen? Flow logis? Step-by-step?" | Programatik, bisa direproduksi |
| **Visioner** | "5-10 tahun ke depan jadi apa?" | Implikasi jangka panjang |
| **Realistis** | "Di lapangan — apa yang bekerja/gagal?" | Anti teori kosong, praktis |

Kunci: **setiap perspektif harus relevan dengan topik utama**. Kreatif bukan
berarti ngelantur, visioner bukan berarti sci-fi kosong, kritis bukan berarti
sinis.

## Arsitektur (Fase 3)

```
knowledge_gap_detector.py        autonomous_researcher.py         note_drafter.py
┌─────────────────────────┐      ┌─────────────────────────┐      ┌──────────────────┐
│ Deteksi gap (confidence │ ──→  │ 1. Generate 4 angles    │ ──→  │ Format markdown  │
│ < 0.42 → log topic)     │      │ 2. Sintesis mentor      │      │ research note    │
│                         │      │ 3. 5-lens multi-POV     │      │ (pending review) │
│ /gaps, /gaps/domains    │      │ 4. Webfetch (opsional)  │      │ /drafts API      │
└─────────────────────────┘      └─────────────────────────┘      └──────────────────┘
                                          ↓
                                 ResearchBundle (raw JSON)
                                          ↓
                              DraftRecord (.data/note_drafts/*.md)
                                          ↓
                              Mentor review → approve → publish ke corpus
```

## Endpoint API

```
POST /research/start?topic_hash=<hash>&multi_perspective=true
     → kick off riset otomatis, return draft_id
GET  /drafts?status=pending
     → list draft yang menunggu review
GET  /drafts/{id}
     → ambil markdown lengkap untuk review
POST /drafts/{id}/approve
     → publish ke brain/public/research_notes/NNN_slug.md + resolve gap
POST /drafts/{id}/reject?reason=<text>
     → tandai rejected, simpan audit trail
```

## Contoh Alur Pembuatan Note Ini

1. Gap terdeteksi: "bagaimana SIDIX bisa riset sendiri?" (frequency naik)
2. Dari `/research/start`, pipeline:
   - Generate 4 sub-pertanyaan (apa/kenapa/bagaimana/contoh)
   - Tiap sub dijawab mentor LLM
   - Topik utama dibahas dari 5 lensa
   - Gabungkan jadi markdown terstruktur
3. Mentor (Fahmi) review via `/drafts/{id}`
4. Approve → publish sebagai `132_multi_perspective_autonomous_research.md`
5. Gap otomatis di-resolve di `summary.json`

## Keterbatasan & Mitigasi

| Keterbatasan | Mitigasi |
|--------------|----------|
| LLM mentor bisa halusinasi | Mentor WAJIB review sebelum approve |
| 5 POV bisa saling kontradiksi | Itu fitur, bukan bug — sinstesis ada di tangan manusia |
| Cost 5× lebih banyak token | Pakai Groq/Gemini gratis; hanya untuk topik prioritas |
| Draft bisa menumpuk | Review UI + auto-expire draft pending >30 hari |

## Relevansi dengan Filosofi SIDIX

Ini langsung terhubung dengan pesan mentor: *"ciptakan murid yang lebih hebat,
bukan bintang tunggal — tapi bintang-bintang."* Multi-perspective research
adalah implementasi teknis dari prinsip itu — SIDIX bukan satu suara, melainkan
simfoni yang tetap terdengar relevan dan fokus.

## Langkah Berikutnya (Fase 4)

- Review UI sederhana untuk mentor approve/reject draft
- Auto-schedule: tiap malam pilih top-3 gaps → trigger `/research/start`
- Export approved drafts → dataset LoRA untuk self-training
