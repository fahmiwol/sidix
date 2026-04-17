# 97 — Arsitektur Bot Gateway: Routing, Queue, Session, Multi-Agent

**Tag:** IMPL / DOC  
**Tanggal:** 2026-04-18  
**Sumber analisis:** `D:\bot gateway` (Python FastAPI + RQ + Playwright agents)

---

## Apa Ini?

Bot Gateway adalah sistem Python berbasis FastAPI yang mengorkestrasi beberapa "agent" spesialis (Navigator, Publisher, Harvester, Sentinel, Librarian) untuk mengotomasi tugas di platform digital. Ia menggunakan **RQ (Redis Queue)** untuk eksekusi asinkron.

---

## Struktur Folder

```
D:\bot gateway\
├── backend/               ← FastAPI app
│   ├── main.py            ← create_app(), router include
│   ├── api/
│   │   ├── agent.py       ← POST /agent/run + GET /agent/status/{job_id}
│   │   ├── auth.py        ← JWT Bearer auth
│   │   ├── llm.py         ← LLM proxy
│   │   ├── social.py      ← Social media endpoints
│   │   └── marketplace.py ← E-commerce endpoints
│   └── services/
│       ├── queue.py       ← get_queue(), get_redis()
│       └── llm/
│           ├── router.py  ← chat(provider, model, messages)
│           └── providers.py ← chat_gemini(), chat_openrouter()
├── agents/                ← Worker agents
│   ├── navigator.py       ← Login via Playwright
│   ├── publisher.py       ← Post konten ke platform
│   ├── harvester.py       ← Kumpulkan metrics
│   ├── sentinel.py        ← Safety check
│   └── librarian.py       ← Store data
└── queue/
    └── worker.py          ← run_task() dispatcher + main() RQ worker
```

---

## Pola Arsitektur Kunci

### 1. Enqueue → Worker → Result

```python
# Client enqueue task:
POST /api/v1/agent/run
{"type": "publisher.post", "payload": {"platform": "instagram", "content": "..."}}
→ {"job_id": "rq:job:xxx", "queue": "default"}

# Worker eksekusi (non-blocking):
run_task("publisher.post", payload) → match case → publish_post(...)

# Client poll status:
GET /api/v1/agent/status/{job_id}
→ {"status": "finished", "result": {...}}
```

### 2. AgentContext — Konteks Shared

```python
@dataclass(frozen=True)
class AgentContext:
    workspace_id: str | None = None
    account_id: str | None = None
    metadata: dict[str, Any] | None = None
```

Setiap agent menerima konteks yang sama → memudahkan multi-tenancy.

### 3. LLM Router (Provider Abstraction)

```python
# router.py
async def chat(*, provider: str, model: str, messages: list) -> ChatResult:
    if provider == "gemini":   return await chat_gemini(...)
    if provider == "openrouter": return await chat_openrouter(...)
    raise LLMError(f"Unsupported: {provider}")
```

Provider diswitch via environment variable, bukan hardcode.

### 4. Auth Pattern

JWT Bearer token:
1. POST `/auth/login` → `{"access_token": "...", "token_type": "bearer"}`
2. Header: `Authorization: Bearer {token}`
3. `get_current_user` dependency di semua endpoint protected

---

## Agent Types

| Agent | Task Type | Fungsi |
|-------|-----------|--------|
| Navigator | `navigator.login` | Login ke platform via Playwright |
| Publisher | `publisher.post` | Post konten ke social media |
| Harvester | `harvester.metrics` | Ambil analytics/metrics |
| Sentinel | `sentinel.safety_check` | Verifikasi keamanan |
| Librarian | `librarian.store` | Simpan data ke database |

---

## Session Management

- Session disimpan ke "Session Vault" (referensi cookie jar)
- `AgentContext.account_id` mengidentifikasi akun mana yang aktif
- Redis dipakai sebagai message broker RQ sekaligus session cache

---

## Keterbatasan

- Worker.py tidak punya retry logic built-in (perlu RQ retry decorator)
- Tidak ada circuit breaker jika platform external down
- Auth masih stub JWT (perlu diperkuat untuk produksi)
- Playwright-based login bisa fail jika platform update UI

---

## Relevansi untuk SIDIX

Pattern yang diadopsi di `channel_adapters.py`:
- `GatewayRouter.route()` mirip `run_task()` — dispatch berdasarkan channel type
- `AgentContext` analog dengan `InboundMessage` — normalized context
- LLM router pattern → SIDIX pakai `brain_qa` bukan vendor LLM

**File implementasi:** `apps/brain_qa/brain_qa/channel_adapters.py` → class `GatewayRouter`
