# SIDIX Architecture — Alur Data Input ke Output

> **Single Source of Truth Diagram** berdasarkan gambar founder (2026-04-30).
> Versi Mermaid + ASCII. Kalau konflik dengan kode, yang di gambar founder menang.

---

## 🎯 Metafora

SIDIX = **Organisme Digital** dengan 12 organ. Input masuk → diserap oleh seluruh organ → output keluar sebagai **penciptaan**, bukan sekadar jawaban.

---

## 📐 Mermaid Diagram (Flowchart)

```mermaid
flowchart TD
    subgraph INPUT_LAYER["🎯 INPUT — Mata & Telinga"]
        IN[teks / gambar / audio / file / url]
    end

    subgraph OTAK_LAYER["🧠 OTAK"]
        INTENT[Intent Classifier<br/>7 intent deterministik]
        PERSONA_SEL[Persona Selector<br/>UTZ / ABOO / OOMAR / ALEY / AYMAN]
        MODE[Mode Detector<br/>Basic / Single / Pro]
    end

    subgraph PERSONA_LAYER["🎭 OTHER PERSONA — Lensa Berpikir"]
        UTZ["UTZ — Kreatif<br/>aku, nih, ajaian, seru"]
        ABOO["ABOO — Teknis<br/>gue, engineering, to-the-point"]
        OOMAR["OOMAR — Strategis<br/>saya, bisnis, ROI"]
        ALEY["ALEY — Akademik<br/>saya, rujukan, metodologi"]
        AYMAN["AYMAN — Ramah<br/>halo, general, welcoming"]
    end

    subgraph JURUS_LAYER["🌪️ JURS 1000 BAYANGAN — Paralel"]
        CORPUS["🧠 Corpus<br/>BM25 + Sanad rerank"]
        DENSE["🕸️ Dense Index<br/>Semantic embedding"]
        WEB["🌍 Web<br/>DuckDuckGo + Wikipedia"]
        TOOLS["🛠️ Tools<br/>Registry heuristic"]
        FANOUT["🎭 Persona Fanout<br/>3-5 persona mikir paralel"]
    end

    subgraph SANAD_LAYER["❤️ SANAD ORKESTRA — Jantung"]
        SINTESIS["Sintesis<br/>Merge multi-source"]
        VALIDATE["Validate<br/>Claim extraction"]
        SCORE["Relevan Score<br/>≥ 9.5++ lolos"]
        LOOP{"Score < 9.5?"}
        REFINE["Refine Query<br/>Loop balik ke Jurs"]
    end

    subgraph OUTPUT_LAYER["✨ OUTPUT — Tangan & Kaki"]
        OUT_TEXT["Teks jawaban<br/>+ Sanad citation"]
        OUT_IMG["Gambar<br/>FLUX.1 / SDXL"]
        OUT_AUDIO["Audio<br/>Piper TTS / Whisper"]
        OUT_FILE["File<br/>CSV / PDF / Kode"]
        OUT_URL["URL<br/>Dashboard / Report"]
    end

    IN --> INTENT
    INTENT --> PERSONA_SEL
    PERSONA_SEL --> MODE

    MODE <---> UTZ
    MODE <---> ABOO
    MODE <---> OOMAR
    MODE <---> ALEY
    MODE <---> AYMAN

    MODE <---> CORPUS
    MODE <---> DENSE
    MODE <---> WEB
    MODE <---> TOOLS
    MODE <---> FANOUT

    CORPUS --> SINTESIS
    DENSE --> SINTESIS
    WEB --> SINTESIS
    TOOLS --> SINTESIS
    FANOUT --> SINTESIS

    SINTESIS --> VALIDATE
    VALIDATE --> SCORE
    SCORE --> LOOP

    LOOP -->|Ya| REFINE
    REFINE --> MODE
    LOOP -->|Tidak| OUT_TEXT
    LOOP -->|Tidak| OUT_IMG
    LOOP -->|Tidak| OUT_AUDIO
    LOOP -->|Tidak| OUT_FILE
    LOOP -->|Tidak| OUT_URL
```

---

## 🔑 Key Design Principles ( LOCK )

| # | Prinsip | Penjelasan |
|---|---------|------------|
| 1 | **Persona = Lensa, Bukan Filter Suara** | Persona aktif sejak **OTAK** — memengaruhi query refinement, source weight, dan synthesis. Bukan cuma ganti vocab di akhir. |
| 2 | **Jurs 1000 Bayangan = Paralel + Interaktif** | 5 sumber jalan bareng. Double arrow: OTAK kasih query → sumber balik → OTAK refine → ulang. |
| 3 | **Sanad Orkestra = Core, Bukan Gate** | Bukan filter setelah synthesis. Sanad adalah **OTAK KE-2** yang menyintesis, memvalidasi, dan kasih skor. |
| 4 | **Relevan Score 9.5++ = Threshold Tinggi** | Kalau < 9.5 → loop balik ke Jurs 1000 Bayangan (cari sumber tambahan) atau output dengan label [UNKNOWN]. |
| 5 | **Output = Input Format** | Multimodal: teks / gambar / audio / file / url. SIDIX = pencipta, bukan chatbot teks. |

---

## 📊 Detail Relevan Score 9.5++

Formula (agregasi weighted):

```
relevan_score = (
    agreement_pct    × 0.30  +  # berapa sumber setuju
    sanad_tier_score × 0.25  +  # primer=1.0, ulama=0.8, peer=0.6, aggregator=0.4
    maqashid_score   × 0.20  +  # etika/safety 0-1
    confidence_idx   × 0.15  +  # dense index confidence
    persona_align    × 0.10    # seberapa align dengan persona lensa
) × 10  # scale ke 0-10
```

**Threshold:**
- **≥ 9.5** → Output langsung
- **7.0 - 9.4** → Output + disclaimer
- **< 7.0** → Loop balik ke Jurs 1000 Bayangan (max 2 iterasi)

---

## 🎨 ASCII Fallback (untuk terminal/view tanpa Mermaid)

```
        ┌─────────────────────────────────────┐
        │  🎯 INPUT — Mata & Telinga          │
        │  (teks/gambar/audio/file/url)       │
        └──────────────┬──────────────────────┘
                       ▼
        ┌─────────────────────────────────────┐
        │  🧠 OTAK                            │
        │  Intent + Persona + Mode Detector   │
        └─┬─────────────────────────────────┬─┘
          │                                 │
    ◄─────┘                                 └─────►
    │                                               │
    ▼                                               ▼
┌──────────────┐                          ┌──────────────────────┐
│ 🎭 Other     │◄────────────────────────►│ 🌪️ Jurs 1000         │
│ Persona      │    Persona-weighted      │ Bayangan             │
│ UTZ/ABOO/    │    lens on reasoning     │ 🧠 Corpus            │
│ OOMAR/ALEY/  │                          │ 🕸️ Dense             │
│ AYMAN        │                          │ 🌍 Web               │
└──────────────┘                          │ 🛠️ Tools             │
                                          │ 🎭 Persona Fanout    │
                                          └──────────┬───────────┘
                                                     │
                       ┌─────────────────────────────┘
                       ▼
        ┌─────────────────────────────────────┐
        │  ❤️ SANAD ORKESTRA                  │
        │  ── Sintesis ──                     │
        │  validate                           │
        │  ── Relevan Score ──                │
        │  9.5++                              │
        │                                     │
        │  Score < 9.5? → Loop balik ↑        │
        └──────────────┬──────────────────────┘
                       ▼
        ┌─────────────────────────────────────┐
        │  ✨ OUTPUT — Tangan & Kaki          │
        │  (teks/gambar/audio/file/url)       │
        └─────────────────────────────────────┘
```

---

*Diagram ini LOCK. Perubahan wajib via ADR + founder approval.*
