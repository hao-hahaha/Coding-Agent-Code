"""OpenAI Agents SDK bridge for the Meta-Agentic \u03b1-AGI demo.

Registers a minimal agent that exposes the demo's meta-search loop as an
OpenAI Agents runtime. Works offline when no API key is configured.
"""
from __future__ import annotations

import os
from openai_agents import Agent, AgentRuntime, Tool

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
    runtime.register(MetaSearchAgent())
    print("Registered MetaSearchAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
