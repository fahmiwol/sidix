"""
Social Radar — analisis tren sosial media dan sentimen publik.
Menggunakan web_search + pattern matching, bukan API sosmed berbayar.

Kemampuan:
- Trend detection dari query search
- Sentiment classification sederhana (positif/negatif/netral)
- Hashtag extraction
- Engagement proxy dari judul/snippet

Standing-alone: tidak butuh API Twitter/Instagram. Bekerja via
DuckDuckGo public HTML search results yang sudah difetch oleh tool
web_search di agent_tools.py.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


# ── Sentiment word lists ──────────────────────────────────────────────────────

_POSITIVE_WORDS: frozenset[str] = frozenset({
    # Indonesia
    "bagus", "baik", "keren", "mantap", "luar biasa", "sukses", "berhasil",
    "senang", "gembira", "positif", "terbaik", "hebat", "amazing", "viral",
    "trending", "populer", "favorit", "setuju", "suka", "cinta", "love",
    "bangga", "optimis", "maju", "berkembang", "meningkat", "naik", "untung",
    "profit", "ramai", "antusias", "semangat", "juara", "unggul", "menang",
    # English
    "good", "great", "excellent", "awesome", "success", "win", "best",
    "top", "hot", "trending", "popular", "like", "love", "happy", "positive",
    "rise", "growth", "gain", "profit", "boom", "viral", "breakthrough",
})

_NEGATIVE_WORDS: frozenset[str] = frozenset({
    # Indonesia
    "buruk", "jelek", "gagal", "kecewa", "sedih", "marah", "negatif",
    "lambat", "rugi", "turun", "anjlok", "drop", "masalah", "masalah",
    "susah", "sulit", "berat", "macet", "korupsi", "penipuan", "bohong",
    "palsu", "fake", "hoax", "krisis", "bangkrut", "tutup", "keluhan",
    "komplain", "mati", "rusak", "error", "bug", "down", "parah", "hancur",
    # English
    "bad", "terrible", "awful", "fail", "failure", "sad", "angry", "hate",
    "worst", "drop", "fall", "loss", "crash", "crisis", "scam", "fraud",
    "fake", "wrong", "broken", "dead", "down", "corrupt", "problem",
})

# Stopwords untuk keyword extraction
_STOPWORDS: frozenset[str] = frozenset({
    "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "adalah", "ini",
    "itu", "ada", "tidak", "bisa", "akan", "juga", "sudah", "belum", "saat",
    "pada", "dalam", "oleh", "atau", "karena", "jika", "kalau", "agar",
    "setelah", "sebelum", "lagi", "lebih", "sangat", "paling", "hanya",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "to", "of", "in", "on", "at", "by", "for", "with", "about", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "from", "up", "down", "out", "off", "over", "under", "again",
    "then", "that", "this", "these", "those", "but", "and", "or", "not",
    "com", "www", "https", "http", "html", "php", "aspx",
})


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class SocialSignal:
    query: str
    platform_hints: list[str]       # ['twitter', 'instagram', 'tiktok'] dari URL
    sentiment: str                  # 'positive' | 'negative' | 'neutral'
    sentiment_score: float          # -1.0 .. +1.0
    trending_keywords: list[str]
    hashtags: list[str]
    estimated_volume: str           # 'low' | 'medium' | 'high' (dari jumlah hasil)
    summary: str
    raw_results: list[dict] = field(default_factory=list)


# ── Core functions ────────────────────────────────────────────────────────────

def detect_sentiment(text: str) -> tuple[str, float]:
    """
    Rule-based sentiment detection (Indonesia + English).

    Returns (label, score):
      - label: 'positive' | 'negative' | 'neutral'
      - score: float -1.0 .. +1.0
    """
    if not text:
        return "neutral", 0.0

    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text_lower)

    pos_count = sum(1 for w in words if w in _POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in _NEGATIVE_WORDS)

    # Cek frasa positif (misal "luar biasa" sebagai satu unit)
    for phrase in ("luar biasa", "tidak bagus", "tidak baik", "kurang bagus"):
        if phrase in text_lower:
            if phrase.startswith("tidak") or phrase.startswith("kurang"):
                neg_count += 1
            else:
                pos_count += 1

    total = pos_count + neg_count
    if total == 0:
        return "neutral", 0.0

    score = (pos_count - neg_count) / max(total, 1)
    score = max(-1.0, min(1.0, score))

    if score > 0.1:
        return "positive", score
    elif score < -0.1:
        return "negative", score
    else:
        return "neutral", score


def extract_hashtags(texts: list[str]) -> list[str]:
    """Extract semua hashtag (#tag) dari list teks."""
    seen: set[str] = set()
    result: list[str] = []
    for text in texts:
        for tag in re.findall(r"#(\w+)", text, re.IGNORECASE):
            key = tag.lower()
            if key not in seen:
                seen.add(key)
                result.append(f"#{tag}")
    return result[:20]  # max 20 hashtag


def extract_keywords(texts: list[str], top_n: int = 10) -> list[str]:
    """
    Ekstrak kata kunci dari list teks via word frequency, filter stopwords.
    Sederhana tapi efektif untuk data web search snippets.
    """
    word_freq: Counter[str] = Counter()
    for text in texts:
        words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9]{2,}\b", text.lower())
        for w in words:
            if w not in _STOPWORDS and len(w) >= 3:
                word_freq[w] += 1

    # Kembalikan top_n paling sering muncul
    return [word for word, _ in word_freq.most_common(top_n)]


def _detect_platform_hints(urls: list[str]) -> list[str]:
    """Deteksi platform dari list URL."""
    platforms: set[str] = set()
    platform_map = {
        "twitter.com": "twitter",
        "x.com": "twitter",
        "instagram.com": "instagram",
        "tiktok.com": "tiktok",
        "facebook.com": "facebook",
        "youtube.com": "youtube",
        "linkedin.com": "linkedin",
        "reddit.com": "reddit",
        "threads.net": "threads",
    }
    for url in urls:
        for domain, platform in platform_map.items():
            if domain in url:
                platforms.add(platform)
    return sorted(platforms)


def _estimate_volume(result_count: int) -> str:
    """Proxy volume berdasarkan jumlah hasil search."""
    if result_count >= 10:
        return "high"
    elif result_count >= 4:
        return "medium"
    else:
        return "low"


def analyze_social_signals(
    query: str,
    search_results: list[dict],
) -> SocialSignal:
    """
    Analisis tren dan sentimen sosial dari hasil web search.

    Args:
        query: Query pencarian yang digunakan
        search_results: List dict dengan keys 'title', 'snippet', 'url'
                        (format output dari _tool_web_search SIDIX)

    Returns:
        SocialSignal dengan semua analisis
    """
    if not search_results:
        return SocialSignal(
            query=query,
            platform_hints=[],
            sentiment="neutral",
            sentiment_score=0.0,
            trending_keywords=[],
            hashtags=[],
            estimated_volume="low",
            summary=f"Tidak ada hasil ditemukan untuk query: {query}",
            raw_results=[],
        )

    # Kumpulkan semua teks
    all_texts: list[str] = []
    all_urls: list[str] = []
    for r in search_results:
        title = str(r.get("title", "")).strip()
        snippet = str(r.get("snippet", "")).strip()
        url = str(r.get("url", "")).strip()
        if title:
            all_texts.append(title)
        if snippet:
            all_texts.append(snippet)
        if url:
            all_urls.append(url)

    combined_text = " ".join(all_texts)

    # Analisis
    sentiment_label, sentiment_score = detect_sentiment(combined_text)
    keywords = extract_keywords(all_texts, top_n=10)
    hashtags = extract_hashtags(all_texts)
    platform_hints = _detect_platform_hints(all_urls)
    volume = _estimate_volume(len(search_results))

    # Summary otomatis
    top_kw = ", ".join(keywords[:5]) if keywords else "tidak ada"
    platforms_str = ", ".join(platform_hints) if platform_hints else "web umum"
    summary = (
        f"Query '{query}': {len(search_results)} hasil ditemukan di {platforms_str}. "
        f"Sentimen: {sentiment_label} (score: {sentiment_score:+.2f}). "
        f"Kata kunci trending: {top_kw}."
    )
    if hashtags:
        summary += f" Hashtag: {', '.join(hashtags[:5])}."

    return SocialSignal(
        query=query,
        platform_hints=platform_hints,
        sentiment=sentiment_label,
        sentiment_score=sentiment_score,
        trending_keywords=keywords,
        hashtags=hashtags,
        estimated_volume=volume,
        summary=summary,
        raw_results=search_results[:20],  # cap untuk efisiensi memori
    )


def format_report(signal: SocialSignal) -> str:
    """
    Format SocialSignal menjadi teks laporan untuk output agent.

    Returns:
        String laporan siap tampil (markdown-friendly).
    """
    lines = [
        f"# Social Radar — {signal.query}",
        "",
        f"**Sentimen**: {signal.sentiment.upper()} (score: {signal.sentiment_score:+.2f})",
        f"**Volume estimasi**: {signal.estimated_volume.upper()}",
        f"**Platform terdeteksi**: {', '.join(signal.platform_hints) if signal.platform_hints else 'tidak terdeteksi'}",
        "",
    ]

    if signal.trending_keywords:
        lines.append("## Kata Kunci Trending")
        for i, kw in enumerate(signal.trending_keywords, 1):
            lines.append(f"{i}. {kw}")
        lines.append("")

    if signal.hashtags:
        lines.append("## Hashtag")
        lines.append(", ".join(signal.hashtags[:10]))
        lines.append("")

    lines.append("## Ringkasan")
    lines.append(signal.summary)

    if signal.raw_results:
        lines.append("")
        lines.append("## Hasil Teratas")
        for r in signal.raw_results[:5]:
            title = r.get("title", "").strip()
            url = r.get("url", "").strip()
            snippet = r.get("snippet", "").strip()
            if title:
                if url:
                    lines.append(f"- **[{title}]({url})**")
                else:
                    lines.append(f"- **{title}**")
                if snippet:
                    lines.append(f"  {snippet[:150]}...")

    lines.append("")
    lines.append(
        "*[Social Radar — SIDIX standing-alone, tanpa API sosmed berbayar. "
        "Data dari public web search. Akurasi sentimen ±rule-based.]*"
    )

    return "\n".join(lines)
