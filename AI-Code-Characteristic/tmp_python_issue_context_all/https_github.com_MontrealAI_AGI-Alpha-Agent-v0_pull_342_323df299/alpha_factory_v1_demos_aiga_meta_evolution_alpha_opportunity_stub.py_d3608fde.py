"""Alpha opportunity discovery agent stub.

This lightweight example exposes a single tool via the OpenAI Agents SDK
that requests the LLM to list live market inefficiencies. It falls back to
a local model when no ``OPENAI_API_KEY`` is configured.
"""
from __future__ import annotations

import os

try:
    from openai_agents import Agent, AgentRuntime, OpenAIAgent, Tool
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit(
        "openai-agents package is required. Install with `pip install openai-agents`"
    ) from exc

LLM = OpenAIAgent(
    model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=(None if os.getenv("OPENAI_API_KEY") else os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")),
)


@Tool(name="identify_alpha", description="Suggest current inefficiencies in a domain")
async def identify_alpha(domain: str = "finance") -> str:
    prompt = (
        f"List three emerging opportunities or inefficiencies in the {domain} domain "
        "that a small team could exploit for outsized value."
    )
    return LLM(prompt)


class AlphaDiscoveryAgent(Agent):
    """Minimal agent exposing the ``identify_alpha`` tool."""

    name = "alpha_discovery"
    tools = [identify_alpha]

    async def policy(self, obs, ctx):  # type: ignore[override]
        domain = obs.get("domain", "finance") if isinstance(obs, dict) else "finance"
        return await identify_alpha(domain)


def main() -> None:
    runtime = AgentRuntime(api_key=None)
    agent = AlphaDiscoveryAgent()
    runtime.register(agent)
    print("Registered AlphaDiscoveryAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
