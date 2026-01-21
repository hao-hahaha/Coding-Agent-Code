"""Placeholder meta-rewrite function."""

from __future__ import annotations

import random
from typing import List
import importlib
import asyncio
import os
import logging
import re


def meta_rewrite(agents: List[int]) -> List[int]:
    """Return a modified copy of ``agents`` with a small random change."""
    new_agents = list(agents)
    idx = random.randrange(len(new_agents))
    new_agents[idx] += random.choice([-1, 1])
    return new_agents


def _parse_numbers(text: str, fallback: List[int]) -> List[int]:
    """Return integers parsed from ``text`` or a simple increment fallback."""
    numbers = [int(n) for n in re.findall(r"-?\d+", text)]
    return numbers or [p + 1 for p in fallback]


def openai_rewrite(agents: List[int]) -> List[int]:
    """Improve ``agents`` using OpenAI Agents SDK and Google ADK when available.

    The routine falls back to :func:`meta_rewrite` when the required
    libraries are missing or any error occurs.  This keeps the demo
    functional in fully offline environments. When the optional
    dependencies are present, a tiny ``RewriterAgent`` is instantiated
    and invoked once to illustrate how the Agents SDK could be wired
    into the search loop.  The implementation uses ``asyncio`` under the
    hood but exposes a synchronous API so the rest of the demo can run
    without an event loop.
    """

    have_oai = importlib.util.find_spec("openai_agents") is not None
    have_adk = importlib.util.find_spec("google_adk") is not None
    have_openai = importlib.util.find_spec("openai") is not None

    if have_oai and have_openai and os.getenv("OPENAI_API_KEY"):
        try:  # pragma: no cover - optional integration
            from openai_agents import Agent, Tool  # type: ignore
            import openai  # type: ignore

            if have_adk:
                from google_adk import agent2agent  # type: ignore

            @Tool(
                name="improve_policy", description="Return an improved integer policy"
            )
            async def improve_policy(policy: list[int]) -> list[int]:
                prompt = (
                    "Given the current integer policy "
                    f"{policy}, suggest a slightly improved list of integers."
                )
                try:
                    response = await openai.ChatCompletion.acreate(
                        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                        messages=[
                            {
                                "role": "system",
                                "content": "You rewrite policies for a simple number line game.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=20,
                    )
                    text = response.choices[0].message.content or ""
                except Exception:
                    text = ""

                return _parse_numbers(text, policy)

            class RewriterAgent(Agent):
                name = "mats_rewriter"
                tools = [improve_policy]

                async def policy(self, obs, _ctx):  # type: ignore[override]
                    cand = obs.get("policy", []) if isinstance(obs, dict) else obs
                    return await improve_policy(list(cand))

            agent = RewriterAgent()

            async def _run() -> list[int]:
                result = await agent.policy({"policy": agents}, {})
                if have_adk:
                    _ = agent2agent  # pragma: no cover - placeholder use
                return list(result)

            return asyncio.run(_run())
        except Exception as exc:  # pragma: no cover - safety net
            logging.warning(f"openai_rewrite fallback due to error: {exc}")

    # Fallback: simple random tweak
    return meta_rewrite(agents)
