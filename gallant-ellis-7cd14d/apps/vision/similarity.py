"""
Image-Text Similarity — Projek Badar Task 97 (G3)
Similarity gambar-teks untuk retrieval hybrid.
Status: STUB — wire ke CLIP atau vision-language model lokal.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Hasil perhitungan similarity gambar-teks."""
    score: float
    image_path: str
    text: str
    model: str = "stub"


def compute_similarity(image_path: str, text: str) -> SimilarityResult:
    """
    Hitung similarity antara gambar dan teks query.

    Args:
        image_path: Path ke file gambar.
        text: Teks query untuk dibandingkan.

    Returns:
        SimilarityResult dengan skor similarity (0.0–1.0).

    Notes:
        # TODO: load CLIP model, compute image embedding + text embedding, cosine similarity
        # Contoh wire ke CLIP lokal:
        #   import torch
        #   import clip
        #   model, preprocess = clip.load("ViT-B/32", device="cpu")
        #   image = preprocess(Image.open(image_path)).unsqueeze(0)
        #   text_tokens = clip.tokenize([text])
        #   with torch.no_grad():
        #       image_features = model.encode_image(image)
        #       text_features = model.encode_text(text_tokens)
        #       similarity = torch.cosine_similarity(image_features, text_features).item()
        # Alternatif: sentence-transformers dengan CLIP-ViT lokal
    """
    logger.warning(
        "[STUB] compute_similarity: model CLIP belum terpasang. "
        "Mengembalikan skor dummy 0.5 untuk gambar='%s', teks='%s'.",
        image_path,
        text[:50] + "..." if len(text) > 50 else text,
    )
    return SimilarityResult(
        score=0.5,
        model="stub",
        image_path=image_path,
        text=text,
    )


def rank_by_similarity(
    image_paths: list[str],
    query_text: str,
) -> list[SimilarityResult]:
    """
    Urutkan daftar gambar berdasarkan similarity dengan teks query.

    Args:
        image_paths: Daftar path gambar yang akan dibandingkan.
        query_text: Teks query sebagai referensi similarity.

    Returns:
        Daftar SimilarityResult diurutkan dari skor tertinggi ke terendah.

    Notes:
        Stub: semua gambar mendapat skor 0.5 (tidak ada ranking bermakna).
        # TODO: wire ke compute_similarity yang sesungguhnya,
        #       lalu sort by score descending.
    """
    logger.warning(
        "[STUB] rank_by_similarity: %d gambar, semua mendapat skor stub 0.5. "
        "Ranking tidak bermakna sampai model CLIP aktif.",
        len(image_paths),
    )
    results = [
        compute_similarity(img_path, query_text)
        for img_path in image_paths
    ]
    # Urutkan descending; dengan skor stub identik, urutan input dipertahankan
    results.sort(key=lambda r: r.score, reverse=True)
    return results
