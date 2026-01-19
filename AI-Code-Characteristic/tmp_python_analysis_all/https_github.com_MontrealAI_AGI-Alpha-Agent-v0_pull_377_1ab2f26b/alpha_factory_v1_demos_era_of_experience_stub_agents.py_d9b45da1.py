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

try:  # OpenAI Agents SDK (tool-calling, memory, planning)
    from openai_agents import Agent
except Exception:  # pragma: no cover - optional dependency
    Agent = object  # type: ignore

try:  # Google Agent Development Kit (A2A protocol)
    from google_adk import Agent as ADKAgent
except Exception:  # pragma: no cover - optional dependency
    ADKAgent = object  # type: ignore


class ExperienceAgent(Agent):
    """Tiny wrapper around :class:`openai_agents.Agent`.

    This stub illustrates where one could attach custom tools or reward
    functions. The default ``act`` simply returns a placeholder action so
    unit tests can run without an API key.
    """

    async def act(self) -> Dict[str, Any]:  # type: ignore[override]
        return {"action": "noop"}


class FederatedExperienceAgent(ADKAgent):
    """Sketch of an ADK-compatible agent for A2A federation.

    Real implementations would define ``handle_request`` to process A2A
    messages. Here we return a minimal canned response.
    """

    async def handle_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:  # type: ignore[override]
        return {"echo": payload}
