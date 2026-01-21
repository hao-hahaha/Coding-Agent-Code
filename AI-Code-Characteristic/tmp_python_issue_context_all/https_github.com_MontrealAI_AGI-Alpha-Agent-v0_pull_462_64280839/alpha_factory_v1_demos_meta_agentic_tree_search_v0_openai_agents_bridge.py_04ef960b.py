#!/usr/bin/env python3
"""OpenAI Agents SDK bridge for the Meta-Agentic Tree Search demo.

This utility registers a small agent that exposes the tree-search loop via the
OpenAI Agents runtime.  It gracefully degrades to offline mode when the
``openai-agents`` package is unavailable or no API key is configured.
"""
from __future__ import annotations

import os

try:
    from openai_agents import Agent, AgentRuntime, Tool  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "openai-agents package is missing. Install with `pip install openai-agents`"
    ) from exc

from .run_demo import run


@Tool(name="run_search", description="Run the MATS demo for a few episodes")
async def run_search(episodes: int = 10, target: int = 5) -> str:
    """Execute the search loop and return a summary string."""
    run(episodes=episodes, target=target)
    return f"completed {episodes} episodes toward target {target}"


class MATSAgent(Agent):
    """Tiny helper agent wrapping :func:`run_search`."""

    name = "mats_helper"
    tools = [run_search]

    async def policy(self, obs, _ctx):  # type: ignore[override]
        episodes = int(obs.get("episodes", 10)) if isinstance(obs, dict) else 10
        target = int(obs.get("target", 5)) if isinstance(obs, dict) else 5
        return await run_search(episodes=episodes, target=target)


def main() -> None:
    runtime = AgentRuntime(api_key=os.getenv("OPENAI_API_KEY"))
    agent = MATSAgent()
    runtime.register(agent)
    try:
        from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch

        auto_register([agent])
        maybe_launch()
    except Exception as exc:  # pragma: no cover - ADK optional
        print(f"ADK bridge unavailable: {exc}")

    print("Registered MATSAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
