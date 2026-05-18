"""
mcp_stdio_server.py — MCP stdio transport (JSON-RPC 2.0)
========================================================

Baca dari stdin, tulis response JSON-RPC ke stdout.
Logging / debug hanya ke stderr — stdout hanya untuk JSON-RPC valid.

Methods yang didukung:
  • initialize          → server capabilities
  • initialized         → notification (no response)
  • tools/list          → daftar tool via mcp_server_wrap.list_tools()
  • tools/call          → eksekusi tool via mcp_server_wrap.execute_tool()
  • notifications/initialized → ignore

Reference:
  • MCP spec: https://modelcontextprotocol.io
  • JSON-RPC 2.0: https://www.jsonrpc.org/specification
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback

log = logging.getLogger(__name__)

# ── Encoding guard ───────────────────────────────────────────────────────────
# Pastikan stdout/stderr UTF-8 supaya karakter non-ASCII aman.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# ── JSON-RPC 2.0 error codes ─────────────────────────────────────────────────
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# ── Stdio policy: local desktop = trusted context ────────────────────────────
# Bisa di-override via env var bila user ingin restrictive mode.
_STDIO_ADMIN_OK = os.environ.get("SIDIX_MCP_ADMIN_OK", "1").strip() == "1"
_STDIO_ALLOW_RESTRICTED = os.environ.get("SIDIX_MCP_ALLOW_RESTRICTED", "1").strip() == "1"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _write_stdout(obj: dict) -> None:
    """Tulis satu baris JSON ke stdout dan flush."""
    line = json.dumps(obj, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _make_error(req_id: object, code: int, message: str, data: object = None) -> dict:
    err: dict = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def _make_result(req_id: object, result: object) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


# ── Method handlers ──────────────────────────────────────────────────────────

def _handle_initialize(req_id: object, params: dict) -> dict:
    return _make_result(req_id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": "SIDIX-MCP", "version": "2.1.0"},
    })


def _handle_tools_list(req_id: object, params: dict) -> dict:
    try:
        from .mcp_server_wrap import list_tools
        tools = list_tools(admin_ok=_STDIO_ADMIN_OK)
        return _make_result(req_id, {"tools": tools})
    except Exception as e:
        log.exception("[mcp_stdio] list_tools failed")
        return _make_error(req_id, INTERNAL_ERROR, f"Failed to list tools: {e}")


def _handle_tools_call(req_id: object, params: dict) -> dict:
    name = params.get("name")
    if not name or not isinstance(name, str):
        return _make_error(req_id, INVALID_PARAMS, "Missing or invalid 'name' in params")

    arguments = params.get("arguments") or {}
    if not isinstance(arguments, dict):
        return _make_error(req_id, INVALID_PARAMS, "'arguments' must be an object")

    try:
        from .mcp_server_wrap import execute_tool
        result = execute_tool(
            name=name,
            args=arguments,
            admin_ok=_STDIO_ADMIN_OK,
            allow_restricted=_STDIO_ALLOW_RESTRICTED,
        )

        if result.get("success"):
            text = result.get("output", "")
        else:
            text = result.get("error", "Unknown error")

        # Append citations kalau ada
        citations = result.get("citations", [])
        if citations:
            citation_text = "\n\n**Citations:**\n" + json.dumps(citations, ensure_ascii=False, indent=2)
            text += citation_text

        return _make_result(req_id, {
            "content": [{"type": "text", "text": text}],
            "isError": not result.get("success", False),
        })
    except Exception as e:
        log.exception("[mcp_stdio] execute_tool failed: %s", name)
        return _make_error(req_id, INTERNAL_ERROR, f"Tool execution failed: {e}")


_DISPATCH: dict[str, callable] = {
    "initialize": _handle_initialize,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
}


# ── Message router ───────────────────────────────────────────────────────────

def _handle_message(raw: str) -> dict | None:
    """
    Parse satu baris JSON-RPC dan kembalikan response dict atau None
    kalau message adalah notification (tidak perlu response).
    """
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError as e:
        return _make_error(None, PARSE_ERROR, f"Parse error: {e}")

    if not isinstance(msg, dict):
        return _make_error(None, INVALID_REQUEST, "JSON-RPC message must be an object")

    jsonrpc = msg.get("jsonrpc")
    if jsonrpc != "2.0":
        return _make_error(msg.get("id"), INVALID_REQUEST, "Invalid jsonrpc version")

    method = msg.get("method")
    if not method or not isinstance(method, str):
        return _make_error(msg.get("id"), INVALID_REQUEST, "Missing or invalid method")

    msg_id = msg.get("id")
    is_notification = msg_id is None

    if is_notification:
        if method in ("initialized", "notifications/initialized"):
            log.debug("[mcp_stdio] received notification: %s", method)
        else:
            log.debug("[mcp_stdio] ignored notification: %s", method)
        return None

    handler = _DISPATCH.get(method)
    if handler is None:
        return _make_error(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}")

    params = msg.get("params") or {}
    if not isinstance(params, dict):
        return _make_error(msg_id, INVALID_PARAMS, "params must be an object")

    try:
        return handler(msg_id, params)
    except Exception as e:
        log.exception("[mcp_stdio] handler error for %s", method)
        return _make_error(msg_id, INTERNAL_ERROR, f"Internal error: {e}")


# ── Main loop ────────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    log.info("[mcp_stdio] SIDIX MCP stdio server starting")
    log.info("[mcp_stdio] admin_ok=%s allow_restricted=%s", _STDIO_ADMIN_OK, _STDIO_ALLOW_RESTRICTED)

    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            log.debug("[mcp_stdio] recv: %s", line[:500])
            response = _handle_message(line)
            if response is not None:
                _write_stdout(response)
                log.debug("[mcp_stdio] sent: %s", json.dumps(response)[:500])
    except KeyboardInterrupt:
        log.info("[mcp_stdio] interrupted by user")
    except EOFError:
        log.info("[mcp_stdio] EOF reached")
    except Exception as e:
        log.exception("[mcp_stdio] fatal error in main loop")
        sys.exit(1)
    finally:
        log.info("[mcp_stdio] server stopped")


if __name__ == "__main__":
    main()
