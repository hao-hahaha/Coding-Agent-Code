"""OpenAI Agents SDK bridge for the alpha_agi_business_v1 demo.

This utility registers a small helper agent that interacts with the
local orchestrator. It works offline when no API key is configured.
"""
from __future__ import annotations

import argparse
import os
import sys
import requests

try:  # soft dependency
    from openai_agents import Agent, AgentRuntime, Tool  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - optional dep
    sys.stderr.write(
        "\n❌  openai_agents not installed. Install with 'pip install openai-agents'\n"
    )
    sys.exit(1)

try:
    # Optional ADK bridge
    from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch
    ADK_AVAILABLE = True
except ImportError:  # pragma: no cover - ADK not installed
    ADK_AVAILABLE = False

HOST = os.getenv("BUSINESS_HOST", "http://localhost:8000")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expose alpha_agi_business_v1 via OpenAI Agents runtime"
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help="Orchestrator host URL (default: http://localhost:8000)",
    )
    return parser.parse_args(argv)


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


@Tool(name="trigger_opportunity", description="Trigger the AlphaOpportunityAgent")
async def trigger_opportunity() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_opportunity/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_opportunity queued"


@Tool(name="trigger_execution", description="Trigger the AlphaExecutionAgent")
async def trigger_execution() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_execution/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_execution queued"


class BusinessAgent(Agent):
    """Tiny agent exposing orchestrator helper tools."""

    name = "business_helper"
    tools = [list_agents, trigger_discovery, trigger_opportunity, trigger_execution]

    async def policy(self, obs, ctx):  # type: ignore[override]
        if isinstance(obs, dict):
            if obs.get("action") == "discover":
                return await self.tools.trigger_discovery()
            elif obs.get("action") == "opportunity":
                return await self.tools.trigger_opportunity()
            elif obs.get("action") == "execute":
                return await self.tools.trigger_execution()
        return await self.tools.list_agents()


def main() -> None:
    args = _parse_args()
    global HOST
    HOST = args.host
    api_key = os.getenv("OPENAI_API_KEY") or None
    runtime = AgentRuntime(api_key=api_key)
    agent = BusinessAgent()
    runtime.register(agent)
    print(f"Registered BusinessAgent -> {HOST}")

    if ADK_AVAILABLE:
        auto_register([agent])
        maybe_launch()
        print("BusinessAgent exposed via ADK gateway")

    runtime.run()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
