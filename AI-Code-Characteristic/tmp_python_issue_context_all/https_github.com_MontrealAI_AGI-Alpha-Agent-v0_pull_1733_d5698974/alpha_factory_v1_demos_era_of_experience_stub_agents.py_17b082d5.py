# SPDX-License-Identifier: Apache-2.0
"""Stub agents illustrating potential OpenAI SDK and Google ADK workflows.

This module provides bare-bones agent classes demonstrating how the
`openai_agents` SDK and Google's ADK could be extended within the
Era-of-Experience demo. These classes intentionally keep the
implementation minimal so they can serve as educational starting points
for custom deployments.

The stubs operate without network calls when the respective libraries
are missing, allowing the tests to import the file even in restricted
CI environments.
"""
from __future__ import annotations

from typing import Any, Dict


def _safe_import_agent(module_name: str, class_name: str) -> type:
    """Safely import an agent class, falling back to `object` if unavailable."""
    try:
        module = __import__(module_name, fromlist=[class_name])
        agent_class = getattr(module, class_name)
        if not isinstance(agent_class, type):  # shim may return a sentinel object
            return object  # type: ignore[misc]
        return agent_class
    except Exception:  # pragma: no cover - optional dependency
        return object  # type: ignore


Agent = _safe_import_agent("openai_agents", "Agent")  # OpenAI Agents SDK
ADKAgent = _safe_import_agent("google_adk", "Agent")  # Google ADK


class ExperienceAgent(Agent):
    """Tiny wrapper around :class:`openai_agents.Agent`.

    This stub illustrates where one could attach custom tools or reward
    functions. The default ``act`` simply returns a placeholder action so
    unit tests can run without an API key.
    """

    def __init__(self, name: str | None = None, **kwargs: Any) -> None:  # type: ignore[override]
        name = name or "experience-agent"
        try:
            super().__init__(name=name, **kwargs)
        except TypeError:
            super().__init__()

    async def act(self) -> Dict[str, Any]:  # type: ignore[override]
        return {"action": "noop"}


class FederatedExperienceAgent(ADKAgent):
    """Sketch of an ADK-compatible agent for A2A federation.

    Real implementations would define ``handle_request`` to process A2A
    messages. Here we return a minimal canned response.
    """

    async def handle_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        return {"echo": payload}
