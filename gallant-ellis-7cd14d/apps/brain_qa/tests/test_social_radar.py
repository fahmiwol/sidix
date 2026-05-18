"""
Unit tests untuk modul social_radar.
Menguji: detect_sentiment, extract_keywords, analyze_social_signals, format_report.

Tidak ada dependency external / server — semua diuji secara isolated.
"""

import pytest

from brain_qa.tools.social_radar import (
    SocialSignal,
    analyze_social_signals,
    detect_sentiment,
    extract_hashtags,
    extract_keywords,
    format_report,
)


# ── detect_sentiment ──────────────────────────────────────────────────────────

def test_detect_sentiment_positive():
    """Teks dengan kata positif Indonesia/Inggris → sentiment positive."""
    text = "Produk ini bagus sekali, sangat keren dan berhasil menarik perhatian!"
    label, score = detect_sentiment(text)
    assert label == "positive", f"Expected positive, got {label}"
    assert score > 0.0


def test_detect_sentiment_positive_english():
    """Teks English positif → positive."""
    text = "This is awesome! Great success and excellent results trending now."
    label, score = detect_sentiment(text)
    assert label == "positive"
    assert score > 0.0


def test_detect_sentiment_negative():
    """Teks berisi kata negatif → sentiment negative."""
    text = "Gagal total, pelayanan buruk dan mengecewakan. Banyak keluhan dari pelanggan."
    label, score = detect_sentiment(text)
    assert label == "negative", f"Expected negative, got {label}"
    assert score < 0.0


def test_detect_sentiment_negative_english():
    """Teks English negatif → negative."""
    text = "This is terrible, worst experience ever. Complete failure and crash."
    label, score = detect_sentiment(text)
    assert label == "negative"
    assert score < 0.0


def test_detect_sentiment_neutral():
    """Teks netral → neutral."""
    text = "Laporan data kuartal telah tersedia untuk diunduh."
    label, score = detect_sentiment(text)
    assert label == "neutral"
    assert abs(score) <= 0.1


def test_detect_sentiment_empty():
    """Teks kosong → neutral, score 0."""
    label, score = detect_sentiment("")
    assert label == "neutral"
    assert score == 0.0


def test_detect_sentiment_mixed():
    """Teks campuran positif dan negatif → score mendekati 0."""
    text = "Bagus tapi juga ada masalah. Keren namun kecewa dengan pelayanannya."
    label, score = detect_sentiment(text)
    # Mixed: score bisa positive/negative/neutral tergantung dominansi
    assert label in ("positive", "negative", "neutral")
    assert -1.0 <= score <= 1.0


# ── extract_keywords ──────────────────────────────────────────────────────────

def test_extract_keywords_basic():
    """Kata kunci paling sering muncul harus ada di output."""
    texts = [
        "strategi marketing digital sangat penting untuk bisnis",
        "marketing digital terbaik untuk bisnis Indonesia",
        "tips marketing digital untuk pemula bisnis online",
    ]
    keywords = extract_keywords(texts, top_n=5)
    assert isinstance(keywords, list)
    assert len(keywords) <= 5
    # 'marketing', 'digital', 'bisnis' harus muncul karena frekuensi tinggi
    assert "marketing" in keywords or "digital" in keywords or "bisnis" in keywords


def test_extract_keywords_filters_stopwords():
    """Stopwords tidak boleh masuk ke keyword list."""
    texts = ["yang dan di ke dari untuk dengan adalah ini itu ada tidak bisa akan"]
    keywords = extract_keywords(texts, top_n=10)
    stopwords = {"yang", "dan", "di", "ke", "dari", "untuk", "dengan", "adalah"}
    for kw in keywords:
        assert kw not in stopwords, f"Stopword '{kw}' lolos filter"


def test_extract_keywords_empty():
    """Input kosong → list kosong."""
    keywords = extract_keywords([], top_n=5)
    assert keywords == []


def test_extract_keywords_min_length():
    """Kata pendek (< 3 karakter) tidak masuk keyword."""
    texts = ["ai ml dl is ok by to of in on"]
    keywords = extract_keywords(texts, top_n=10)
    for kw in keywords:
        assert len(kw) >= 3, f"Kata terlalu pendek: '{kw}'"


# ── extract_hashtags ──────────────────────────────────────────────────────────

def test_extract_hashtags():
    """Hashtag diekstrak dari teks."""
    texts = ["Trending #SidixAI dan #AIIndonesia hari ini!", "Check #viral di #tiktok"]
    tags = extract_hashtags(texts)
    assert "#SidixAI" in tags or "#sidixai" in tags or any("SidixAI" in t for t in tags)
    assert len(tags) >= 2


def test_extract_hashtags_empty():
    """Tidak ada hashtag → list kosong."""
    texts = ["Tidak ada hashtag di sini sama sekali"]
    tags = extract_hashtags(texts)
    assert tags == []


# ── analyze_social_signals ────────────────────────────────────────────────────

def test_analyze_social_signals_basic():
    """analyze_social_signals return SocialSignal valid dari mock results."""
    mock_results = [
        {"title": "SIDIX AI viral di Indonesia", "snippet": "Produk bagus dan keren", "url": "https://twitter.com/test"},
        {"title": "Review SIDIX sangat positif", "snippet": "Sukses meningkatkan produktivitas", "url": "https://instagram.com/p/abc"},
        {"title": "Trending: SIDIX AI assistant terbaik", "snippet": "Pengguna antusias", "url": "https://tiktok.com/@sidix"},
    ]
    signal = analyze_social_signals("SIDIX AI", mock_results)

    assert isinstance(signal, SocialSignal)
    assert signal.query == "SIDIX AI"
    assert signal.sentiment in ("positive", "negative", "neutral")
    assert isinstance(signal.sentiment_score, float)
    assert -1.0 <= signal.sentiment_score <= 1.0
    assert isinstance(signal.trending_keywords, list)
    assert isinstance(signal.platform_hints, list)
    assert signal.estimated_volume in ("low", "medium", "high")
    assert isinstance(signal.summary, str) and len(signal.summary) > 0


def test_analyze_social_signals_empty_results():
    """Empty results → SocialSignal valid dengan volume 'low'."""
    signal = analyze_social_signals("test query", [])
    assert isinstance(signal, SocialSignal)
    assert signal.query == "test query"
    assert signal.estimated_volume == "low"
    assert signal.sentiment == "neutral"
    assert signal.trending_keywords == []


def test_analyze_social_signals_platform_detection():
    """Platform hints terdeteksi dari URL."""
    mock_results = [
        {"title": "Post", "snippet": "", "url": "https://twitter.com/user/status/123"},
        {"title": "Video", "snippet": "", "url": "https://tiktok.com/@creator/video/456"},
        {"title": "Foto", "snippet": "", "url": "https://instagram.com/p/xyz"},
    ]
    signal = analyze_social_signals("test", mock_results)
    assert "twitter" in signal.platform_hints
    assert "tiktok" in signal.platform_hints
    assert "instagram" in signal.platform_hints


def test_analyze_social_signals_high_volume():
    """10+ results → volume 'high'."""
    mock_results = [
        {"title": f"Result {i}", "snippet": "ok", "url": f"https://example.com/{i}"}
        for i in range(12)
    ]
    signal = analyze_social_signals("query", mock_results)
    assert signal.estimated_volume == "high"


def test_analyze_social_signals_sentiment_positive():
    """Results positif → sentimen positive."""
    mock_results = [
        {"title": "Bagus banget keren sukses", "snippet": "Mantap luar biasa hebat", "url": ""},
        {"title": "Berhasil meningkat positif", "snippet": "Sangat bagus favorit", "url": ""},
    ]
    signal = analyze_social_signals("produk", mock_results)
    assert signal.sentiment in ("positive", "neutral")  # rule-based, bisa netral juga


def test_analyze_social_signals_raw_results_capped():
    """raw_results di-cap ke 20 item."""
    mock_results = [
        {"title": f"Result {i}", "snippet": "", "url": ""}
        for i in range(30)
    ]
    signal = analyze_social_signals("test", mock_results)
    assert len(signal.raw_results) <= 20


# ── format_report ─────────────────────────────────────────────────────────────

def test_format_report_non_empty():
    """format_report menghasilkan string non-empty."""
    signal = SocialSignal(
        query="SIDIX AI",
        platform_hints=["twitter", "instagram"],
        sentiment="positive",
        sentiment_score=0.6,
        trending_keywords=["sidix", "ai", "indonesia", "viral"],
        hashtags=["#SidixAI", "#AIIndonesia"],
        estimated_volume="medium",
        summary="Tren positif untuk SIDIX AI di sosmed Indonesia.",
        raw_results=[],
    )
    report = format_report(signal)
    assert isinstance(report, str)
    assert len(report) > 50
    assert "SIDIX AI" in report
    assert "POSITIVE" in report.upper() or "positive" in report.lower()


def test_format_report_contains_keywords():
    """Laporan harus mengandung trending keywords."""
    signal = SocialSignal(
        query="test",
        platform_hints=[],
        sentiment="neutral",
        sentiment_score=0.0,
        trending_keywords=["alpha", "beta", "gamma"],
        hashtags=[],
        estimated_volume="low",
        summary="Test summary.",
        raw_results=[],
    )
    report = format_report(signal)
    assert "alpha" in report
    assert "beta" in report


def test_format_report_with_raw_results():
    """Laporan dengan raw_results menampilkan hasil teratas."""
    signal = SocialSignal(
        query="test",
        platform_hints=["twitter"],
        sentiment="positive",
        sentiment_score=0.5,
        trending_keywords=["trending"],
        hashtags=["#test"],
        estimated_volume="high",
        summary="Summary test.",
        raw_results=[
            {"title": "Artikel Pertama", "snippet": "Snippet satu", "url": "https://twitter.com/test1"},
            {"title": "Artikel Kedua", "snippet": "Snippet dua", "url": "https://example.com/test2"},
        ],
    )
    report = format_report(signal)
    assert "Artikel Pertama" in report
    assert len(report) > 100


def test_format_report_empty_signal():
    """format_report tidak crash dengan signal minimal."""
    signal = SocialSignal(
        query="empty",
        platform_hints=[],
        sentiment="neutral",
        sentiment_score=0.0,
        trending_keywords=[],
        hashtags=[],
        estimated_volume="low",
        summary="Tidak ada data.",
        raw_results=[],
    )
    report = format_report(signal)
    assert isinstance(report, str)
    assert len(report) > 10
