"""Minimal OpenAI Agents SDK bridge for the α‑ASI demo.

This utility registers a tiny inspector agent with the local orchestrator
and prints the list of active agents. It works offline when no API key is
provided. Run after the demo server is up:

    python openai_agents_bridge.py
"""
from __future__ import annotations

import requests
from openai_agents import Agent, AgentRuntime, Tool


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
    rt.register(InspectorAgent())
    print("Registered InspectorAgent with runtime")
    rt.run()


if __name__ == "__main__":
    main()
