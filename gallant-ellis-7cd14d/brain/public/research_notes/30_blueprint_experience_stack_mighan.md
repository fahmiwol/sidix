# Blueprint: Experience Engine — pemetaan ke stack **nyata** Mighan

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

Dokumen ini menangkap arsitektur “5 layer + flow + dataset” dari diskusi produk, lalu **menerjemahkannya** ke repo ini: **Python `brain_qa`**, RAG yang sudah ada, **LLM lokal / SIDIX**, dan **prinsip nilai** di `brain/public/principles/` — **bukan** menjadikan Node.js + OpenAI API sebagai jalur default (selaras `AGENTS.md`: inference inti = stack sendiri; API vendor hanya perbandingan / POC eksplisit).

**Prasyarat baca:** `29_human_experience_engine_sidix.md`, `28_sidix_epistemic_modes_multi_perspective.md`.

---

## 1. Arsitektur lima lapisan (versi operasional)

| Lapisan | Fungsi | Di Mighan (pemetaan konkret) |
|---------|--------|------------------------------|
| **1 — LLM / bahasa** | Merumuskan teks, gaya, reasoning permukaan | `brain_qa` + `local_llm` / adapter SIDIX; atau mock saat dev |
| **2 — Experience Engine** | Penyimpanan & retrieval **kasus terstruktur** (CSDOR + tag) | Korpus baru: mis. `brain/public/experience/` (Markdown/JSONL) **atau** `apps/brain_qa/.data/experience/` — diindeks seperti dokumen lain + metadata |
| **3 — Value system** | Filter / penimbang: halal–haram (domain syar’i), etika, maqasid, mudarat | `brain/public/principles/` (ihos, maqasid, dsb.); **bukan** menggantikan ulama untuk fatwa spesifik |
| **4 — Reasoning engine** | Aturan + pola + analogi terbatas; bandingkan kasus gagal vs berhasil | Router persona + (nanti) modul rule; ReAct tools di `agent_react` bisa diperluas |
| **5 — Generative output** | Saran hidup, narasi, simulasi keputusan — dengan **label mode** | Response API + template; bedakan **sintesis pengalaman** vs **klaim hukum** |

---

## 2. Flow contoh (user: “mau ekspansi bisnis, takut gagal”)

Langkah **internal** (bukan langsung satu prompt kosong):

1. **Klasifikasi** — domain bisnis + mode epistemik (pengalaman / nilai / campuran).
2. **Retrieve pengalaman** — kasus **gagal ekspansi** vs **scale bertahap** dari Experience Engine (tag + similarity).
3. **Bandingkan pola** — apa yang berulang (cashflow, sistem, timing).
4. **Value pass** — spekulasi berlebihan, utang, riba, zalim karyawan: **flag** untuk prompt atau penolakan lembut.
5. **Generate** — **sintesis** (bukan opini tunggal): pola + caveat + rujukan ke prinsip umum; **bukan** nasihat investasi resmi kecuali produk mendefinisikan itu.

---

## 3. Dataset minimal (JSON) — sama semangat, beda lokasi file

Contoh entri (diselaraskan `29`):

```json
{
  "id": "exp_001",
  "context": { "age_band": "30-35", "role": "entrepreneur", "locale": "ID" },
  "situation": "ekspansi bisnis terlalu cepat",
  "decision": "buka tiga cabang sekaligus",
  "outcome": "cashflow kritis",
  "lesson": "scale setelah sistem stabil",
  "tags": ["bisnis", "ekspansi", "cashflow"],
  "value_flags": ["greed_risk", "leverage_risk"],
  "confidence": 0.7
}
```

**Penyimpanan pilot:** satu file **`experiences.jsonl`** (satu objek JSON per baris) di folder korpus publik yang bisa di-`index` oleh `brain_qa`, atau koleksi `.md` dengan frontmatter YAML — konsisten dengan pola dataset yang sudah dipakai repo.

---

## 4. Teknik: RAG, embedding, prompt layering

| Teknik | Di Mighan |
|--------|-----------|
| **RAG** | Sudah ada alur index + ask; Experience Engine = **sumber dokumen baru** yang di-chunk dengan aturan jelas (satu kasus = satu unit retrieval idealnya). |
| **Embedding + vector** | Lihat `04_embeddings_tradeoffs.md`; bisa lokal (`sentence-transformers`) selaras own-stack. Chroma/Pinecone = **opsional** infra terpisah, bukan keharusan hari pertama. |
| **Prompt layering** | `[VALUE / PRINSIP]` + `[FRAGMEN PENGALAMAN RELEVAN]` + `[PERTANYAAN]` + instruksi **sidq/tabayyun** — dirakit di **Python** (bukan wajib Node). |

---

## 5. Mengapa literatur umum pakai Node + OpenAI — dan bedanya di repo ini

Tutorial sering menunjukkan:

- Express + `openai` SDK + embedding API.

Itu valid untuk **POC cepat**, tetapi **bukan** arsitektur inti Mighan. Di sini:

- **Backend utama:** `apps/brain_qa` (FastAPI / serve).
- **Generate:** prioritas **lokal** (`generate_sidix`, `/agent/generate`, `/ask` dengan RAG).
- **Vendor embedding** hanya jika tim **menulis eksplisit** ingin POC; default dokumen tetap **own stack**.

---

## 6. “Mini engine” — struktur folder **dalam repo** (tanpa repo baru Node)

Usulan rapi (boleh disesuaikan):

```text
brain/public/experience/          # atau experience_pilot/
  README.md                       # cara kurasi + etika
  experiences.jsonl               # atau cases/*.md + frontmatter

apps/brain_qa/brain_qa/
  (nanti) experience_retrieval.py # filter tag + optional vector
  # terintegrasi dengan query yang ada, bukan layanan terpisah wajib hari pertama
```

Upgrade path: **tag / keyword** → **embedding lokal** → **value_flags** di prompt builder.

---

## 7. Validasi sistem

- **100–500 skenario** uji: bandingkan baseline LLM tanpa kasus vs dengan retrieval pengalaman + value prompt.
- Ukur: relevansi, konsistensi nilai (checklist), **tidak** melanggar garis merah (fatwa palsu, diagnosis medis dari anekdot).

---

## 8. Fokus produk pertama (pilih satu untuk pilot dataset)

| Fokus | Kegunaan | Catatan |
|-------|----------|---------|
| **Bisnis & uang** | Pola jelas (cashflow, scale) | Cocok untuk CSDOR + value_flags ekonomi |
| **Kehidupan / wisdom** | Luas; perlu batas mode | Hati-hati generalisasi berlebihan |
| **Relationship** | Sangat sensitif | Privasi + non-judgmental + bukan terapis |
| **General berbasis manusia** | Dataset campuran | Baik untuk proof-of-concept retrieval |

**Rekomendasi ringkas:** pilot **bisnis + kehidupan umum** dengan tag keras; relasi dalam jumlah kecil dan terkurasi.

---

## 9. Narasi sejarah LLM (Transformer → GPT → alignment)

Ringkas untuk konteks tim: model bahasa modern dilatih dari **pola teks** + **umpan balik**; itu menjelaskan mengapa jawaban terasa “hidup” tanpa pengalaman sungguhan. Produk Mighan menambahkan lapisan **pengalaman terstruktur + nilai + reasoning** — bukan mengganti fakta bahwa LLM tetap **prediksi**; justru **transparansi** itu bagian dari sidq produk.

---

## 10. Status

- Blueprint **eksekusi** = mulai dari **file pengalaman + index + prompt berlapis** di `brain_qa`; vector DB terpisah = fase berikutnya.
- Revisi dokumen ini saat schema `experience_retrieval` pertama kali di-merge.
