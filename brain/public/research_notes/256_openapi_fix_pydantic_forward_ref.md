# 256 — Sprint 14g SHIPPED + LIVE VERIFIED: /openapi.json 500 → 200

**Date**: 2026-04-27 (sesi-baru evening, post-Sprint 14e)
**Sprint**: 14g (quick win, defer-able known issue dari Sprint 14c)
**Status**: ✅ SHIPPED + DEPLOYED + LIVE VERIFIED
**Authority**: Self-discovered di brain logs Sprint 14c

---

## Apa yang di-ship

`/openapi.json` endpoint: **500 → 200 OK** (151KB, 270 paths, OpenAPI 3.1.0).

### Pre-Execution Alignment Check (per CLAUDE.md 6.4)
- ✅ Bug fix tidak ubah direction → no North Star conflict
- ✅ No persona/prompt edit → no pivot 2026-04-25 conflict
- ✅ 10 hard rules preserved (no vendor, MIT, self-hosted)
- ✅ Verdict: PROCEED

### Root cause exact

Brain logs reveal:
```
pydantic.errors.PydanticUserError: `TypeAdapter[Annotated[ForwardRef('CouncilRequest')...]
is not fully defined; you should define ... and call `.rebuild()`.
For further information: https://errors.pydantic.dev/2.13/u/class-not-fully-defined
```

3 Pydantic models defined **inline inside `create_app()` function scope**:
- `CouncilRequest` (line 766) — `/agent/council` endpoint
- `GenerateRequest` (line 982) — shadow module-top GenerateRequest (different schema)
- `GenerateResponse` (line 988) — companion

Pydantic 2.13 strict mode: forward references inside function scope tidak ter-resolve untuk `/openapi.json` schema generation. Endpoint sendiri fungsional (FastAPI body validation tetap jalan), tapi spec gen fail → /openapi.json 500 + /docs Swagger UI broken.

### Fix

Same pattern as Sprint 14b iterasi #1 (`CreativeBriefRequest` fix):

```diff
- # Inline (di create_app function)
- class CouncilRequest(BaseModel):
-     question: str
-     personas: list[str] | None = None

+ # Module top-level (line 456)
+ class CouncilRequest(BaseModel):
+     """Multi-Agent Council reasoning request. Moved Sprint 14g."""
+     question: str
+     personas: Optional[list[str]] = None
+     allow_restricted: bool = False
```

Rename strategy untuk inline `GenerateRequest`/`GenerateResponse`:
- Avoid shadow dengan module-top `GenerateRequest` (line 312, schema beda)
- Rename → `AgentGenerateRequest` / `AgentGenerateResponse`
- Endpoint usage update accordingly

### Defensive sweep

Post-fix audit:
```bash
grep "    class .*Request.*BaseModel\|    class .*Response.*BaseModel" agent_serve.py
# → empty (zero inline)
```

Pattern recurrence prevention: convention dokumented — semua Pydantic
request/response model **WAJIB module top-level**, bukan inline inside
function. Documented di research note 254 (alignment audit) self-audit
checklist sekarang ditambah point ini implicitly.

---

## LIVE verification result

| Test | Before | After |
|---|---|---|
| `GET /openapi.json` | 500 Internal Server Error | **200 OK, 151KB** |
| `GET /docs` (Swagger UI) | Broken (depends on openapi.json) | **200 OK, accessible** |
| `POST /creative/brief` | OK (already worked) | Still OK |
| Schema: `CreativeBriefRequest` | Missing in spec | ✅ In `components.schemas` |
| Schema: `CouncilRequest` | Cause of error | ✅ In `components.schemas` |
| Schema: `AgentGenerateRequest` | N/A (was shadow) | ✅ In `components.schemas` |
| Schema: `AgentGenerateResponse` | N/A | ✅ In `components.schemas` |
| Total paths registered | Unknown (gen fail) | **270 paths** |

LIVE proof:
```
$ curl -s -o /dev/null -w "HTTP %{http_code} | size %{size_download}b" \
       http://localhost:8765/openapi.json
HTTP 200 | size 151663b
```

---

## Side benefits compound

1. **Swagger UI /docs accessible** untuk demo ke calon UMKM customer / dev integration (sebelumnya broken page)
2. **OpenAPI spec available** untuk codegen tools (openapi-generator, openapi-typescript) → auto-generate client SDK
3. **API discovery cleaner** — developer/integrator bisa explore endpoints visually
4. **Compound dengan Sprint 14 + 14b + 14c** — semua endpoint baru sekarang properly documented di OpenAPI spec
5. **Convention establishment** — module top-level Pydantic models = pattern locked untuk future endpoint development

---

## Mandatory loop coverage

```
1. CATAT (start)            ✅ LIVING_LOG entry + Pre-Exec Alignment Check
2. PRE-EXEC ALIGNMENT       ✅ checked vs North Star + 2 pivots — PASS
3. IMPL                     ✅ move 3 inline class → top-level + rename collisions
4. TESTING (offline)        ✅ syntax pass
5. ITERASI                  (none — single pass build)
6. REVIEW                   ✅ defensive grep audit confirms zero inline
7. CATAT                    ✅ commit message + this note
8. VALIDASI                 ✅ /openapi.json 200 + 270 paths + 5 schemas verified
9. QA                       ✅ no leak audit clean
10. CATAT (note 256)        ✅ ini
11. DEPLOY                  ✅ git pull + pm2 restart + LIVE verified
```

---

## Pattern locked (conventions untuk sesi mendatang)

**ATURAN: SEMUA Pydantic Request/Response models di `agent_serve.py` HARUS module top-level.**

Lokasi convention: lines 246-485 (sekarang ada 25 model di top-level).

**Anti-pattern yang HARUS dihindari**:
```python
# ❌ JANGAN
def create_app():
    @app.post("/foo")
    class FooRequest(BaseModel):  # inline = forward-ref bug
        bar: str
    def handle(req: FooRequest): ...
```

**Pattern yang BENAR**:
```python
# ✅ Di module top-level (sebelum create_app())
class FooRequest(BaseModel):
    bar: str

def create_app():
    @app.post("/foo")
    def handle(req: FooRequest, request: Request): ...
```

---

## Compound integrity sesi 2026-04-27

8 sprint shipped + 4 iterasi + discipline lock + 1 quick fix:

```
Sprint 12  CT 4-pilar           ✅ LIVE
Sprint 14  Creative pipeline     ✅ LIVE
Sprint 14b Image gen wire        ✅ LIVE 637KB PNG
Sprint 14c Multi-persona         ✅ LIVE 0 blanket label (post iterasi #3)
Sprint 14e 3D mascot wire        ⚠️  WIRING (LIVE pending GPU supply)
Sprint 14g /openapi.json fix     ✅ LIVE 200
Sprint 15  Visioner foresight    ✅ LIVE
DISCIPLINE CLAUDE.md 6.4 lock    ✅ Pre-Exec Alignment + Anti-halusinasi
```

API surface sekarang **discoverable + integrable** untuk future customer/dev work.
