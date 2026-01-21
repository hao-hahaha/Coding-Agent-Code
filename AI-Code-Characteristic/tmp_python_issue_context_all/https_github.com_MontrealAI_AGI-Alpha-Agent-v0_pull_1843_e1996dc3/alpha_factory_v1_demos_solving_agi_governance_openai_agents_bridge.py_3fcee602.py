# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""OpenAI Agents SDK bridge for the solving_agi_governance demo."""
from __future__ import annotations

import argparse
import logging

from .governance_sim import run_sim

logger = logging.getLogger(__name__)

try:
    from openai_agents import Agent, AgentRuntime, Tool
except ModuleNotFoundError as exc:  # pragma: no cover - optional dep
    raise SystemExit(
        "openai-agents package is missing. Install with `pip install openai-agents`"
    ) from exc


@Tool(name="run_sim", description="Run governance simulation")
async def run_sim_tool(
    agents: int = 100,
    rounds: int = 1000,
    delta: float = 0.8,
    stake: float = 2.5,
) -> float:
    return run_sim(agents=agents, rounds=rounds, delta=delta, stake=stake)


class GovernanceSimAgent(Agent):
    """Agent exposing the governance simulation."""

    name = "governance_sim"
    tools = [run_sim_tool]

    async def policy(self, obs, ctx):  # type: ignore[override]
        if isinstance(obs, dict):
            return await self.tools.run_sim(
                int(obs.get("agents", 100)),
                int(obs.get("rounds", 1000)),
                float(obs.get("delta", 0.8)),
                float(obs.get("stake", 2.5)),
            )
        return await self.tools.run_sim()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Expose the governance simulation via OpenAI Agents runtime"
    )
    ap.add_argument(
        "--enable-adk",
        action="store_true",
        help="Expose agent via ADK gateway",
    )
    ap.add_argument(
        "--port",
        type=int,
        help="Custom port for the Agents runtime",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    if args.port is not None:
        runtime = AgentRuntime(port=args.port, api_key=None)
    else:
        runtime = AgentRuntime(api_key=None)
    agent = GovernanceSimAgent()
    runtime.register(agent)
    if args.enable_adk:
        try:
            from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch

            auto_register([agent])
            maybe_launch()
        except Exception as exc:  # pragma: no cover - ADK optional
            logger.warning(f"ADK bridge unavailable: {exc}")
    logger.info("Registered GovernanceSimAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
