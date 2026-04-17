"""
channel_adapters.py — SIDIX Channel Adapter Layer
====================================================
Bridge antara SIDIX brain_qa dan berbagai channel komunikasi:
  - WhatsApp Business API (Meta Cloud API + Baileys/unofficial)
  - Telegram Bot API
  - Generic HTTP webhook

Pola arsitektur diambil dari:
  - D:\\WA API GATeway\\cosmic-architect-os  (NestJS, Baileys + Meta dual-engine)
  - D:\\bot gateway  (Python FastAPI + RQ worker, agent multi-type)
  - D:\\Chat Bot Agent  (init-db schema pattern)
  - D:\\artifact  (TTS app, Next.js API routes)

Semua dependency eksternal (httpx, requests) di-import dengan try/except
agar modul tetap dapat di-import tanpa error walau package belum terpasang.

Usage minimal:
    from brain_qa.channel_adapters import GatewayRouter
    router = GatewayRouter()
    result = await router.route("whatsapp", payload)
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency: httpx (preferred) / requests (fallback)
# ---------------------------------------------------------------------------
try:
    import httpx  # type: ignore
    _HTTP_CLIENT = "httpx"
except ImportError:
    httpx = None  # type: ignore
    _HTTP_CLIENT = None

try:
    import requests  # type: ignore
    if _HTTP_CLIENT is None:
        _HTTP_CLIENT = "requests"
except ImportError:
    requests = None  # type: ignore


# ===========================================================================
# Data Types
# ===========================================================================

@dataclass
class InboundMessage:
    """Pesan masuk yang sudah dinormalisasi dari channel manapun."""
    channel: str           # "whatsapp" | "telegram" | "generic"
    sender_id: str         # phone E.164 (WA) atau chat_id string (TG)
    text: str              # teks pesan
    message_id: str = ""   # ID unik dari platform (external ref)
    media_url: str = ""    # URL media jika ada (gambar/dokumen/suara)
    media_type: str = ""   # "image" | "document" | "audio" | "video" | ""
    raw_payload: dict = field(default_factory=dict)  # payload asli dari platform
    timestamp: float = field(default_factory=time.time)


@dataclass
class OutboundMessage:
    """Pesan keluar yang disiapkan oleh adapter untuk dikirim ke platform."""
    channel: str
    recipient_id: str      # phone atau chat_id tujuan
    text: str
    buttons: list[dict] = field(default_factory=list)   # optional quick replies
    media_url: str = ""
    media_type: str = ""
    parse_mode: str = ""   # "HTML" | "Markdown" — khusus Telegram


@dataclass
class SendResult:
    ok: bool
    message_id: str = ""
    error: str = ""
    raw_response: dict = field(default_factory=dict)


# ===========================================================================
# Base Adapter
# ===========================================================================

class BaseAdapter(ABC):
    """Kontrak wajib semua adapter channel."""

    channel_name: str = "base"

    @abstractmethod
    def parse_incoming(self, raw_payload: dict) -> InboundMessage:
        """
        Ubah payload mentah dari webhook platform → InboundMessage yang dinormalisasi.
        Raise ValueError jika payload tidak dikenali / bukan pesan yang bisa diproses.
        """

    @abstractmethod
    def format_message(self, sidix_response: dict) -> OutboundMessage:
        """
        Ubah respons SIDIX (dict dengan key 'answer', 'sources', dll.)
        → OutboundMessage siap kirim ke platform.
        """

    @abstractmethod
    async def send_reply(self, recipient_id: str, message: str, **kwargs: Any) -> SendResult:
        """
        Kirim teks ke platform secara async.
        Implementasi sync juga boleh; wrap dengan asyncio bila perlu.
        """

    def _http_post(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        """
        Helper HTTP POST sync — menggunakan httpx atau requests (whichever tersedia).
        Dipakai oleh adapter yang tidak perlu async penuh.
        """
        hdrs = headers or {"Content-Type": "application/json"}
        if httpx is not None:
            resp = httpx.post(url, json=payload, headers=hdrs, timeout=15)
            resp.raise_for_status()
            return resp.json()
        if requests is not None:
            resp = requests.post(url, json=payload, headers=hdrs, timeout=15)
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError(
            "Tidak ada HTTP client tersedia. Install: pip install httpx"
        )

    async def _http_post_async(self, url: str, payload: dict, headers: dict | None = None) -> dict:
        """Versi async dari _http_post."""
        hdrs = headers or {"Content-Type": "application/json"}
        if httpx is not None:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=payload, headers=hdrs)
                resp.raise_for_status()
                return resp.json()
        # Fallback ke sync dalam executor (thread pool)
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._http_post(url, payload, hdrs))


# ===========================================================================
# WhatsApp Adapter
# ===========================================================================

class WAAdapter(BaseAdapter):
    """
    WhatsApp Business API Gateway adapter.

    Mendukung dua engine (sesuai pola D:\\WA API GATeway):
    - engine="meta"    → Meta Cloud API v21.0 (webhook POST + Graph API send)
    - engine="baileys" → @whiskeysockets/baileys (via sidecar HTTP jika ada)

    Config env yang diharapkan (opsional, bisa di-pass langsung):
      WA_ENGINE         : "meta" | "baileys" | "none"
      META_ACCESS_TOKEN : Bearer token Meta Graph API
      META_PHONE_NUMBER_ID : Phone Number ID dari Meta dashboard
      META_VERIFY_TOKEN : Token verifikasi webhook
      WA_SIDECAR_URL    : URL sidecar Baileys jika pakai mode baileys (default: http://localhost:3100)
    """

    channel_name = "whatsapp"

    def __init__(
        self,
        engine: str = "meta",
        access_token: str = "",
        phone_number_id: str = "",
        verify_token: str = "",
        sidecar_url: str = "http://localhost:3100",
    ):
        import os
        self.engine = engine or os.getenv("WA_ENGINE", "meta")
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN", "")
        self.phone_number_id = phone_number_id or os.getenv("META_PHONE_NUMBER_ID", "")
        self.verify_token = verify_token or os.getenv("META_VERIFY_TOKEN", "")
        self.sidecar_url = sidecar_url or os.getenv("WA_SIDECAR_URL", "http://localhost:3100")

        # Statistik sederhana
        self._stats: dict[str, int] = {
            "messages_in": 0,
            "messages_out": 0,
            "errors": 0,
        }

    # ------------------------------------------------------------------
    # parse_incoming — Meta Cloud API payload
    # ------------------------------------------------------------------
    def parse_incoming(self, raw_payload: dict) -> InboundMessage:
        """
        Parse webhook Meta Cloud API format:
        {
          "entry": [{
            "changes": [{
              "value": {
                "messages": [{
                  "from": "628XXXX",
                  "id": "wamid.xxx",
                  "text": {"body": "halo"},
                  "type": "text"
                }]
              }
            }]
          }]
        }

        Atau Baileys sidecar format (lebih flat):
        {
          "from": "628XXXX@s.whatsapp.net",
          "message_id": "xxx",
          "text": "halo",
          "type": "text"
        }
        """
        self._stats["messages_in"] += 1

        # --- Deteksi format Meta Cloud API ---
        if "entry" in raw_payload:
            return self._parse_meta(raw_payload)

        # --- Deteksi format Baileys sidecar flat ---
        if "from" in raw_payload and "text" in raw_payload:
            return self._parse_baileys(raw_payload)

        raise ValueError(f"WAAdapter: payload tidak dikenali. Keys: {list(raw_payload.keys())}")

    def _parse_meta(self, payload: dict) -> InboundMessage:
        try:
            entries = payload.get("entry", [])
            for entry in entries:
                for change in entry.get("changes", []):
                    messages = change.get("value", {}).get("messages", [])
                    for m in messages:
                        sender = m.get("from", "")
                        msg_id = m.get("id", "")
                        msg_type = m.get("type", "text")
                        text = ""
                        media_url = ""
                        media_type_str = ""

                        if msg_type == "text":
                            text = m.get("text", {}).get("body", "")
                        elif msg_type == "image":
                            media_type_str = "image"
                            media_url = m.get("image", {}).get("link", "")
                            text = m.get("image", {}).get("caption", "")
                        elif msg_type == "document":
                            media_type_str = "document"
                            media_url = m.get("document", {}).get("link", "")
                            text = m.get("document", {}).get("filename", "")
                        elif msg_type == "audio":
                            media_type_str = "audio"
                            media_url = m.get("audio", {}).get("link", "")
                        elif msg_type == "video":
                            media_type_str = "video"
                            media_url = m.get("video", {}).get("link", "")
                            text = m.get("video", {}).get("caption", "")

                        # Normalisasi nomor: hapus @s.whatsapp.net jika ada
                        sender_clean = sender.replace("@s.whatsapp.net", "")
                        if not sender_clean.startswith("+"):
                            sender_clean = "+" + sender_clean

                        return InboundMessage(
                            channel="whatsapp",
                            sender_id=sender_clean,
                            text=text.strip(),
                            message_id=msg_id,
                            media_url=media_url,
                            media_type=media_type_str,
                            raw_payload=m,
                        )
        except (KeyError, IndexError, TypeError) as exc:
            self._stats["errors"] += 1
            raise ValueError(f"WAAdapter Meta parse error: {exc}") from exc

        raise ValueError("WAAdapter: tidak ada message ditemukan dalam payload Meta")

    def _parse_baileys(self, payload: dict) -> InboundMessage:
        """Parse format sidecar Baileys yang lebih flat."""
        sender = payload.get("from", "").replace("@s.whatsapp.net", "")
        if not sender.startswith("+"):
            sender = "+" + sender
        return InboundMessage(
            channel="whatsapp",
            sender_id=sender,
            text=str(payload.get("text", "")).strip(),
            message_id=str(payload.get("message_id", "")),
            media_url=str(payload.get("media_url", "")),
            media_type=str(payload.get("media_type", "")),
            raw_payload=payload,
        )

    # ------------------------------------------------------------------
    # format_message — SIDIX response → OutboundMessage
    # ------------------------------------------------------------------
    def format_message(self, sidix_response: dict) -> OutboundMessage:
        """
        Ubah dict respons SIDIX ke OutboundMessage untuk WA.
        Format SIDIX: {"answer": "...", "sources": [...], "confidence": 0.9}
        """
        answer = sidix_response.get("answer", "")
        sources = sidix_response.get("sources", [])

        # Susun teks dengan sumber jika ada
        if sources:
            source_lines = []
            for s in sources[:3]:  # Batasi 3 sumber agar tidak terlalu panjang
                if isinstance(s, dict):
                    title = s.get("title", s.get("file", ""))
                    if title:
                        source_lines.append(f"• {title}")
                elif isinstance(s, str):
                    source_lines.append(f"• {s}")
            if source_lines:
                answer = answer + "\n\n_Sumber:_\n" + "\n".join(source_lines)

        # WA tidak punya parse mode resmi — pakai plain text
        # Tapi *teks* (italic) dan *bold* bisa di-support WhatsApp native
        recipient = sidix_response.get("recipient_id", "")

        return OutboundMessage(
            channel="whatsapp",
            recipient_id=recipient,
            text=answer,
        )

    # ------------------------------------------------------------------
    # send_reply
    # ------------------------------------------------------------------
    async def send_reply(self, recipient_id: str, message: str, **kwargs: Any) -> SendResult:
        """
        Kirim teks ke nomor WhatsApp.
        - engine=meta    → POST ke Graph API
        - engine=baileys → POST ke sidecar HTTP
        - engine=none    → hanya log (dry-run / test)
        """
        if self.engine == "none":
            logger.info("[WAAdapter DRY-RUN] → %s: %s", recipient_id, message[:80])
            self._stats["messages_out"] += 1
            return SendResult(ok=True, message_id="dry_run")

        if self.engine == "meta":
            return await self._send_meta(recipient_id, message)

        if self.engine == "baileys":
            return await self._send_baileys(recipient_id, message)

        return SendResult(ok=False, error=f"Engine tidak dikenal: {self.engine}")

    async def _send_meta(self, phone: str, text: str) -> SendResult:
        if not self.access_token or not self.phone_number_id:
            logger.warning("WAAdapter: META_ACCESS_TOKEN atau META_PHONE_NUMBER_ID kosong.")
            return SendResult(ok=False, error="Meta credentials missing")

        url = f"https://graph.facebook.com/v21.0/{self.phone_number_id}/messages"
        # Normalisasi nomor: hapus '+' untuk Meta API
        to = phone.lstrip("+")
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            raw = await self._http_post_async(url, payload, headers)
            msg_id = raw.get("messages", [{}])[0].get("id", "")
            self._stats["messages_out"] += 1
            return SendResult(ok=True, message_id=msg_id, raw_response=raw)
        except Exception as exc:
            self._stats["errors"] += 1
            logger.error("WAAdapter Meta send error: %s", exc)
            return SendResult(ok=False, error=str(exc))

    async def _send_baileys(self, phone: str, text: str) -> SendResult:
        """Kirim lewat Baileys sidecar service (Node.js)."""
        url = f"{self.sidecar_url}/send"
        payload = {"to": phone, "text": text}
        try:
            raw = await self._http_post_async(url, payload)
            self._stats["messages_out"] += 1
            return SendResult(ok=True, message_id=raw.get("id", ""), raw_response=raw)
        except Exception as exc:
            self._stats["errors"] += 1
            logger.error("WAAdapter Baileys send error: %s", exc)
            return SendResult(ok=False, error=str(exc))

    # ------------------------------------------------------------------
    # Webhook Verification helper
    # ------------------------------------------------------------------
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        """
        Verifikasi GET webhook Meta.
        Return challenge string jika valid, None jika token tidak cocok.
        """
        if mode == "subscribe" and token == self.verify_token and challenge:
            return challenge
        return None

    def get_stats(self) -> dict:
        return {"channel": self.channel_name, "engine": self.engine, **self._stats}


# ===========================================================================
# Telegram Adapter
# ===========================================================================

class TelegramAdapter(BaseAdapter):
    """
    Telegram Bot API adapter.

    Pola: https://api.telegram.org/bot{TOKEN}/sendMessage
    Webhook payload format standar Telegram Update object.

    Config env:
      TELEGRAM_BOT_TOKEN : Token dari @BotFather
      TELEGRAM_PARSE_MODE: "HTML" | "Markdown" | "" (default: "HTML")
    """

    channel_name = "telegram"

    def __init__(
        self,
        bot_token: str = "",
        parse_mode: str = "HTML",
    ):
        import os
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.parse_mode = parse_mode or os.getenv("TELEGRAM_PARSE_MODE", "HTML")
        self._base_url = f"https://api.telegram.org/bot{self.bot_token}"

        self._stats: dict[str, int] = {
            "messages_in": 0,
            "messages_out": 0,
            "errors": 0,
        }

    # ------------------------------------------------------------------
    # parse_incoming
    # ------------------------------------------------------------------
    def parse_incoming(self, raw_payload: dict) -> InboundMessage:
        """
        Parse Telegram Update object:
        {
          "update_id": 123456,
          "message": {
            "message_id": 1,
            "from": {"id": 111, "first_name": "Fahmi"},
            "chat": {"id": 111, "type": "private"},
            "text": "/halo",
            "date": 1700000000
          }
        }
        Mendukung juga: callback_query (inline buttons).
        """
        self._stats["messages_in"] += 1

        # Pesan teks biasa
        if "message" in raw_payload:
            return self._parse_message(raw_payload["message"])

        # Edited message
        if "edited_message" in raw_payload:
            return self._parse_message(raw_payload["edited_message"])

        # Callback dari inline keyboard
        if "callback_query" in raw_payload:
            return self._parse_callback(raw_payload["callback_query"])

        raise ValueError(
            f"TelegramAdapter: tipe update tidak dikenali. Keys: {list(raw_payload.keys())}"
        )

    def _parse_message(self, msg: dict) -> InboundMessage:
        chat_id = str(msg.get("chat", {}).get("id", ""))
        message_id = str(msg.get("message_id", ""))
        text = msg.get("text", "")
        caption = msg.get("caption", "")

        media_url = ""
        media_type_str = ""

        # Cek media
        if "photo" in msg:
            media_type_str = "image"
            # Ambil foto resolusi tertinggi (item terakhir)
            photos = msg["photo"]
            if photos:
                media_url = photos[-1].get("file_id", "")
        elif "document" in msg:
            media_type_str = "document"
            media_url = msg["document"].get("file_id", "")
        elif "audio" in msg:
            media_type_str = "audio"
            media_url = msg["audio"].get("file_id", "")
        elif "voice" in msg:
            media_type_str = "audio"
            media_url = msg["voice"].get("file_id", "")
        elif "video" in msg:
            media_type_str = "video"
            media_url = msg["video"].get("file_id", "")

        return InboundMessage(
            channel="telegram",
            sender_id=chat_id,
            text=(text or caption).strip(),
            message_id=message_id,
            media_url=media_url,
            media_type=media_type_str,
            raw_payload=msg,
            timestamp=float(msg.get("date", time.time())),
        )

    def _parse_callback(self, callback: dict) -> InboundMessage:
        chat_id = str(callback.get("message", {}).get("chat", {}).get("id", ""))
        callback_id = str(callback.get("id", ""))
        data = callback.get("data", "")
        return InboundMessage(
            channel="telegram",
            sender_id=chat_id,
            text=data,
            message_id=callback_id,
            raw_payload=callback,
        )

    # ------------------------------------------------------------------
    # format_message
    # ------------------------------------------------------------------
    def format_message(self, sidix_response: dict) -> OutboundMessage:
        """
        Format respons SIDIX untuk Telegram.
        Mendukung HTML parse mode dengan bold/italic.
        """
        answer = sidix_response.get("answer", "")
        sources = sidix_response.get("sources", [])
        recipient = sidix_response.get("recipient_id", "")

        if sources:
            source_lines = []
            for s in sources[:3]:
                if isinstance(s, dict):
                    title = s.get("title", s.get("file", ""))
                    url = s.get("url", "")
                    if title and url:
                        source_lines.append(f'• <a href="{url}">{title}</a>')
                    elif title:
                        source_lines.append(f"• <b>{title}</b>")
                elif isinstance(s, str):
                    source_lines.append(f"• {s}")
            if source_lines:
                answer = answer + "\n\n<i>Sumber:</i>\n" + "\n".join(source_lines)

        return OutboundMessage(
            channel="telegram",
            recipient_id=recipient,
            text=answer,
            parse_mode=self.parse_mode,
        )

    # ------------------------------------------------------------------
    # send_reply
    # ------------------------------------------------------------------
    async def send_reply(self, recipient_id: str, message: str, **kwargs: Any) -> SendResult:
        """
        Kirim pesan ke chat Telegram via Bot API.
        kwargs opsional:
          parse_mode  : override parse mode
          reply_to    : message_id untuk reply
          buttons     : list[list[dict]] inline keyboard
        """
        if not self.bot_token:
            logger.warning("TelegramAdapter: TELEGRAM_BOT_TOKEN kosong.")
            return SendResult(ok=False, error="Bot token missing")

        url = f"{self._base_url}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": recipient_id,
            "text": message,
        }

        parse_mode = kwargs.get("parse_mode", self.parse_mode)
        if parse_mode:
            payload["parse_mode"] = parse_mode

        reply_to = kwargs.get("reply_to")
        if reply_to:
            payload["reply_to_message_id"] = reply_to

        buttons = kwargs.get("buttons")
        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}

        try:
            raw = await self._http_post_async(url, payload)
            self._stats["messages_out"] += 1
            msg_id = str(raw.get("result", {}).get("message_id", ""))
            return SendResult(ok=True, message_id=msg_id, raw_response=raw)
        except Exception as exc:
            self._stats["errors"] += 1
            logger.error("TelegramAdapter send error: %s", exc)
            return SendResult(ok=False, error=str(exc))

    async def answer_callback(self, callback_query_id: str, text: str = "") -> SendResult:
        """Jawab callback query (untuk menonaktifkan loading spinner di button)."""
        url = f"{self._base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id, "text": text}
        try:
            raw = await self._http_post_async(url, payload)
            return SendResult(ok=True, raw_response=raw)
        except Exception as exc:
            return SendResult(ok=False, error=str(exc))

    def get_stats(self) -> dict:
        return {"channel": self.channel_name, **self._stats}


# ===========================================================================
# Generic Webhook Adapter
# ===========================================================================

class GenericWebhookAdapter(BaseAdapter):
    """
    Adapter generik untuk channel lain yang menggunakan JSON webhook.
    Asumsi payload minimal: {"sender_id": "...", "text": "...", "reply_url": "..."}

    Cocok untuk: custom web widget, API klien, Slack (slim), Line, dll.
    """

    channel_name = "generic"

    def __init__(self, reply_url: str = ""):
        self.reply_url = reply_url
        self._stats: dict[str, int] = {
            "messages_in": 0,
            "messages_out": 0,
            "errors": 0,
        }

    def parse_incoming(self, raw_payload: dict) -> InboundMessage:
        self._stats["messages_in"] += 1
        sender = str(raw_payload.get("sender_id", raw_payload.get("user_id", "unknown")))
        text = str(raw_payload.get("text", raw_payload.get("message", ""))).strip()
        message_id = str(raw_payload.get("message_id", raw_payload.get("id", "")))
        if not sender or not text:
            raise ValueError(f"GenericAdapter: payload harus punya 'sender_id' dan 'text'. Got: {list(raw_payload.keys())}")
        return InboundMessage(
            channel="generic",
            sender_id=sender,
            text=text,
            message_id=message_id,
            raw_payload=raw_payload,
        )

    def format_message(self, sidix_response: dict) -> OutboundMessage:
        return OutboundMessage(
            channel="generic",
            recipient_id=sidix_response.get("recipient_id", ""),
            text=sidix_response.get("answer", ""),
        )

    async def send_reply(self, recipient_id: str, message: str, **kwargs: Any) -> SendResult:
        reply_url = kwargs.get("reply_url", self.reply_url)
        if not reply_url:
            # Tidak ada URL tujuan → log saja
            logger.info("[GenericAdapter] → %s: %s", recipient_id, message[:80])
            self._stats["messages_out"] += 1
            return SendResult(ok=True, message_id="logged")

        payload = {"recipient_id": recipient_id, "message": message}
        try:
            raw = await self._http_post_async(reply_url, payload)
            self._stats["messages_out"] += 1
            return SendResult(ok=True, raw_response=raw if isinstance(raw, dict) else {})
        except Exception as exc:
            self._stats["errors"] += 1
            logger.error("GenericAdapter send error: %s", exc)
            return SendResult(ok=False, error=str(exc))

    def get_stats(self) -> dict:
        return {"channel": self.channel_name, **self._stats}


# ===========================================================================
# Gateway Router
# ===========================================================================

class GatewayRouter:
    """
    Router utama: terima pesan dari channel mana saja → normalize → kirim ke SIDIX
    → format jawaban → kirim balik ke channel.

    Pola dari D:\\WA API GATeway: MessagePipelineService (NestJS)
    Pola dari D:\\bot gateway:    run_task (RQ worker) + match case

    Usage:
        router = GatewayRouter()
        router.register("whatsapp", WAAdapter(engine="meta"))
        router.register("telegram", TelegramAdapter())

        # Dalam FastAPI route / webhook handler:
        result = await router.route("whatsapp", payload, sidix_fn=my_sidix_call)
    """

    def __init__(self):
        self._adapters: dict[str, BaseAdapter] = {}
        self._route_log: list[dict] = []  # in-memory log terakhir (max 500)
        self._max_log = 500

        # Daftarkan adapter default
        self.register("whatsapp", WAAdapter())
        self.register("telegram", TelegramAdapter())
        self.register("generic", GenericWebhookAdapter())

    def register(self, channel: str, adapter: BaseAdapter) -> None:
        """Daftarkan adapter untuk channel tertentu."""
        self._adapters[channel.lower()] = adapter
        logger.info("GatewayRouter: adapter '%s' terdaftar.", channel)

    def get_adapter(self, channel: str) -> BaseAdapter | None:
        return self._adapters.get(channel.lower())

    def get_adapters(self) -> list[dict]:
        """Return list info adapter yang terdaftar."""
        return [
            {
                "channel": name,
                "adapter_class": type(adapter).__name__,
                "stats": adapter.get_stats() if hasattr(adapter, "get_stats") else {},
            }
            for name, adapter in self._adapters.items()
        ]

    async def route(
        self,
        channel: str,
        raw_payload: dict,
        sidix_fn=None,
        **sidix_kwargs: Any,
    ) -> dict:
        """
        Full pipeline:
        1. Parse incoming dari channel
        2. Panggil sidix_fn(inbound_message, **sidix_kwargs) → dict
        3. Format jawaban ke channel
        4. Kirim ke channel
        5. Return result dict

        Args:
            channel      : nama channel ("whatsapp", "telegram", "generic")
            raw_payload  : payload mentah dari webhook
            sidix_fn     : callable async/sync → dict dengan key "answer".
                           Jika None, routing selesai di parse saja (untuk testing).
            **sidix_kwargs: argumen tambahan untuk sidix_fn

        Returns:
            {
                "ok": bool,
                "channel": str,
                "sender_id": str,
                "inbound_text": str,
                "answer": str,
                "send_result": {...}
            }
        """
        adapter = self.get_adapter(channel)
        if adapter is None:
            return {"ok": False, "error": f"Channel tidak dikenal: {channel}"}

        # Step 1: Parse incoming
        try:
            inbound = adapter.parse_incoming(raw_payload)
        except ValueError as exc:
            logger.error("Route parse error [%s]: %s", channel, exc)
            return {"ok": False, "channel": channel, "error": str(exc)}

        # Step 2: Panggil SIDIX (jika sidix_fn diberikan)
        sidix_response: dict = {"answer": "", "sources": [], "recipient_id": inbound.sender_id}
        if sidix_fn is not None:
            try:
                result = sidix_fn(inbound, **sidix_kwargs)
                # Support async dan sync function
                if hasattr(result, "__await__"):
                    import asyncio
                    result = await result
                if isinstance(result, dict):
                    sidix_response.update(result)
                elif isinstance(result, str):
                    sidix_response["answer"] = result
            except Exception as exc:
                logger.error("SIDIX fn error [%s]: %s", channel, exc)
                sidix_response["answer"] = "Maaf, terjadi kesalahan saat memproses pertanyaan Anda."

        sidix_response.setdefault("recipient_id", inbound.sender_id)

        # Step 3: Format jawaban
        outbound = adapter.format_message(sidix_response)
        outbound.recipient_id = outbound.recipient_id or inbound.sender_id

        # Step 4: Kirim jawaban (jika ada teks jawaban)
        send_result = SendResult(ok=True, message_id="no_send")
        if outbound.text and outbound.recipient_id:
            send_result = await adapter.send_reply(
                outbound.recipient_id,
                outbound.text,
                parse_mode=outbound.parse_mode,
            )

        # Step 5: Log
        log_entry = {
            "ts": time.time(),
            "channel": channel,
            "sender_id": inbound.sender_id,
            "text": inbound.text[:200],
            "answer": sidix_response["answer"][:200],
            "send_ok": send_result.ok,
        }
        self._route_log.append(log_entry)
        if len(self._route_log) > self._max_log:
            self._route_log = self._route_log[-self._max_log:]

        return {
            "ok": send_result.ok,
            "channel": channel,
            "sender_id": inbound.sender_id,
            "inbound_text": inbound.text,
            "answer": sidix_response["answer"],
            "send_result": {
                "ok": send_result.ok,
                "message_id": send_result.message_id,
                "error": send_result.error,
            },
        }

    def get_recent_log(self, n: int = 20) -> list[dict]:
        """Ambil n entri log routing terakhir."""
        return self._route_log[-n:]


# ===========================================================================
# Public Stats Function
# ===========================================================================

def get_channel_stats() -> dict:
    """
    Return statistik seluruh adapter dalam router default.
    Berguna untuk health check / monitoring endpoint.
    """
    router = _default_router()
    total_in = 0
    total_out = 0
    total_errors = 0
    channels = []
    for info in router.get_adapters():
        stats = info.get("stats", {})
        mi = stats.get("messages_in", 0)
        mo = stats.get("messages_out", 0)
        er = stats.get("errors", 0)
        total_in += mi
        total_out += mo
        total_errors += er
        channels.append({
            "channel": info["channel"],
            "adapter": info["adapter_class"],
            "messages_in": mi,
            "messages_out": mo,
            "errors": er,
        })
    return {
        "active_channels": len(channels),
        "channels": channels,
        "total_messages_in": total_in,
        "total_messages_out": total_out,
        "total_errors": total_errors,
        "http_client": _HTTP_CLIENT,
    }


# Singleton router ringan — dibuat saat pertama kali dipakai
_router_instance: GatewayRouter | None = None


def _default_router() -> GatewayRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = GatewayRouter()
    return _router_instance


def get_router() -> GatewayRouter:
    """Ambil singleton GatewayRouter."""
    return _default_router()
