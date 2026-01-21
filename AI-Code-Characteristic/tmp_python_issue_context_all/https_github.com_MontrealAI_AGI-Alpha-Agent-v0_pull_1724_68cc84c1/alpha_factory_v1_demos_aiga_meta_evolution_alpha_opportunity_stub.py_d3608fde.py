# SPDX-License-Identifier: Apache-2.0
"""Alpha opportunity discovery agent stub.

This lightweight example exposes a single tool via the OpenAI Agents SDK
that requests the LLM to list live market inefficiencies. It falls back to
a local model when no ``OPENAI_API_KEY`` is configured.
"""
from __future__ import annotations

try:
    from openai_agents import Agent, AgentRuntime, OpenAIAgent, Tool
except Exception as exc:  # pragma: no cover - optional dependency
    raise SystemExit("openai-agents package is required. Install with `pip install openai-agents`") from exc

from .utils import build_llm

LLM = build_llm()


@Tool(name="identify_alpha", description="Suggest current inefficiencies in a domain")
async def identify_alpha(domain: str = "finance") -> str:
    prompt = (
        f"List three emerging opportunities or inefficiencies in the {domain} domain "
        "that a small team could exploit for outsized value."
    )
    return await LLM(prompt)


class AlphaDiscoveryAgent(Agent):
    """Minimal agent exposing the ``identify_alpha`` tool."""

    name = "alpha_discovery"
    tools = [identify_alpha]

    async def policy(self, obs, ctx):  # type: ignore[override]
        domain = obs.get("domain", "finance") if isinstance(obs, dict) else "finance"
        return await identify_alpha(domain)


def main(argv: list[str] | None = None) -> None:
    """Launch the agent runtime or run a single query."""
    import argparse
    import asyncio

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--domain", default="finance", help="domain to scan")
    ap.add_argument(
        "--once",
        action="store_true",
        help="run a single identify_alpha call and exit",
    )
    args = ap.parse_args(argv)

    if args.once:
        result = asyncio.run(identify_alpha(args.domain))
        print(result)
        return

    runtime = AgentRuntime(api_key=None)
    agent = AlphaDiscoveryAgent()
    runtime.register(agent)
    print("Registered AlphaDiscoveryAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
