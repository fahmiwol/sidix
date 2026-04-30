# Sprint 42 — SIDIX-as-Pixel (Chrome Extension MVP)

> **Mandate (founder LOCK 2026-04-29):** *"di platform manapun selama terhubung internet, sidix bisa dipanggil. seperti di crawling ketika ada yg mention. mau di blog, di sosial media di foto, dia harus bisa ditanam dalam meta tag juga, seperti pixel. hanya titik, atau seperti extensi buat saya. jadi misalnya saya nemu konten bagus di ig, saya asal sebut di komen dengan kata kunci pemanggil sidix spawn dan rekam, sintesis, cognitive, pelajari analisa multi dimesi, multi persona, olah sendiri entah jadi apa."*
>
> **Sprint window:** Q3 2026 minggu 3-5 (per 12-week sequence lock di SPRINT_40_AUTONOMOUS_DEV_PLAN.md)

---

## Arah tujuan (LOCKED)

Bos sebut bukan "fitur kecil" — ini **distribution layer + data input flywheel**. Tanpa ini, SIDIX tidak belajar dari dunia nyata, cuma echo chamber internal.

**End goal:** SIDIX dipanggil dari mana saja terhubung internet dengan keyword `@sidix` → spawn → record → synthesize (Sprint 41) → cognitive multi-persona (Sprint 40 fanout) → output (research note / tool / method / inovasi).

**Compound dengan sprint lain:**
- **Sprint 41 (DONE)** Conversation Synthesizer = engine yang dipanggil saat pixel trigger
- **Sprint 40 Phase 2** persona fanout = multi-angle analysis layer
- **Sprint 42 (this)** = distribution surface yang feed input ke 41+40
- **Sprint 45 (future)** Persona-to-Innovation pipeline = output layer

---

## Yang sudah (catat sebelum lanjut)

Sprint 41 LIVE, deliver:
- `conversation_synthesizer.py` — parser + extractor + note generator + Hafidz hook
- CLI `python -m brain_qa synthesize_conversation --file=X.{md,jsonl}`
- JSONL auto-detect (Claude Code session direct feed)
- Smoke test PASS + dogfood note 290 (sesi 2026-04-29)

Bos workflow yang sudah live:
```bash
# Cara pakai sekarang (Sprint 41 v1.1):
$ cd apps/brain_qa
$ python -m brain_qa synthesize_conversation \
    --file="C:/Users/ASUS/.claude/projects/<proj>/<session-uuid>.jsonl" \
    --source="claude_session_2026-04-29_X"
# → research note baru di brain/public/research_notes/N_<slug>.md
# → Hafidz Ledger entry otomatis
```

---

## Yang akan (Sprint 42 deliverable)

### MVP scope (3 minggu)

**1. Chrome Extension v3 Manifest**
- `extension/manifest.json` — name "SIDIX Pixel", permissions, content scripts
- Compatible Chrome 120+, Edge, Brave (chromium family)

**2. Content Script (`content.js`)**
- Detect `@sidix` mention pattern di:
  - Page text (Twitter/X, IG, Facebook, LinkedIn, blog)
  - Form input live typing (deteksi sebelum submit)
  - Comment fields
- Capture context: URL, surrounding text, page title, screenshot (optional)

**3. Background Service Worker (`background.js`)**
- Receive trigger from content script
- POST ke endpoint SIDIX `/sidix/pixel/capture`
- Track per-domain opt-in/opt-out preference
- Local IndexedDB queue kalau offline (replay saat online)

**4. Popup UI (`popup.html` + `popup.js`)**
- Status: connected / disconnected
- Manual trigger: "Capture this page"
- Domain settings: enable/disable per site
- Recent captures list (5 latest)
- Link ke dashboard tiranyx (future)

**5. SIDIX endpoint `/sidix/pixel/capture`**
- POST: `{url, page_title, surrounding_text, trigger_keyword, screenshot_b64?}`
- Authenticate via X-SIDIX-PIXEL-TOKEN
- Pipeline:
  1. Save context to corpus queue
  2. Call `conversation_synthesizer.synthesize()` jika long content
  3. Optional: invoke `persona_research_fanout.gather()` jika "deep" flag
  4. Hafidz Ledger entry
  5. Return note_id

**6. Optional: Meta tag pixel (Phase 2)**
- 1-line embed: `<script src="https://cdn.tiranyx.co.id/sidix-pixel.js"></script>`
- Detect `<meta name="sidix:embed" content="...">`  
- Defer ke Sprint 42b setelah Chrome extension validated

---

## Cara solve (method)

**Pattern:** Chrome Extension Manifest V3 + Service Worker.

**Trigger detection logic:**
```javascript
// content.js (simplified)
const KEYWORD = /@sidix\b/i;

document.addEventListener("input", (e) => {
  if (KEYWORD.test(e.target.value)) {
    chrome.runtime.sendMessage({
      type: "SIDIX_TRIGGER",
      url: location.href,
      title: document.title,
      content: extractSurroundingText(e.target),
    });
  }
});

// Also scan static page content
const observer = new MutationObserver(() => {
  if (KEYWORD.test(document.body.innerText)) {
    chrome.runtime.sendMessage({type: "SIDIX_PAGE_MENTION", ...});
  }
});
```

**Privacy boundary:**
- Default: opt-in per domain (whitelist)
- Never capture password/credential fields
- Surrounding text capped 500 chars
- Screenshot opt-in only
- All payloads encrypted in transit (HTTPS)

---

## Verifikasi (testing strategy)

**Unit test:**
- Manifest validates (Chrome web store linter)
- Content script regex matches edge cases (`@sidix.something`, `email@sidix.com` should NOT trigger)
- Background worker handles offline queue

**Integration test:**
- Load extension unpacked di Chrome dev mode
- Visit Twitter/X, type `@sidix test capture`
- Verify POST received di SIDIX dev endpoint
- Verify research note generated end-to-end

**Smoke test scenarios:**
1. ✅ Twitter compose tweet `@sidix bagus banget produk ini` → capture
2. ✅ IG comment `@sidix sintesis ini` → capture
3. ✅ Blog post static text mengandung `@sidix` → page mention capture
4. ❌ Email field `user@sidix.com` → NO trigger (edge case)
5. ❌ Password/credential field with text → NO capture (privacy)

---

## Optimasi (Phase 2+ improvements)

- **Local SLM untuk pre-classification** — extension run small model offline untuk decide "worth sending to SIDIX?", reduce server load
- **Debounce trigger** — kalau user type `@sidix` lalu hapus, tidak fire
- **Batch POST** — collect N triggers, POST sekaligus untuk reduce network
- **Visual feedback** — chrome notification kalau capture sukses + link ke note
- **Quick reply** — popup show SIDIX response inline (need streaming endpoint)
- **Mobile companion** — Tasker integration Android, Shortcuts iOS (Phase 3)

---

## Temuan untuk agen selanjutnya

**Decision rationale (jangan diulang):**
1. **Manifest V3** dipilih (bukan V2) — V2 deprecated by Chrome
2. **Chromium-only first** — Chrome+Edge+Brave (90% dev market). Firefox WebExtension API differ slightly, defer
3. **`@sidix` keyword** — universal, recognizable, low false-positive (vs `sidix:` yang bisa muncul di domain)
4. **Opt-in per domain** — privacy-first default. Trust building dengan user
5. **Endpoint terpisah `/sidix/pixel/capture`** (bukan reuse /sidix/synthesize_conversation) — different auth, different rate limit, different queue priority

**Dependencies:**
- Sprint 41 LIVE (Conversation Synthesizer engine) ✅
- BRAIN_QA_ADMIN_TOKEN (or new SIDIX_PIXEL_TOKEN) untuk auth
- Public HTTPS endpoint (sudah ada via ctrl.sidixlab.com)

**Risk + mitigation:**
- ⚠️ Chrome web store review reject → submit early, iterate
- ⚠️ User suspect tracking → very transparent UI + minimal permissions
- ⚠️ Rate limit abuse → token bucket per domain + IP
- ⚠️ Privacy concern → comprehensive privacy policy + opt-in default

---

## Sprint 42 timeline

| Phase | Duration | Deliverable |
|---|---|---|
| **Phase 1** (this commit) | 1 hari | Scaffold: manifest + content + background + popup + endpoint stub |
| **Phase 2** | 1 minggu | Trigger detection + capture flow + endpoint LIVE |
| **Phase 3** | 1 minggu | Privacy controls + opt-in UI + offline queue |
| **Phase 4** | 3 hari | Smoke test + Chrome web store submission preparation |
| **Phase 5** | 4 hari | Real-world test + iterate based on dogfood |

Total ~3 minggu sesuai 12-week sequence lock.

---

## Owner decisions perlu sebelum Phase 2 wire-up

1. **Domain default whitelist?** Saya rekomendasi: `twitter.com, x.com, instagram.com, facebook.com, linkedin.com, youtube.com, github.com` opt-in default
2. **Endpoint subdomain** — pakai `ctrl.sidixlab.com/sidix/pixel/capture` atau buka `pixel.sidixlab.com` baru?
3. **Branding extension** — name: "SIDIX Pixel" / "SIDIX Capture" / "Tiranyx SIDIX"?
4. **Logo extension** — pakai logo SIDIX existing atau bikin baru "pixel" themed?
5. **Privacy policy URL** — wajib untuk Chrome web store. Bos siap draft atau saya draft skeleton?

---

*Sprint 42 plan drafted by Claude · Sonnet 4.6 · 2026-04-29 · sambil Sprint 13 LoRA training continues + setelah Sprint 41 LIVE.*

*Reference: docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md, project_sidix_distribution_pixel_basirport.md, project_sidix_multi_agent_pattern.md.*
