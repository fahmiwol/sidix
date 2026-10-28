"""
example_plugin.py — Example SIDIX Tool Plugin.

Copy this file as a template for new plugins:
    cp apps/brain_qa/brain_qa/plugins/example_plugin.py \
       apps/brain_qa/brain_qa/plugins/my_plugin.py

Then:
    1. Rename ExamplePlugin → MyPlugin
    2. Replace summarize_text() with your tool function(s)
    3. Update the register() call with your tool name and permissions
    4. Import in brain_qa/plugins/__init__.py to auto-register on startup

Plugin Interface Contract:
    - Tool functions must accept only JSON-serialisable arguments (str, int,
      float, bool, list, dict).
    - Tool functions must return a str (the final answer / result).
    - Tool functions should be pure or side-effect-free where possible.
    - Permissions declared at registration time are enforced by the SIDIX
      ReAct agent loop before calling the tool.

Available permission tokens:
    "read"    — read-only access to corpus / index
    "write"   — may mutate state (use sparingly)
    "network" — may make outbound HTTP calls (no vendor APIs)
    "system"  — may call subprocess / OS commands (requires explicit approval)
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

# ---------------------------------------------------------------------------
# Lazy import guard — ToolRegistry may not exist yet in early bootstrap.
# The registration block at the bottom handles import errors gracefully.
# ---------------------------------------------------------------------------
if TYPE_CHECKING:
    from brain_qa.agent_tools import ToolRegistry  # noqa: F401


# ---------------------------------------------------------------------------
# ExamplePlugin class
# ---------------------------------------------------------------------------

class ExamplePlugin:
    """
    Example plugin demonstrating the SIDIX plugin architecture.

    Plugins are plain Python classes. The class itself is optional — you can
    also register module-level functions directly. The class pattern is useful
    when your tool needs initialisation state (e.g. a loaded model or cache).

    Lifecycle:
        1. Module is imported (e.g. by brain_qa/plugins/__init__.py)
        2. The bottom-of-file registration block runs
        3. ToolRegistry.register() stores the callable under a named key
        4. The SIDIX ReAct agent loop calls the tool by name when needed
    """

    def __init__(self) -> None:
        # Place any one-time initialisation here (load model, open DB, etc.)
        self._initialized = True

    # ------------------------------------------------------------------
    # Tool function: summarize_text
    # ------------------------------------------------------------------

    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
        """
        Summarise *text* to at most *max_sentences* sentences.

        This is a stub implementation using simple sentence splitting.
        Replace with a real summarisation model or algorithm for production.

        Args:
            text:          The input text to summarise.
            max_sentences: Maximum number of sentences to include (default 3).

        Returns:
            A short summary string.

        Example (as used by ReAct agent):
            tool_call: summarize_text(text="long article...", max_sentences=2)
            → "First sentence. Second sentence."
        """
        if not text or not text.strip():
            return "[ExamplePlugin] No text provided to summarize."

        # Naive sentence split — replace with spaCy / nltk for production
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        selected = sentences[:max_sentences]
        summary = ". ".join(selected)
        if summary and not summary.endswith("."):
            summary += "."

        # Wrap long lines for readability in the agent scratchpad
        summary = textwrap.fill(summary, width=100)

        return f"[ExamplePlugin.summarize] {summary}"


# ---------------------------------------------------------------------------
# Module-level tool function (alternative registration style)
# ---------------------------------------------------------------------------

def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Module-level wrapper around ExamplePlugin.summarize_text.

    This function is what gets registered with ToolRegistry — it delegates
    to an ExamplePlugin instance. Keeping the registration target as a plain
    function (not a bound method) makes the registry simpler.

    Args:
        text:          Input text to summarise.
        max_sentences: Number of sentences to return (default 3).

    Returns:
        Summary string starting with "[ExamplePlugin.summarize]".
    """
    _plugin = ExamplePlugin()
    return _plugin.summarize_text(text=text, max_sentences=max_sentences)


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------
# This block runs when the module is imported. It registers the tool with
# SIDIX's ToolRegistry so the ReAct agent can call it by name.
#
# ToolRegistry.register(
#     name        — unique key used in agent tool_call JSON
#     fn          — callable(text: str, ...) → str
#     permissions — list of permission tokens the agent must hold
#     description — human-readable description shown in agent system prompt
# )
# ---------------------------------------------------------------------------

try:
    from brain_qa.agent_tools import ToolRegistry  # type: ignore[import]

    ToolRegistry.register(
        name="summarize_text",
        fn=summarize_text,
        permissions=["read"],
        description=(
            "Summarise a block of text into a fixed number of sentences. "
            "Args: text (str), max_sentences (int, default 3). "
            "Returns a concise summary string."
        ),
    )

except ImportError:
    # ToolRegistry not yet available (e.g. during unit tests or early import).
    # The plugin is still importable; registration simply does not occur.
    import warnings
    warnings.warn(
        "brain_qa.agent_tools not found — ExamplePlugin not registered with ToolRegistry. "
        "This is expected during standalone testing.",
        ImportWarning,
        stacklevel=1,
    )
