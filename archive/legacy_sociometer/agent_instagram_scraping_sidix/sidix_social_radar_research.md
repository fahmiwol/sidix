# SIDIX SOCIAL RADAR — Technical Deep-Dive Research
## Executive Summary untuk 8 Area Riset Strategis

**Tanggal:** 23 April 2026
**Versi:** v1.0 — Sprint 7 Research
**Status:** Foundation untuk MVP 3-4 hari

---

## 1. INSTAGRAM SCRAPING: Technical Deep-Dive

### Rekomendasi Utama: Hybrid Approach (GraphQL API + curl_cffi)

Berdasarkan riset terbaru (2025-2026), Instagram scraping landscape telah berubah secara fundamental. Pendekatan hybrid adalah satu-satunya cara yang sustainable untuk MVP Social Radar.

#### 1.1 Instagram Anti-Scraping Stack (2026)

Instagram menerapkan **5 layer defense** yang harus dipahami:

| Layer | Mekanisme | Countermeasure |
|-------|-----------|----------------|
| Layer 1 | IP Quality Check | Residential proxy rotation |
| Layer 2 | TLS Fingerprinting | curl_cffi (impersonate browser) |
| Layer 3 | Rate Limiting (200 req/hour/IP) | Random delays + proxy rotation |
| Layer 4 | Behavioral Detection | Human-like browsing patterns |
| Layer 5 | doc_id Rotation (2-4 minggu) | Monitoring + auto-update |

**Kritis:** Python `requests` standard akan **selalu gagal** di production karena TLS fingerprint mismatch. Ini adalah kesalahan #1 yang membuat scraper baru berhenti.

```python
# ❌ SALAH - Akan kena block dalam hitungan menit
import requests
response = requests.get("https://www.instagram.com/google/")

# ✅ BENAR - curl_cffi mengimpersonasi TLS fingerprint Chrome
from curl_cffi import requests as crequests
response = crequests.get(
    "https://www.instagram.com/google/",
    impersonate="chrome110"
)
```

#### 1.2 Three-Layer Scraping Architecture

**Layer 1: Chrome Extension (Data Collection)**
- Menggunakan **Network Interception Pattern** — paling robust untuk SPA (Single Page Application)
- Tidak scrape DOM — intercept API calls Instagram ke GraphQL endpoint
- Extract structured JSON langsung dari response body
- Keuntungan: Immune ke UI changes, lebih stealth, structured data

**Layer 2: Backend Python (Data Processing)**
- FastAPI endpoint menerima payload dari Chrome Extension
- Queue ke Redis untuk processing async
- curl_cffi sebagai fallback untuk scrape langsung jika extension tidak aktif

**Layer 3: Data Pipeline (Storage & Analysis)**
- PostgreSQL untuk structured data
- Redis untuk queue dan caching
- MinIO/S3 untuk media storage

#### 1.3 GraphQL Endpoint Critical doc_ids (2026)

| Data Type | Endpoint | doc_id | Frequency Change |
|-----------|----------|--------|------------------|
| Profile Info | `/api/v1/users/web_profile_info/` | N/A (REST) | Rare |
| Posts Feed | `/graphql/query` | `9310670392322965` | 2-4 minggu |
| Post Detail | `/graphql/query` | `8845758582119845` | 2-4 minggu |
| Reels | `/graphql/query` | `25981206651899035` | 2-4 minggu |
| Comments | `/graphql/query` | Variable | Frequent |

**Strategy untuk doc_id changes:**
```python
# doc_id discovery automation (run weekly)
async def discover_doc_ids():
    """Auto-discover current doc_ids via headless browser"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Intercept network requests
        doc_ids = {}
        page.on("request", lambda req: 
            extract_doc_id(req.url, req.post_data_json)
        )
        
        await page.goto("https://www.instagram.com/")
        # Trigger actions yang memicu GraphQL calls
        await page.evaluate("window.scrollTo(0, 500)")
        
        return doc_ids
```

#### 1.4 MVP Scraping Spec

```python
# social_radar/scraper/instagram.py
from curl_cffi import requests as crequests
import hashlib
import time
import random
from datetime import datetime
from typing import Optional, Dict, List

class InstagramScraper:
    """Production-grade Instagram scraper untuk SIDIX Social Radar"""
    
    def __init__(self, proxy_pool: List[str]):
        self.session = crequests.Session()
        self.proxy_pool = proxy_pool
        self.ig_app_id = "936619743392459"
        self.request_count = 0
        self.last_request_time = 0
        
    def _get_headers(self) -> Dict:
        return {
            "x-ig-app-id": self.ig_app_id,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
    
    def _rate_limit(self):
        """1 request per 6 seconds minimum (10 req/minute)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < 6:
            sleep_time = random.uniform(6.5, 8.0) - elapsed
            time.sleep(max(0, sleep_time))
        self.last_request_time = time.time()
    
    def get_profile(self, username: str) -> Optional[Dict]:
        """Scrape public profile — no login required"""
        self._rate_limit()
        proxy = random.choice(self.proxy_pool) if self.proxy_pool else None
        
        try:
            response = self.session.get(
                f"https://i.instagram.com/api/v1/users/web_profile_info/",
                params={"username": username},
                headers=self._get_headers(),
                proxies={"http": proxy, "https": proxy} if proxy else None,
                timeout=15
            )
            
            if response.status_code == 429:
                # Rate limited — exponential backoff
                time.sleep(random.uniform(60, 120))
                return self.get_profile(username)  # Retry once
                
            data = response.json()
            user = data.get("data", {}).get("user", {})
            
            return {
                "username": user.get("username"),
                "full_name": user.get("full_name"),
                "biography": user.get("biography"),
                "followers": user.get("edge_followed_by", {}).get("count"),
                "following": user.get("edge_follow", {}).get("count"),
                "posts_count": user.get("edge_owner_to_timeline_media", {}).get("count"),
                "is_business": user.get("is_business_account"),
                "is_verified": user.get("is_verified"),
                "profile_pic_url": user.get("profile_pic_url"),
                "scraped_at": datetime.utcnow().isoformat(),
                "source": "public_api"
            }
            
        except Exception as e:
            # Log error, return None (tidak raise — graceful degradation)
            return None
    
    def get_recent_posts(self, user_id: str, count: int = 12) -> List[Dict]:
        """Scrape recent posts via GraphQL — public data only"""
        # Implementation menggunakan doc_id dan pagination cursor
        pass
```

#### 1.5 Proxy Strategy untuk MVP

Mengingat budget constraint, rekomendasi **3-tier proxy approach**:

| Tier | Service | Cost | Use Case |
|------|---------|------|----------|
| Free | Rotating free proxies | $0 | Development/testing only |
| Budget | Webshare.io residential | $7/month | MVP (5-10 proxies) |
| Production | Bright Data/Oxylabs | $50+/month | Scale (50+ proxies) |

**SIDIX-specific:** Karena self-hosted dan no vendor API, user bisa supply proxy mereka sendiri. Ini adalah **differentiator** — transparansi total.

---

## 2. CHROME EXTENSION ARCHITECTURE

### Rekomendasi: Manifest V3 + Network Interception Pattern

#### 2.1 Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                    SIDIX SOCIAL RADAR                        │
│                    Chrome Extension                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐ │
│  │   Popup UI   │◄──►│   Service    │◄──►│  Backend    │ │
│  │  (React/Vue) │    │   Worker     │    │  (port 8765)│ │
│  └──────────────┘    └──────┬───────┘    └─────────────┘ │
│                             │                              │
│                       ┌─────┴──────┐                       │
│                       ▼            ▼                       │
│               ┌──────────────┐ ┌──────────────┐           │
│               │ Content      │ │ Offscreen    │           │
│               │ Script       │ │ Document     │           │
│               │ (DOM/        │ │ (Heavy       │           │
│               │  Network     │ │  Processing) │           │
│               │  Intercept)  │ │              │           │
│               └──────────────┘ └──────────────┘           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 2.2 Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Manifest Version | V3 | Required by Chrome Web Store (MV2 deprecated) |
| Framework | Vanilla JS + Web Components | Lightweight, no build step untuk MVP |
| Storage | chrome.storage.local + IndexedDB | Local-only, privacy-first |
| Communication | chrome.runtime.sendMessage | Simple, reliable |
| Pattern | Network Interception | Robust untuk SPA seperti Instagram |

#### 2.3 Network Interception Implementation

Ini adalah **game-changer** untuk Social Radar. Daripada scrape DOM yang fragile, intercept API calls Instagram:

```javascript
// page-interceptor.js — injected into page context
(function() {
    const originalFetch = window.fetch;
    
    window.fetch = async function(...args) {
        const response = await originalFetch.apply(this, args);
        const url = args[0];
        
        // Intercept Instagram GraphQL calls
        if (url.includes('instagram.com/graphql') || 
            url.includes('instagram.com/api')) {
            
            const clone = response.clone();
            const body = await clone.text();
            
            // Dispatch custom event untuk content script
            window.dispatchEvent(new CustomEvent('instaApiIntercepted', {
                detail: { url, body, timestamp: Date.now() }
            }));
        }
        
        return response;
    };
    
    // Similar interception untuk XMLHttpRequest
    const originalXHR = window.XMLHttpRequest.prototype.open;
    window.XMLHttpRequest.prototype.open = function(method, url) {
        this.addEventListener('load', function() {
            if (url.includes('instagram.com/graphql')) {
                window.dispatchEvent(new CustomEvent('instaApiIntercepted', {
                    detail: { url, body: this.responseText, timestamp: Date.now() }
                }));
            }
        });
        return originalXHR.apply(this, arguments);
    };
})();
```

```javascript
// content.js — listens for intercepted data
// Inject page interceptor
const script = document.createElement('script');
script.src = chrome.runtime.getURL('page-interceptor.js');
script.onload = function() { this.remove(); };
(document.head || document.documentElement).appendChild(script);

// Listen for intercepted API data
window.addEventListener('instaApiIntercepted', (event) => {
    const { url, body, timestamp } = event.detail;
    
    // Forward to background service worker
    chrome.runtime.sendMessage({
        type: 'INSTAGRAM_API_DATA',
        payload: { url, body, timestamp, tabUrl: window.location.href }
    });
});
```

```javascript
// background.js — process and send to backend
const processedIds = new Set();

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'INSTAGRAM_API_DATA') {
        processInstagramData(message.payload, sender.tab?.id);
    }
    return true; // Keep channel open for async
});

async function processInstagramData(data, tabId) {
    try {
        const json = JSON.parse(data.body);
        
        // Deduplicate by shortcode/content ID
        const id = extractId(json);
        if (processedIds.has(id)) return;
        processedIds.add(id);
        
        // Send ke SIDIX backend (port 8765)
        const response = await fetch('http://localhost:8765/api/social-radar/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platform: 'instagram',
                data_type: inferDataType(data.url, json),
                raw_data: json,
                source_url: data.tabUrl,
                collected_at: new Date(data.timestamp).toISOString(),
                // OpHarvest metadata
                consent_verified: true,
                collection_method: 'public_api_intercept',
                anonymization_level: 'hash_username'
            })
        });
        
        if (response.ok) {
            // Update badge count
            const count = processedIds.size;
            chrome.action.setBadgeText({ text: String(count), tabId });
            chrome.action.setBadgeBackgroundColor({ color: '#10B981' });
        }
        
    } catch (e) {
        // Non-JSON response or irrelevant
    }
}
```

#### 2.4 manifest.json

```json
{
  "manifest_version": 3,
  "name": "SIDIX Social Radar",
  "version": "1.0.0",
  "description": "Competitor intelligence & social listening — powered by SIDIX AI",
  "permissions": [
    "storage",
    "activeTab",
    "offscreen"
  ],
  "host_permissions": [
    "https://www.instagram.com/*",
    "http://localhost:8765/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["https://www.instagram.com/*"],
      "js": ["content.js"],
      "run_at": "document_start",
      "world": "ISOLATED"
    }
  ],
  "web_accessible_resources": [
    {
      "resources": ["page-interceptor.js"],
      "matches": ["https://www.instagram.com/*"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

#### 2.5 Data Flow (User Journey)

```
1. User install extension dari Chrome Web Store
2. User navigasi ke Instagram profile kompetitor
3. Content script auto-inject page-interceptor.js
4. User scroll/browse — Instagram app fetch data via GraphQL
5. page-interceptor.js intercept fetch/XHR calls
6. Raw JSON data dikirim ke content script via CustomEvent
7. Content script forward ke background service worker
8. Background worker:
   a. Deduplicate (cek processedIds Set)
   b. Parse relevant fields
   c. POST ke SIDIX backend (/api/social-radar/ingest)
9. Backend queue untuk processing
10. AI analysis (Qwen2.5-7B) generate competitor report
11. Report tersedia di dashboard SIDIX (Next.js port 3000)
```

---

## 3. REAL-TIME ALERT SYSTEM

### Rekomendasi: Tiered Approach (Polling → SSE → WebSocket)

Mengingat constraint self-hosted dan minimal resource, pendekatan bertahap:

#### 3.1 Architecture Decision Matrix

| Method | Complexity | Real-time | Resource | Best For |
|--------|-----------|-----------|----------|----------|
| Polling | Low | 30-60s delay | Minimal | MVP — Free tier (24h refresh) |
| SSE (Server-Sent Events) | Medium | Near real-time | Low | Pro tier (6h refresh) |
| WebSocket | High | Real-time | Medium | Enterprise tier |
| Webhook | Low-Medium | Event-driven | Low | External integrations |

#### 3.2 MVP Implementation: Smart Polling

```python
# social_radar/alerts/poller.py
import asyncio
from datetime import datetime, timedelta
from typing import Set

class SmartPoller:
    """
    Intelligent polling dengan adaptive frequency.
    - Semakin sering kompetitor posting, semakin sering poll
    - Rate limit respect (max 1 req/6 detik)
    - Priority queue untuk accounts yang lebih aktif
    """
    
    def __init__(self, scraper, min_interval: int = 3600):
        self.scraper = scraper
        self.min_interval = min_interval  # minimum seconds between polls
        self.account_states = {}  # username -> last_poll, post_count, frequency
        
    async def calculate_poll_interval(self, username: str) -> int:
        """Adaptive interval based on posting frequency"""
        state = self.account_states.get(username, {})
        posts_per_day = state.get('posts_per_day', 1)
        
        # More active accounts = more frequent polling
        if posts_per_day >= 5:
            return max(3600, self.min_interval)  # 1 hour
        elif posts_per_day >= 2:
            return max(7200, self.min_interval)  # 2 hours
        else:
            return max(14400, self.min_interval)  # 4 hours
    
    async def poll_account(self, username: str):
        """Poll single account, detect changes"""
        profile = await self.scraper.get_profile_async(username)
        if not profile:
            return
            
        current_posts = profile['posts_count']
        last_state = self.account_states.get(username, {})
        last_posts = last_state.get('posts_count', 0)
        
        # Detect new posts
        if current_posts > last_posts:
            new_posts_count = current_posts - last_posts
            await self.trigger_alert(username, 'new_posts', {
                'count': new_posts_count,
                'previous_count': last_posts,
                'current_count': current_posts
            })
        
        # Update state
        self.account_states[username] = {
            'last_poll': datetime.utcnow(),
            'posts_count': current_posts,
            'followers': profile['followers'],
            'posts_per_day': self._calculate_posting_frequency(username)
        }
    
    async def run(self, usernames: Set[str]):
        """Main polling loop"""
        while True:
            tasks = []
            for username in usernames:
                interval = await self.calculate_poll_interval(username)
                last_poll = self.account_states.get(username, {}).get('last_poll')
                
                if not last_poll or (datetime.utcnow() - last_poll).seconds >= interval:
                    tasks.append(self.poll_account(username))
                    
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(60)  # Check every minute
```

#### 3.3 Alert Types & Triggers

| Alert Type | Trigger | Priority | Channel |
|-----------|---------|----------|---------|
| New Post | Kompetitor publish post baru | High | In-app + Email |
| Follower Spike | +X% followers dalam Y jam | Medium | In-app |
| Engagement Anomaly | Post mendapat >X% engagement | Medium | In-app |
| Bio Change | Profile bio/link berubah | Low | In-app digest |
| Hashtag Trend | Hashtag baru muncul di niche | Low | Weekly report |
| Content Strategy Shift | Perubahan pattern posting | High | AI Report |

#### 3.4 Upgrade Path ke SSE (Pro Tier)

```python
# social_radar/alerts/sse.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI()

class SSEManager:
    def __init__(self):
        self.clients = set()
    
    async def connect(self):
        queue = asyncio.Queue()
        self.clients.add(queue)
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
        finally:
            self.clients.discard(queue)
    
    async def broadcast(self, message: dict):
        dead_clients = set()
        for client in self.clients:
            try:
                client.put_nowait(message)
            except asyncio.QueueFull:
                dead_clients.add(client)
        self.clients -= dead_clients

sse_manager = SSEManager()

@app.get("/api/alerts/stream")
async def alert_stream():
    return StreamingResponse(
        sse_manager.connect(),
        media_type="text/event-stream"
    )

# Trigger dari polling loop
async def on_new_post_detected(username: str, post_data: dict):
    await sse_manager.broadcast({
        "type": "new_post",
        "username": username,
        "data": post_data,
        "timestamp": datetime.utcnow().isoformat()
    })
```

---

## 4. COMPETITOR INTELLIGENCE AI PROMPT ENGINEERING

### Rekomendasi: Zero-Shot Chain-of-Thought (Bukan Few-Shot) untuk Qwen2.5-7B

#### 4.1 Key Research Findings (2025)

Penelitian terbaru tentang Qwen2.5 models menunjukkan:

> **"Zero-shot chain-of-thought equals or beats few-shot chain-of-thought on arithmetic, algebra, and logic puzzles"** — Tianpan, 2026

> **"Qwen2.5-7B and Qwen2.5-72B are insensitive to all 162 personas"** — Stanford, 2024

**Implikasi untuk SIDIX:**
- ❌ Jangan gunakan few-shot examples (boros token, tidak meningkatkan kualitas)
- ❌ Jangan gunakan role-playing personas (tidak efektif untuk Qwen2.5-7B)
- ✅ Gunakan zero-shot dengan explicit reasoning instructions
- ✅ Gunakan structured output format (JSON)
- ✅ Gunakan task decomposition (break down complex analysis)

#### 4.2 Prompt Template: Competitor Analysis

```python
COMPETITOR_ANALYSIS_PROMPT = """Analyze the following Instagram competitor data and provide strategic insights.

## Input Data
- Competitor Username: {username}
- Profile Data: {profile_json}
- Recent Posts (last 30 days): {posts_json}
- Engagement Metrics: {engagement_json}
- Your Account Data: {user_account_json}

## Analysis Requirements

Perform the following analyses in sequence:

### 1. Content Strategy Analysis
Identify:
- Posting frequency and timing patterns
- Content themes and categories
- Visual style consistency
- Caption writing style and CTA usage
- Hashtag strategy (branded vs. community vs. trending)

### 2. Engagement Pattern Analysis
Calculate:
- Average engagement rate (likes + comments / followers)
- Engagement trend (increasing/stable/decreasing)
- Best performing content types
- Community interaction level (reply to comments?)
- Audience sentiment from comments

### 3. Growth Strategy Analysis
Evaluate:
- Follower growth rate
- Content-to-growth correlation
- Collaboration patterns (tagged accounts)
- Cross-platform presence indicators
- Monetization signals (affiliate links, shop tags)

### 4. Competitive Positioning
Compare dengan user's account:
- Relative strengths and weaknesses
- Content gaps (topics they cover that you don't)
- Audience overlap estimation
- Differentiation opportunities

### 5. Actionable Recommendations
Provide 3-5 specific, actionable recommendations:
- Content ideas inspired by their success (tapi bukan copy)
- Timing optimization suggestions
- Engagement tactics
- Differentiation strategies

## Output Format
Return valid JSON dengan struktur berikut:

```json
{
  "competitor_username": "string",
  "analysis_date": "ISO8601",
  "content_strategy": {
    "posting_frequency": "string",
    "optimal_posting_times": ["string"],
    "content_themes": [{"theme": "string", "frequency": "number"}],
    "visual_style": "string",
    "hashtag_strategy": "string"
  },
  "engagement_analysis": {
    "avg_engagement_rate": "number",
    "engagement_trend": "increasing|stable|decreasing",
    "best_performing_content": ["string"],
    "community_sentiment": "positive|neutral|negative"
  },
  "growth_strategy": {
    "follower_growth_rate": "number",
    "growth_tactics": ["string"],
    "monetization_indicators": ["string"]
  },
  "competitive_positioning": {
    "your_relative_strength": "string",
    "content_gaps": ["string"],
    "differentiation_opportunities": ["string"]
  },
  "recommendations": [
    {
      "priority": 1,
      "category": "content|timing|engagement|differentiation",
      "action": "string",
      "expected_impact": "string",
      "difficulty": "easy|medium|hard"
    }
  ]
}
```

Think step by step. Analyze the data carefully before forming conclusions. Be specific and data-driven, not generic.
"""
```

#### 4.3 Prompt Template: Trend Detection

```python
TREND_DETECTION_PROMPT = """Analyze Instagram content from multiple competitors to identify emerging trends in this niche.

## Input Data
- Niche/Industry: {niche}
- Competitors Analyzed: {competitor_list}
- Posts Data (last 90 days): {aggregated_posts_json}
- Hashtag Frequency: {hashtag_stats_json}
- Engagement Correlation: {engagement_correlation_json}

## Analysis Requirements

### 1. Content Trend Identification
- Rising content formats (Reels, Carousels, Stories)
- Emerging themes and topics
- Visual/meme trends
- Audio/trending sounds usage

### 2. Engagement Trend Analysis
- What type of content gets highest engagement NOW
- Changing audience preferences
- Comment sentiment shifts
- Viral content patterns

### 3. Hashtag & Keyword Trends
- Growing hashtags in the niche
- New hashtag strategies being adopted
- Keyword trends in captions
- Branded hashtag campaigns

### 4. Timing & Frequency Trends
- Best posting times (shifted?)
- Posting frequency changes
- Story vs. Feed vs. Reel ratio changes

### 5. Prediction & Opportunity
- Predict upcoming trends (next 30 days)
- Early-adopter opportunities
- Content gaps where competition is low

## Output Format
```json
{
  "analysis_period": "string",
  "niche": "string",
  "trends": [
    {
      "trend_name": "string",
      "category": "content_format|theme|hashtag|engagement|timing",
      "confidence": "high|medium|low",
      "evidence": "string",
      "timeline": "emerging|peak|declining",
      "opportunity_score": 1-10
    }
  ],
  "recommendations": [
    {
      "action": "string",
      "urgency": "now|this_week|this_month",
      "expected_impact": "string"
    }
  ]
}
```

Focus on actionable trends backed by data. Do not list generic advice.
"""
```

#### 4.4 Persona Integration (SIDIX-specific)

Meskipun research menunjukkan persona tidak meningkatkan akurasi, **persona tetap valuable untuk SIDIX** dari perspektif UX dan brand consistency. Persona TIDAK ditulis dalam system prompt sebagai role-playing, melainkan sebagai **output style guide**:

```python
# Persona selection affects output STYLE, not reasoning quality
PERSONA_STYLE_GUIDE = {
    "AYMAN": {
        "tone": "creative, inspiring, visionary",
        "focus": "content strategy, brand storytelling, creative differentiation",
        "language": "metaphor-rich, encouraging, big-picture"
    },
    "ABOO": {
        "tone": "analytical, precise, data-driven", 
        "focus": "metrics, benchmarks, ROI calculation",
        "language": "structured, numbers-oriented, factual"
    },
    "OOMAR": {
        "tone": "practical, hands-on, implementation-focused",
        "focus": "step-by-step tactics, tools, workflows",
        "language": "direct, actionable, checklist-oriented"
    }
}

# Usage: Append style instructions ke prompt (bukan persona role-play)
def apply_persona_style(prompt: str, persona: str) -> str:
    style = PERSONA_STYLE_GUIDE.get(persona, PERSONA_STYLE_GUIDE["ABOO"])
    return f"""{prompt}

## Output Style
- Tone: {style['tone']}
- Focus: {style['focus']}
- Language: {style['language']}
"""
```

---

## 5. DATA PIPELINE ARCHITECTURE

### Rekomendasi: asyncio + Redis (Tanpa Celery untuk MVP)

#### 5.1 Architecture Overview

Mengingat constraint "paling cepat, paling murah", Celery adalah overkill untuk MVP Social Radar. Gunakan **asyncio + Redis lightweight queue**:

```
┌─────────────────────────────────────────────────────────┐
│                 SIDIX SOCIAL RADAR PIPELINE             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Chrome Extension / Scraper                               │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────────┐     ┌──────────────┐                 │
│  │  FastAPI     │────►│  Redis       │                 │
│  │  (port 8765) │     │  Queue       │                 │
│  └──────────────┘     └──────┬───────┘                 │
│                              │                          │
│                       ┌──────┴──────┐                   │
│                       ▼             ▼                   │
│               ┌──────────┐  ┌──────────┐               │
│               │ Worker 1 │  │ Worker 2 │               │
│               │ (async)  │  │ (async)  │               │
│               └────┬─────┘  └────┬─────┘               │
│                    │             │                       │
│                    ▼             ▼                       │
│               ┌──────────────────────┐                  │
│               │  PostgreSQL +        │                  │
│               │  MinIO (media)       │                  │
│               └──────────────────────┘                  │
│                         │                               │
│                         ▼                               │
│               ┌──────────────────────┐                  │
│               │  Qwen2.5-7B          │                  │
│               │  (Analysis Engine)   │                  │
│               └──────────────────────┘                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 5.2 Lightweight Async Queue Implementation

```python
# social_radar/queue/redis_queue.py
import redis.asyncio as redis
import json
import asyncio
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class AsyncTaskQueue:
    """Lightweight asyncio task queue menggunakan Redis — alternative Celery untuk MVP"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.task_registry: dict[str, Callable] = {}
        self.running = False
        
    def register_task(self, name: str, handler: Callable):
        """Register task handler — seperti Celery @app.task"""
        self.task_registry[name] = handler
        logger.info(f"Registered task: {name}")
        
    async def enqueue(self, task_name: str, payload: dict, 
                      queue: str = "default",
                      delay: Optional[int] = None) -> str:
        """Add task ke queue — seperti task.delay()"""
        task_id = f"{task_name}:{asyncio.get_event_loop().time()}"
        task_data = {
            "id": task_id,
            "name": task_name,
            "payload": payload,
            "queue": queue,
            "retries": 0,
            "max_retries": 3,
            "created_at": asyncio.get_event_loop().time()
        }
        
        if delay:
            # Delayed task menggunakan Redis sorted set
            await self.redis.zadd(
                f"delayed:{queue}",
                {json.dumps(task_data): asyncio.get_event_loop().time() + delay}
            )
        else:
            # Immediate task
            await self.redis.lpush(f"queue:{queue}", json.dumps(task_data))
            
        return task_id
    
    async def process_queue(self, queue: str = "default", 
                           concurrency: int = 3):
        """Main worker loop — process tasks dengan asyncio concurrency"""
        self.running = True
        semaphore = asyncio.Semaphore(concurrency)
        
        async def process_single_task(task_data: dict):
            async with semaphore:
                handler = self.task_registry.get(task_data["name"])
                if not handler:
                    logger.error(f"Unknown task: {task_data['name']}")
                    return
                    
                try:
                    await handler(task_data["payload"])
                    # Log success
                    await self.redis.hset(
                        f"task:{task_data['id']}",
                        mapping={"status": "completed", "completed_at": str(asyncio.get_event_loop().time())}
                    )
                except Exception as e:
                    logger.exception(f"Task failed: {task_data['name']}")
                    if task_data["retries"] < task_data["max_retries"]:
                        task_data["retries"] += 1
                        await self.redis.lpush(f"queue:{queue}", json.dumps(task_data))
                    else:
                        # Dead letter queue
                        await self.redis.lpush("queue:dead_letter", json.dumps(task_data))
        
        while self.running:
            # Check delayed tasks
            now = asyncio.get_event_loop().time()
            delayed_tasks = await self.redis.zrangebyscore(
                f"delayed:{queue}", 0, now
            )
            for task_json in delayed_tasks:
                await self.redis.zrem(f"delayed:{queue}", task_json)
                await self.redis.lpush(f"queue:{queue}", task_json)
            
            # Process immediate tasks
            task_json = await self.redis.brpop(f"queue:{queue}", timeout=5)
            if task_json:
                _, task_data_str = task_json
                task_data = json.loads(task_data_str)
                asyncio.create_task(process_single_task(task_data))
            
            await asyncio.sleep(0.1)  # Prevent busy loop

# Usage — mirip Celery tapi pure asyncio
queue = AsyncTaskQueue()

@queue.register_task("analyze_profile")
async def analyze_profile_task(payload: dict):
    """Analyze competitor profile menggunakan Qwen2.5-7B"""
    username = payload["username"]
    profile_data = await fetch_profile_data(username)
    analysis = await generate_ai_analysis(profile_data)
    await save_analysis_to_db(username, analysis)

@queue.register_task("detect_trends")
async def detect_trends_task(payload: dict):
    """Detect trends dari aggregated data"""
    niche = payload["niche"]
    posts = await fetch_recent_posts(niche, days=30)
    trends = await generate_trend_analysis(posts)
    await save_trends_to_db(niche, trends)

# Enqueue dari endpoint
task_id = await queue.enqueue("analyze_profile", {"username": "competitor123"})
```

#### 5.3 Pipeline Stages

| Stage | Function | Queue | Priority |
|-------|----------|-------|----------|
| Ingest | Terima data dari Chrome Extension/scraper | `ingest` | High |
| Validate | Validasi & deduplicate data | `validate` | High |
| Transform | Normalize ke standard format | `transform` | Medium |
| Enrich | Tambah metadata & context | `enrich` | Medium |
| Analyze | AI analysis dengan Qwen2.5-7B | `analysis` | Low (CPU heavy) |
| Report | Generate user-facing report | `report` | Low |

#### 5.4 Error Handling & Retry

```python
# social_radar/pipeline/error_handler.py
class PipelineErrorHandler:
    """Centralized error handling untuk Social Radar pipeline"""
    
    RETRY_POLICY = {
        "network_error": {"max_retries": 5, "backoff": "exponential", "base_delay": 10},
        "rate_limit": {"max_retries": 3, "backoff": "fixed", "base_delay": 300},
        "parse_error": {"max_retries": 1, "backoff": "none", "base_delay": 0},
        "ai_timeout": {"max_retries": 2, "backoff": "linear", "base_delay": 30},
    }
    
    async def handle_error(self, task: dict, error: Exception) -> str:
        """Return action: 'retry', 'dead_letter', atau 'skip'"""
        error_type = self.classify_error(error)
        policy = self.RETRY_POLICY.get(error_type, self.RETRY_POLICY["network_error"])
        
        if task["retries"] < policy["max_retries"]:
            delay = self.calculate_backoff(task["retries"], policy)
            task["retries"] += 1
            await self.requeue_with_delay(task, delay)
            return "retry"
        else:
            await self.send_to_dead_letter(task, error)
            return "dead_letter"
    
    def classify_error(self, error: Exception) -> str:
        error_msg = str(error).lower()
        if "429" in error_msg or "rate limit" in error_msg:
            return "rate_limit"
        elif "timeout" in error_msg or "connection" in error_msg:
            return "network_error"
        elif "parse" in error_msg or "json" in error_msg:
            return "parse_error"
        elif "cuda" in error_msg or "gpu" in error_msg:
            return "ai_timeout"
        return "network_error"
```

---

## 6. PRIVACY ENGINEERING (OpHarvest Protocol)

### Prinsip: Privacy by Design, bukan Privacy sebagai afterthought

#### 6.1 Anonymization Pipeline

```python
# social_radar/privacy/anonymizer.py
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Optional
import json

class OpHarvestAnonymizer:
    """
    Privacy-first data processing untuk Social Radar.
    Sesuai dengan IHOS principles — transparansi dan keadilan.
    """
    
    def __init__(self, secret_key: bytes):
        self.secret_key = secret_key
        
    def anonymize_username(self, username: str) -> str:
        """
        Hash username dengan HMAC — irreversible tapi consistent.
        Berguna untuk deduplication tanpa menyimpan username asli.
        """
        return hmac.new(
            self.secret_key,
            username.lower().encode(),
            hashlib.sha256
        ).hexdigest()[:16]
    
    def anonymize_profile_data(self, profile: Dict) -> Dict:
        """
        Anonymize profile data sebelum storage.
        Keep data yang useful untuk analysis, remove PII.
        """
        return {
            # Hashed identifier (untuk tracking tanpa identifikasi)
            "user_hash": self.anonymize_username(profile["username"]),
            
            # Aggregated metrics only
            "follower_bucket": self._bucket_followers(profile.get("followers", 0)),
            "following_bucket": self._bucket_followers(profile.get("following", 0)),
            "posts_bucket": self._bucket_posts(profile.get("posts_count", 0)),
            
            # Non-PII attributes
            "is_business": profile.get("is_business", False),
            "is_verified": profile.get("is_verified", False),
            "account_age_days": self._estimate_account_age(profile),
            
            # Content analysis (bukan teks asli)
            "bio_sentiment": self._analyze_sentiment(profile.get("biography", "")),
            "bio_category": self._categorize_bio(profile.get("biography", "")),
            "has_link_in_bio": bool(profile.get("bio_links", [])),
            
            # Metadata
            "collected_at": datetime.utcnow().isoformat(),
            "data_source": profile.get("source", "unknown"),
            "anonymization_version": "1.0"
        }
    
    def _bucket_followers(self, count: int) -> str:
        """Bucket followers untuk privacy — exact count tidak disimpan"""
        if count < 1000:
            return "0-1K"
        elif count < 10000:
            return "1K-10K"
        elif count < 100000:
            return "10K-100K"
        elif count < 1000000:
            return "100K-1M"
        else:
            return "1M+"
    
    def _bucket_posts(self, count: int) -> str:
        if count < 50:
            return "0-50"
        elif count < 200:
            return "50-200"
        elif count < 500:
            return "200-500"
        elif count < 1000:
            return "500-1K"
        else:
            return "1K+"
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Extract sentiment tanpa menyimpan teks asli"""
        # Gunakan simple heuristic atau SIDIX sentiment tool
        return {
            "positive_words": 0,  # count only
            "negative_words": 0,
            "language": "id" if self._is_indonesian(text) else "en",
            "has_cta": any(word in text.lower() for word in ["link", "click", "shop", "order"])
        }
    
    def _categorize_bio(self, bio: str) -> str:
        """Kategorikan bio ke high-level category"""
        categories = {
            "business": [" bisnis", " business", " jual", " order"],
            "creator": [" content creator", " influencer", " blogger"],
            "personal": [" personal", " life", " journey"],
            "education": [" education", " course", " belajar", " learn"],
            "fashion": [" fashion", " style", " ootd"],
            "food": [" food", " kuliner", " makan", " recipe"],
        }
        bio_lower = bio.lower()
        for category, keywords in categories.items():
            if any(kw in bio_lower for kw in keywords):
                return category
        return "general"
    
    def _estimate_account_age(self, profile: Dict) -> Optional[int]:
        """Estimate account age dari posting history (exact join date tidak tersedia)"""
        # Implementasi: gunakan earliest post timestamp
        return None
    
    def _is_indonesian(self, text: str) -> bool:
        """Deteksi bahasa Indonesia"""
        id_markers = [" yang", " dan", " untuk", " dengan", " ini", " dari"]
        return sum(1 for m in id_markers if m in text.lower()) >= 2
```

#### 6.2 Consent Management System

```python
# social_radar/privacy/consent.py
from enum import Enum
from datetime import datetime
from typing import Optional, Dict
import json

class ConsentLevel(Enum):
    """Explicit opt-in levels — default OFF"""
    NONE = "none"           # No consent given
    BASIC = "basic"         # Profile metrics only (anonymized)
    FULL = "full"           # Include posts analysis (anonymized)
    RESEARCH = "research"   # Contribute to training data (anonymized + aggregated)

class ConsentManager:
    """
    User consent management — GDPR-aligned, transparent.
    
    Prinsip:
    1. Default OFF — user harus explicitly opt-in
    2. Granular consent levels — tidak all-or-nothing
    3. Audit trail — setiap consent change tercatat
    4. Easy withdrawal — user bisa withdraw kapan saja
    5. Data portability — user bisa export data mereka
    """
    
    def __init__(self, db):
        self.db = db
        
    async def get_consent(self, user_id: str) -> Dict:
        """Get current consent status untuk user"""
        record = await self.db.fetchrow(
            "SELECT * FROM user_consent WHERE user_id = $1 ORDER BY created_at DESC LIMIT 1",
            user_id
        )
        if not record:
            return {
                "user_id": user_id,
                "level": ConsentLevel.NONE.value,
                "granted_at": None,
                "expires_at": None,
                "purposes": [],
                "withdrawn": False
            }
        return dict(record)
    
    async def grant_consent(self, user_id: str, level: ConsentLevel,
                          purposes: list[str], duration_days: int = 365) -> Dict:
        """Record consent grant dengan audit trail"""
        now = datetime.utcnow()
        expires = now + timedelta(days=duration_days)
        
        consent = await self.db.fetchrow("""
            INSERT INTO user_consent 
                (user_id, level, purposes, granted_at, expires_at, withdrawn, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, false, $6, $7)
            RETURNING *
        """, user_id, level.value, purposes, now, expires, "", "")
        
        return dict(consent)
    
    async def withdraw_consent(self, user_id: str, reason: Optional[str] = None) -> Dict:
        """
        Withdraw consent — GDPR Article 17 Right to Erasure.
        Trigger data deletion process.
        """
        now = datetime.utcnow()
        
        # Mark consent sebagai withdrawn
        await self.db.execute("""
            UPDATE user_consent 
            SET withdrawn = true, withdrawn_at = $1, withdraw_reason = $2
            WHERE user_id = $3 AND withdrawn = false
        """, now, reason, user_id)
        
        # Trigger data deletion (soft delete + scheduled hard delete)
        await self.schedule_data_deletion(user_id)
        
        return {
            "user_id": user_id,
            "withdrawn_at": now.isoformat(),
            "deletion_scheduled": True,
            "deletion_within_days": 30  # GDPR requirement: 30 days
        }
    
    async def check_data_usage_permission(self, user_id: str, 
                                         purpose: str) -> bool:
        """Check apakah user mengizinkan data usage untuk purpose tertentu"""
        consent = await self.get_consent(user_id)
        
        if consent["withdrawn"]:
            return False
        if consent["expires_at"] and consent["expires_at"] < datetime.utcnow():
            return False
        if purpose not in consent.get("purposes", []):
            return False
            
        return True
    
    async def get_transparency_report(self, user_id: str) -> Dict:
        """
        Generate transparency report untuk user.
        User bisa lihat:
        - What data we have
        - How it's used
        - Who has access
        - When it will be deleted
        """
        # Fetch all data related to this user
        scraped_data = await self.db.fetch("""
            SELECT platform, data_type, collected_at, anonymization_level, usage_purpose
            FROM collected_data 
            WHERE collected_by_user = $1
            ORDER BY collected_at DESC
        """, user_id)
        
        consent_history = await self.db.fetch("""
            SELECT level, granted_at, expires_at, withdrawn, purposes
            FROM user_consent
            WHERE user_id = $1
            ORDER BY granted_at DESC
        """, user_id)
        
        return {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "total_data_points": len(scraped_data),
            "consent_status": consent_history[0] if consent_history else None,
            "consent_history": [dict(c) for c in consent_history],
            "data_breakdown": {
                "by_platform": self._group_by(scraped_data, "platform"),
                "by_type": self._group_by(scraped_data, "data_type"),
                "by_month": self._group_by_month(scraped_data)
            },
            "retention_policy": {
                "data_retention_days": 365,
                "anonymized_data_retention_days": 1825,  # 5 years
                "deletion_scheduled": None
            }
        }
    
    async def schedule_data_deletion(self, user_id: str):
        """Schedule user data untuk deletion dalam 30 hari"""
        deletion_date = datetime.utcnow() + timedelta(days=30)
        await self.db.execute("""
            INSERT INTO scheduled_deletions (user_id, scheduled_at, status)
            VALUES ($1, $2, 'pending')
        """, user_id, deletion_date)
```

#### 6.3 Transparency Dashboard (UI)

```javascript
// transparency-dashboard.tsx — Next.js component
// Tampilkan di SIDIX dashboard (port 3000)

interface TransparencyReport {
  user_id: string;
  total_data_points: number;
  consent_status: ConsentStatus;
  data_breakdown: {
    by_platform: Record<string, number>;
    by_type: Record<string, number>;
  };
  retention_policy: RetentionPolicy;
}

export function TransparencyDashboard() {
  const [report, setReport] = useState<TransparencyReport | null>(null);
  
  return (
    <div className="transparency-dashboard">
      <h2>Your Data Transparency Report</h2>
      
      {/* Consent Control */}
      <ConsentControlPanel 
        currentLevel={report?.consent_status.level}
        onChange={handleConsentChange}
        onWithdraw={handleWithdrawConsent}
      />
      
      {/* Data Summary */}
      <DataSummaryCard 
        totalPoints={report?.total_data_points}
        platforms={report?.data_breakdown.by_platform}
      />
      
      {/* Data Usage Log */}
      <DataUsageLog userId={userId} />
      
      {/* Export & Deletion */}
      <div className="actions">
        <button onClick={exportMyData}>Export My Data (JSON)</button>
        <button onClick={requestDeletion} className="danger">
          Request Data Deletion
        </button>
      </div>
      
      {/* OpHarvest Badge */}
      <OpHarvestBadge level={report?.consent_status.level} />
    </div>
  );
}
```

---

## 7. GROWTH STRATEGY: 10 → 50 → 500 BETA USERS

### Context: Indonesia Creator Economy Market

**Market Size:** USD 38.5 billion (2025) → USD 112.7 billion (2031), CAGR 19.7%
**UMKM Social Media Adoption:** 70% menggunakan Instagram/TikTok
**Pain Point:** Tool existing (Sprout, Brandwatch) terlalu mahal dan enterprise-focused

#### 7.1 Three-Phase Growth Plan

### PHASE 1: First 10 Users (Week 1-2) — "Founding Circle"

**Target:** UMKM owners, content creators, digital marketers yang sudah kenal SIDIX

**Channels:**
| Channel | Tactic | Expected Result |
|---------|--------|-----------------|
| Komunitas SIDIX existing | Personal invitation ke 20 orang | 5-10 signups |
| LinkedIn direct | DM ke 50 UMKM owners/creators | 2-3 signups |
| WhatsApp grup | Share ke 5 komunitas UMKM | 1-2 signups |

**Messaging:**
> "SIDIX Social Radar — pantau kompetitor Instagrammu dengan AI. Self-hosted, privasi terjaga, tidak perlu kartu kredit. Join Founding Circle dan bentuk fitur ini bersama kami."

**Onboarding:**
- Personal onboarding call (30 menit)
- Setup Chrome extension bersama
- Weekly check-in via WhatsApp
- Langsung implement feedback mereka

**Incentive:**
- Lifetime free Pro tier untuk Founding Circle
- Nama mereka di "Pioneer Wall" di website
- Direct access ke founder (Fahmi) untuk feedback

### PHASE 2: 10 → 50 Users (Week 3-6) — "Niche Domination"

**Target:** UMKM Indonesia di niche spesifik (F&B, Fashion, Edukasi)

**Channels:**
| Channel | Tactic | Expected Result |
|---------|--------|-----------------|
| Instagram | Case study reel dari Founding Circle | 10-15 leads |
| TikTok | Tutorial "Cara spy kompetitor gratis" | 10-15 leads |
| Forum UMKM | Post di Kaskus, Facebook Groups | 5-10 leads |
| Micro-influencer | Gift Pro tier ke 10 niche creators | 5-10 signups |

**Content Strategy:**
- Weekly "Competitor Analysis Case Study" (Instagram reel)
- "3 Hal yang Saya Pelajari dari Memantau 10 Kompetitor" (blog post)
- Template gratis: "Competitor Analysis Worksheet"

**Product-Led Growth Loop:**
```
1. User install Chrome extension
2. Analyze 1 competitor → generate AI report
3. Report menunjukkan insight valuable
4. User screenshot report → share ke sosial media
5. Friends ask "Ini dari aplikasi apa?"
6. Referral signup
```

**Referral Program:**
- Refer 1 friend → 1 extra competitor slot (Free tier)
- Refer 3 friends → 1 month Pro tier
- Refer 10 friends → Lifetime Pro tier

### PHASE 3: 50 → 500 Users (Month 3-6) — "Scale"

**Target:** Broader UMKM market, agency digital marketing, komunitas creator

**Channels:**
| Channel | Tactic | Expected Result |
|---------|--------|-----------------|
| Product Hunt | Launch dengan "Indonesia-first" angle | 50-100 signups |
| SEO | Target keywords: "cara analisis kompetitor instagram gratis" | 50-100 signups |
| Podcast | Guest di podcast UMKM Indonesia | 20-30 signups |
| Webinar | Free webinar "AI untuk UMKM" | 30-50 signups |
| Chrome Web Store | Optimized listing | 50-100 signups |

**Partnership Opportunities:**
- **Komunitas UMKM:** Kolaborasi dengan UMKM Go Digital, Rumah UMKM
- **Agency Digital:** White-label option untuk agency
- **Kampus:** Program internship untuk mahasiswa marketing

#### 7.2 Pricing Strategy Detail

| Tier | Free | Pro ($9/mo) | Enterprise ($99/mo) |
|------|------|-------------|---------------------|
| Competitors | 1 | 10 | Unlimited |
| Platforms | Instagram | IG + TikTok + Twitter | All + API |
| Refresh | 24 hours | 6 hours | Real-time |
| Reports | Basic (text) | PDF + Excel | White-label |
| AI Analysis | Summary only | Full + Recommendations | Custom prompts |
| Export | JSON | PDF, CSV, Excel | API access |
| Support | Community | Email | WhatsApp + Call |

**Indonesia-specific pricing:**
- Accept payment via Midtrans (transfer bank, e-wallet, QRIS)
- "Cicilan" option via PayLater
- Free tier yang genuinely useful (bukan teaser yang useless)

#### 7.3 Success Metrics (North Star)

| Metric | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|---------------|---------------|---------------|
| Weekly Active Users | 8/10 (80%) | 35/50 (70%) | 300/500 (60%) |
| Competitors Analyzed/User | 3 | 5 | 8 |
| Reports Generated/Week | 10 | 100 | 1000 |
| Chrome Extension Install | 10 | 50 | 500 |
| NPS Score | 50+ | 40+ | 35+ |
| Revenue | $0 | $200/mo | $2000/mo |

---

## 8. INTEGRASI DENGAN SIDIX BRAIN EXISTING

### The Flywheel: Social Radar → Training Data → Smarter SIDIX

```
┌─────────────────────────────────────────────────────────────┐
│                    SIDIX FLYWHEEL                           │
│                                                             │
│   Social Radar        Training Pairs       LoRA Retrain    │
│   ┌─────────┐        ┌─────────────┐      ┌──────────┐    │
│   │ Scrape  │───────►│ Generate    │─────►│ Quarterly│    │
│   │ Data    │        │ Instruction │      │ Retrain  │    │
│   └─────────┘        │ Pairs       │      └────┬─────┘    │
│        ▲             └─────────────┘           │          │
│        │                      │                │          │
│        │              ┌───────┘                │          │
│        │              ▼                        ▼          │
│   ┌────┴─────┐   ┌─────────────┐      ┌──────────┐      │
│   │ AI Report│   │ Quality     │      │ Smarter  │      │
│   │ (Qwen)   │   │ Filter      │      │ SIDIX    │      │
│   └──────────┘   └─────────────┘      └────┬─────┘      │
│                                             │             │
│                                             ▼             │
│                                       ┌──────────┐       │
│                                       │ Better   │       │
│                                       │ Reports  │───────┘
│                                       └──────────┘
└─────────────────────────────────────────────────────────────┘
```

#### 8.1 Training Pair Generation Pipeline

Setiap Social Radar report yang di-generate adalah **kandidat training pair**. Pipeline konversi:

```python
# social_radar/training/pair_generator.py
from typing import Dict, List, Optional
import json

class TrainingPairGenerator:
    """
    Convert Social Radar reports menjadi training pairs untuk Qwen2.5-7B LoRA retraining.
    
    Format: ShareGPT / Alpaca instruction tuning
    Quality: Filtered via CQF (Content Quality Framework) rubrik
    """
    
    # Quality rubrik — minimum score untuk diterima
    QUALITY_THRESHOLD = 7.0  # dari 10
    
    async def generate_training_pair(self, report: Dict) -> Optional[Dict]:
        """
        Konversi single report menjadi instruction tuning pair.
        Return None jika kualitas tidak memenuhi threshold.
        """
        
        # Extract instruction (input)
        instruction = self._create_instruction(report)
        
        # Extract response (output dari AI yang sudah ada)
        response = report["ai_analysis"]["full_response"]
        
        # Hitung quality score
        quality_score = await self._score_quality(report, instruction, response)
        
        if quality_score < self.QUALITY_THRESHOLD:
            return None  # Skip low-quality pairs
        
        # Format dalam ShareGPT format (untuk conversational tasks)
        sharegpt_pair = {
            "conversations": [
                {
                    "from": "human",
                    "value": instruction
                },
                {
                    "from": "gpt",
                    "value": response
                }
            ],
            "metadata": {
                "source": "social_radar",
                "platform": report["platform"],
                "competitor_count": len(report["competitors_analyzed"]),
                "quality_score": quality_score,
                "generated_at": report["generated_at"],
                "anonymized": True,
                "task_type": "competitor_analysis"
            }
        }
        
        # Format dalam Alpaca format (untuk instruction following)
        alpaca_pair = {
            "instruction": self._extract_core_instruction(report),
            "input": self._extract_context(report),
            "output": response,
            "metadata": sharegpt_pair["metadata"]
        }
        
        return {
            "sharegpt": sharegpt_pair,
            "alpaca": alpaca_pair,
            "quality_score": quality_score
        }
    
    def _create_instruction(self, report: Dict) -> str:
        """Buat natural language instruction dari report data"""
        competitors = ", ".join([c["username"] for c in report["competitors_analyzed"]])
        niche = report.get("niche", "general")
        
        templates = [
            f"Analyze these Instagram competitors in the {niche} niche: {competitors}. Provide strategic insights and actionable recommendations.",
            f"I'm running a {niche} business on Instagram. My competitors are {competitors}. What can I learn from their content strategy and engagement patterns?",
            f"Compare my Instagram performance with these competitors: {competitors}. Identify my strengths, weaknesses, and opportunities in the {niche} market.",
            f"These {niche} accounts on Instagram are my main competitors: {competitors}. Analyze their recent content and suggest how I can differentiate my brand.",
        ]
        
        # Rotate templates untuk variasi
        import random
        return random.choice(templates)
    
    async def _score_quality(self, report: Dict, instruction: str, response: str) -> float:
        """
        Score kualitas training pair menggunakan CQF rubrik.
        
        Criteria:
        1. Data richness (0-2): Apakah input data cukup rich?
        2. Response specificity (0-2): Apakah response spesifik atau generic?
        3. Actionability (0-2): Apakah ada actionable recommendations?
        4. Accuracy (0-2): Apakah facts/numbers correct?
        5. Uniqueness (0-2): Apakah insight unique atau cliché?
        """
        scores = {
            "data_richness": min(2.0, len(report.get("competitors_analyzed", [])) * 0.5),
            "response_specificity": self._score_specificity(response),
            "actionability": self._score_actionability(response),
            "accuracy": 1.5,  # Default — bisa ditingkatkan dengan fact-checking
            "uniqueness": self._score_uniqueness(response)
        }
        
        return sum(scores.values())
    
    def _score_specificity(self, response: str) -> float:
        """Score seberapa spesifik response (bukan generic advice)"""
        generic_phrases = [
            "engaging content", "high quality", "be consistent",
            "know your audience", "use hashtags", "post regularly"
        ]
        generic_count = sum(1 for phrase in generic_phrases if phrase in response.lower())
        return max(0, 2.0 - generic_count * 0.3)
    
    def _score_actionability(self, response: str) -> float:
        """Score seberapa actionable recommendations"""
        action_indicators = [
            "try", "implement", "create", "use", "schedule",
            "post at", "focus on", "experiment", "test"
        ]
        action_count = sum(1 for indicator in action_indicators if indicator in response.lower())
        return min(2.0, action_count * 0.3)
    
    def _score_uniqueness(self, response: str) -> float:
        """Score uniqueness — compare dengan training set existing"""
        # Placeholder — implement dengan deduplication menggunakan MinHash
        return 1.5
    
    async def batch_generate_pairs(self, reports: List[Dict], 
                                   min_quality: float = 7.0) -> List[Dict]:
        """Generate training pairs dari batch reports, filter by quality"""
        pairs = []
        for report in reports:
            pair = await self.generate_training_pair(report)
            if pair and pair["quality_score"] >= min_quality:
                pairs.append(pair)
        return pairs
```

#### 8.2 Integration dengan Existing SIDIX Systems

| SIDIX System | Integration Point | How |
|-------------|-------------------|-----|
| **Maqashid Profiles** | Pre-filter output analysis | Setiap AI report melalui Maqashid filter sebelum ditampilkan ke user |
| **Naskh Handler** | Handle conflicting insights | Jika AI report bertentangan dengan data lama, trigger Naskh resolution |
| **Raudah Protocol** | Multi-agent report generation | AYMAN (creative), ABOO (analytical), OOMAR (practical) collaborate |
| **Memory (Growth Loop)** | Store & retrieve patterns | Patterns dari Social Radar masuk ke corpus untuk retrieval |
| **35 Tools** | Extend dengan social tools | Social Radar menjadi tool #36, callable dari agent |
| **Persona System** | Route analysis requests | User selects persona → different analysis angle |

#### 8.3 Quarterly LoRA Retraining Pipeline

```python
# training/quarterly_retrain.py
async def quarterly_retrain_pipeline():
    """
    Pipeline retraining LoRA adapter setiap quarter.
    Trigger: otomatis setiap 3 bulan atau ketika training pairs > 5000.
    """
    
    # 1. Collect training pairs dari Social Radar
    pairs = await db.fetch("""
        SELECT * FROM training_pairs 
        WHERE source = 'social_radar'
        AND quality_score >= 7.0
        AND used_for_training = false
        ORDER BY quality_score DESC
        LIMIT 10000
    """)
    
    if len(pairs) < 1000:
        logger.info("Insufficient training pairs for retrain (< 1000)")
        return
    
    # 2. Prepare dataset
    dataset = prepare_lora_dataset(pairs, format="alpaca")
    
    # 3. Validate dengan existing test set
    validation_result = await validate_new_dataset(dataset)
    if validation_result.accuracy_drop > 0.05:  # Max 5% regression
        logger.warning("Dataset causes accuracy drop, aborting retrain")
        return
    
    # 4. Train new LoRA adapter
    new_adapter_path = await train_lora_adapter(
        base_model="Qwen/Qwen2.5-7B-Instruct",
        dataset=dataset,
        output_dir=f"./adapters/social_radar_v{quarter}_{year}",
        epochs=3,
        lora_r=8,
        lora_alpha=16
    )
    
    # 5. A/B test new adapter
    test_result = await ab_test_adapter(new_adapter_path)
    
    # 6. Deploy if improved
    if test_result.win_rate > 0.55:  # 55% win rate vs current
        await deploy_new_adapter(new_adapter_path)
        await mark_pairs_as_used(pairs)
        logger.info(f"New adapter deployed: {new_adapter_path}")
    else:
        logger.info("New adapter doesn't improve, keeping current")
```

#### 8.4 Data Schema Integration

```sql
-- Migration: Add Social Radar tables ke existing SIDIX database

-- Core tables
CREATE TABLE sr_competitors (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    platform VARCHAR(50) NOT NULL,  -- instagram, tiktok, twitter
    username_hash VARCHAR(64) NOT NULL,  -- anonymized
    username_encrypted TEXT,  -- encrypted actual username (for display)
    added_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    monitoring_frequency VARCHAR(20) DEFAULT 'daily',  -- hourly, daily, weekly
    last_scraped_at TIMESTAMP,
    UNIQUE(user_id, platform, username_hash)
);

CREATE TABLE sr_scraped_data (
    id SERIAL PRIMARY KEY,
    competitor_id INT REFERENCES sr_competitors(id),
    data_type VARCHAR(50) NOT NULL,  -- profile, post, story, reel
    raw_data JSONB,  -- original scraped data (encrypted)
    anonymized_data JSONB NOT NULL,  -- privacy-safe version
    collected_at TIMESTAMP DEFAULT NOW(),
    collection_method VARCHAR(50),  -- chrome_extension, api_direct
    quality_score FLOAT  -- untuk training pair selection
);

CREATE TABLE sr_reports (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) REFERENCES users(id),
    report_type VARCHAR(50) NOT NULL,  -- competitor_analysis, trend_detection, etc
    prompt_used TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    structured_output JSONB,
    quality_score FLOAT,
    maqashid_filter_applied BOOLEAN DEFAULT false,
    generated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE training_pairs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- social_radar, manual, synthetic
    source_report_id INT REFERENCES sr_reports(id),
    instruction TEXT NOT NULL,
    response TEXT NOT NULL,
    format VARCHAR(20) NOT NULL,  -- sharegpt, alpaca
    quality_score FLOAT NOT NULL,
    used_for_training BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consent & privacy tables
CREATE TABLE user_consent (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    level VARCHAR(20) NOT NULL,  -- none, basic, full, research
    purposes TEXT[],
    granted_at TIMESTAMP,
    expires_at TIMESTAMP,
    withdrawn BOOLEAN DEFAULT false,
    withdrawn_at TIMESTAMP,
    withdraw_reason TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE TABLE scheduled_deletions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'  -- pending, completed, failed
);
```

---

## APPENDIX A: Implementation Priority (MVP 3-4 hari)

### Day 1: Foundation
- [ ] Setup Chrome Extension skeleton (MV3, popup, content script)
- [ ] Implement page-interceptor.js untuk Instagram
- [ ] Setup backend endpoint `/api/social-radar/ingest`
- [ ] Basic data storage (PostgreSQL schema)

### Day 2: Scraping Engine
- [ ] Implement curl_cffi Instagram scraper (profile + posts)
- [ ] Redis queue setup
- [ ] Async worker untuk process scraped data
- [ ] Chrome Extension → Backend data pipeline

### Day 3: AI Analysis
- [ ] Prompt templates (competitor analysis, trend detection)
- [ ] Integration dengan Qwen2.5-7B (existing SIDIX inference)
- [ ] Report generation endpoint
- [ ] Basic dashboard UI (Next.js)

### Day 4: Polish & Privacy
- [ ] OpHarvest anonymization pipeline
- [ ] Consent management UI
- [ ] Transparency dashboard
- [ ] Chrome Web Store submission prep

---

## APPENDIX B: Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Instagram blocks scraper | High | High | Network interception pattern lebih stealthy; rotating proxies; user-supplied proxies |
| Chrome Extension rejected | Medium | High | Patuhi CWS policies; no deceptive practices; clear privacy policy |
| Qwen2.5-7B slow untuk analysis | Medium | Medium | Async processing; caching; summary-first approach |
| User tidak mau install extension | Medium | Medium | API-only fallback; value demonstration sebelum install |
| Competitor data tidak valuable | Low | High | Quality scoring; user feedback loop; iterate prompts |
| Privacy concerns | Medium | High | OpHarvest transparency; default OFF; easy data deletion |

---

## APPENDIX C: Open Questions untuk Clarification

1. **Proxy Strategy:** Apakah SIDIX akan provide proxy gratis untuk user, atau user harus supply sendiri? (Impact: pricing & UX)
2. **Chrome Extension Distribution:** Via Chrome Web Store publik, atau sideload untuk beta?
3. **Training Data Ownership:** Siapa yang own training pairs yang di-generate? (User, SIDIX, or shared?)
4. **Maqashid Integration Scope:** Sejauh mana Maqashid filter diterapkan untuk Social Radar? (Pre-filter, post-filter, atau both?)
5. **Monetization Timeline:** Kapan mulai charge? Setelah 500 users, atau dari MVP?

---

*Dokumen ini adalah living document. Update setiap sprint based on learnings dari implementation.*
