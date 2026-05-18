"""spawning package — Sprint K: Multi-Agent Spawning Foundation."""
from .shared_context import SharedContext, ContextEntry, SpawnSession
from .sub_agent_factory import SubAgentFactory, SubAgentHandle, AgentSpec

__all__ = [
    "SharedContext",
    "ContextEntry",
    "SpawnSession",
    "SubAgentFactory",
    "SubAgentHandle",
    "AgentSpec",
]
