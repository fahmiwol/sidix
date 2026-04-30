# SIDIX SOCIAL RADAR: Strategic Pivot Document
## AI-Native Analytics Dashboard + MCP Plugin Ecosystem

**Tanggal:** 23 April 2026
**Versi:** v2.0 — Vision Pivot
**Status:** Foundation untuk Product Vision dan Technical Architecture

---

# EXECUTIVE SUMMARY

Fahmi's vision telah berkembang: Social Radar bukan sekadar **competitor monitoring tool** — ini adalah **AI-native social analytics dashboard** yang:

1. **Dashboard "Semrawut"** — Dense, data-rich, multi-platform analytics (FB, IG, TikTok, YouTube, LinkedIn) dengan performance profile + competitor comparison
2. **MCP Plugin Ecosystem** — Menjadi tool standar yang bisa dikonsumsi AI agents lain (Claude, ChatGPT, Cursor, Windsurf, VS Code Copilot)
3. **Chrome Extension sebagai Collection Layer** — Universal data ingestion dari browser user
4. **Self-hosted by design** — Tidak ada vendor API lock-in, data tetap di kontrol user

**Konsep inti:** User browsing social media → Chrome Extension intercept data → SIDIX backend analyze dengan Qwen2.5-7B → Dashboard menampilkan analytics semrawut → AI agents bisa query via MCP

---

# PART 1: VISION — "SEMRAWUT" DASHBOARD

## 1.1 Apa itu "Semrawut"?

Bukan chaos tanpa arah — tapi **information density maksimal** seperti cockpit pesawat. Setiap piksel punya fungsi. Tidak ada white space yang tidak berguna. User yang mengerti analytics akan merasa "seperti di rumah."

### Referensi Visual:
- **Bloomberg Terminal** — dense financial data, every pixel counts
- **Hootsuite Streams** — multi-column social monitoring
- **Sprout Social Analytics** — clean tapi bisa lebih dense
- **Google Analytics 4** — customizable dashboards
- **TradingView** — charts + metrics + news dalam satu layar

### Dashboard Philosophy untuk SIDIX:

```
┌──────────────────────────────────────────────────────────────────────┐
│  SIDIX SOCIAL RADAR — DASHBOARD v1.0                                 │
│  Niche: [Fashion UMKM Indonesia ▼]  Period: [Last 30 Days ▼]        │
├──────────────────┬──────────────────┬──────────────────┬─────────────┤
│ MY ACCOUNTS      │ COMPETITOR A     │ COMPETITOR B     │  COMPETITOR │
│ @fahmistore      │ @rivalstore      │ @trendystore     │  C @bigbrand│
│ ───────────────  │ ───────────────  │ ───────────────  │  ────────── │
│ IG: 12.5K ▲8%   │ IG: 45K ▲12%    │ IG: 8.2K ▲3%    │  IG: 120K ▼2%│
│ TT: 5.1K ▲15%   │ TT: 22K ▲28%    │ TT: 15K ▲9%     │  TT: 80K ▲5% │
│ FB: 3.2K ▲2%    │ FB: 18K ▲5%     │ FB: 6K ▲7%      │  FB: 200K ▲1%│
│ YT: 850 ▲45%    │ YT: 12K ▲8%     │ YT: 3K ▲22%     │  YT: 50K ▲3% │
│ LI: 420 ▲12%    │ LI: 8K ▲15%     │ LI: 1.2K ▲30%   │  LI: 25K ▲8% │
├──────────────────┼──────────────────┼──────────────────┼─────────────┤
│ ENGAGEMENT RATE  │ ENGAGEMENT RATE  │ ENGAGEMENT RATE  │ ENGAGEMENT  │
│ ┌────────────┐  │ ┌────────────┐  │ ┌────────────┐  │  ┌────────┐ │
│ │▓▓▓▓░░░░░░│  │ │▓▓▓▓▓▓▓░░░│  │ │▓▓▓▓▓░░░░░│  │  │▓▓▓░░░░░│ │
│ │  4.2%      │  │ │  7.8%      │  │ │  6.1%      │  │  │  3.5%   │ │
│ │  ▼ -0.3pp  │  │ │  ▲ +1.2pp  │  │ │  ▲ +0.5pp  │  │  │ ▲ +0.1  │ │
│ └────────────┘  │ └────────────┘  │ └────────────┘  │  └────────┘ │
├──────────────────┼──────────────────┼──────────────────┼─────────────┤
│ TOP CONTENT      │ TOP CONTENT      │ TOP CONTENT      │ TOP CONTENT │
│ [Reel ▶] 45K    │ [Carousel] 89K  │ [Video ▶] 32K   │ [Reel ▶]156K│
│ "Cara style..."  │ "10 Tips..."    │ "Behind the..." │ "Trend..."  │
│ [Carousel] 38K   │ [Reel ▶] 67K    │ [Carousel] 28K  │ [Carousel]98K│
│ [Video ▶] 32K    │ [Video ▶] 45K   │ [Reel ▶] 22K    │ [Video ▶]67K│
├──────────────────┼──────────────────┼──────────────────┼─────────────┤
│ POSTING SCHEDULE │ POSTING SCHEDULE │ POSTING SCHEDULE │ POSTING SCH │
│ Mon ████░░░░░░  │ Mon ██████░░░░  │ Mon ████████░░  │ Mon ██████░░│
│ Tue ██████░░░░  │ Tue ████████░░  │ Tue ██████░░░░  │ Tue ████████│
│ Wed ███░░░░░░░  │ Wed ██████░░░░  │ Wed ██████████  │ Wed ██████░░│
│ Thu ██████░░░░  │ Thu ██████████  │ Thu ██████░░░░  │ Thu ████████│
│ Fri ████░░░░░░  │ Fri ████████░░  │ Fri ██████████  │ Fri ████████│
│ Sat ████████░░  │ Sat ████░░░░░░  │ Sat ██████░░░░  │ Sat ████░░░░│
│ Sun ██████░░░░  │ Sun ████░░░░░░  │ Sun ████████░░  │ Sun ██████░░│
├──────────────────┴──────────────────┴──────────────────┴─────────────┤
│ TREND DETECTION (AI-Powered)                                         │
│ ┌─────────────────────────────────────────────────────────────────┐  │
│ │ 🔥 Rising: "Sustainable Fashion" +45% mentions (vs last month)  │  │
│ │ 📈 Trending: "Thrifting" +32% engagement in your niche           │  │
│ │ 🆕 New Format: Carousel "Before/After" getting 2x more saves    │  │
│ │ ⚠️ Declining: "OOTD flatlay" engagement dropping -18%           │  │
│ │ 💡 Opportunity: No competitor covering "Modest Fashion" niche    │  │
│ └─────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│ AI INSIGHT (Qwen2.5-7B via ABOO persona) — Updated 2 hours ago      │
│ ┌─────────────────────────────────────────────────────────────────┐  │
│ │ Competitor A doubled Reel frequency (3→6/week) driving +28% TT  │  │
│ │ growth. Their "Tutorial" format gets 3x avg engagement. You     │  │
│ │ posted 0 tutorials this month. Opportunity: Create "Styling     │  │
│ │ Guide" series (1/week, Tue/Thu 7PM). Expected impact: +15-25%   │  │
│ │ engagement within 4 weeks. Difficulty: Medium.                  │  │
│ └─────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### Design Principles "Semrawut":

| Principle | Implementation |
|-----------|---------------|
| **No wasted pixels** | Minimal padding, compact spacing, data-first |
| **Color-coded status** | Green = good, Yellow = watch, Red = alert — instant recognition |
| **At-a-glance comparison** | Side-by-side columns, metrics aligned untuk easy scan |
| **Progressive detail** | Summary first, click untuk drill-down detail |
| **AI insight always visible** | Bottom panel dengan latest AI analysis |
| **Trend-aware** | Trending topics, rising formats, declining patterns |

---

## 1.2 Dashboard Components Detail

### Component 1: Multi-Platform Account Cards
Setiap competitor (termasuk user's account) punya card yang menampilkan:
- **Platform icons** dengan follower count dan growth %
- **Mini sparkline** untuk growth trend (7 days)
- **Engagement rate gauge** — visual meter dengan benchmark comparison
- **Health indicator** — green/yellow/red dot

### Component 2: Engagement Heatmap
- **Calendar heatmap** seperti GitHub contributions
- Warna menunjukkan engagement intensity
- Hover untuk detail post dan metrics

### Component 3: Content Performance Grid
- **Top 3 posts per competitor** dengan thumbnail + metrics
- Sortable by: engagement, reach, saves, shares
- Filter by: format (Reel, Carousel, Video, Image)

### Component 4: Posting Frequency Comparison
- **Bar chart per day** — visual comparison posting schedule
- Optimal posting time overlay (AI-calculated)

### Component 5: Trend Radar (AI-Generated)
- **Emerging trends** di niche
- **Format popularity shifts**
- **Hashtag trend analysis**
- **Opportunity gaps** (niche yang tidak ditutup kompetitor)

### Component 6: AI Insight Panel
- **Natural language analysis** dari Qwen2.5-7B
- **Actionable recommendations** dengan difficulty score
- **Priority-ranked** (P0, P1, P2)
- **Confidence score** untuk setiap recommendation

---

# PART 2: MCP PLUGIN ARCHITECTURE

## 2.1 Mengapa MCP? (Model Context Protocol)

MCP adalah **open standard** yang mendefinisikan bagaimana AI models connect ke external tools. Diadopsi oleh:

| Platform | Adoption Status | Date |
|----------|----------------|------|
| **Anthropic Claude** | Native support | Nov 2024 (creator) |
| **OpenAI ChatGPT** | Official adoption | Mar 2025 |
| **Google Gemini** | Full support | Dec 2024 |
| **Microsoft VS Code** | Integrated | 2025 |
| **Cursor** | Native | 2025 |
| **Windsurf** | Native | 2025 |

**Keuntungan untuk SIDIX:**
- **Build once, use everywhere** — 1 MCP server = consumable oleh semua AI platforms
- **No custom integration** — tidak perlu bikin connector per platform
- **Tool discovery otomatis** — AI agent auto-detect tools yang tersedia
- **Standardized** — JSON-RPC 2.0, vendor-neutral (Linux Foundation)

---

## 2.2 SIDIX Social Radar sebagai MCP Server

```
┌──────────────────────────────────────────────────────────────────┐
│                    MCP CLIENTS (AI Agents)                       │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐          │
│  │ Claude  │  │ ChatGPT  │  │ Cursor │  │ Windsurf │          │
│  │ Desktop │  │ Desktop  │  │  IDE   │  │   IDE    │          │
│  └────┬────┘  └────┬─────┘  └───┬────┘  └────┬─────┘          │
│       │            │            │            │                  │
│       └────────────┴─────┬──────┴────────────┘                  │
│                          │                                       │
│                    MCP PROTOCOL                                   │
│              (JSON-RPC 2.0 over stdio/HTTP)                      │
│                          │                                       │
│       ┌──────────────────┴──────────────────┐                   │
│       ▼                                   ▼                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           SIDIX SOCIAL RADAR MCP SERVER                  │   │
│  │                                                          │   │
│  │  Tools:                                                  │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ analyze_competitor()                                │ │   │
│  │  │ detect_trends()                                     │ │   │
│  │  │ compare_accounts()                                  │ │   │
│  │  │ generate_report()                                   │ │   │
│  │  │ get_best_performing_content()                       │ │   │
│  │  │ schedule_analysis()                                 │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                          │   │
│  │  Resources:                                              │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ social://{niche}/trends                             │ │   │
│  │  │ social://{niche}/top_hashtags                       │ │   │
│  │  │ social://{username}/profile                         │ │   │
│  │  │ social://{username}/recent_posts                    │ │   │
│  │  │ social://{niche}/benchmarks                         │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                          │   │
│  │  Prompts:                                                │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ competitive_audit_template                          │ │   │
│  │  │ content_strategy_analysis                           │ │   │
│  │  │ trend_opportunity_report                            │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           SIDIX BRAIN (port 8765)                        │   │
│  │  - Qwen2.5-7B-Instruct + LoRA adapter                   │   │
│  │  - Maqashid Profile Filter                              │   │
│  │  - Naskh Handler                                        │   │
│  │  - Raudah Protocol (multi-agent)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         CHROME EXTENSION (Data Collection)               │   │
│  │  - Network Interception on Instagram/TikTok/FB/etc      │   │
│  │  - No extra API calls — ethical by design               │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2.3 MCP Tool Definitions untuk Social Radar

```python
# social_radar/mcp/server.py
from mcp.server.fastmcp import FastMCP
from social_radar.analyzer import CompetitorAnalyzer
from social_radar.trends import TrendDetector

mcp = FastMCP("sidix-social-radar")

@mcp.tool()
async def analyze_competitor(
    username: str,
    platform: str = "instagram",
    analysis_depth: str = "standard"
) -> str:
    """
    Analyze a competitor's social media profile and recent performance.
    
    Returns strategic insights including:
    - Content strategy analysis (posting frequency, themes, formats)
    - Engagement metrics and trends
    - Growth patterns and tactics
    - Content gap analysis vs your account
    - Actionable recommendations
    
    Args:
        username: Social media handle (e.g., 'nike', 'zara')
        platform: Platform name — one of 'instagram', 'tiktok', 
                  'facebook', 'youtube', 'linkedin', 'twitter'
        analysis_depth: 'quick' (summary only), 'standard' (full analysis),
                       'deep' (with trend prediction and strategic planning)
    
    Returns:
        Structured analysis report with recommendations
    """
    analyzer = CompetitorAnalyzer()
    result = await analyzer.analyze(username, platform, analysis_depth)
    return result.to_markdown()

@mcp.tool()
async def compare_accounts(
    usernames: list[str],
    platform: str = "instagram",
    metrics: list[str] = None
) -> str:
    """
    Compare multiple social media accounts side-by-side.
    
    Perfect for competitive benchmarking — see how your account
    stacks up against competitors across key metrics.
    
    Args:
        usernames: List of social media handles to compare
        platform: Platform to analyze on
        metrics: Specific metrics to compare (engagement_rate, 
                follower_growth, post_frequency, best_content_format)
    
    Returns:
        Side-by-side comparison table with ranked insights
    """
    pass

@mcp.tool()
async def detect_trends(
    niche: str,
    platforms: list[str] = None,
    timeframe_days: int = 30
) -> str:
    """
    Detect emerging trends in a specific niche across social platforms.
    
    Identifies:
    - Rising content formats and themes
    - Trending hashtags and keywords
    - Engagement pattern shifts
    - Early opportunity signals
    
    Args:
        niche: Industry/niche to analyze (e.g., 'fashion', 'food', 
               'technology', 'fitness')
        platforms: Platforms to monitor (defaults to all)
        timeframe_days: Analysis window in days
    
    Returns:
        Trend report with opportunity scores and timeline predictions
    """
    pass

@mcp.tool()
async def generate_report(
    report_type: str,
    competitors: list[str],
    platform: str = "instagram",
    output_format: str = "markdown"
) -> str:
    """
    Generate a comprehensive competitive intelligence report.
    
    Report types:
    - 'weekly_digest': Quick summary of competitor activity
    - 'content_audit': Deep dive into content strategy
    - 'growth_analysis': Follower growth and tactics analysis
    - 'opportunity_map': Content gaps and opportunities
    - 'full_report': Everything combined
    
    Args:
        report_type: Type of report to generate
        competitors: List of competitor usernames
        platform: Primary platform for analysis
        output_format: 'markdown', 'json', or 'html'
    
    Returns:
        Complete formatted report
    """
    pass

@mcp.tool()
async def get_best_performing_content(
    username: str,
    platform: str = "instagram",
    count: int = 5,
    metric: str = "engagement_rate"
) -> str:
    """
    Get the top performing content from a specific account.
    
    Useful for content inspiration — see what works for 
    successful accounts in your niche.
    
    Args:
        username: Account to analyze
        platform: Platform name
        count: Number of top posts to return
        metric: Sort metric ('engagement_rate', 'reach', 'saves', 'shares')
    
    Returns:
        List of top posts with performance breakdown
    """
    pass

@mcp.tool()
def list_supported_platforms() -> str:
    """List all social media platforms supported by Social Radar."""
    return """
    Supported platforms:
    - instagram (public profiles, posts, reels, stories)
    - tiktok (public profiles, videos)
    - facebook (public pages, posts)
    - youtube (channels, videos)
    - linkedin (public profiles, company pages)
    - twitter/X (public profiles, tweets)
    """

# Resources — static/semi-static data AI bisa akses
@mcp.resource("social://{niche}/trends")
async def get_niche_trends(niche: str) -> str:
    """Get current trends for a specific niche."""
    trends = await TrendDetector().get_current_trends(niche)
    return trends.to_json()

@mcp.resource("social://{niche}/benchmarks")
async def get_niche_benchmarks(niche: str) -> str:
    """Get engagement rate benchmarks for a niche."""
    return json.dumps({
        "niche": niche,
        "avg_engagement_rate": 0.045,
        "top_quartile": 0.089,
        "median": 0.038,
        "bottom_quartile": 0.015
    })

# Prompts — reusable analysis templates
@mcp.prompt()
def competitive_audit_template(competitors: list[str]) -> str:
    """Generate a comprehensive competitive audit."""
    return f"""
    Perform a full competitive audit of: {', '.join(competitors)}
    
    For each competitor, analyze:
    1. Content strategy (themes, formats, frequency)
    2. Engagement patterns (what drives interaction)
    3. Growth tactics (collaborations, campaigns, viral content)
    4. Audience sentiment (comment analysis)
    5. Differentiation opportunities
    
    End with 3-5 prioritized actionable recommendations.
    """

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

---

## 2.4 MCP Client Configuration

User cukup tambahkan ke config file AI agent mereka:

### Claude Desktop
```json
// claude_desktop_config.json
{
  "mcpServers": {
    "sidix-social-radar": {
      "command": "python",
      "args": ["-m", "social_radar.mcp.server"],
      "env": {
        "SIDIX_API_URL": "http://localhost:8765",
        "SIDIX_API_KEY": "user_api_key_here"
      }
    }
  }
}
```

### ChatGPT / OpenAI
```json
// GPT Actions schema (auto-generated dari MCP tools)
{
  "schema_version": "v1",
  "namespace": "sidix_social_radar",
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "analyze_competitor",
        "description": "Analyze a competitor's social media profile...",
        "parameters": { ... }
      }
    }
  ]
}
```

### Cursor / Windsurf
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "sidix-social-radar": {
      "url": "http://localhost:8765/mcp"
    }
  }
}
```

---

# PART 3: UNIFIED DATA MODEL

## 3.1 Cross-Platform Schema

Setiap platform punya data structure yang berbeda. SIDIX normalizes ke unified schema:

```python
# social_radar/models/unified.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

class Platform(str, Enum):
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"

class ContentFormat(str, Enum):
    REEL = "reel"           # Short-form video (IG, TT)
    CAROUSEL = "carousel"   # Multi-image post
    VIDEO = "video"         # Long-form video
    IMAGE = "image"         # Single image
    STORY = "story"         # Ephemeral content
    TEXT = "text"           # Text-only post
    LIVE = "live"           # Live stream

class UnifiedProfile(BaseModel):
    """Normalized profile data across all platforms"""
    platform: Platform
    username: str
    display_name: str
    bio: Optional[str]
    follower_count: int
    following_count: Optional[int]
    post_count: int
    is_verified: bool
    is_business: bool
    profile_picture_url: Optional[str]
    external_links: List[str] = []
    created_at: Optional[datetime]  # Account creation date
    scraped_at: datetime
    
    # Engagement metrics (last 30 days avg)
    avg_engagement_rate: Optional[float]
    avg_likes: Optional[int]
    avg_comments: Optional[int]
    avg_shares: Optional[int]
    avg_saves: Optional[int]  # Platform-specific (IG saves, TT bookmarks)
    
    # Computed fields
    audience_health_score: Optional[float]  # 0-100
    growth_rate_weekly: Optional[float]  # % per week

class UnifiedPost(BaseModel):
    """Normalized post/content across all platforms"""
    platform: Platform
    content_id: str
    author_username: str
    
    # Content
    caption: Optional[str]
    media_urls: List[str] = []
    format: ContentFormat
    duration_seconds: Optional[int]  # For video content
    
    # Engagement (absolute numbers)
    likes: int
    comments: int
    shares: int
    saves: int
    views: Optional[int]
    
    # Computed metrics
    engagement_rate: Optional[float]  # (likes+comments+shares+saves)/followers
    reach: Optional[int]
    impressions: Optional[int]
    
    # Metadata
    posted_at: datetime
    hashtags: List[str] = []
    mentions: List[str] = []
    location: Optional[str]
    is_sponsored: bool = False
    scraped_at: datetime
    
    # Cross-platform comparison fields
    performance_percentile: Optional[float]  # How this post performs vs author's avg
    viral_score: Optional[float]  # 0-100, likelihood of going viral

class UnifiedMetrics(BaseModel):
    """Time-series metrics for analytics"""
    platform: Platform
    username: str
    date: datetime
    
    # Follower metrics
    followers: int
    follower_growth: int  # Net change from previous period
    
    # Content metrics
    posts_published: int
    
    # Engagement metrics
    total_likes: int
    total_comments: int
    total_shares: int
    total_saves: int
    total_views: int
    
    # Computed
    engagement_rate: float
    avg_reach_per_post: Optional[int]
    
    # Benchmark comparison
    engagement_rate_vs_niche_avg: Optional[float]  # percentage difference

class CompetitorComparison(BaseModel):
    """Side-by-side comparison result"""
    niche: str
    analysis_date: datetime
    accounts: List[UnifiedProfile]
    
    # Rankings
    follower_ranking: List[dict]  # [{rank, username, followers, growth}]
    engagement_ranking: List[dict]
    content_quality_ranking: List[dict]
    growth_velocity_ranking: List[dict]
    
    # AI-generated insights
    content_gaps: List[str]  # Topics nobody is covering
    opportunity_areas: List[dict]  # [{area, potential_impact, difficulty}]
    threat_analysis: List[dict]  # Competitor moves to watch
    recommendations: List[dict]  # Prioritized action items
```

---

## 3.2 Platform-Specific Mapping

| Unified Field | Instagram | TikTok | Facebook | YouTube | LinkedIn | Twitter |
|--------------|-----------|--------|----------|---------|----------|---------|
| `follower_count` | followers | followers | page_likes | subscribers | connections | followers |
| `following_count` | following | following | N/A | N/A | connections | following |
| `likes` | likes | likes | reactions | likes | reactions | likes |
| `comments` | comments | comments | comments | comments | comments | replies |
| `shares` | shares | shares | shares | N/A | reposts | retweets |
| `saves` | saves | bookmarks | saves | watch_later | bookmarks | bookmarks |
| `views` | views | views | impressions | views | impressions | impressions |
| `REEL` | Reel | TikTok Video | Reel | Short | Video | N/A |
| `CAROUSEL` | Carousel | Photo Swipe | Album | Playlist | Carousel | Thread |

---

# PART 4: MULTI-PLATFORM SCRAPING STRATEGY

## 4.1 Platform Prioritization (MVP → Scale)

| Priority | Platform | Difficulty | Data Richness | Method |
|----------|----------|-----------|---------------|--------|
| **P0** | Instagram | Medium | Very High | Chrome Extension + curl_cffi |
| **P1** | TikTok | High | High | Chrome Extension (primary) |
| **P2** | Facebook | Medium | Medium | Chrome Extension + Graph API |
| **P3** | YouTube | Low | High | YouTube Data API (official) |
| **P4** | LinkedIn | High | Medium | Chrome Extension |
| **P5** | Twitter/X | High | Medium | Chrome Extension |

---

## 4.2 Chrome Extension: Universal Multi-Platform Collector

Satu extension untuk semua platform — intercept network calls dari SPA masing-masing:

```javascript
// universal-interceptor.js
(function() {
    const PLATFORM_PATTERNS = {
        instagram: {
            apiPatterns: ['instagram.com/graphql', 'instagram.com/api'],
            extractors: {
                profile: extractInstagramProfile,
                post: extractInstagramPost,
                reel: extractInstagramReel
            }
        },
        tiktok: {
            apiPatterns: ['tiktokv.com', 'tiktok.com/api'],
            extractors: {
                profile: extractTikTokProfile,
                video: extractTikTokVideo
            }
        },
        facebook: {
            apiPatterns: ['facebook.com/api/graphql'],
            extractors: {
                page: extractFacebookPage,
                post: extractFacebookPost
            }
        },
        youtube: {
            apiPatterns: ['youtubei.googleapis.com'],
            extractors: {
                channel: extractYouTubeChannel,
                video: extractYouTubeVideo
            }
        },
        linkedin: {
            apiPatterns: ['linkedin.com/voyager/api'],
            extractors: {
                profile: extractLinkedInProfile,
                post: extractLinkedInPost
            }
        }
    };
    
    // Auto-detect platform dari URL
    function detectPlatform(url) {
        for (const [platform, config] of Object.entries(PLATFORM_PATTERNS)) {
            if (config.apiPatterns.some(p => url.includes(p))) {
                return platform;
            }
        }
        return null;
    }
    
    // Interceptor logic (sama untuk semua platform)
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const response = await originalFetch.apply(this, args);
        const url = args[0];
        
        const platform = detectPlatform(url);
        if (platform) {
            const clone = response.clone();
            const body = await clone.text();
            
            window.dispatchEvent(new CustomEvent('socialDataIntercepted', {
                detail: { platform, url, body, timestamp: Date.now() }
            }));
        }
        return response;
    };
})();
```

---

# PART 5: PLUGIN DISTRIBUTION STRATEGY

## 5.1 Four-Marketplace Blueprint

Berdasarkan best practices 2026, Social Radar harus hadir di 4 marketplace:

### 1. MCP Server → mcp.so, Smithery, PulseMCP
```
Ship core capability sebagai MCP server.
One build → consumable oleh Claude Desktop, Cursor, Claude Code, Windsurf, VS Code Copilot
```
**Submission:**
- GitHub repo dengan README yang jelas
- `llms-install.md` — instalation guide untuk AI agents
- Logo 400×400 PNG
- Submit ke mcp.so, Smithery, PulseMCP

### 2. Custom GPT → GPT Store (OpenAI)
```
Parallel GPT tuned untuk ChatGPT.
Actions call SIDIX backend API.
Prompt dan personality tuned untuk GPT-5.x behavior.
```
**Requirements:**
- OpenAPI schema dari SIDIX API
- GPT instructions (system prompt)
- Knowledge files (niche benchmarks, best practices)
- Actions (API endpoints)

### 3. Hugging Face Space → Demo Surface
```
Gradio/Streamlit space untuk interactive demo.
Zero-friction: user bisa coba tanpa install.
Top-of-funnel yang convert ke actual install.
```
**Features:**
- Input: competitor username
- Output: sample analytics report
- Watermarked: "Powered by SIDIX Social Radar"
- CTA: "Install full version"

### 4. Chrome Web Store → End User Distribution
```
Chrome Extension untuk data collection.
Free tier yang useful.
Upsell ke dashboard + AI features.
```

---

## 5.2 Distribution Timeline

| Phase | Timeline | Marketplace | Goal |
|-------|----------|-------------|------|
| **Alpha** | Week 1-2 | MCP (stdio) — local only | 10 beta testers (Founding Circle) |
| **Beta** | Week 3-6 | MCP + Chrome Web Store | 50 users |
| **Launch** | Month 2-3 | MCP Hubs + GPT Store | 500 users |
| **Scale** | Month 4-6 | HF Space + all hubs | 5000+ users |

---

# PART 6: INTEGRATION DENGAN EXISTING SIDIX

## 6.1 Architecture: Social Radar sebagai Layer di Atas SIDIX Brain

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Next.js      │  │ Chrome Ext   │  │ MCP Server       │  │
│  │ (port 3000)  │  │ (Collection) │  │ (Plugin API)     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘  │
│         │                  │                   │              │
└─────────┼──────────────────┼───────────────────┼──────────────┘
          │                  │                   │
          ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    SIDIX BRAIN (port 8765)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  API Gateway (FastAPI)                                │    │
│  │  ├── /api/social-radar/ingest   (Chrome Extension)  │    │
│  │  ├── /api/social-radar/analyze  (Trigger analysis)  │    │
│  │  ├── /api/social-radar/compare  (Competitor compare)│    │
│  │  ├── /api/social-radar/trends   (Trend detection)   │    │
│  │  ├── /api/social-radar/reports  (Report generation) │    │
│  │  └── /mcp                       (MCP protocol)      │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │  AI CORE (Qwen2.5-7B + LoRA)                        │    │
│  │  ├── Prompt Templates                                 │    │
│  │  │   ├── competitor_analysis.prompt                  │    │
│  │  │   ├── trend_detection.prompt                      │    │
│  │  │   └── comparison_report.prompt                    │    │
│  │  ├── Persona Router                                   │    │
│  │  │   ├── AYMAN (creative strategy)                    │    │
│  │  │   ├── ABOO (analytical)                            │    │
│  │  │   └── OOMAR (practical tactics)                    │    │
│  │  └── Maqashid Filter (post-analysis)                  │    │
│  └───────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │  DATA LAYER                                          │    │
│  │  ├── PostgreSQL (structured data)                     │    │
│  │  ├── Redis (queue + cache)                            │    │
│  │  ├── MinIO (media storage)                            │    │
│  │  └── Corpus (training pairs)                          │    │
│  └───────────────────────────────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │  SIDIX SYSTEMS INTEGRATION                           │    │
│  │  ├── Maqashid Profiles (output filter)               │    │
│  │  ├── Naskh Handler (conflict resolution)             │    │
│  │  ├── Raudah Protocol (multi-agent DAG)               │    │
│  │  ├── Growth Loop (training pair generation)          │    │
│  │  └── 35 Tools (+ Social Radar as #36)                │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 6.2 Social Radar sebagai Tool #36

```python
# tools/social_radar_tool.py
from tools.base import BaseTool

class SocialRadarTool(BaseTool):
    """
    Tool #36: Social Radar — Multi-platform competitor intelligence
    
    Integrated ke SIDIX agent system. Bisa dipanggil oleh:
    - User via chat ("Analyze @rivalstore on Instagram")
    - AYMAN persona ("What are competitors doing?")
    - ABOO persona ("Show me engagement data")
    - Raudah Protocol (multi-agent collaboration)
    - External AI agents via MCP
    """
    
    name = "social_radar"
    description = """
    Analyze competitors across social media platforms (Instagram, TikTok, 
    Facebook, YouTube, LinkedIn). Provides strategic insights including 
    content strategy, engagement analysis, growth tactics, and actionable 
    recommendations. Requires competitor username and platform.
    """
    
    parameters = {
        "username": "Social media handle to analyze",
        "platform": "One of: instagram, tiktok, facebook, youtube, linkedin",
        "depth": "quick/standard/deep analysis level",
        "compare_with": "Optional: your username for comparison"
    }
    
    async def execute(self, username: str, platform: str = "instagram",
                     depth: str = "standard", compare_with: str = None):
        # 1. Fetch data (via Chrome Extension cache or direct scrape)
        data = await self.data_service.get_profile_data(username, platform)
        
        # 2. Run AI analysis dengan persona yang sesuai
        analysis = await self.ai_service.analyze(
            data=data,
            prompt_template="competitor_analysis",
            persona=self.select_persona(depth)
        )
        
        # 3. Apply Maqashid filter
        filtered = self.maqashid.filter(analysis, mode="General")
        
        # 4. Generate training pair (flywheel)
        await self.growth_loop.save_training_pair(
            input=f"Analyze {username} on {platform}",
            output=filtered,
            quality_score=self.assess_quality(filtered)
        )
        
        return filtered
```

---

# PART 7: IMPLEMENTATION ROADMAP

## 7.1 MVP Phase (3-4 hari) — "Foundation"

| Day | Focus | Deliverables |
|-----|-------|-------------|
| **Day 1** | Chrome Extension + Backend skeleton | Universal interceptor, FastAPI endpoints, DB schema |
| **Day 2** | Instagram scraper + pipeline | curl_cffi scraper, Redis queue, async workers |
| **Day 3** | AI Analysis + Dashboard | Prompt templates, Qwen integration, basic dashboard UI |
| **Day 4** | MCP Server skeleton | FastMCP server, 2-3 tools, local testing |

## 7.2 Phase 2 (Week 2-3) — "Multi-Platform"

| Week | Focus | Deliverables |
|------|-------|-------------|
| **Week 2** | TikTok + Facebook | Extension support, scrapers, unified data model |
| **Week 3** | YouTube + LinkedIn | API integration, comparison features |

## 7.3 Phase 3 (Week 4-6) — "Dashboard Semrawut"

| Week | Focus | Deliverables |
|------|-------|-------------|
| **Week 4** | Dashboard v1 | Dense UI, all components, real-time updates |
| **Week 5** | AI Insights panel | Full prompt suite, persona integration, trend detection |
| **Week 6** | MCP polish | Full tool suite, resources, prompts, documentation |

## 7.4 Phase 4 (Month 2-3) — "Plugin Ecosystem"

| Week | Focus | Deliverables |
|------|-------|-------------|
| **Month 2** | Distribution | MCP Hubs submission, GPT Store, HF Space |
| **Month 3** | Growth | Founding Circle, case studies, content marketing |

---

## 7.5 Tech Stack Final

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend Dashboard** | Next.js 15 + Tailwind + Recharts | Existing SIDIX UI stack |
| **Chrome Extension** | Vanilla JS (MV3) | Lightweight, no build step |
| **Backend API** | FastAPI (Python) | Existing SIDIX backend |
| **AI Engine** | Qwen2.5-7B-Instruct + LoRA | Existing SIDIX brain |
| **Queue** | Redis + asyncio | Lightweight, self-hosted |
| **Database** | PostgreSQL | Existing SIDIX DB |
| **MCP Server** | FastMCP (Python) | Native Python, easy integration |
| **Scraping** | curl_cffi + Extension | Stealthy, efficient |
| **Media Storage** | MinIO | S3-compatible, self-hosted |

---

# PART 8: DIFFERENTIATOR ANALYSIS

## 8.1 SIDIX Social Radar vs Existing Tools

| Feature | Sprout Social ($249/mo) | Hootsuite ($199/mo) | Brandwatch (Enterprise) | **SIDIX Social Radar** |
|---------|------------------------|---------------------|------------------------|----------------------|
| **Price** | $249/month | $199/month | $10K+/year | **Free / $9 / $99** |
| **Self-hosted** | No | No | No | **Yes** |
| **No vendor API** | No | No | No | **Yes** |
| **MCP Plugin** | No | No | No | **Yes** |
| **AI Analysis** | Basic | Basic | Advanced | **Full (Qwen2.5-7B)** |
| **Multi-platform** | 5 | 5 | 10+ | **6 (MVP)** |
| **Real-time** | 15-min delay | 15-min delay | Near real-time | **Real-time (Extension)** |
| **Training data flywheel** | No | No | No | **Yes** |
| **Open source** | No | No | No | **Yes (MIT)** |
| **Indonesia-focused** | No | No | No | **Yes** |

---

## 8.2 Moat (Competitive Advantage)

1. **Data Flywheel** — Setiap report jadi training data → smarter AI → better reports → more users → more data
2. **Self-hosted by design** — Enterprise yang concern privacy tidak punya opsi lain
3. **MCP Ecosystem** — Menjadi infrastructure layer, bukan sekadar tool
4. **IHOS Philosophy** — Transparansi, ethical data collection, keadilan
5. **Indonesia-first** — Bahasa Indonesia, payment lokal, niche lokal

---

# APPENDIX: PROMPT TEMPLATES UNTUK MCP

## A. analyze_competitor prompt (Qwen2.5-7B)

```
You are a social media competitive intelligence analyst. Analyze the following 
competitor data and provide strategic insights.

INPUT DATA:
- Username: {username}
- Platform: {platform}
- Profile: {profile_json}
- Recent Posts (last 30 days): {posts_json}
- Engagement Metrics: {engagement_json}

ANALYZE IN THIS ORDER:
1. Content Strategy: posting frequency, themes, formats, visual style
2. Engagement Patterns: what drives interaction, community sentiment
3. Growth Strategy: follower growth rate, tactics, collaborations
4. Competitive Position: strengths, weaknesses, differentiation opportunities
5. Actionable Recommendations: 3-5 specific, prioritized actions

OUTPUT: Valid JSON with structured fields.
Think step by step. Be data-driven and specific, not generic.
```

## B. detect_trends prompt

```
Analyze social media content from {niche} niche across {platforms}.
Identify emerging trends in:
1. Content formats (what's rising, what's declining)
2. Themes and topics gaining traction
3. Hashtag evolution
4. Engagement pattern shifts
5. Early opportunity signals

Predict: What will be trending in the next 30 days?
Output: JSON with trend list and opportunity scores (1-10).
```

---

*This document is a living strategic guide. Updated per sprint based on implementation learnings.*
