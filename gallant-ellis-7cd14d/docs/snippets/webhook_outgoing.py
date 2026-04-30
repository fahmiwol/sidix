# -*- coding: utf-8 -*-
"""
OPSIONAL — Contoh webhook outgoing SIDIX.

Snippet ini menunjukkan cara POST event SIDIX (e.g. "new_corpus_entry",
"qa_answer") ke URL webhook eksternal dengan:
  - Retry logic: 3 percobaan dengan exponential backoff
  - Tanda tangan HMAC-SHA256 (header X-SIDIX-Signature)
  - Menggunakan httpx (bukan vendor API)

CATATAN: CONTOH SAJA — bukan production code langsung.
         Sesuaikan webhook_url dan secret sebelum digunakan.

Dependensi:
    pip install httpx

Cara menggunakan:
    python webhook_outgoing.py
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Konfigurasi default (ganti dengan nilai nyata) ────────────────────────────
DEFAULT_WEBHOOK_URL = "https://hooks.example.com/sidix/notify"
DEFAULT_SECRET = "ganti-dengan-secret-kuat-min-32-karakter"
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]   # Exponential backoff dalam detik
TIMEOUT_SECONDS = 10.0

# Tipe event SIDIX yang dikenal
VALID_EVENT_TYPES = {
    "new_corpus_entry",   # Dokumen baru masuk corpus
    "qa_answer",          # Jawaban QA selesai diproses
    "ledger_verified",    # Ledger berhasil diverifikasi
    "index_rebuilt",      # Indeks BM25 dibangun ulang
    "agent_tool_call",    # ReAct agent memanggil tool
}


# ── HMAC-SHA256 signature ─────────────────────────────────────────────────────
def compute_signature(payload_bytes: bytes, secret: str) -> str:
    """
    Hitung tanda tangan HMAC-SHA256.

    Format: "sha256=<hex_digest>" — kompatibel dengan konvensi GitHub/Stripe.
    Penerima harus memverifikasi dengan secret yang sama.
    """
    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"sha256={digest}"


# ── Builder payload ───────────────────────────────────────────────────────────
def build_payload(event_type: str, data: dict[str, Any]) -> dict:
    """Bangun payload event SIDIX standar."""
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Event tidak valid: '{event_type}'. Pilih: {sorted(VALID_EVENT_TYPES)}"
        )
    return {
        "event_type": event_type,
        "source": "sidix",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "data": data,
    }


# ── Pengirim webhook dengan retry ─────────────────────────────────────────────
def send_webhook(
    event_type: str,
    data: dict[str, Any],
    webhook_url: str = DEFAULT_WEBHOOK_URL,
    secret: str = DEFAULT_SECRET,
    max_retries: int = MAX_RETRIES,
    timeout: float = TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """
    Kirim event ke webhook eksternal.

    - Retry 3 kali dengan exponential backoff (1s, 2s, 4s)
    - Header X-SIDIX-Signature berisi HMAC-SHA256

    Returns:
        dict: success, attempts, status_code, error
    """
    payload = build_payload(event_type, data)
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    signature = compute_signature(payload_bytes, secret)

    headers = {
        "Content-Type": "application/json",
        "X-SIDIX-Event": event_type,
        "X-SIDIX-Signature": signature,
        "X-SIDIX-Timestamp": payload["timestamp"],
        "User-Agent": "SIDIX-Webhook/1.0",
    }

    last_error: Optional[str] = None
    last_status: Optional[int] = None

    for attempt in range(1, max_retries + 1):
        logger.info(
            "Webhook '%s' -> %s (percobaan %d/%d)",
            event_type, webhook_url, attempt, max_retries,
        )
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(webhook_url, content=payload_bytes, headers=headers)
                last_status = resp.status_code
                if resp.is_success:
                    logger.info("Berhasil: HTTP %d", resp.status_code)
                    return {"success": True, "attempts": attempt,
                            "status_code": resp.status_code, "error": None}
                last_error = f"HTTP {resp.status_code}"
                logger.warning("Gagal: %s", last_error)

        except httpx.TimeoutException:
            last_error = f"Timeout {timeout}s"
            logger.warning("Percobaan %d timeout", attempt)
        except httpx.ConnectError as exc:
            last_error = str(exc)
            logger.warning("Koneksi gagal: %s", exc)
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            logger.error("Error: %s", exc)

        if attempt < max_retries:
            delay = RETRY_DELAYS[attempt - 1] if attempt - 1 < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
            logger.info("Retry dalam %.1fs ...", delay)
            time.sleep(delay)

    logger.error("Webhook GAGAL setelah %d percobaan: %s", max_retries, last_error)
    return {"success": False, "attempts": max_retries,
            "status_code": last_status, "error": last_error}


# ── Helper per event ──────────────────────────────────────────────────────────
def notify_new_corpus_entry(doc_id: str, title: str, source: str, **kw) -> dict:
    """Kirim notifikasi dokumen baru masuk corpus."""
    return send_webhook("new_corpus_entry",
                        {"doc_id": doc_id, "title": title, "source": source}, **kw)


def notify_qa_answer(query: str, persona: str, answer_preview: str,
                     citation_count: int, **kw) -> dict:
    """Kirim notifikasi jawaban QA selesai."""
    return send_webhook("qa_answer", {
        "query": query[:200], "persona": persona,
        "answer_preview": answer_preview[:300], "citation_count": citation_count,
    }, **kw)


# ── Contoh penggunaan ─────────────────────────────────────────────────────────
def main() -> None:
    print("=== OPSIONAL: Webhook Outgoing SIDIX (contoh) ===\n")

    # Preview tanda tangan tanpa HTTP call
    payload = build_payload("qa_answer", {
        "query": "Apa hukum zakat fitrah?",
        "persona": "fiqh",
        "citation_count": 3,
    })
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    sig = compute_signature(payload_bytes, DEFAULT_SECRET)
    print("Contoh signature:", sig)
    print("Payload preview:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    print("\nCatatan: Panggil send_webhook() dengan URL nyata untuk pengiriman sungguhan.")


if __name__ == "__main__":
    main()
