"""OpenAI Agents SDK bridge for the alpha_agi_business_v1 demo.

This utility registers a small helper agent that interacts with the
local orchestrator. It works offline when no API key is configured.
"""
from __future__ import annotations

import requests
from openai_agents import Agent, AgentRuntime, Tool

HOST = "http://localhost:8000"


@Tool(name="list_agents", description="List active orchestrator agents")
async def list_agents() -> list[str]:
    resp = requests.get(f"{HOST}/agents", timeout=5)
    resp.raise_for_status()
    return resp.json()


@Tool(name="trigger_discovery", description="Trigger the AlphaDiscoveryAgent")
async def trigger_discovery() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_discovery/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_discovery queued"


class BusinessAgent(Agent):
    """Tiny agent exposing orchestrator helper tools."""

    name = "business_helper"
    tools = [list_agents, trigger_discovery]

    async def policy(self, obs, ctx):  # type: ignore[override]
        if isinstance(obs, dict) and obs.get("action") == "discover":
            return await self.tools.trigger_discovery()
        return await self.tools.list_agents()


def main() -> None:
    runtime = AgentRuntime(api_key=None)
    runtime.register(BusinessAgent())
    print("Registered BusinessAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
