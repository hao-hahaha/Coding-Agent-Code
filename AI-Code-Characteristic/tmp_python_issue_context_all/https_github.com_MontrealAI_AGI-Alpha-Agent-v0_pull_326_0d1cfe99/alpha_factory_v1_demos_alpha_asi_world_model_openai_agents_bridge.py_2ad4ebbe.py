"""Minimal OpenAI Agents & Google ADK bridge for the α‑ASI demo.

This utility registers a tiny inspector agent with the local orchestrator
and prints the list of active agents. When the optional Google ADK
dependency is installed and ``ALPHA_FACTORY_ENABLE_ADK=true`` is set,
the agent is also exposed via an ADK gateway. It works offline when no API
key is provided. Run after the demo server is up:

    python openai_agents_bridge.py
"""
from __future__ import annotations

import requests
from openai_agents import Agent, AgentRuntime, Tool

try:
    # Optional ADK integration
    from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch
    ADK_AVAILABLE = True
except Exception:  # pragma: no cover - adk not installed
    ADK_AVAILABLE = False


@Tool(name="list_agents", description="List active orchestrator agents")
async def list_agents() -> list[str]:
    resp = requests.get("http://localhost:7860/agents", timeout=5)
    resp.raise_for_status()
    return resp.json()


class InspectorAgent(Agent):
    name = "inspector"
    tools = [list_agents]

    async def policy(self, obs, ctx):  # type: ignore[override]
        return await self.tools.list_agents()


def main() -> None:
    rt = AgentRuntime(api_key=None)
    agent = InspectorAgent()
    rt.register(agent)
    print("Registered InspectorAgent with runtime")

    if ADK_AVAILABLE:
        auto_register([agent])
        maybe_launch()
        print("InspectorAgent exposed via ADK gateway")

    rt.run()


if __name__ == "__main__":
    main()
