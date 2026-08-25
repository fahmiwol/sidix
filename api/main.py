"""
SIDIX API — FastAPI Backend
MCP support, tools, streaming chat, history
"""

import asyncio
import json
import os
import re
import uuid
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import redis

app = FastAPI(
    title="SIDIX API",
    version="0.1.0",
    description="SIDIX — Web Chat + MCP + Tools",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=5)
    redis_client.ping()
except Exception:
    redis_client = None

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "sidix-lora")

# Load system prompt from file
SYSTEM_PROMPT = "Kamu adalah SIDIX, asisten AI."
try:
    with open("/app/system_prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except Exception:
    pass

# ============================================================================
# Models
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    model: str = DEFAULT_MODEL
    stream: bool = True
    temperature: float = 0.7
    tools_enabled: bool = True

class ToolCall(BaseModel):
    name: str
    arguments: dict

class ToolResult(BaseModel):
    name: str
    result: str
    error: Optional[str] = None

# ============================================================================
# Session / History
# ============================================================================

def get_session_key(sid: str) -> str:
    return f"sidix:session:{sid}"

def load_history(session_id: str, limit: int = 20) -> List[dict]:
    if not redis_client:
        return []
    try:
        raw = redis_client.lrange(get_session_key(session_id), -limit, -1)
        return [json.loads(r) for r in raw]
    except Exception:
        return []

def save_message(session_id: str, msg: dict):
    if not redis_client:
        return
    key = get_session_key(session_id)
    msg["timestamp"] = datetime.utcnow().isoformat()
    redis_client.rpush(key, json.dumps(msg))
    redis_client.expire(key, 60 * 60 * 24 * 7)

def clear_history(session_id: str):
    if redis_client:
        redis_client.delete(get_session_key(session_id))

# ============================================================================
# Tools
# ============================================================================

TOOLS_REGISTRY = {}

def register_tool(name: str, desc: str, params: dict):
    def decorator(fn):
        TOOLS_REGISTRY[name] = {"function": fn, "description": desc, "parameters": params}
        return fn
    return decorator

@register_tool("web_search", "Search the web for current information.", {"query": {"type": "string"}})
async def tool_web_search(query: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            results = []
            for line in r.text.split("\n"):
                if "class=\"result__a\"" in line or "class=\"result__snippet\"" in line:
                    clean = re.sub(r"<[^>]+>", "", line).strip()
                    if clean and len(clean) > 20:
                        results.append(clean)
            return "\n".join(results[:5]) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"

@register_tool("calculator", "Evaluate math expressions safely.", {"expression": {"type": "string"}})
async def tool_calculator(expression: str) -> str:
    try:
        import ast
        import operator as op
        allowed = {
            ast.Expression: ast.Expression, ast.BinOp: ast.BinOp, ast.UnaryOp: ast.UnaryOp,
            ast.Constant: ast.Constant, ast.Num: ast.Num,
            ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
            ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg,
            ast.FloorDiv: op.floordiv, ast.Mod: op.mod,
        }
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, (ast.Constant, ast.Num)):
                return node.n if hasattr(node, "n") else node.value
            elif isinstance(node, ast.BinOp):
                return allowed[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                return allowed[type(node.op)](_eval(node.operand))
            raise TypeError(f"Unsupported: {type(node)}")
        return str(_eval(ast.parse(expression, mode="eval")))
    except Exception as e:
        return f"Calculator error: {e}"

@register_tool("datetime_now", "Get current datetime.", {"timezone": {"type": "string", "default": "Asia/Jakarta"}})
async def tool_datetime_now(timezone: str = "Asia/Jakarta") -> str:
    try:
        from datetime import datetime
        import pytz
        tz = pytz.timezone(timezone)
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z (%A)")
    except Exception as e:
        return f"Datetime error: {e}"

@register_tool("read_url", "Fetch webpage text content.", {"url": {"type": "string"}})
async def tool_read_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SIDIX-Bot/0.1)"})
            text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", r.text, flags=re.IGNORECASE)
            text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:4000]
    except Exception as e:
        return f"URL error: {e}"

# ============================================================================
# Tool System Prompt
# ============================================================================

TOOL_SYSTEM_PROMPT = SYSTEM_PROMPT + """

Kamu punya akses ke TOOLS. Gunakan format:
<tool_call>
{"name": "nama_tool", "arguments": {"param": "value"}}
</tool_call>

Tools:"""
for tname, tinfo in TOOLS_REGISTRY.items():
    TOOL_SYSTEM_PROMPT += f"\n- {tname}: {tinfo['description']}"
TOOL_SYSTEM_PROMPT += """

Aturan: Jika perlu info real-time → web_search. Jika hitung → calculator. Jika waktu → datetime_now. Jika URL → read_url. Jika tidak perlu tool, jawab langsung.
"""

def detect_tool_calls(text: str) -> List[ToolCall]:
    calls = []
    for m in re.finditer(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', text, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            calls.append(ToolCall(name=data.get("name"), arguments=data.get("arguments", {})))
        except Exception:
            pass
    return calls

def strip_tool_calls(text: str) -> str:
    return re.sub(r'<tool_call>[\s\S]*?</tool_call>', '', text).strip()

async def execute_tool(tool_call: ToolCall) -> ToolResult:
    name = tool_call.name
    args = tool_call.arguments
    if name not in TOOLS_REGISTRY:
        return ToolResult(name=name, result="", error=f"Tool '{name}' not found.")
    try:
        result = await TOOLS_REGISTRY[name]["function"](**args)
        return ToolResult(name=name, result=result)
    except Exception as e:
        return ToolResult(name=name, result="", error=str(e))

# ============================================================================
# Ollama Streaming
# ============================================================================

async def ollama_chat_stream(model: str, messages: List[dict], temperature: float = 0.7) -> AsyncGenerator[str, None]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "top_p": 0.9, "num_ctx": 4096},
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload) as response:
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        yield f"\n[Error: {e}]\n"

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health")
async def health():
    redis_ok = False
    try:
        if redis_client:
            redis_client.ping()
            redis_ok = True
    except Exception:
        pass
    return {
        "status": "healthy",
        "service": "sidix-api",
        "version": "0.1.0",
        "model": DEFAULT_MODEL,
        "redis": redis_ok,
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            data = r.json()
            return {"models": [m["name"] for m in data.get("models", [])]}
    except Exception as e:
        raise HTTPException(503, f"Ollama unavailable: {e}")

@app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {"name": name, "description": info["description"], "parameters": info["parameters"]}
            for name, info in TOOLS_REGISTRY.items()
        ]
    }

@app.post("/chat")
async def chat(req: ChatRequest):
    sid = req.session_id or str(uuid.uuid4())
    history = load_history(sid)
    messages = [{"role": "system", "content": TOOL_SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": req.message})
    save_message(sid, {"role": "user", "content": req.message})

    if not req.stream:
        full_response = ""
        async for chunk in ollama_chat_stream(req.model, messages, req.temperature):
            full_response += chunk
        tool_calls = detect_tool_calls(full_response)
        if tool_calls and req.tools_enabled:
            tool_results = []
            for tc in tool_calls:
                tool_results.append(await execute_tool(tc))
            tool_msg = "\n".join([f"Tool '{r.name}': {r.result or r.error}" for r in tool_results])
            messages.append({"role": "tool", "content": tool_msg})
            full_response = ""
            async for chunk in ollama_chat_stream(req.model, messages, req.temperature):
                full_response += chunk
        clean = strip_tool_calls(full_response)
        save_message(sid, {"role": "assistant", "content": clean, "model": req.model})
        return {"session_id": sid, "response": clean, "model": req.model}

    async def event_stream():
        buffer = ""
        async for chunk in ollama_chat_stream(req.model, messages, req.temperature):
            buffer += chunk
            yield f"data: {json.dumps({'chunk': chunk, 'session_id': sid})}\n\n"
        tool_calls = detect_tool_calls(buffer)
        if tool_calls and req.tools_enabled:
            yield f"data: {json.dumps({'tool_calls': [tc.dict() for tc in tool_calls], 'session_id': sid})}\n\n"
            tool_results = []
            for tc in tool_calls:
                tr = await execute_tool(tc)
                tool_results.append(tr)
                yield f"data: {json.dumps({'tool_result': {'name': tr.name, 'result': tr.result or tr.error}, 'session_id': sid})}\n\n"
            tool_msg = "\n".join([f"Tool '{r.name}': {r.result or r.error}" for r in tool_results])
            messages.append({"role": "tool", "content": tool_msg})
            async for chunk in ollama_chat_stream(req.model, messages, req.temperature):
                yield f"data: {json.dumps({'chunk': chunk, 'session_id': sid})}\n\n"
        clean = strip_tool_calls(buffer)
        save_message(sid, {"role": "assistant", "content": clean, "model": req.model})
        yield f"data: {json.dumps({'done': True, 'session_id': sid})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    return {"session_id": session_id, "messages": load_history(session_id)}

@app.delete("/history/{session_id}")
async def delete_history(session_id: str):
    clear_history(session_id)
    return {"session_id": session_id, "cleared": True}

# MCP endpoints
@app.get("/mcp/sse")
async def mcp_sse(request: Request):
    async def event_stream():
        while True:
            if await request.is_disconnected():
                break
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            await asyncio.sleep(30)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/mcp/tools/list")
async def mcp_tools_list():
    return {
        "tools": [
            {"name": name, "description": info["description"], "inputSchema": info["parameters"]}
            for name, info in TOOLS_REGISTRY.items()
        ]
    }

@app.post("/mcp/tools/call")
async def mcp_tools_call(request: Request):
    body = await request.json()
    name = body.get("name")
    arguments = body.get("arguments", {})
    if name not in TOOLS_REGISTRY:
        return JSONResponse({"error": f"Tool '{name}' not found"}, 404)
    tr = await execute_tool(ToolCall(name=name, arguments=arguments))
    return {"result": tr.result or tr.error, "name": tr.name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
