"""
backend/agent_factory.py
────────────────────────
Canonical factory helpers that mint *production-ready* agents for
Alpha-Factory v1 👁️✨.

Design principles
=================
1. **Fail-open** – demos never crash if a dependency is missing;
   they transparently fall back to stubs.
2. **Hardened defaults** – only audited, read-only tools are enabled
   unless the user opts-in to risky local code execution.
3. **Graceful degradation** – cloud LLM → local llama-cpp → SBERT
   heuristics, chosen automatically.
4. **Single source of truth** – every domain-specific agent imports
   *one* helper from here, so the stack remains consistent.
5. **No hidden side-effects** – importing this module never attempts to
   read files, phone home, or allocate GPUs.

Typical usage
=============
```python
from backend.agent_factory import build_core_agent

sentinel = build_core_agent(
    name="Macro-Sentinel",
    instructions="Monitor macro news and hedge the portfolio.",
)
print(sentinel.run("Headline risk today?"))
```
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import platform
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Optional, Sequence

# Environment variables
ALLOW_LOCAL_CODE_ENV = "ALPHA_FACTORY_ALLOW_LOCAL_CODE"
LEGACY_ALLOW_LOCAL_CODE_ENV = "ALPHAFAC_ALLOW_LOCAL_CODE"

LOGGER = logging.getLogger(__name__)

# ╭──────────────────────────────────────────────────────────────────────╮
# │ 1 ▸ Attempt to import the OpenAI Agents SDK                          │
# ╰──────────────────────────────────────────────────────────────────────╯
SDK_AVAILABLE = False
_AGENTS: ModuleType | None = None

try:
    _AGENTS = importlib.import_module("agents")  # optional heavy import
except ModuleNotFoundError:
    LOGGER.warning("OpenAI Agents SDK not found – running in *stub* mode.")
else:
    # Basic sanity check: make sure the SDK looks recent enough.
    SDK_AVAILABLE = hasattr(_AGENTS, "Agent") and hasattr(_AGENTS, "function_tool")

if SDK_AVAILABLE:  # pragma: no cover
    from agents import (  # type: ignore
        Agent,
        ComputerTool,
        FileSearchTool,
        ModelSettings,
        PythonTool,
        RunContextWrapper,
        WebSearchTool,
    )
else:  # --------------------------- stub fall-backs --------------------------

    class _StubTool:  # noqa: D401
        """Callable that only reports unavailability."""

        name = "UnavailableTool"

        def __init__(self, *_, **__):
            pass

        def __call__(self, *_, **__) -> str:  # noqa: D401
            return f"[{self.name} missing – install `openai-agents`]"

        def __repr__(self) -> str:  # noqa: D401
            return self.__class__.__name__

    class FileSearchTool(_StubTool):  # type: ignore
        name = "FileSearchTool"

    class WebSearchTool(_StubTool):  # type: ignore
        name = "WebSearchTool"

    class ComputerTool(_StubTool):  # type: ignore
        name = "ComputerTool"

    class PythonTool(_StubTool):  # type: ignore
        name = "PythonTool"

    class ModelSettings:  # type: ignore
        """Tiny placeholder mirroring SDK signature."""

        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class Agent:  # type: ignore
        """Minimal stand-in that simply echoes prompts."""

        def __init__(
            self,
            *,
            name: str,
            instructions: str,
            model: str,
            model_settings: ModelSettings | None = None,
            tools: Sequence[Any] | None = None,
        ):
            self.name = name
            self.instructions = instructions
            self.model = model
            self._tools = list(tools or [])
            self.model_settings = model_settings or ModelSettings()

        # SDK exposes both run() *and* chat_stream(); we provide both.
        def run(self, prompt: str, *_, **__) -> str:  # noqa: D401
            return f"[{self.name}-stub] echo: {prompt}"

        chat_stream = run  # type: ignore

    # Dummy RunContextWrapper so stubs in tools remain importable
    RunContextWrapper = Dict  # type: ignore

# ╭──────────────────────────────────────────────────────────────────────╮
# │ 2 ▸ Alpha-Factory internal tools                                    │
# ╰──────────────────────────────────────────────────────────────────────╯
try:
    # Always present – shipped in backend/tools/
    from .tools.local_pytest import run_pytest, run_pytest_tool
except Exception as exc:  # pragma: no cover
    LOGGER.error("local_pytest tool could not be imported: %s", exc)
    _exc_msg = str(exc)

    def run_pytest(*_, **__) -> str:  # type: ignore
        return f"[local_pytest unavailable: {_exc_msg}]"

    def run_pytest_tool(*_, **__) -> str:  # type: ignore
        return run_pytest(*_, **__)


# ╭──────────────────────────────────────────────────────────────────────╮
# │ 3 ▸ Model auto-selection helpers                                    │
# ╰──────────────────────────────────────────────────────────────────────╯
def _has_llama_cpp() -> bool:
    """Detect if a llama-cpp based local model is configured."""
    return bool(os.getenv("LLAMA_MODEL_PATH"))


def _auto_select_model() -> str:
    """
    Decide which ``model`` string to pass to the Agent constructor.

    Preference order
    ----------------
    1. ``OPENAI_MODEL`` env override
    2. OPENAI_API_KEY present     → gpt-4o-mini
    3. ANTHROPIC_API_KEY present  → claude-3-sonnet-20240229
    4. llama-cpp env present      → local-llama3-8b-q4
    5. Fallback stub              → local-sbert
    """
    override = os.getenv("OPENAI_MODEL")
    if override:
        return override

    if os.getenv("OPENAI_API_KEY"):
        return "gpt-4o-mini"

    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude-3-sonnet-20240229"

    if _has_llama_cpp():
        return "local-llama3-8b-q4"

    return "local-sbert"


def _allow_local_code() -> bool:
    """Check both new and legacy opts for enabling local PythonTool."""
    return (os.getenv(ALLOW_LOCAL_CODE_ENV) or os.getenv(LEGACY_ALLOW_LOCAL_CODE_ENV)) == "1"


# ╭──────────────────────────────────────────────────────────────────────╮
# │ 4 ▸ Default, *safe* tool-chain                                      │
# ╰──────────────────────────────────────────────────────────────────────╯
def get_default_tools() -> List[Any]:
    """Return the hardened default tool-chain.

    The selection is recalculated each time to honour environment variables
    that may change at runtime.  The returned list is safe to mutate.
    """
    base: List[Any] = [
        FileSearchTool(max_num_results=5),
        WebSearchTool(),
        run_pytest_tool,
    ]

    # Remote tools (ComputerTool runs in OpenAI's sandbox) need an API key.
    if SDK_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        base.append(ComputerTool())

    # PythonTool executes *locally* – only enable if user opts in explicitly.
    if SDK_AVAILABLE and _allow_local_code():
        base.append(PythonTool())

    return base


DEFAULT_TOOLS: List[Any] = get_default_tools()


# ╭──────────────────────────────────────────────────────────────────────╮
# │ 5 ▸ Public factory helpers                                          │
# ╰──────────────────────────────────────────────────────────────────────╯
def build_core_agent(
    *,
    name: str,
    instructions: str,
    extra_tools: Optional[Sequence[Any]] = None,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> Agent:
    """
    Construct and return a fully configured **Agent** (or stub).

    Parameters
    ----------
    name:
        Human-readable identifier (also becomes the ``system`` name in logs).
    instructions:
        High-level role or behaviour guidelines for the agent.
    extra_tools:
        Additional tool callables to append to the default safe set.
    model:
        Override the automatic model selection.
    temperature:
        LLM sampling temperature (ignored in stub mode).
    max_tokens:
        Optional generation cap; forwarded to ModelSettings when supported.

    Notes
    -----
    The default tool selection honours ``OPENAI_API_KEY`` and
    ``ALPHA_FACTORY_ALLOW_LOCAL_CODE`` (or legacy ``ALPHAFAC_ALLOW_LOCAL_CODE``)
    environment variables at call time.
    Set them before invoking this function if the agent requires
    networked or local code execution tools.
    """
    toolset: List[Any] = [*get_default_tools(), *(extra_tools or [])]

    selected_model = model or _auto_select_model()
    model_kwargs: Dict[str, Any] = {"temperature": temperature}
    if max_tokens is not None:
        model_kwargs["max_tokens"] = max_tokens

    LOGGER.debug(
        "Creating agent • name=%s • model=%s • tools=%s",
        name,
        selected_model,
        [getattr(t, "name", str(t)) for t in toolset],
    )

    return Agent(
        name=name,
        instructions=instructions,
        model=selected_model,
        model_settings=ModelSettings(**model_kwargs),
        tools=toolset,
    )


def save_agent_manifest(agent: Agent, path: str | Path) -> None:
    """
    Persist a JSON manifest of an agent for auditing, sharing, or versioning.

    The manifest is *pure metadata* – no weights, no secrets.
    """
    out = {
        "name": getattr(agent, "name", ""),
        "instructions": getattr(agent, "instructions", ""),
        "model": getattr(agent, "model", ""),
        "tools": [getattr(t, "name", str(t)) for t in getattr(agent, "_tools", [])],
        "temperature": getattr(getattr(agent, "model_settings", None), "kwargs", {}),
        "sdk_available": SDK_AVAILABLE,
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    out_path = Path(path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    LOGGER.info("Agent manifest saved to %s", out_path)


# Backwards-compat shim – older notebooks call ``build_agent``
build_agent = build_core_agent

__all__ = [
    "build_core_agent",
    "build_agent",
    "save_agent_manifest",
    "get_default_tools",
    "DEFAULT_TOOLS",
    *(
        # Only export SDK symbols when they are genuinely available
        ["Agent", "FileSearchTool", "WebSearchTool", "ComputerTool", "PythonTool"]
        if SDK_AVAILABLE
        else []
    ),
]
