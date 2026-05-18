"""
creative_tools_registry.py — Adoption Registry untuk Creative Agent Stack
============================================================================

Per research_notes/229_full_stack_creative_agent_ecosystem.md.

Modul ini = **registry + status tracker** untuk adopsi creative tools yang
disurvei di note 229. Bukan wrapper inference (itu Q3 2026 phase 1).

Tujuan:
- Catat tool yang sudah dipertimbangkan untuk adopsi
- Track status (planned / wired / shipped / deprecated)
- Quick lookup: kalau user tanya "tools apa SIDIX punya untuk X?"
- Foundation untuk MCP server registry (Q3 2026)

Hari ini (vol 16): minimal registry + status tracking + admin viewer.

Future (Q3 2026):
- Wire actual tool wrapper (visual_engine, audio_engine, video_engine)
- MCP server adapter per tool
- Tool selection routing (saat user message → pick optimal tool)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class CreativeTool:
    """1 tool dalam creative ecosystem registry."""
    id: str
    name: str
    category: str           # "visual" | "video" | "audio" | "3d" | "agent" | "rag" | "marketing"
    license: str            # "open_source" | "commercial" | "freemium" | "api_paid"
    sidix_status: str       # "planned" | "wired" | "shipped" | "deprecated" | "evaluating"
    target_quarter: str     # "Q3_2026" | "Q4_2026" | "Q1_2027" | "moonshot"
    description: str
    primary_url: str = ""
    integration_module: str = ""   # path ke module SIDIX kalau wired
    notes: str = ""


# ── Path ───────────────────────────────────────────────────────────────────────

def _registry_path() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "creative_tools_registry.json"


# ── Default registry seeds (dari note 229) ───────────────────────────────────

_DEFAULT_TOOLS: list[CreativeTool] = [
    # === Phase 0 (immediate Q3 2026) — wire ke mighan-media-worker ===
    CreativeTool(
        id="mighan_media_worker_sdxl",
        name="mighan-media-worker (SDXL via RunPod)",
        category="visual",
        license="self_hosted",
        sidix_status="evaluating",
        target_quarter="Q3_2026",
        description="Shared backend Mighan Lab — SDXL image gen via RunPod serverless. "
                    "SIDIX consume sebagai client (shared GPU cost).",
        primary_url="(internal RunPod endpoint)",
        notes="Phase 0 wire 2-3 hari. Sanad chain wrapper di SIDIX side.",
    ),
    CreativeTool(
        id="mighan_media_worker_tts",
        name="mighan-media-worker (coqui-tts)",
        category="audio",
        license="self_hosted",
        sidix_status="evaluating",
        target_quarter="Q3_2026",
        description="Shared backend coqui-tts via RunPod. SIDIX wrap untuk TTS.",
        primary_url="(internal RunPod endpoint)",
    ),

    # === Visual Generation ===
    CreativeTool(
        id="stable_diffusion_xl",
        name="Stable Diffusion XL",
        category="visual",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Image generation base model, SDXL 1.0 OpenRAIL license.",
        primary_url="https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
    ),
    CreativeTool(
        id="comfyui",
        name="ComfyUI",
        category="visual",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Node-based pipeline GUI untuk image gen workflow control.",
        primary_url="https://github.com/comfyanonymous/ComfyUI",
    ),
    CreativeTool(
        id="controlnet",
        name="ControlNet",
        category="visual",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Pose/depth/edge conditioning untuk presisi image gen.",
        primary_url="https://github.com/lllyasviel/ControlNet",
    ),
    CreativeTool(
        id="kohya_ss",
        name="Kohya_ss / SD-Trainer",
        category="visual",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="LoRA training framework untuk style/character/brand specific.",
        primary_url="https://github.com/kohya-ss/sd-scripts",
    ),
    CreativeTool(
        id="ip_adapter",
        name="IP-Adapter",
        category="visual",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Reference image conditioning untuk style transfer.",
        primary_url="https://huggingface.co/h94/IP-Adapter",
    ),

    # === Video Generation ===
    CreativeTool(
        id="animate_diff",
        name="AnimateDiff",
        category="video",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="T2V via SD-LoRA, integrate dengan ComfyUI.",
        primary_url="https://huggingface.co/papers/2307.04725",
    ),
    CreativeTool(
        id="svd_stable_video",
        name="Stable Video Diffusion (SVD)",
        category="video",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Image-to-video, 4-second clip dari still image.",
        primary_url="https://huggingface.co/stabilityai/stable-video-diffusion-img2vid",
    ),
    CreativeTool(
        id="cogvideox",
        name="CogVideoX",
        category="video",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q4_2026",
        description="T2V/I2V Tsinghua 5B weights open. 6-10 sec narrative clip.",
        primary_url="https://huggingface.co/THUDM/CogVideoX-5b",
    ),
    CreativeTool(
        id="mochi_1",
        name="Mochi-1 (Genmo)",
        category="video",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q4_2026",
        description="Open T2V 480p, 10B params.",
        primary_url="https://huggingface.co/genmo/mochi-1-preview",
    ),
    CreativeTool(
        id="ffmpeg_moviepy",
        name="FFmpeg + MoviePy",
        category="video",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Programmatic video editing — cut, splice, transition, export.",
        primary_url="https://github.com/Zulko/moviepy",
    ),

    # === Audio ===
    CreativeTool(
        id="whisper_large_v3",
        name="Whisper large-v3 (OpenAI)",
        category="audio",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="STT lokal, multi-language. Faster-whisper for streaming.",
        primary_url="https://huggingface.co/openai/whisper-large-v3",
    ),
    CreativeTool(
        id="xtts_v2",
        name="XTTS v2 (Coqui)",
        category="audio",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="TTS expressive dengan voice clone (3-5s sample).",
        primary_url="https://huggingface.co/coqui/XTTS-v2",
    ),
    CreativeTool(
        id="step_audio",
        name="Step-Audio",
        category="audio",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Native multimodal voice — listen+understand+respond real-time.",
        primary_url="https://huggingface.co/papers/2502.11946",
    ),
    CreativeTool(
        id="audiocraft",
        name="AudioCraft (Meta)",
        category="audio",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q4_2026",
        description="Music generation + sound effects.",
        primary_url="https://github.com/facebookresearch/audiocraft",
    ),
    CreativeTool(
        id="openvoice_v2",
        name="OpenVoice v2 (MyShell)",
        category="audio",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Voice cloning + emotional control.",
        primary_url="https://huggingface.co/myshell-ai/OpenVoiceV2",
    ),

    # === 3D + Game ===
    CreativeTool(
        id="hunyuan3d_2",
        name="Hunyuan3D-2 (Tencent)",
        category="3d",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q4_2026",
        description="3D model generation dari image/text.",
        primary_url="https://huggingface.co/tencent/Hunyuan3D-2",
    ),
    CreativeTool(
        id="trellis",
        name="TRELLIS (Microsoft)",
        category="3d",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q4_2026",
        description="Image-to-3D high-quality 2024.",
        primary_url="https://huggingface.co/Microsoft/TRELLIS-image-large",
    ),
    CreativeTool(
        id="three_js",
        name="Three.js",
        category="3d",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q1_2027",
        description="Web 3D engine untuk asset embed di app.",
        primary_url="https://threejs.org",
    ),
    CreativeTool(
        id="phaser_js",
        name="Phaser.js",
        category="3d",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q1_2027",
        description="Web 2D game engine untuk asset gen + embed.",
        primary_url="https://phaser.io",
    ),

    # === Multi-Agent + RAG ===
    CreativeTool(
        id="qdrant",
        name="Qdrant",
        category="rag",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Vector DB untuk scale (BM25 fallback existing).",
        primary_url="https://qdrant.tech",
    ),
    CreativeTool(
        id="bge_m3",
        name="BGE-M3 (BAAI)",
        category="rag",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="Multi-lingual embedding model 2024.",
        primary_url="https://huggingface.co/BAAI/bge-m3",
    ),

    # === MCP ===
    CreativeTool(
        id="fastmcp_python",
        name="FastMCP (Python SDK)",
        category="mcp",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="MCP server framework untuk wrap SIDIX tools.",
        primary_url="https://github.com/jlowin/fastmcp",
    ),
    CreativeTool(
        id="mcp_blender",
        name="MCP Blender Server",
        category="mcp",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q4_2026",
        description="Blender control via MCP — 3D ops dari SIDIX chat.",
        primary_url="https://modelcontextprotocol.io",
    ),
    CreativeTool(
        id="mcp_filesystem",
        name="MCP Filesystem Server",
        category="mcp",
        license="open_source",
        sidix_status="planned",
        target_quarter="Q3_2026",
        description="File ops via MCP — SIDIX akses local FS user (consent).",
        primary_url="https://github.com/modelcontextprotocol/servers",
    ),

    # === Marketing ===
    CreativeTool(
        id="tokopedia_api",
        name="Tokopedia API",
        category="marketing",
        license="api_paid",
        sidix_status="planned",
        target_quarter="Q1_2027",
        description="E-commerce Indonesia — product listing + analytics.",
        primary_url="https://developer.tokopedia.com",
    ),
    CreativeTool(
        id="shopee_api",
        name="Shopee Open Platform",
        category="marketing",
        license="api_paid",
        sidix_status="planned",
        target_quarter="Q1_2027",
        description="E-commerce SE Asia — product + order management.",
        primary_url="https://open.shopee.com",
    ),

    # === Existing SIDIX (already shipped) ===
    CreativeTool(
        id="sidix_burst_mode",
        name="SIDIX Burst Mode",
        category="agent",
        license="self_hosted",
        sidix_status="shipped",
        target_quarter="Q2_2026",
        description="6-angle parallel + Pareto-pilih (existing vol 4).",
        integration_module="apps/brain_qa/brain_qa/agent_burst.py",
    ),
    CreativeTool(
        id="sidix_critic_loop",
        name="SIDIX Innovator-Critic Loop",
        category="agent",
        license="self_hosted",
        sidix_status="shipped",
        target_quarter="Q2_2026",
        description="Multi-iteration refine via dedicated Critic agent (vol 10).",
        integration_module="apps/brain_qa/brain_qa/agent_critic.py",
    ),
    CreativeTool(
        id="sidix_tadabbur",
        name="SIDIX Tadabbur Mode",
        category="agent",
        license="self_hosted",
        sidix_status="shipped",
        target_quarter="Q2_2026",
        description="3-persona iterate konvergensi untuk deep question (vol 10).",
        integration_module="apps/brain_qa/brain_qa/tadabbur_mode.py",
    ),
    CreativeTool(
        id="sidix_persona_router",
        name="SIDIX Persona Auto-Router",
        category="agent",
        license="self_hosted",
        sidix_status="shipped",
        target_quarter="Q2_2026",
        description="Auto-detect optimal persona dari user message style (vol 11).",
        integration_module="apps/brain_qa/brain_qa/persona_router.py",
    ),
    CreativeTool(
        id="sidix_proactive_feeds",
        name="SIDIX Proactive Feeds",
        category="agent",
        license="self_hosted",
        sidix_status="shipped",
        target_quarter="Q2_2026",
        description="HN + arxiv + GitHub + HF papers trend monitor (vol 15).",
        integration_module="apps/brain_qa/brain_qa/proactive_feeds.py",
    ),
]


# ── Persistence ────────────────────────────────────────────────────────────────

def _load_or_init_registry() -> dict:
    """Load registry dari file, atau init dari default."""
    path = _registry_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Init dari default seeds
    registry = {
        "version": 1,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "tools": [asdict(t) for t in _DEFAULT_TOOLS],
    }
    try:
        path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        log.warning("[creative_registry] init save fail: %s", e)
    return registry


def list_tools(category: str = "", status: str = "") -> list[dict]:
    """List tools, filter optional by category & status."""
    registry = _load_or_init_registry()
    tools = registry.get("tools", [])
    if category:
        tools = [t for t in tools if t.get("category") == category]
    if status:
        tools = [t for t in tools if t.get("sidix_status") == status]
    return tools


def stats() -> dict:
    """Stats by category & status."""
    registry = _load_or_init_registry()
    tools = registry.get("tools", [])
    by_category: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_quarter: dict[str, int] = {}
    for t in tools:
        c = t.get("category", "?")
        s = t.get("sidix_status", "?")
        q = t.get("target_quarter", "?")
        by_category[c] = by_category.get(c, 0) + 1
        by_status[s] = by_status.get(s, 0) + 1
        by_quarter[q] = by_quarter.get(q, 0) + 1
    return {
        "total": len(tools),
        "by_category": by_category,
        "by_status": by_status,
        "by_quarter": by_quarter,
        "last_updated": registry.get("last_updated", ""),
    }


def update_status(tool_id: str, new_status: str, integration_module: str = "") -> bool:
    """Update status (planned → wired → shipped, dll)."""
    valid_status = {"planned", "evaluating", "wired", "shipped", "deprecated"}
    if new_status not in valid_status:
        return False

    registry = _load_or_init_registry()
    found = False
    for t in registry.get("tools", []):
        if t.get("id") == tool_id:
            t["sidix_status"] = new_status
            if integration_module:
                t["integration_module"] = integration_module
            t["updated_at"] = datetime.now(timezone.utc).isoformat()
            found = True
            break

    if found:
        registry["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            _registry_path().write_text(
                json.dumps(registry, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            return False
    return found


__all__ = [
    "CreativeTool", "list_tools", "stats", "update_status",
]
