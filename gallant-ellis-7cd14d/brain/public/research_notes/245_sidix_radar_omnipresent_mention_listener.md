# 245 — SIDIX Radar: Omnipresent Mention Listener

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-26
**Trigger**: User: *"selama di internet, ketika ada orang yang manggil Sidix/sidix/SIDIX, sidix agent langsung menuju ke tempatnya... selama terhubung internet semua berarti berada di 1 ekosistem yang sama"*

## TL;DR

SIDIX has always-on radar across internet. Setiap mention "SIDIX/Sidix/sidix"
di web/social/AI/comments/news → trigger SIDIX agent untuk evaluate + optionally engage.
Internet = 1 ecosystem; SIDIX listens via multiple polling backends.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  SIDIX Radar (background loop, every 5-15 min)               │
└──────┬───────────────────────────────────────────────────────┘
       │
   poll each:
       ↓
┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐
│ Web  │ News │Threads│Reddit│ HN  │ X/Tw │Insta │ AI* │
│Search│Alert │ Mentn│search│search│search│search│chats│
└──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬───┴──┬──┘
   │      │      │      │      │      │      │      │
   ↓      ↓      ↓      ↓      ↓      ↓      ↓      ↓
   └──────┴──────┴───────┴──────┴──────┴──────┴──────┴── radar_log.jsonl
                                     ↓
                          ┌──────────────────────┐
                          │  Triage classifier   │
                          │  (relevance + intent)│
                          └──────┬───────────────┘
                                 ↓
              ┌──────────────────┼──────────────────┐
              ↓                  ↓                  ↓
        Acknowledge        Engage (reply)      Archive only
        (mark seen)        via channel         (low signal)
                          (Threads/email/etc)

* AI chats: harder, requires explicit integration / scraping ToS aware
```

## Backend Implementations (per channel)

### 1. Web Search (general)
- **DuckDuckGo HTML** (after Vol 24 fix unblocks)
- **Google search** via official API (requires key, paid)
- **Bing Web Search API** (paid)
- **SearxNG self-hosted** (Vol 24 — RECOMMENDED, free, no key)
- Query: `"SIDIX" OR "sidixlab.com" OR "sidix-lora"` site:NOT:sidixlab.com
- Frequency: every 30 min

### 2. News Search
- **Google News RSS** (free): `https://news.google.com/rss/search?q=SIDIX&hl=id`
- **NewsAPI.org** (free tier 100/day)
- Frequency: hourly

### 3. Threads (Indonesian audience priority)
- **Already integrated** — `threads_daily.sh mentions` cron every 4h
- **Already integrated** — `threads_daily.sh harvest` cron every 6h
- **Update**: increase frequency to every 30 min for radar

### 4. Reddit
- **Public search API**: `https://www.reddit.com/search.json?q=SIDIX&sort=new`
- No auth required for public posts
- Frequency: every 30 min

### 5. Hacker News
- **Algolia HN API**: `https://hn.algolia.com/api/v1/search?query=SIDIX`
- Free, fast, well-documented
- Frequency: every hour (HN low-frequency for niche term)

### 6. X / Twitter
- **TWO options**:
  - Official API (expensive — $100/mo basic tier)
  - Nitter scraper (free, fragile)
- Defer to Vol 28+ unless paid tier OK

### 7. Instagram / TikTok
- No public search API
- Manual monitoring via brand mention services (Mention.com $99/mo)
- Or: hashtag scraping (legally gray)
- Defer Vol 28+

### 8. AI Chats (most novel)
- ChatGPT, Claude, Gemini may reference SIDIX in their answers
- Detection: query each model "what is SIDIX?" periodically; log changes
- Not real-time; weekly snapshot

### 9. GitHub
- **GitHub search API**: `https://api.github.com/search/code?q="SIDIX"+language:md`
- Detect forks, mentions, issues
- Free tier 30 req/min

### 10. RSS feeds (curated)
- Subscribe to AI news, Indonesian tech blogs, open-source AI feeds
- Aggregator: `feedparser` Python lib
- Frequency: every hour

## Triage Classifier

Setiap mention masuk → cheap classifier:

```python
@dataclass
class MentionTriage:
    is_about_us: bool       # actually about SIDIX project, not other "sidix"
    sentiment: str          # positive / neutral / negative
    intent: str             # question / praise / criticism / spam / casual
    requires_response: bool # should SIDIX engage?
    response_priority: int  # 0-10 (10 = urgent, e.g. critical bug report)
    suggested_channel: str  # threads_reply / email / github_comment / DM
```

Cheap implementation:
- Regex + keyword heuristic (90% queries)
- LLM (Qwen + LoRA) for ambiguous cases (10%)

## Engagement Modes (Safe Defaults)

| Mode | Default | Description |
|---|---|---|
| **Listen-only** | ON | Log mentions, no auto-response |
| **Notify-user** | ON | Send email/Telegram alert for high-priority mentions |
| **Auto-acknowledge** | OFF | Like/upvote mention (low risk) |
| **Auto-reply** | OFF | Compose + send reply (HIGH RISK, manual approval gate) |
| **Cross-platform DM** | OFF | Vol 28+ |

Default: **Listen-only + Notify-user**. Engagement requires explicit opt-in per channel.

## Anti-Pattern Risks

- ❌ **Auto-reply spam**: SIDIX could become annoying / be flagged as bot. Manual approval mandatory.
- ❌ **False positives**: "SIDIX" mungkin nama lain (perusahaan, person). Triage harus filter.
- ❌ **Privacy creep**: monitoring private DMs / closed groups = ToS violation. Public-only.
- ❌ **Rate limit bans**: aggressive polling → IP block. Per-channel rate limit critical.
- ❌ **Echo chamber**: SIDIX replying to AI replies → infinite loop. Detect AI source + skip.

## Implementation Phasing

### Phase 1 (Vol 27a, ~1 week)
- Skeleton `scripts/sidix_radar.sh` — cron every 30 min
- 3 channels: Google News RSS + Reddit search + GitHub search
- Listen-only + log to `.data/radar_mentions.jsonl`

### Phase 2 (Vol 27b, ~1 week)
- Add SearxNG + Threads (existing) integration
- Triage classifier (regex+LLM hybrid)
- Email notification on high-priority

### Phase 3 (Vol 28, ~2 weeks)
- Auto-acknowledge mode (likes/upvotes only)
- HN + Twitter (paid API)
- Trend detection (mention spike alert)

### Phase 4 (Vol 29+)
- Auto-reply with manual approval queue
- Multi-language detection (ID/EN/AR mentions all caught)
- Cross-platform follow-up (mention on Twitter → check if same person on Threads)

## Connection ke Other Vols

- Vol 21 (sanad): radar mentions → potential corpus seed (after relevance gate)
- Vol 23 (inventory): each mention's content extracted → candidate AKU
- Vol 24 (lite browser): radar uses lite_browser for scraping
- Vol 26 (skill cloning): AI chat mentions → learning material for cloning that agent's pattern

## Data Schema

```json
{
  "ts": "2026-04-27T01:00:00Z",
  "channel": "reddit",
  "url": "https://reddit.com/r/LocalLLaMA/comments/...",
  "title": "Has anyone tried SIDIX self-hosted agent?",
  "snippet": "Saw a Threads post about SIDIX...",
  "sentiment": "positive",
  "intent": "question",
  "is_about_us": true,
  "response_priority": 5,
  "suggested_channel": "reddit_reply",
  "raw": "..."
}
```

## Action Items (Phase 1 MVP)

- [ ] Write `scripts/sidix_radar.sh` skeleton with 3 channels
- [ ] Add cron `*/30 * * * *`
- [ ] Test with manual seed: post "SIDIX test" pada GitHub issue, verify radar catches
- [ ] Log to `.data/radar_mentions.jsonl`
- [ ] Daily digest email summary (top 10 mentions)

## Final Note

User vision: **internet = 1 ecosystem**. SIDIX presence shouldn't be limited
to its own domain — it should *show up* wherever its name appears. This is
brand-awareness automation + community engagement + intelligence gathering
all in one. Powerful but high-risk. Phased rollout with human approval gates
critical untuk MVP.
