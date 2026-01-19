#!/usr/bin/env python3
"""Alpha‑AGI Business v1 demo.

Bootstraps a minimal Alpha‑Factory orchestrator with two stub agents.
The demo operates fully offline but upgrades to cloud LLM tooling
automatically when ``OPENAI_API_KEY`` is present.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
from pathlib import Path

from alpha_factory_v1.backend import orchestrator
from alpha_factory_v1.backend.agents import AgentMetadata, register_agent
from alpha_factory_v1.backend.agents.base import AgentBase


class IncorporatorAgent(AgentBase):
    """Toy agent that emits a one‑time incorporation event."""

    NAME = "incorporator"
    CAPABILITIES = ["incorporate"]
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.business", {"msg": "company incorporated"})


class AlphaDiscoveryAgent(AgentBase):
    """Stub agent that emits a placeholder alpha opportunity."""

    NAME = "alpha_discovery"
    CAPABILITIES = ["discover"]
    CYCLE_SECONDS = 120
    __slots__ = ()

    async def step(self) -> None:
        await self.publish(
            "alpha.discovery", {"alpha": "cross-market synergy identified"}
        )

class AlphaOpportunityAgent(AgentBase):
    """Stub agent emitting a sample market inefficiency."""

    NAME = "alpha_opportunity"
    CAPABILITIES = ["opportunity"]
    CYCLE_SECONDS = 300
    __slots__ = ("_opportunities",)

    def __init__(self) -> None:
        super().__init__()
        env_path = os.getenv("ALPHA_OPPS_FILE")
        path = Path(env_path) if env_path else Path(__file__).with_name("examples") / "alpha_opportunities.json"
        try:
            self._opportunities = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:  # pragma: no cover - fallback when file missing
            self._opportunities = [
                {"alpha": "generic supply-chain inefficiency"}
            ]
        except json.JSONDecodeError:  # pragma: no cover - fallback for invalid JSON
            self._opportunities = [
                {"alpha": "generic supply-chain inefficiency"}
            ]

    async def step(self) -> None:
        choice = random.choice(self._opportunities)
        await self.publish("alpha.opportunity", choice)


class AlphaExecutionAgent(AgentBase):
    """Stub agent converting an opportunity into an executed trade."""

    NAME = "alpha_execution"
    CAPABILITIES = ["execute"]
    CYCLE_SECONDS = 180
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.execution", {"alpha": "order executed"})


class AlphaRiskAgent(AgentBase):
    """Stub agent performing a placeholder risk assessment."""

    NAME = "alpha_risk"
    CAPABILITIES = ["risk"]
    CYCLE_SECONDS = 240
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.risk", {"risk": "risk level nominal"})


def register_demo_agents() -> None:
    """Register built-in demo agents with the framework."""

    register_agent(
        AgentMetadata(
            name=IncorporatorAgent.NAME,
            cls=IncorporatorAgent,
            version="1.0.0",
            capabilities=IncorporatorAgent.CAPABILITIES,
        )
    )

    register_agent(
        AgentMetadata(
            name=AlphaDiscoveryAgent.NAME,
            cls=AlphaDiscoveryAgent,
            version="1.0.0",
            capabilities=AlphaDiscoveryAgent.CAPABILITIES,
        )
    )

    register_agent(
        AgentMetadata(
            name=AlphaOpportunityAgent.NAME,
            cls=AlphaOpportunityAgent,
            version="1.0.0",
            capabilities=AlphaOpportunityAgent.CAPABILITIES,
        )
    )

    register_agent(
        AgentMetadata(
            name=AlphaExecutionAgent.NAME,
            cls=AlphaExecutionAgent,
            version="1.0.0",
            capabilities=AlphaExecutionAgent.CAPABILITIES,
        )
    )

    register_agent(
        AgentMetadata(
            name=AlphaRiskAgent.NAME,
            cls=AlphaRiskAgent,
            version="1.0.0",
            capabilities=AlphaRiskAgent.CAPABILITIES,
        )
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the α‑AGI Business v1 demo")
    parser.add_argument(
        "--loglevel",
        default=os.getenv("LOGLEVEL", "INFO"),
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Launch the orchestrator with the demo agent registered."""

    args = _parse_args(argv)
    logging.basicConfig(
        level=args.loglevel.upper(),
        format="%(asctime)s %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    register_demo_agents()

    try:
        orchestrator.Orchestrator().run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":  # pragma: no cover - manual execution
    import sys

    main(sys.argv[1:])
