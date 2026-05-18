# 243 — Next Sprint Tools: Lite Browser + Image Gen + Skill Cloning

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-26
**Author**: User vision (handoff brief)
**Status**: SPRINT BACKLOG (next session)
**Trigger**: User: *"harus siapin dulu tools-tools di background proses SIDIX, yg diperluin..."*

## TL;DR

Sebelum Vol 21 sanad MVP wired, butuh **3 background tools** ready:
1. Mini lite browser (multi-source web, bukan cuma Wikipedia)
2. Image generator (SDXL self-host atau RunPod endpoint)
3. Skill Cloning tool — record perilaku setiap agent AI yang kontribusi

Setelah 3 tools ready → wire sanad_orchestrator → ship Vol 21.

## Tool 1: Mini Lite Browser (Vol 24)

User spec: *"sangat-sangat ringan, scrape friendly, multi tab web, ga harus wiki doang, bisa dari berita atau nanya langsung ke search engine"*

### Requirements

| Property | Spec |
|---|---|
| Memory footprint | <50MB total (vs Playwright 200MB+) |
| Speed | <500ms per fetch (warm) |
| Multi-tab | Async parallel fetches (asyncio.gather) |
| Scrape-friendly | Plain-text extract from HTML (no JS render needed for 90%) |
| Search engine | Direct query to multiple search backends |
| Source diversity | News, blogs, forums, Wikipedia, gov sites |

### Architecture (Two-Tier)

**Tier 1 — HTTP-only (90% queries)**:
- `httpx.AsyncClient` HTTP/2 + connection pool
- `selectolax.parser.HTMLParser` (10x faster than BeautifulSoup, MIT)
- `trafilatura.extract()` for text extraction (handles boilerplate strip)
- Multi-tab = `asyncio.gather([client.get(url) for url in urls])`

**Tier 2 — Headless Chromium (10% JS-required)**:
- `playwright` async chromium
- Pool size: max 2 instances
- Spawned on-demand, killed after use
- Reserved for SPA / heavy JS sites

### Search Engine Backends

Replace single-DDG dependency:
1. **SearxNG self-hosted** (recommended) — meta-search, no rate limit, MIT
2. **Brave Search API** — if usage allowed (requires API key)
3. **Marginalia self-hosted** — alternative open search
4. **Direct domain whitelisting** — trusted news/gov sites scraped directly
5. **Wikipedia API** (already integrated)
6. **DDG** (deprioritize, last fallback only)

### Implementation Outline

```python
# apps/brain_qa/brain_qa/lite_browser.py

class LiteBrowser:
    """Multi-tab async HTTP-first scraper."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            http2=True, timeout=10.0,
            limits=httpx.Limits(max_keepalive_connections=10),
        )
        self.search_backends = [
            SearxNGBackend("http://localhost:8080"),  # self-hosted
            WikipediaBackend(),
            DirectDomainBackend(["kompas.com", "tempo.co", "bbc.com"]),
        ]

    async def search(self, query: str, max_results: int = 5) -> list[SearchHit]:
        """Try each backend, return first non-empty (or merged top-N)."""
        for backend in self.search_backends:
            hits = await backend.search(query, max_results)
            if hits:
                return hits[:max_results]
        return []

    async def fetch_multi(self, urls: list[str]) -> list[ScrapeResult]:
        """Tier 1: parallel HTTP fetch + text extract."""
        responses = await asyncio.gather(*[
            self._fetch_one(u) for u in urls
        ], return_exceptions=True)
        return [r for r in responses if not isinstance(r, Exception)]

    async def _fetch_one(self, url: str) -> ScrapeResult:
        try:
            resp = await self.client.get(url, follow_redirects=True)
            text = trafilatura.extract(resp.text) or ""
            return ScrapeResult(url=url, text=text[:5000], status=resp.status_code)
        except Exception as e:
            return ScrapeResult(url=url, text="", error=str(e))
```

### Estimated Effort

- 2-3 days for Tier 1 + SearxNG integration
- +1 day for Tier 2 (playwright pool)
- +1 day for direct domain whitelist + tests

## Tool 2: Image Generator (Vol 24-fu1)

User spec: *"Tools generator image"*

### Requirements

- Self-hosted (no vendor API per CLAUDE.md no-vendor rule)
- SDXL or comparable open model
- GPU-backed (RunPod serverless separate endpoint)
- Async-friendly (queue-based, no block on user request)

### Architecture

```
SIDIX brain (VPS) -> HTTP request -> RunPod SDXL endpoint -> S3 / local storage -> URL back
```

**Endpoint setup**:
- New RunPod serverless deployment (parallel to existing LLM endpoint `ws3p5ryxtlambj`)
- Container: `runwayml/stable-diffusion-v1-5` or SDXL base
- Cold start: 30-60s (acceptable for image gen)
- Response time per image: 10-15s @ 1024x1024

### Existing Hook

`text_to_image` tool already exists in agent_tools (commented as "SDXL self-hosted") — needs actual endpoint wiring.

### Implementation Outline

```python
# apps/brain_qa/brain_qa/image_gen.py

async def generate_image(prompt: str, size: str = "1024x1024") -> ImageResult:
    """Call RunPod SDXL endpoint, upload result, return URL."""
    sdxl_endpoint = os.getenv("SIDIX_SDXL_ENDPOINT")
    if not sdxl_endpoint:
        return ImageResult(url=None, error="SDXL endpoint not configured")

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            sdxl_endpoint,
            json={"input": {"prompt": prompt, "size": size}},
            headers={"Authorization": f"Bearer {os.getenv('RUNPOD_API_KEY')}"},
        )
        data = resp.json()
        # data["output"] contains base64 image OR S3 URL
        image_url = upload_to_storage(data["output"])
        return ImageResult(url=image_url)
```

### Estimated Effort

- 1 day RunPod endpoint deploy + test
- 1 day wire `text_to_image` tool
- 1 day storage (S3 / local) + URL serving
- = ~3 days

## Tool 3: Skill Cloning (Vol 26 — most novel)

User spec: *"tool skill Cloning, buat cloning skill pengetahuan dari setiap agent AI yang kontribusi, pasti caranya beda-beda tapi harus ada penjelasan bagaimana SIDIX merekam perilaku, action dan tindakan mereka. learning by doing lebih cepet, apalagi ada gurunya."*

### Concept

Each contributing AI agent (Claude Code, GPT, Gemini, manual contributors) has unique **operational signature**:
- Tool selection patterns
- Decision-making heuristics
- Code style + idioms
- Documentation conventions
- Iteration/correction patterns

SIDIX learns by recording these signatures + replicating in own runtime.

### Per-Agent Signature Format

```python
@dataclass
class AgentSignature:
    """Captured operational signature dari one AI agent."""
    agent_name: str             # "claude-code-opus-4.7" / "gpt-5" / "gemini-2.5-pro"
    capture_session_id: str     # which session(s) observed
    captured_at: int            # timestamp

    # 5 transferable modules (per note 242)
    nlu_examples: list[NLUPair]       # (user_msg, parsed_intent)
    nlg_examples: list[NLGPair]       # (intent+context, response_text)
    synthesis_examples: list[Synth]   # (sources, synthesized_answer)
    doc_examples: list[DocPair]       # (action, doc_output)
    code_examples: list[CodePair]     # (spec, code, corrections)

    # Behavioral fingerprint
    tool_use_pattern: dict            # frequency + order of tool calls
    decision_heuristics: list[str]    # extracted "when X, do Y" rules
    code_style: dict                  # indent, comment style, naming
    iteration_pattern: dict           # when does agent retry? max iters?

    # Quality metrics
    success_rate: float               # % task completion
    avg_latency_per_action: float
```

### How SIDIX Records Each Agent

**For Claude Code (this teacher)**:
- Source: session JSONL log (Claude harness writes everything)
- Session log path: `.claude/projects/.../session-uuid.jsonl`
- Extract: per-message turn → intent + tools + response
- Frequency: every session = new contribution

**For other agents (future)**:
- API integration if available
- Manual import via paste-log feature
- Webhook from agent-to-SIDIX integration
- Each agent adapter = 1 module per agent

### Skill Replay (Learning by Doing)

```python
async def replay_skill(agent_signature: AgentSignature, task: Task) -> Result:
    """
    Replay an agent's signature on a new task.
    SIDIX uses recorded patterns to act like the source agent.
    """
    # Pattern matching: find similar past task in agent's examples
    similar = find_similar_examples(agent_signature, task)

    # Compose response using agent's NLG pattern
    response = compose_in_agent_style(
        agent_signature.nlg_examples,
        task,
        guidance_from=similar,
    )

    # If task involves code, use agent's code style
    if task.requires_code:
        code = generate_in_agent_code_style(
            agent_signature.code_examples,
            agent_signature.code_style,
            task.code_spec,
        )
        response = inject_code(response, code)

    return Result(
        output=response,
        replayed_from=agent_signature.agent_name,
        similar_examples=similar,
    )
```

### Multi-Teacher Learning

```
SIDIX
  ├── Skill from Claude Code  (90% — primary teacher this phase)
  ├── Skill from GPT          (future)
  ├── Skill from Gemini       (future)
  ├── Skill from human contributors (always)
  └── Self-generated (cycle: SIDIX teaches itself from own actions)
```

Per task, SIDIX picks best matching teacher signature. Or ensemble across teachers.

### Estimated Effort

- 3 days session log parser (extract signatures from Claude Code JSONL)
- 2 days signature schema + storage (SQLite + JSON)
- 3 days replay engine (pattern matching + composition)
- 2 days adapter for other agents (when API available)
- Tests + tuning: 2 days
- = ~12 days

## Sprint Sequencing

| Phase | Tools to ship | Dependencies | Effort |
|---|---|---|---|
| **Sprint 1** (next session) | Tool 1: Lite Browser MVP | httpx, selectolax, trafilatura | 3-4 days |
| Sprint 1 cont | Tool 1: SearxNG self-host setup | docker | 1 day |
| **Sprint 2** | Tool 2: Image gen wire RunPod | RunPod separate endpoint | 3 days |
| **Sprint 3** | Tool 3 MVP: Claude Code signature extractor | session JSONL parsing | 3 days |
| Sprint 3 cont | Tool 3: replay engine | tool 3 schema | 5 days |
| **Vol 21 wire** | Wire sanad_orchestrator ke /ask + use new tools | all 3 tools ready | 2 days |

**Total to fully operational sanad**: ~3-4 weeks across 3-4 sprints.

## Why This Order Matters

Sanad fan-out membutuhkan diverse + reliable sources. Tools above unlock:
- Lite Browser → diverse web data (sebelum ini cuma Wikipedia + DDG block)
- Image gen → multimodal output (visual answers, diagrams)
- Skill Cloning → SIDIX's own learning loop (continuous improvement)

Without these 3, sanad MVP would be limited (cuma 3 branches dengan satu sumber web yang stale).

## Connection ke Existing Spec

- Note 239 (sanad spec) → Vol 21+ depends on these tools
- Note 240 (Claude pattern as template) → Tool 3 makes this operational
- Note 241 (session as corpus) → Tool 3 is the ingest mechanism
- Note 242 (5 modules) → Tool 3 records all 5 per agent

## Action Items (Next Session Start)

1. [ ] Read this note (243) first
2. [ ] Confirm sprint ordering with user
3. [ ] Begin Sprint 1: Lite Browser
   - Install httpx, selectolax, trafilatura on VPS
   - Write `lite_browser.py` skeleton
   - Test against 5 sample news URLs
4. [ ] Setup SearxNG container (docker run)
5. [ ] Test multi-backend search
6. [ ] Iterate

## Final Note

User: *"learning by doing lebih cepet, apalagi ada gurunya."*

Beautifully put. SIDIX's training strategy:
- Phase 1 (now): Claude Code as primary teacher (this session = first lesson)
- Phase 2: Multi-teacher (other AI agents + human contributors)
- Phase 3: Self-teaching (SIDIX observes own correct/incorrect outputs, refines)
- Phase 4: Teaching others (SIDIX as teacher for next-gen models)

We're at Phase 1, ~30+ "lessons" recorded today. Continue the curriculum.
