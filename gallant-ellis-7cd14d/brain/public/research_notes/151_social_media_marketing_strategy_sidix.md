# 151. Social Media Marketing Strategy — SIDIX Menjangkau Dunia

> **Domain**: marketing / growth / social-media
> **Status**: `[OPINION]` + `[FACT]` (platform facts verified, strategi rekomendasi)
> **Tanggal**: 2026-04-19

---

## Latar Belakang

SIDIX adalah AI agent self-hosted dengan epistemic integrity berbasis nilai
Islam + open-source. Tantangan unik: positioning bukan "ChatGPT lokal biasa"
tapi platform epistemic yang bisa percaya hasilnya. Strategi marketing harus
mencerminkan identitas ini — bukan hard-sell, tapi **demonstration of value**.

---

## Prinsip Marketing SIDIX

1. **Show, don't tell** — posting demo nyata lebih kuat dari klaim
2. **Community first** — bangun komunitas belajar, bukan hanya user
3. **Identity masking** — semua konten publik: `@sidixlab`, `Mighan Lab`,
   bukan nama owner
4. **Multilingual** — target global: EN + ID + AR (3 bahasa utama)
5. **Epistemic content** — setiap post punya label
   `[FACT]/[OPINION]/[SPECULATION]` → diferensiasi dari AI lain

---

## Platform & Strategi Per Channel

### 1. Threads (@sidixlab)
**Sudah ada** — Threads autopost sudah live (note 120, 149).

**Taktik**:
- 1-2 post/hari: demo epistemic reasoning, quote dari research notes
- Thread panjang tiap minggu: "SIDIX belajar X hari ini" (journal transparansi)
- Reply ke percakapan AI Indonesia besar (Grok, Gemini, lokal)
- Hashtag: `#SIDIX #AI #OpenSource #IslamicEpistemology #SelfHosted`

**Content Types**:
- 🧵 "Cara SIDIX menjawab pertanyaan vs ChatGPT" (comparison thread)
- 🧵 "5 hal yang SIDIX tahu tentang [topik] hari ini" (learning log)
- 🧵 "SIDIX epistemic label: kenapa ini penting?" (education)

---

### 2. Twitter/X (@sidixlab)
**Perlu dibuat** — cross-post dari Threads via API.

**API**: Twitter API v2 Free tier (500 tweet/bulan read+write)
- Endpoint: `POST /2/tweets`
- Auth: OAuth 2.0 Bearer Token
- Rate limit: 50 req/15min

**Taktik**:
- Cross-post top-performing Threads content
- Engage AI/open-source community global (Yann LeCun, Karpathy, etc.)
- Quote tweet benchmark results saat SIDIX improve
- `#OpenSourceAI #LocalLLM #EpistemicAI`

---

### 3. LinkedIn (Mighan Lab Page)
**Perlu dibuat** — profesional/B2B.

**API**: LinkedIn Marketing API (free untuk personal + org page)
- `POST /ugcPosts` → publish post
- Auth: OAuth 2.0

**Taktik**:
- 2-3x/minggu: thought leadership (Islamic epistemology + AI)
- Case study: "Bagaimana SIDIX membantu X"
- Job/contributor posting (developer open-source)
- Target: CTOs, academic researchers, Islamic finance sector

---

### 4. YouTube (@sidixlab)
**Target medium-term** — video demo = trust builder terkuat.

**API**: YouTube Data API v3 (free, 10,000 units/day)
- `POST /youtube/v3/videos` → upload video
- Auth: OAuth 2.0

**Content**:
- Demo video 3-5 menit: "SIDIX menjawab pertanyaan tentang [X]"
- Tutorial: "Install SIDIX di server kamu sendiri"
- Komparasi: SIDIX vs model populer pada topik spesifik
- Podcast-style: "Ngobrol dengan SIDIX tentang [isu dunia]"

---

### 5. TikTok / Instagram Reels
**Target long-term** — reach anak muda Indonesia + global.

**API**: TikTok for Developers (content posting API)
- Perlu TikTok Developer Account
- `POST /v2/post/publish/video/init/`

**Content**:
- 60-90 detik: "SIDIX vs [trending question]" quick demo
- Behind the scenes: training SIDIX
- Educational: "Apa itu epistemic label?" (animated)

---

### 6. Mastodon / ActivityPub (Fediverse)
**Target privacy-conscious community**.

**API**: Mastodon API (open, free)
- `POST /api/v1/statuses`
- Instance: mastodon.social atau buat instance `sidixlab.social`

Relevan untuk komunitas: open-source developer, privacy advocates, akademisi.

---

### 7. Hacker News / Reddit
**Earned media** — submit milestone SIDIX.

- HN: Submit `Show HN: SIDIX — self-hosted AI agent with Islamic epistemic framework`
- Reddit: r/LocalLLaMA, r/selfhosted, r/MachineLearning, r/artificial
- Target: upvote → organic discovery oleh developer global

---

### 8. Discord Community
**Community hub**.

- Server: SIDIX Community
- Channels: #general, #sidix-demos, #contribute, #research-notes, #bugs
- Bot SIDIX bisa menjawab pertanyaan langsung di Discord
- Invite link di landing page + README

---

## Content Calendar Template (Minggu 1)

| Hari | Platform | Konten |
|------|----------|--------|
| Sen | Threads | "SIDIX hari ini belajar tentang [topik dari research note]" |
| Sel | LinkedIn | Thought leadership: epistemic AI vs black-box AI |
| Rab | Twitter/X | Demo screenshot: SIDIX jawab pertanyaan sulit |
| Kam | Threads | Thread: 5 API yang SIDIX pelajari minggu ini |
| Jum | YouTube | Upload: Demo video terbaru |
| Sab | Reddit/HN | Share milestone terbaru (bila ada) |
| Min | - | Review performa, plan minggu depan |

---

## Automated Social Agent (`promote_agent.py`)

Rencana implementasi sub-agent promosi otomatis:

```python
# apps/brain_qa/brain_qa/promote_agent.py

class PromoteAgent:
    """
    Autonomous social media promotion sub-agent.
    
    Tugas:
    1. Ambil research note terbaru → ekstrak highlight
    2. Generate konten platform-specific (Threads/Twitter/LinkedIn)
    3. Schedule + post via API masing-masing
    4. Monitor engagement → feedback ke content strategy
    """
    
    def pick_content_source(self) -> dict:
        """Pilih research note / milestone terbaru untuk diposting."""
    
    def generate_post(self, source: dict, platform: str) -> str:
        """Generate konten sesuai gaya platform via SIDIX inference."""
    
    def schedule_post(self, content: str, platform: str, time: datetime):
        """Antri post ke waktu optimal (engagement hours)."""
    
    def post_now(self, content: str, platform: str) -> dict:
        """Post langsung ke platform via API."""
    
    def monitor_engagement(self) -> dict:
        """Fetch likes/shares/replies → simpan ke analytics log."""
```

---

## Metrik Sukses (KPI)

| Metrik | Target 1 bulan | Target 3 bulan |
|--------|---------------|----------------|
| Threads followers | 100 | 500 |
| GitHub stars | 50 | 200 |
| Monthly visitors sidixlab.com | 500 | 2,000 |
| Discord members | 20 | 100 |
| YouTube views (total) | 500 | 5,000 |

---

## Keterbatasan Jujur

1. **Token API rate limits** — semua platform punya quota; perlu manajemen antrian
2. **Identity masking** — konten tidak boleh expose nama owner
3. **Konten harus otentik** — spammy AI content justru merusak brand epistemic
4. **Bahasa** — EN untuk global reach, ID untuk komunitas lokal; perlu balance
5. **Time investment** — automation bisa bantu tapi review manusia tetap perlu

---

## Sumber

- Twitter API v2 docs: https://developer.x.com/en/docs/x-api
- LinkedIn Marketing API: https://learn.microsoft.com/en-us/linkedin/marketing/
- YouTube Data API v3: https://developers.google.com/youtube/v3
- TikTok Developer: https://developers.tiktok.com/
- Mastodon API: https://docs.joinmastodon.org/api/
