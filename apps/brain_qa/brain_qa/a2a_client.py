"""
a2a_client.py — A2A (Agent-to-Agent) Protocol Client for SIDIX
Phase 3: SIDIX can SEND tasks to external agents — making SIDIX an orchestrator.

Core subset:
  - discover_agent(url) → fetch AgentCard from /.well-known/agent-card.json
  - send_task(agent_url, message) → POST /a2a/tasks/send (sync)
  - send_task_stream(agent_url, message) → POST /a2a/tasks/sendSubscribe (SSE)
  - poll_task(agent_url, task_id) → GET /a2a/tasks/{taskId}
  - find_best_agent_for_task(message, agents) → simple keyword matching

Self-hosted ONLY: HTTP calls to external A2A agents via the A2A protocol.
No vendor LLM API calls for inference.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel, Field

try:
    import httpx
    _HTTPX_OK = True
except ImportError:
    _HTTPX_OK = False

log = logging.getLogger(__name__)


# ── Models ────────────────────────────────────────────────────────────────────


class ExternalAgent(BaseModel):
    """Representation of a discovered external A2A-compatible agent."""

    name: str
    url: str
    agent_card: dict = Field(default_factory=dict)
    skills: list[str] = Field(default_factory=list)
    mcp_endpoint: str = ""
    capabilities: dict = Field(default_factory=dict)


class A2AClientConfig(BaseModel):
    """Configuration for A2A client HTTP behavior."""

    timeout: float = 30.0
    max_retries: int = 3
    poll_interval: float = 1.0


class DelegationResult(BaseModel):
    """Result of delegating a task to an external agent."""

    success: bool
    task_id: str = ""
    agent_name: str = ""
    artifact_text: str = ""
    duration_ms: int = 0
    error: str = ""


# ── In-memory registry of known external agents ──────────────────────────────

_KNOWN_AGENTS: list[ExternalAgent] = []


def register_agent(agent: ExternalAgent) -> None:
    """Register an external agent in the in-memory registry."""
    # Replace if same URL already exists
    for i, a in enumerate(_KNOWN_AGENTS):
        if a.url == agent.url:
            _KNOWN_AGENTS[i] = agent
            return
    _KNOWN_AGENTS.append(agent)


def list_known_agents() -> list[ExternalAgent]:
    """Return a copy of known external agents."""
    return list(_KNOWN_AGENTS)


def clear_known_agents() -> None:
    """Clear the in-memory registry (mainly for testing)."""
    _KNOWN_AGENTS.clear()


# ── HTTP helpers ─────────────────────────────────────────────────────────────


def _http_client(config: A2AClientConfig | None = None) -> "httpx.Client":
    cfg = config or A2AClientConfig()
    if not _HTTPX_OK:
        raise RuntimeError("httpx tidak terinstall. Jalankan: pip install httpx")
    return httpx.Client(
        timeout=httpx.Timeout(cfg.timeout, connect=10.0),
        follow_redirects=True,
        headers={
            "User-Agent": "SIDIX-A2A-Client/1.0 (mighan-brain-qa; self-hosted)",
            "Accept": "application/json",
        },
    )


def _safe_json(r: "httpx.Response") -> dict:
    try:
        return r.json()
    except Exception:
        return {"raw_text": r.text[:500]}


# ── Discovery ────────────────────────────────────────────────────────────────


def discover_agent(url: str, config: A2AClientConfig | None = None) -> ExternalAgent | None:
    """
    Fetch AgentCard from external agent's well-known path.
    Returns ExternalAgent on success, None on failure.
    """
    url = url.rstrip("/")
    well_known = f"{url}/.well-known/agent-card.json"

    try:
        with _http_client(config) as client:
            r = client.get(well_known)
            if r.status_code == 404:
                # Fallback: some agents may host at root
                r = client.get(f"{url}/agent-card.json")
            r.raise_for_status()
            card = r.json()
    except Exception as exc:
        log.warning("[a2a_client] discover_agent failed for %s: %s", url, exc)
        return None

    skills: list[str] = []
    for skill in card.get("skills", []):
        if isinstance(skill, dict):
            skills.extend(skill.get("tags", []))
            skills.append(skill.get("id", ""))
            skills.append(skill.get("name", ""))
        elif isinstance(skill, str):
            skills.append(skill)
    skills = [s.lower() for s in skills if s]

    agent = ExternalAgent(
        name=card.get("name", "Unknown Agent"),
        url=url,
        agent_card=card,
        skills=list(dict.fromkeys(skills)),  # dedup preserve order
        mcp_endpoint=card.get("mcpEndpoint", ""),
        capabilities=card.get("capabilities", {}),
    )
    register_agent(agent)
    return agent


# ── Task sending (sync) ──────────────────────────────────────────────────────


def send_task(
    agent_url: str,
    message: str,
    config: A2AClientConfig | None = None,
) -> DelegationResult:
    """
    Send a sync task to an external A2A agent via POST /a2a/tasks/send.
    Blocks until the agent returns a final task state.
    """
    agent_url = agent_url.rstrip("/")
    cfg = config or A2AClientConfig()
    t0 = time.time()

    payload = {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": message}],
        }
    }

    try:
        with _http_client(cfg) as client:
            r = client.post(f"{agent_url}/a2a/tasks/send", json=payload)
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        log.warning("[a2a_client] send_task failed for %s: %s", agent_url, exc)
        return DelegationResult(
            success=False,
            error=f"send_task failed: {exc}",
            duration_ms=int((time.time() - t0) * 1000),
        )

    if data.get("error"):
        return DelegationResult(
            success=False,
            error=f"Agent error: {data['error']}",
            duration_ms=int((time.time() - t0) * 1000),
        )

    task_id = data.get("id", "")
    artifacts = data.get("artifacts", [])
    artifact_text = ""
    if artifacts and isinstance(artifacts, list):
        first = artifacts[0]
        parts = first.get("parts", []) if isinstance(first, dict) else []
        for part in parts:
            if isinstance(part, dict) and part.get("type") == "text":
                artifact_text = part.get("text", "")
                break

    # Also try to extract from history if artifacts empty
    if not artifact_text:
        history = data.get("history", [])
        for msg in reversed(history):
            if isinstance(msg, dict) and msg.get("role") == "agent":
                for part in msg.get("parts", []):
                    if isinstance(part, dict) and part.get("type") == "text":
                        artifact_text = part.get("text", "")
                        break
                if artifact_text:
                    break

    return DelegationResult(
        success=data.get("status") == "completed",
        task_id=task_id,
        agent_name=data.get("metadata", {}).get("agent_name", "external"),
        artifact_text=artifact_text or "(no artifact text)",
        duration_ms=int((time.time() - t0) * 1000),
        error="" if data.get("status") == "completed" else f"status={data.get('status')}",
    )


# ── Task sending (streaming) ─────────────────────────────────────────────────


def send_task_stream(
    agent_url: str,
    message: str,
    config: A2AClientConfig | None = None,
) -> Iterator[dict]:
    """
    Send a streaming task to an external A2A agent via POST /a2a/tasks/sendSubscribe.
    Yields SSE event dicts: {event: 'task_status_update'|'task_artifact_update'|'close', ...}
    """
    agent_url = agent_url.rstrip("/")
    cfg = config or A2AClientConfig()

    payload = {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": message}],
        }
    }

    if not _HTTPX_OK:
        yield {"event": "error", "error": "httpx not installed"}
        return

    try:
        with httpx.Client(
            timeout=httpx.Timeout(cfg.timeout, connect=10.0),
            follow_redirects=True,
            headers={
                "User-Agent": "SIDIX-A2A-Client/1.0 (mighan-brain-qa; self-hosted)",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
            },
        ) as client:
            with client.stream("POST", f"{agent_url}/a2a/tasks/sendSubscribe", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        raw = line[6:]
                        try:
                            event = __import__("json").loads(raw)
                        except Exception:
                            event = {"event": "raw", "data": raw}
                        yield event
                    elif line.strip() == "":
                        continue
    except Exception as exc:
        log.warning("[a2a_client] send_task_stream failed for %s: %s", agent_url, exc)
        yield {"event": "error", "error": str(exc)}


# ── Polling ──────────────────────────────────────────────────────────────────


def poll_task(
    agent_url: str,
    task_id: str,
    max_wait: int = 300,
    config: A2AClientConfig | None = None,
) -> DelegationResult:
    """
    Poll an external A2A agent until task completion or timeout.
    GET /a2a/tasks/{taskId}
    """
    agent_url = agent_url.rstrip("/")
    cfg = config or A2AClientConfig()
    t0 = time.time()
    elapsed = 0.0

    terminal = {"completed", "failed", "canceled"}

    try:
        with _http_client(cfg) as client:
            while elapsed < max_wait:
                r = client.get(f"{agent_url}/a2a/tasks/{task_id}")
                if r.status_code != 200:
                    time.sleep(cfg.poll_interval)
                    elapsed += cfg.poll_interval
                    continue

                data = _safe_json(r)
                status = data.get("status", "")

                if status in terminal:
                    artifacts = data.get("artifacts", [])
                    artifact_text = ""
                    if artifacts and isinstance(artifacts, list):
                        first = artifacts[0]
                        parts = first.get("parts", []) if isinstance(first, dict) else []
                        for part in parts:
                            if isinstance(part, dict) and part.get("type") == "text":
                                artifact_text = part.get("text", "")
                                break

                    if not artifact_text:
                        history = data.get("history", [])
                        for msg in reversed(history):
                            if isinstance(msg, dict) and msg.get("role") == "agent":
                                for part in msg.get("parts", []):
                                    if isinstance(part, dict) and part.get("type") == "text":
                                        artifact_text = part.get("text", "")
                                        break
                                if artifact_text:
                                    break

                    return DelegationResult(
                        success=status == "completed",
                        task_id=task_id,
                        agent_name=data.get("metadata", {}).get("agent_name", "external"),
                        artifact_text=artifact_text or "(no artifact text)",
                        duration_ms=int((time.time() - t0) * 1000),
                        error="" if status == "completed" else f"status={status}",
                    )

                time.sleep(cfg.poll_interval)
                elapsed += cfg.poll_interval
    except Exception as exc:
        log.warning("[a2a_client] poll_task failed for %s/%s: %s", agent_url, task_id, exc)
        return DelegationResult(
            success=False,
            task_id=task_id,
            error=f"poll_task failed: {exc}",
            duration_ms=int((time.time() - t0) * 1000),
        )

    return DelegationResult(
        success=False,
        task_id=task_id,
        error=f"poll timeout after {max_wait}s",
        duration_ms=int((time.time() - t0) * 1000),
    )


# ── Best-agent selection (simple keyword match) ──────────────────────────────


def find_best_agent_for_task(message: str, agents: list[ExternalAgent]) -> ExternalAgent | None:
    """
    Simple keyword matching against agent skills.
    Returns the agent with the highest match score, or None if no agents.
    """
    if not agents:
        return None

    msg_lower = message.lower()
    words = set(w.strip(".,;:!?()[]{}\"'") for w in msg_lower.split() if len(w) > 2)

    best_agent: ExternalAgent | None = None
    best_score = -1

    for agent in agents:
        score = 0
        for skill in agent.skills:
            skill_lower = skill.lower()
            if skill_lower in msg_lower:
                score += 3  # phrase match
            for word in words:
                if word in skill_lower:
                    score += 1  # word match
        # Small bonus for agents with more skills (generalists)
        score += min(len(agent.skills), 5) * 0.1

        if score > best_score:
            best_score = score
            best_agent = agent

    return best_agent
