"""End-to-end Alpha Factory workflow demo.

This script chains the ``alpha_discovery`` and ``alpha_conversion``
stubs via the OpenAI Agents runtime. It works offline when
``OPENAI_API_KEY`` is unset and optionally exposes the agent over
the Google ADK gateway if available.
"""
from __future__ import annotations

import os

try:
    from openai_agents import Agent, AgentRuntime, OpenAIAgent, Tool
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "openai_agents package is required. Install with `pip install openai-agents`"
    ) from exc

from alpha_opportunity_stub import identify_alpha
from alpha_conversion_stub import convert_alpha

try:
    from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch
    ADK_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    ADK_AVAILABLE = False

# ---------------------------------------------------------------------------
# LLM setup -----------------------------------------------------------------
# ---------------------------------------------------------------------------
LLM = OpenAIAgent(
    model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=(None if os.getenv("OPENAI_API_KEY") else os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")),
)


@Tool(name="discover_alpha", description="List market opportunities in a domain")
async def discover_alpha(domain: str = "finance") -> str:
    return await identify_alpha(domain)


@Tool(name="convert_alpha", description="Turn an opportunity into an execution plan")
async def convert_alpha_tool(alpha: str) -> dict:
    return convert_alpha(alpha)


class WorkflowAgent(Agent):
    """Simple agent chaining discovery and conversion."""

    name = "alpha_workflow"
    tools = [discover_alpha, convert_alpha_tool]

    async def policy(self, obs, ctx):  # type: ignore[override]
        domain = obs.get("domain", "finance") if isinstance(obs, dict) else "finance"
        alphas = await discover_alpha(domain)
        first = alphas.split("\n")[0].strip()
        plan = await convert_alpha_tool(first)
        return {"alpha": first, "plan": plan}


def main() -> None:
    runtime = AgentRuntime(llm=LLM)
    agent = WorkflowAgent()
    runtime.register(agent)
    print("Registered WorkflowAgent with runtime")

    if ADK_AVAILABLE:
        auto_register([agent])
        maybe_launch()
        print("WorkflowAgent exposed via ADK gateway")

    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
