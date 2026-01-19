"""OpenAI Agents SDK bridge for the Meta-Agentic \u03b1-AGI demo.

Registers a minimal agent that exposes the demo's meta-search loop as an
OpenAI Agents runtime. Works offline when no API key is configured.
"""
from __future__ import annotations

import os
try:
    from openai_agents import Agent, AgentRuntime, Tool
except ModuleNotFoundError as exc:  # pragma: no cover - graceful degradation
    raise SystemExit(
        "openai-agents package is missing. Install with `pip install openai-agents`"
    ) from exc

from meta_agentic_agi_demo import meta_loop


@Tool(name="run_meta_search", description="Run the meta-agentic search loop")
async def run_meta_search(generations: int = 3) -> str:
    """Execute the demo search loop for a given number of generations."""
    provider = os.getenv("LLM_PROVIDER", "mistral:7b-instruct.gguf")
    await meta_loop(generations, provider)
    return f"Completed {generations} generations"


class MetaSearchAgent(Agent):
    """Tiny agent wrapping the demo entry point."""

    name = "meta_search"
    tools = [run_meta_search]

    async def policy(self, obs, ctx):  # type: ignore[override]
        gens = int(obs.get("generations", 3)) if isinstance(obs, dict) else 3
        return await self.tools.run_meta_search(gens)


def main() -> None:
    runtime = AgentRuntime(api_key=None)
    agent = MetaSearchAgent()
    runtime.register(agent)
    # Optional cross-process federation via Google ADK
    try:
        from alpha_factory_v1.backend import adk_bridge
        if adk_bridge.adk_enabled():
            adk_bridge.auto_register([agent])
            adk_bridge.maybe_launch()
    except Exception as exc:  # pragma: no cover - ADK optional
        print(f"ADK bridge unavailable: {exc}")

    print("Registered MetaSearchAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
