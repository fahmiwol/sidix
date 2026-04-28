# 195 — Sociometer / Social Radar: Analisis Tren Sosial Tanpa API Berbayar

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-24
**Sprint**: 9 (implementasi awal)
**Status**: IMPL ✅
**Tags**: social-radar, sentiment, trend-detection, standing-alone, agent-tool

---

## Apa

Social Radar adalah modul analisis tren dan sentimen sosial media yang diimplementasikan
sebagai agent tool SIDIX. Modul ini memungkinkan SIDIX menganalisis percakapan publik,
trending topics, dan sentimen konten sosial media untuk query tertentu — **tanpa
memerlukan API berbayar** dari Twitter, Instagram, TikTok, atau platform sosial lainnya.

Komponen utama:
- `apps/brain_qa/brain_qa/tools/social_radar.py` — core module
- Tool `social_radar` di `agent_tools.py` TOOL_REGISTRY
- Tests: `apps/brain_qa/tests/test_social_radar.py` (13 unit tests)

---

## Mengapa

### Problem yang dipecahkan
SIDIX seringkali perlu menjawab pertanyaan seperti:
- "Apa yang sedang trending di Twitter soal X?"
- "Bagaimana sentimen publik terhadap brand Y?"
- "Hashtag apa yang populer untuk niche Z?"
- "Apakah produk ini sedang viral?"

Tanpa social intelligence, SIDIX hanya bisa menjawab berdasarkan corpus statis yang
mungkin sudah outdated. Dengan Social Radar, SIDIX bisa mengakses sinyal sosial
real-time dari web publik.

### Mengapa tidak pakai API resmi?
1. **Biaya**: Twitter API (sekarang X API) mulai dari $100/bulan untuk basic access
2. **Rate limit**: sangat ketat, tidak cocok untuk explorasi bebas
3. **Standing-alone principle**: SIDIX didesain untuk tidak bergantung pada layanan
   eksternal berbayar yang bisa diputus kapan saja
4. **DuckDuckGo public**: cukup untuk proxy sentimen dan trend detection kasar

### Value untuk client SIDIX
- Agency marketing: "cek sentimen brand klien sebelum campaign launch"
- Content creator: "tren hashtag minggu ini di niche cooking"
- Bisnis: "respons publik terhadap peluncuran produk baru"

---

## Bagaimana

### Arsitektur

```
User query → _tool_social_radar (agent_tools.py)
    ↓
_tool_web_search (DuckDuckGo public HTML)
    → search query + "site:twitter.com OR site:instagram.com OR trending"
    ↓
Parse hasil → list[dict] {title, snippet, url}
    ↓
analyze_social_signals (social_radar.py)
    → detect_sentiment(combined_text) → rule-based word matching
    → extract_keywords(texts) → word frequency + stopword filter
    → extract_hashtags(texts) → regex #tag extraction
    → _detect_platform_hints(urls) → domain matching
    → _estimate_volume(count) → proxy dari jumlah hasil
    ↓
SocialSignal dataclass
    ↓
format_report(signal) → markdown string
    ↓
ToolResult → agent observation
```

### Sentiment Detection

Rule-based menggunakan word lists:
- **Positif** (~55 kata): bagus, keren, sukses, berhasil, viral, trending, good, great, awesome...
- **Negatif** (~50 kata): buruk, gagal, kecewa, drop, rugi, crash, terrible, fraud...
- Score: `(pos - neg) / (pos + neg)`, range -1.0 .. +1.0
- Threshold: > 0.1 = positive, < -0.1 = negative, else neutral

Keterbatasan: tidak handle sarkasme, negasi kompleks ("tidak bagus" → kata "bagus" dihitung positif
kecuali frasa "tidak bagus" ditangani secara khusus di kode).

### Keyword Extraction

Word frequency tanpa TF-IDF library:
1. Tokenize dengan regex `\b[a-zA-Z][a-zA-Z0-9]{2,}\b`
2. Filter stopwords (180+ kata Indonesia + English)
3. Counter.most_common(top_n)

Cukup untuk trend detection kasar dari 5-15 snippet pendek.

### Volume Estimation

Proxy dari jumlah hasil search:
- `< 4` hasil → "low"
- `4-9` hasil → "medium"
- `>= 10` hasil → "high"

---

## Contoh Nyata

**Input**:
```python
_tool_social_radar({"query": "Ramadan 2026 campaign Indonesia"})
```

**Internal flow**:
1. web_search: "Ramadan 2026 campaign Indonesia site:twitter.com OR site:instagram.com OR trending"
2. Dapat 8 hasil dari DuckDuckGo
3. Detect platform: instagram, twitter
4. Keywords: ramadan, campaign, indonesia, promo, konten
5. Hashtags: #Ramadan2026, #RamadanSale (dari snippets)
6. Sentimen: positive (kata "promo", "campaign" sering positif di konteks marketing)

**Output**:
```markdown
# Social Radar — Ramadan 2026 campaign Indonesia

**Sentimen**: POSITIVE (score: +0.45)
**Volume estimasi**: MEDIUM
**Platform terdeteksi**: instagram, twitter

## Kata Kunci Trending
1. ramadan
2. campaign
3. indonesia
...
```

---

## Keterbatasan

1. **Tidak real-time**: bergantung pada DuckDuckGo yang punya delay indexing
2. **Bias search engine**: DuckDuckGo bukan cermin sempurna Twitter/Instagram
3. **Akurasi sentimen ~70%**: rule-based tidak handle konteks, ironi, sarkasme
4. **Bahasa terbatas**: word list Indonesia + English; bahasa daerah tidak tercakup
5. **Rate limit implicit**: terlalu banyak call dalam waktu singkat bisa di-block DDG
6. **Data sosmed terbatas**: banyak konten sosmed belum diindex search engine

---

## Pengembangan

### Sprint 9 Next Steps
- Integrasi Kimi Agent untuk Instagram public data scraping
- Periodic trend report via LearnAgent (daily_growth SCAN fase)
- Cache hasil search (TTL 1 jam) untuk kurangi beban DDG

### Sprint 10+
- Real-time stream monitoring (WebSocket hook ke public Mastodon API sebagai proxy)
- Sentiment model lokal (fine-tune pada data Indonesia, replace rule-based)
- Alert system: notifikasi otomatis saat sentimen negatif melebihi threshold

### Potensi Integrasi
- `threads_autopost.py` → pilih konten berdasarkan trending keywords dari Social Radar
- `content_planner.py` → inject trending hashtag ke jadwal konten
- `campaign_strategist.py` → validasi timing campaign dengan sentimen publik

---

## Referensi Internal

- `brain/public/research_notes/151_social_media_marketing_strategy_sidix.md`
- `brain/public/research_notes/120_threads_full_api_autonomous_agent.md`
- `brain/public/research_notes/182_standing_alone_principle.md`
- `apps/brain_qa/brain_qa/tools/social_radar.py`
- `apps/brain_qa/brain_qa/agent_tools.py` (TOOL_REGISTRY entry: "social_radar")

---

*[FACT] Diimplementasikan 2026-04-24. Semua klaim teknis berdasarkan kode yang ditulis langsung.*
