# -*- coding: utf-8 -*-
"""
Snippet: Query RAG brain_qa secara lokal menggunakan httpx.

Dependensi:
    pip install httpx

Cara menggunakan:
    python python_rag_query.py

Pastikan brain_qa berjalan di port 8000 sebelum menjalankan snippet ini.
"""

import json
import sys

import httpx

# ── Konfigurasi ────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8000"   # URL brain_qa (own-stack, bukan vendor API)
TIMEOUT = 30.0                       # Detik


# ── Client sederhana ───────────────────────────────────────────────────────────
class BrainQAClient:
    """Client minimal untuk brain_qa RAG endpoint."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def query(
        self,
        question: str,
        persona: str = "general",
        top_k: int = 5,
    ) -> dict:
        """
        Kirim pertanyaan ke brain_qa dan kembalikan respons lengkap.

        Args:
            question: Pertanyaan dalam bahasa natural
            persona:  Persona/domain (e.g. "fiqh", "ushul", "general")
            top_k:    Jumlah dokumen yang diambil dari indeks BM25

        Returns:
            dict dengan kunci: answer, citations, persona, query
        """
        payload = {
            "query": question,
            "persona": persona,
            "top_k": top_k,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/qa",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    def health(self) -> dict:
        """Cek status brain_qa."""
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()


# ── Contoh penggunaan ──────────────────────────────────────────────────────────
def main() -> None:
    client = BrainQAClient()

    # 1. Health check
    print("=== Health Check ===")
    try:
        health = client.health()
        print(json.dumps(health, ensure_ascii=False, indent=2))
    except httpx.ConnectError:
        print("ERROR: brain_qa tidak berjalan di", BASE_URL)
        sys.exit(1)

    # 2. Query dengan persona fiqh
    print("\n=== RAG Query ===")
    result = client.query(
        question="Apa hukum zakat fitrah menurut mazhab Syafi'i?",
        persona="fiqh",
        top_k=3,
    )

    print("Jawaban:", result.get("answer", "—"))
    print("\nSitasi:")
    for i, cite in enumerate(result.get("citations", []), start=1):
        # Setiap sitasi berisi: source, score, excerpt
        print(f"  [{i}] {cite.get('source', '?')} (skor: {cite.get('score', 0):.3f})")
        print(f"      {cite.get('excerpt', '')[:120]}...")


if __name__ == "__main__":
    main()
