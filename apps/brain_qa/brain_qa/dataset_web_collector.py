"""
dataset_web_collector.py — SIDIX Web Dataset Collector (Legal Sources Only)
===========================================================================
Collect image dataset metadata dari sumber web yang legal dan ethical.

Sumber yang didukung:
  1. Unsplash API       — Free photo API (Unsplash License, free for commercial use)
  2. Pexels API         — Free photo/video API (Pexels License, free for commercial use)
  3. Wikimedia Commons  — CC-licensed images (CC0, CC-BY, CC-BY-SA)
  4. LAION-5B metadata  — Open metadata index (URL + caption, no images downloaded)

Sumber yang DITOLAK (legal risk tinggi):
  - Shutterstock, Adobe Stock, Getty Images, iStock — copyrighted, ToS violation
  - Instagram scraping — ToS Meta violation, bisa kena ban/lawsuit
  - Canva — proprietary content, ToS violation

Legal basis:
  - US Copyright Office Report May 2025: unauthorized copying = infringement
  - Getty vs Stability AI (2025): landmark copyright case
  - LAION-5B: metadata-only distribution to minimize liability

Research notes:
  - 319 web dataset source analysis
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any


# ── Constants ─────────────────────────────────────────────────────────────────

UNSPLASH_API_URL = "https://api.unsplash.com"
PEXELS_API_URL = "https://api.pexels.com/v1"
WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
LAION_METADATA_BASE = "https://laion.ai/blog/laion-5b/"

# Safety limits
MAX_RESULTS_PER_CALL = 30
MAX_TOTAL_RESULTS = 1000


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


def _get_env_key(name: str) -> str | None:
    return os.environ.get(name) or None


def _http_get(url: str, headers: dict | None = None, timeout: int = 15) -> dict:
    """Simple HTTP GET with JSON response."""
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── 1. Unsplash API ───────────────────────────────────────────────────────────


def search_unsplash(
    query: str,
    per_page: int = 20,
    orientation: str | None = None,
    order_by: str = "relevant",
) -> dict:
    """Search photos via Unsplash API (free tier: 50 req/hour).

    License: Unsplash License — free to use for commercial and non-commercial purposes.
    Attribution appreciated but not required.
    """
    api_key = _get_env_key("UNSPLASH_ACCESS_KEY")
    if not api_key:
        return _fallback(
            "UNSPLASH_ACCESS_KEY tidak di-set. Daftar gratis di https://unsplash.com/developers"
        )

    if per_page > MAX_RESULTS_PER_CALL:
        per_page = MAX_RESULTS_PER_CALL

    params = {
        "query": query,
        "per_page": per_page,
        "order_by": order_by,
    }
    if orientation:
        params["orientation"] = orientation

    url = f"{UNSPLASH_API_URL}/search/photos?{urllib.parse.urlencode(params)}"
    headers = {"Authorization": f"Client-ID {api_key}"}

    try:
        data = _http_get(url, headers)
        results = data.get("results", [])
        photos = []
        for p in results:
            photos.append({
                "id": p.get("id"),
                "source": "unsplash",
                "source_url": p.get("links", {}).get("html"),
                "image_url": p.get("urls", {}).get("regular"),
                "thumb_url": p.get("urls", {}).get("small"),
                "width": p.get("width"),
                "height": p.get("height"),
                "description": p.get("description") or p.get("alt_description") or "",
                "author": p.get("user", {}).get("name"),
                "author_url": p.get("user", {}).get("links", {}).get("html"),
                "license": "Unsplash License (free to use)",
                "color": p.get("color"),
                "created_at": p.get("created_at"),
                "tags": [t.get("title") for t in p.get("tags", []) if t.get("title")],
            })
        return _ok({
            "query": query,
            "total": data.get("total", 0),
            "total_pages": data.get("total_pages", 0),
            "photos": photos,
            "license_note": "Unsplash License: free to use, attribution appreciated",
        })
    except Exception as exc:
        return _fallback(f"Unsplash API error: {exc}")


def get_unsplash_photo(photo_id: str) -> dict:
    """Get single photo metadata from Unsplash."""
    api_key = _get_env_key("UNSPLASH_ACCESS_KEY")
    if not api_key:
        return _fallback("UNSPLASH_ACCESS_KEY tidak di-set")

    url = f"{UNSPLASH_API_URL}/photos/{photo_id}?client_id={api_key}"
    try:
        p = _http_get(url)
        return _ok({
            "id": p.get("id"),
            "source": "unsplash",
            "image_url": p.get("urls", {}).get("regular"),
            "width": p.get("width"),
            "height": p.get("height"),
            "description": p.get("description") or p.get("alt_description") or "",
            "author": p.get("user", {}).get("name"),
            "license": "Unsplash License (free to use)",
            "downloads": p.get("downloads"),
            "likes": p.get("likes"),
        })
    except Exception as exc:
        return _fallback(f"Unsplash photo error: {exc}")


# ── 2. Pexels API ─────────────────────────────────────────────────────────────


def search_pexels(
    query: str,
    per_page: int = 20,
    orientation: str | None = None,
    color: str | None = None,
) -> dict:
    """Search photos via Pexels API (free tier: 200 req/hour, 20k req/month).

    License: Pexels License — free to use and modify, no attribution required.
    """
    api_key = _get_env_key("PEXELS_API_KEY")
    if not api_key:
        return _fallback(
            "PEXELS_API_KEY tidak di-set. Daftar gratis di https://www.pexels.com/api/"
        )

    if per_page > MAX_RESULTS_PER_CALL:
        per_page = MAX_RESULTS_PER_CALL

    params = {"query": query, "per_page": per_page}
    if orientation:
        params["orientation"] = orientation
    if color:
        params["color"] = color

    url = f"{PEXELS_API_URL}/search?{urllib.parse.urlencode(params)}"
    headers = {"Authorization": api_key}

    try:
        data = _http_get(url, headers)
        photos = []
        for p in data.get("photos", []):
            photos.append({
                "id": p.get("id"),
                "source": "pexels",
                "source_url": p.get("url"),
                "image_url": p.get("src", {}).get("large"),
                "thumb_url": p.get("src", {}).get("small"),
                "width": p.get("width"),
                "height": p.get("height"),
                "description": p.get("alt") or "",
                "author": p.get("photographer"),
                "author_url": p.get("photographer_url"),
                "license": "Pexels License (free to use)",
                "avg_color": p.get("avg_color"),
            })
        return _ok({
            "query": query,
            "total": data.get("total_results", 0),
            "page": data.get("page", 1),
            "photos": photos,
            "license_note": "Pexels License: free to use and modify, no attribution required",
        })
    except Exception as exc:
        return _fallback(f"Pexels API error: {exc}")


# ── 3. Wikimedia Commons API ──────────────────────────────────────────────────


def search_wikimedia(
    query: str,
    limit: int = 20,
    file_type: str = "image",
    license_filter: str | None = None,
) -> dict:
    """Search CC-licensed media dari Wikimedia Commons.

    License: Varies by file — CC0, CC-BY, CC-BY-SA (filterable).
    All files on Commons are freely licensed for reuse.
    """
    if limit > MAX_RESULTS_PER_CALL:
        limit = MAX_RESULTS_PER_CALL

    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "srnamespace": 6,  # File namespace
    }

    url = f"{WIKIMEDIA_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        data = _http_get(url)
        search_results = data.get("query", {}).get("search", [])
        files = []
        for s in search_results:
            title = s.get("title", "")
            if not title.startswith("File:"):
                continue
            # Build file page URL
            file_page = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
            # Direct image URL (thumbnail)
            filename = title.replace("File:", "").replace(" ", "_")
            thumb_url = f"https://upload.wikimedia.org/wikipedia/commons/thumb/{filename[0]}/{filename[:2]}/{filename}/320px-{filename}"
            files.append({
                "id": s.get("pageid"),
                "source": "wikimedia",
                "title": title,
                "source_url": file_page,
                "thumb_url": thumb_url,
                "description": s.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                "license": license_filter or "CC-licensed (check file page)",
                "size_bytes": s.get("size"),
                "word_count": s.get("wordcount"),
            })
        return _ok({
            "query": query,
            "total": data.get("query", {}).get("searchinfo", {}).get("totalhits", 0),
            "files": files,
            "license_note": "Wikimedia Commons: all files freely licensed (CC0/CC-BY/CC-BY-SA). Check individual file page.",
        })
    except Exception as exc:
        return _fallback(f"Wikimedia API error: {exc}")


def get_wikimedia_file_info(title: str) -> dict:
    """Get detailed file info including exact license dari Wikimedia Commons."""
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
    }
    url = f"{WIKIMEDIA_API_URL}?{urllib.parse.urlencode(params)}"
    try:
        data = _http_get(url)
        pages = data.get("query", {}).get("pages", {})
        for page_id, page in pages.items():
            info = page.get("imageinfo", [{}])[0]
            meta = info.get("extmetadata", {})
            return _ok({
                "title": title,
                "source": "wikimedia",
                "image_url": info.get("url"),
                "width": info.get("width"),
                "height": info.get("height"),
                "mime": info.get("mime"),
                "size_bytes": info.get("size"),
                "license": meta.get("LicenseShortName", {}).get("value", "Unknown"),
                "license_url": meta.get("LicenseUrl", {}).get("value"),
                "artist": meta.get("Artist", {}).get("value", "")[:200],
                "description": meta.get("ImageDescription", {}).get("value", "")[:500],
                "usage_terms": meta.get("UsageTerms", {}).get("value", ""),
            })
        return _fallback("File not found")
    except Exception as exc:
        return _fallback(f"Wikimedia file info error: {exc}")


# ── 4. LAION-5B Metadata Reference ────────────────────────────────────────────


def get_laion_info() -> dict:
    """Return LAION-5B dataset information and download pointers.

    LAION-5B does not distribute actual images — only metadata (URL, caption, CLIP embeddings).
    This minimizes copyright liability per LAION's design.
    """
    return _ok({
        "dataset": "LAION-5B",
        "description": "5.85 billion CLIP-filtered image-text pairs",
        "license": "CC-BY 4.0 (metadata only)",
        "subsets": [
            {
                "name": "LAION-2B-en",
                "size": "2.32 billion entries",
                "language": "English",
                "use_case": "Primary training corpus for SD, CLIP, GLIDE",
            },
            {
                "name": "LAION-2B-multi",
                "size": "2.26 billion entries",
                "language": "Multi-language",
                "use_case": "Multilingual vision-language training",
            },
            {
                "name": "LAION-1B-nolang",
                "size": "1.27 billion entries",
                "language": "Undetected",
                "use_case": "General pretraining",
            },
            {
                "name": "LAION-Aesthetics",
                "size": "~1.2 billion entries",
                "filter": "Aesthetic score >= 6 (LAP)",
                "use_case": "High-quality image generation training",
                "caveat": "LAP has documented bias (western art, gender imbalance)",
            },
            {
                "name": "LAION-High-Resolution",
                "size": "170 million entries",
                "filter": "Width >= 1024 or height >= 1024",
                "use_case": "Super-resolution model training",
            },
        ],
        "download": {
            "metadata": "https://laion.ai/blog/laion-5b/",
            "clip_embeddings": "https://github.com/rom1504/clip-retrieval",
            "aesthetic_predictor": "https://github.com/christophschuhmann/improved-aesthetic-predictor",
        },
        "caveats": [
            "LAION-5B contains NSFW content (punsafe score available)",
            "Web-scraped nature = inherent societal bias",
            "Watermark detection score available per entry",
            "Must download actual images yourself from URLs (copyright responsibility shifts to downloader)",
        ],
        "legal_note": "LAION distributes metadata only. Downloading images from URLs may still infringe copyright if the original is copyrighted. Use with caution.",
    })


# ── 5. Unified Search ─────────────────────────────────────────────────────────


def search_all(
    query: str,
    sources: list[str] | None = None,
    per_source: int = 10,
) -> dict:
    """Search across all configured legal sources."""
    if sources is None:
        sources = ["unsplash", "pexels", "wikimedia"]

    results = {}
    errors = []

    for src in sources:
        try:
            if src == "unsplash":
                r = search_unsplash(query, per_page=per_source)
            elif src == "pexels":
                r = search_pexels(query, per_page=per_source)
            elif src == "wikimedia":
                r = search_wikimedia(query, limit=per_source)
            else:
                errors.append(f"Unknown source: {src}")
                continue
            results[src] = r
        except Exception as exc:
            errors.append(f"{src}: {exc}")
            results[src] = _fallback(str(exc))

    total_photos = sum(
        len(r.get("data", {}).get("photos", []))
        for r in results.values()
        if r.get("ok")
    )
    total_files = sum(
        len(r.get("data", {}).get("files", []))
        for r in results.values()
        if r.get("ok")
    )

    return _ok({
        "query": query,
        "sources": sources,
        "results": results,
        "total_items": total_photos + total_files,
        "errors": errors if errors else None,
        "legal_summary": (
            "All sources used are freely licensed or public domain. "
            "Unsplash/Pexels = free commercial use. Wikimedia = CC-licensed. "
            "No copyrighted stock photos scraped."
        ),
    })


# ── 6. Dataset DNA Analysis ───────────────────────────────────────────────────


def analyze_dataset_dna(entries: list[dict]) -> dict:
    """Analyze dataset DNA (characteristics, quality, bias indicators).

    Input: list of entries dari search_unsplash, search_pexels, search_wikimedia, atau scan_folder.
    Output: DNA profile untuk memutuskan apakah dataset cocok untuk LoRA training.
    """
    if not entries:
        return _fallback("No entries to analyze")

    widths = [e.get("width") for e in entries if e.get("width")]
    heights = [e.get("height") for e in entries if e.get("height")]
    sizes = [e.get("size_bytes") for e in entries if e.get("size_bytes")]

    # Resolution distribution
    resolutions = {}
    for w, h in zip(widths, heights):
        if w and h:
            mp = round((w * h) / 1_000_000, 1)
            resolutions[f"{mp}MP"] = resolutions.get(f"{mp}MP", 0) + 1

    # Aspect ratio distribution
    ratios = {}
    for w, h in zip(widths, heights):
        if w and h:
            r = round(w / h, 2)
            bucket = "square" if 0.9 <= r <= 1.1 else "landscape" if r > 1.1 else "portrait"
            ratios[bucket] = ratios.get(bucket, 0) + 1

    # Source distribution
    sources = {}
    for e in entries:
        src = e.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    # License distribution
    licenses = {}
    for e in entries:
        lic = e.get("license", "unknown")
        licenses[lic] = licenses.get(lic, 0) + 1

    # Quality heuristic
    high_res = sum(1 for w, h in zip(widths, heights) if w and h and w >= 1024 and h >= 1024)
    total_with_dim = len(widths)
    quality_score = round(high_res / total_with_dim * 100, 1) if total_with_dim else 0

    # Caption/description coverage
    with_caption = sum(1 for e in entries if e.get("description") or e.get("tags"))
    caption_coverage = round(with_caption / len(entries) * 100, 1) if entries else 0

    # Diversity heuristic (simple: count unique authors)
    authors = set()
    for e in entries:
        a = e.get("author") or e.get("photographer") or e.get("artist")
        if a:
            authors.add(a)
    diversity_score = min(100, round(len(authors) / len(entries) * 100, 1)) if entries else 0

    # Bias risk flags
    bias_flags = []
    if diversity_score < 30:
        bias_flags.append("LOW_AUTHOR_DIVERSITY — risk of style homogenization")
    if caption_coverage < 50:
        bias_flags.append("LOW_CAPTION_COVERAGE — hurts text-to-image training quality")
    if quality_score < 30:
        bias_flags.append("LOW_RESOLUTION_DOMINANT — may need upscaling before training")

    return _ok({
        "total_entries": len(entries),
        "resolution_distribution": resolutions,
        "aspect_ratio_distribution": ratios,
        "source_distribution": sources,
        "license_distribution": licenses,
        "quality_score": {
            "high_res_percentage": quality_score,
            "high_res_count": high_res,
            "total_with_dimensions": total_with_dim,
        },
        "caption_coverage": {
            "percentage": caption_coverage,
            "with_caption": with_caption,
        },
        "diversity_score": {
            "unique_authors": len(authors),
            "diversity_percentage": diversity_score,
        },
        "bias_risk_flags": bias_flags if bias_flags else ["None detected"],
        "lora_suitability": {
            "recommended": quality_score >= 50 and caption_coverage >= 60 and diversity_score >= 30,
            "notes": (
                "Good for LoRA if: >=50% high-res, >=60% with captions, >=30% author diversity. "
                "LAION-5B metadata can supplement captions via CLIP retrieval."
            ),
        },
    })
