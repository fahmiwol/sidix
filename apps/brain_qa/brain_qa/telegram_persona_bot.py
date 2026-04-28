"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

telegram_persona_bot.py — Sprint 43 Phase 1 (5 Persona Discussion via Telegram)

Telegram bot yang spawn 5 persona SIDIX (UTZ/ABOO/OOMAR/ALEY/AYMAN) sebagai
advisor bench. Founder workflow: di mana saja → Telegram → tag persona →
dapat response dengan voice consistency dari LoRA Sprint 13.

Founder mandate (LOCK 2026-04-29): *"spawn 5 persona buat temen diskusi sidix"*

Commands supported:
  /start          — welcome + usage
  /persona        — list 5 persona
  /utz <Q>        — UTZ creative mode
  /aboo <Q>       — ABOO engineer mode
  /oomar <Q>      — OOMAR strategist mode
  /aley <Q>       — ALEY researcher mode
  /ayman <Q>      — AYMAN warm listener mode
  /council <Q>    — all 5 paralel (multi-angle)
  /save           — save thread → research note (Conversation Synthesizer)
  /help           — show commands

Phase 1 scope: scaffold module + command router + dispatch placeholders.
Phase 2: wire to /agent/chat existing endpoint, add long-poll loop, deploy.

Reference:
- docs/SPRINT_43_PERSONA_DISCUSSION_PLAN.md
- apps/brain_qa/brain_qa/persona_research_fanout.py (5 persona angles)
- apps/brain_qa/brain_qa/cot_system_prompts.py (PERSONA_DESCRIPTIONS)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


# ── Persona registry ─────────────────────────────────────────────────────────

PERSONAS = {
    "UTZ":   {"emoji": "🎨", "tagline": "Creative director, visual-playful",
              "command": "/utz"},
    "ABOO":  {"emoji": "🔧", "tagline": "Engineer praktis, sharp, fail-fast",
              "command": "/aboo"},
    "OOMAR": {"emoji": "🧭", "tagline": "Strategist, framework-driven",
              "command": "/oomar"},
    "ALEY":  {"emoji": "📚", "tagline": "Researcher methodical, curious",
              "command": "/aley"},
    "AYMAN": {"emoji": "💛", "tagline": "Pendengar hangat, empathetic",
              "command": "/ayman"},
}


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class TelegramMessage:
    """Parsed inbound Telegram message."""
    chat_id: int = 0
    user_id: int = 0
    username: str = ""
    text: str = ""
    message_id: int = 0
    is_command: bool = False
    command: str = ""
    args: str = ""


@dataclass
class BotResponse:
    """Outbound Telegram message to send."""
    chat_id: int = 0
    text: str = ""
    parse_mode: str = "MarkdownV2"
    reply_to_message_id: int = 0
    error: str = ""


# ── Telegram API helpers ─────────────────────────────────────────────────────

def _bot_token() -> Optional[str]:
    return os.environ.get("TELEGRAM_BOT_TOKEN")


def _owner_whitelist() -> set[int]:
    """Comma-separated TELEGRAM_OWNER_IDS env var."""
    raw = os.environ.get("TELEGRAM_OWNER_IDS", "")
    out: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            out.add(int(part))
    return out


def is_authorized(user_id: int) -> bool:
    """Check if user is in owner whitelist."""
    whitelist = _owner_whitelist()
    if not whitelist:
        # Phase 1: no whitelist set = no access (fail closed)
        log.warning("[telegram_bot] TELEGRAM_OWNER_IDS not set — all access denied")
        return False
    return user_id in whitelist


def parse_message(update: dict) -> Optional[TelegramMessage]:
    """Parse Telegram update JSON → TelegramMessage."""
    msg = update.get("message", {})
    if not msg:
        return None
    chat = msg.get("chat", {})
    user = msg.get("from", {})
    text = msg.get("text", "").strip()
    is_cmd = text.startswith("/")
    command = ""
    args = ""
    if is_cmd:
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        # Strip @BotName suffix if present
        if "@" in command:
            command = command.split("@")[0]
        args = parts[1] if len(parts) > 1 else ""
    return TelegramMessage(
        chat_id=chat.get("id", 0),
        user_id=user.get("id", 0),
        username=user.get("username", ""),
        text=text,
        message_id=msg.get("message_id", 0),
        is_command=is_cmd,
        command=command,
        args=args,
    )


def escape_markdown_v2(text: str) -> str:
    """Escape Telegram MarkdownV2 special chars."""
    chars = r"_*[]()~`>#+-=|{}.!"
    out = []
    for c in text:
        if c in chars:
            out.append("\\" + c)
        else:
            out.append(c)
    return "".join(out)


# ── Command handlers ─────────────────────────────────────────────────────────

def handle_start(msg: TelegramMessage) -> BotResponse:
    text = (
        "👋 *SIDIX Persona Advisor Bot*\n"
        "\n"
        "Pilih advisor yang sesuai konteks:\n"
        "🎨 /utz \\- creative director\n"
        "🔧 /aboo \\- engineer praktis\n"
        "🧭 /oomar \\- strategist\n"
        "📚 /aley \\- researcher\n"
        "💛 /ayman \\- pendengar hangat\n"
        "\n"
        "Atau /council untuk semua 5 paralel\\.\n"
        "\n"
        "Powered by SIDIX \\- Tiranyx Lab\\."
    )
    return BotResponse(chat_id=msg.chat_id, text=text)


def handle_persona_list(msg: TelegramMessage) -> BotResponse:
    lines = ["*5 Persona SIDIX:*", ""]
    for p, info in PERSONAS.items():
        lines.append(f"{info['emoji']} *{p}* \\- {escape_markdown_v2(info['tagline'])}")
        lines.append(f"  → {escape_markdown_v2(info['command'])} `<pertanyaan>`")
        lines.append("")
    return BotResponse(chat_id=msg.chat_id, text="\n".join(lines))


def handle_persona_query(msg: TelegramMessage, persona: str) -> BotResponse:
    """Single-persona query via /utz, /aboo, etc.

    Phase 1 stub. Phase 2 wires to /agent/chat?persona=X via httpx.
    """
    if not msg.args:
        return BotResponse(
            chat_id=msg.chat_id,
            text=f"Usage: /{persona.lower()} `<pertanyaan>`",
        )
    info = PERSONAS.get(persona, {})
    stub = (
        f"{info.get('emoji', '🤖')} *{escape_markdown_v2(persona)}*\n"
        f"\n"
        f"_\\[Phase 1 stub\\] Akan call /agent/chat?persona\\={escape_markdown_v2(persona)} di Phase 2\\._\n"
        f"\n"
        f"Pertanyaan: {escape_markdown_v2(msg.args[:200])}"
    )
    return BotResponse(
        chat_id=msg.chat_id, text=stub,
        reply_to_message_id=msg.message_id,
    )


def handle_council(msg: TelegramMessage) -> BotResponse:
    """All 5 persona paralel via /council.

    Phase 1 stub. Phase 2 wires to /agent/council existing endpoint.
    """
    if not msg.args:
        return BotResponse(
            chat_id=msg.chat_id,
            text="Usage: /council `<pertanyaan>`",
        )
    lines = ["*Council \\- 5 perspektif paralel*", ""]
    for p, info in PERSONAS.items():
        lines.append(f"{info['emoji']} *{p}*: _\\[Phase 1 stub\\]_")
    lines.append("")
    lines.append(f"Pertanyaan: {escape_markdown_v2(msg.args[:200])}")
    return BotResponse(chat_id=msg.chat_id, text="\n".join(lines))


def handle_save(msg: TelegramMessage) -> BotResponse:
    """Save Telegram thread → research note via Conversation Synthesizer.

    Phase 1 stub. Phase 2 fetches last N messages from Telegram + synthesize.
    """
    return BotResponse(
        chat_id=msg.chat_id,
        text="_\\[Phase 1 stub\\] Save thread will use conversation\\_synthesizer di Phase 2\\._",
    )


def handle_help(msg: TelegramMessage) -> BotResponse:
    return handle_start(msg)


# ── Main router ──────────────────────────────────────────────────────────────

def route_command(msg: TelegramMessage) -> BotResponse:
    """Dispatch command → appropriate handler."""
    if not is_authorized(msg.user_id):
        return BotResponse(
            chat_id=msg.chat_id,
            text="🔒 Access denied\\. Bot is private \\(owner\\-only Phase 1\\)\\.",
        )

    cmd = msg.command
    if cmd in ("/start", "/help"):
        return handle_start(msg)
    if cmd == "/persona":
        return handle_persona_list(msg)
    if cmd == "/utz":
        return handle_persona_query(msg, "UTZ")
    if cmd == "/aboo":
        return handle_persona_query(msg, "ABOO")
    if cmd == "/oomar":
        return handle_persona_query(msg, "OOMAR")
    if cmd == "/aley":
        return handle_persona_query(msg, "ALEY")
    if cmd == "/ayman":
        return handle_persona_query(msg, "AYMAN")
    if cmd == "/council":
        return handle_council(msg)
    if cmd == "/save":
        return handle_save(msg)

    return BotResponse(
        chat_id=msg.chat_id,
        text=f"Unknown command: `{escape_markdown_v2(cmd)}`\\. Try /help\\.",
    )


# ── Long-poll loop (Phase 2 entry point) ─────────────────────────────────────

def run_long_poll(timeout: int = 30) -> None:
    """Long-poll Telegram for updates → route → reply.

    Phase 1: stub function signature.
    Phase 2: implement via requests + Telegram getUpdates / sendMessage.
    """
    token = _bot_token()
    if not token:
        log.error("[telegram_bot] TELEGRAM_BOT_TOKEN not set")
        return
    log.info("[telegram_bot] long-poll Phase 2 wires here. Phase 1 = scaffold only.")
    # Phase 2:
    #   url_get = f"https://api.telegram.org/bot{token}/getUpdates"
    #   url_send = f"https://api.telegram.org/bot{token}/sendMessage"
    #   loop with offset, parse_message, route_command, send reply


__all__ = [
    "PERSONAS", "TelegramMessage", "BotResponse",
    "is_authorized", "parse_message", "escape_markdown_v2",
    "route_command", "run_long_poll",
    "handle_start", "handle_persona_list", "handle_persona_query",
    "handle_council", "handle_save", "handle_help",
]
