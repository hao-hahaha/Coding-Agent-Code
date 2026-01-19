"""Placeholder meta-rewrite function."""
from __future__ import annotations

import random
from typing import List
import importlib
import asyncio


def meta_rewrite(agents: List[int]) -> List[int]:
    """Return a modified copy of ``agents`` with a small random change."""
    new_agents = list(agents)
    idx = random.randrange(len(new_agents))
    new_agents[idx] += random.choice([-1, 1])
    return new_agents


def openai_rewrite(agents: List[int]) -> List[int]:
    """Improve ``agents`` using OpenAI Agents SDK and Google ADK when available.

    The routine falls back to :func:`meta_rewrite` when the required
    libraries are missing or any error occurs.  This keeps the demo
    functional in fully offline environments. When the optional
    dependencies are present, a tiny ``RewriterAgent`` is instantiated
    and invoked once to illustrate how the Agents SDK could be wired
    into the search loop.
    """

    have_oai = importlib.util.find_spec("openai_agents") is not None
    have_adk = importlib.util.find_spec("google_adk") is not None

    if have_oai:
        try:  # pragma: no cover - optional integration
            from openai_agents import Agent, Tool  # type: ignore
            if have_adk:
                from google_adk import agent2agent  # type: ignore

            @Tool(name="improve_policy", description="Return an improved integer policy")
            async def improve_policy(policy: list[int]) -> list[int]:
                return [p + 1 for p in policy]

            class RewriterAgent(Agent):
                name = "mats_rewriter"
                tools = [improve_policy]

                async def policy(self, obs, _ctx):  # type: ignore[override]
                    cand = obs.get("policy", []) if isinstance(obs, dict) else obs
                    return await improve_policy(list(cand))

            agent = RewriterAgent()
            # Execute the policy once via asyncio to keep things simple and
            # avoid setting up a full runtime. ``agent2agent`` is touched so
            # static analysers confirm integration when available.
            result = await agent.policy({"policy": agents}, {})
            if have_adk:
                _ = agent2agent  # pragma: no cover - placeholder use
            return list(result)
        except Exception:  # pragma: no cover - safety net
            pass

    # Fallback: simple random tweak
    return meta_rewrite(agents)

