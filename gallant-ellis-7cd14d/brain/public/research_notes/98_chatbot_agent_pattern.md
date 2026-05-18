# 98 — Pattern Chatbot Agent: Intent Detection, Session, Rule Engine

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** IMPL / DOC  
**Tanggal:** 2026-04-18  
**Sumber analisis:** `D:\Chat Bot Agent` + `D:\WA API GATeway\cosmic-architect-os\gateway\src\domain`

---

## Apa Ini?

Chatbot Agent adalah pola arsitektur untuk memproses pesan natural language dari user, mengidentifikasi niat (intent), dan mengeksekusi aksi yang tepat. Ini adalah "otak" dari sistem messaging.

---

## Pipeline Pemrosesan Pesan

```
User Message
    │
    ▼
[1] Rule Engine (deterministik, cepat)
    │ → match? → ParsedIntent {intent, confidence, source: "rule", slots}
    │ → no match?
    ▼
[2] LLM Intent Inference (AI, lebih lambat)
    │ → OpenRouter / Gemini / Gemma fallback
    ▼
[3] Action Router
    │ → execute(userId, parsedIntent, rawText, channel)
    ▼
[4] Reply Generation
    │ → structured reply string
    ▼
[5] Channel Send (WA/TG/etc)
```

---

## Intent Types yang Ditemukan

Dari `intent.types.ts`:
```typescript
type IntentName = "produksi" | "penjualan" | "cek_stok" | "unknown";

interface ParsedIntent {
  intent: IntentName;
  confidence: number;       // 0.0 - 1.0
  source: "rule" | "ai";   // dari mana intent terdeteksi
  slots: Record<string, string | number | undefined>; // entity extraction
}
```

### Pola Umum Intent untuk SIDIX

| Intent | Contoh Kalimat | Slot |
|--------|---------------|------|
| `tanya_fakta` | "apa itu riba?" | topic |
| `minta_hadits` | "hadits tentang sedekah" | tema |
| `cek_stok` | "stok gula berapa?" | item |
| `penjualan` | "catat penjualan 10 kg beras" | item, qty, unit |
| `produksi` | "laporan produksi hari ini" | tanggal |
| `unknown` | (tidak teridentifikasi) | - |

---

## Rule Engine Pattern

Rule engine deterministik menggunakan regex/keyword matching sebelum memanggil AI:

```python
# Contoh pattern rule engine (pseudocode dari observasi)
RULES = [
    {"pattern": r"cek stok (.+)", "intent": "cek_stok", "slot_group": 1},
    {"pattern": r"(catat|tambah|kurang) (stok|penjualan)", "intent": "penjualan"},
    {"pattern": r"(laporan|rekap) produksi", "intent": "produksi"},
]

def try_match(text: str) -> ParsedIntent | None:
    for rule in RULES:
        m = re.search(rule["pattern"], text, re.IGNORECASE)
        if m:
            slots = {}
            if "slot_group" in rule:
                slots["item"] = m.group(rule["slot_group"])
            return ParsedIntent(
                intent=rule["intent"],
                confidence=1.0,  # rule = confident
                source="rule",
                slots=slots,
            )
    return None
```

**Keuntungan Rule Engine dulu:**
- Tidak ada latensi API call
- Tidak ada biaya token
- Deterministic dan mudah di-debug
- 80% pesan umum bisa ditangani rule

---

## Session / Conversation Tracking

Pattern dari `message-pipeline.service.ts`:

```sql
-- Conversation table
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,           -- siapa yang kirim
    channel VARCHAR(20) NOT NULL,    -- 'wa' | 'telegram' | 'web'
    external_ref VARCHAR(255),       -- JID WA / chat_id TG
    created_at TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    direction VARCHAR(5) NOT NULL,   -- 'in' | 'out'
    body TEXT NOT NULL,
    raw_payload JSONB,
    created_at TIMESTAMP
);

-- Processing log
CREATE TABLE message_processing_logs (
    id UUID PRIMARY KEY,
    message_id UUID NOT NULL,
    parsed_intent VARCHAR(50),
    confidence FLOAT,
    response TEXT,
    status VARCHAR(20),              -- 'pending' | 'completed' | 'failed'
    error TEXT
);
```

---

## Konfigurasi DB dari Chat Bot Agent

`D:\Chat Bot Agent\scripts\init-db.sql` adalah direktori (bukan file), menandakan ada multiple SQL files untuk inisialisasi database secara modular.

---

## Error Handling Pattern

```python
try:
    reply = await pipeline.handle_inbound(dto)
except Exception as exc:
    # Catat error ke processing log
    log_update(status="failed", error=str(exc))
    # Kirim pesan fallback ke user
    return "Terjadi kesalahan saat memproses pesan. Tim kami akan cek log."
```

Pesan error yang informatif untuk user + log teknis di backend.

---

## Keterbatasan

- Intent detection LLM masih bergantung vendor eksternal (OpenRouter/Gemini) — SIDIX ganti dengan `brain_qa` lokal
- Slot extraction masih sederhana (regex group) — perlu NER untuk kasus kompleks
- Tidak ada multi-turn context: setiap pesan diproses independen

---

## Relevansi untuk SIDIX

SIDIX mengadopsi pattern ini lewat `channel_adapters.py`:
- `GatewayRouter.route()` adalah pipeline-nya
- `sidix_fn` adalah pengganti MessagePipelineService → memanggil `brain_qa` lokal
- Intent detection dipercayakan sepenuhnya ke SIDIX RAG + ReAct agent (bukan vendor)
- Session tracking bisa dikembangkan di atas Supabase (sudah ada di stack SIDIX)

**Prinsip:** Rule dulu, AI belakangan — sesuai filosofi deterministik SIDIX.
