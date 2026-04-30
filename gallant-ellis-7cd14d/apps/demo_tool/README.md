# demo_tool — SIDIX FastAPI Demo Tool Scaffold

Scaffold FastAPI minimal untuk demonstrasi routing persona dan integrasi dengan brain_qa.

## Cara Menjalankan

```bash
cd apps/demo_tool
pip install -r requirements.txt
uvicorn main:app --reload --port 8901
```

Server akan berjalan di: http://localhost:8901

## Endpoint

| Method | Path       | Deskripsi                                              |
|--------|------------|--------------------------------------------------------|
| GET    | `/`        | Info tool, versi, dan daftar persona                   |
| POST   | `/analyze` | Analisis teks dengan persona routing                   |
| GET    | `/health`  | Health check                                           |

## Contoh Request

### POST /analyze

```bash
curl -X POST http://localhost:8901/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Apa hukum zakat fitrah menurut ulama?", "persona": "fiqh"}'
```

Respons:
```json
{
  "text_preview": "Apa hukum zakat fitrah menurut ulama?",
  "persona": "fiqh",
  "persona_description": "Hukum Islam — mazhab dan dalil",
  "routing_hint": "→ brain_qa corpus: kutub_fiqhiyyah, fatawa",
  "mock_analysis": { ... },
  "latency_ms": 0.12,
  "note": "Wire to brain_qa agent_serve.py for real inference"
}
```

## Persona yang Didukung

| Persona    | Domain                          |
|------------|---------------------------------|
| `general`  | Analisis umum                   |
| `fiqh`     | Hukum Islam                     |
| `ushul`    | Ushul fiqh                      |
| `tafsir`   | Tafsir Al-Qur'an                |
| `hadith`   | Ilmu hadith                     |
| `science`  | Sains dan teknologi             |
| `philosophy` | Filsafat dan logika           |

## Integrasi dengan brain_qa

Ganti fungsi `_mock_analyze()` di `main.py` dengan panggilan httpx ke
`http://localhost:8000/agent/chat`. Lihat `docs/snippets/python_react_agent.py`
untuk contoh lengkap.

```python
import httpx

async def real_analyze(text: str, persona: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/agent/chat",
            json={"messages": [{"role": "user", "content": text}], "persona": persona},
            timeout=30.0,
        )
        return resp.json()
```
