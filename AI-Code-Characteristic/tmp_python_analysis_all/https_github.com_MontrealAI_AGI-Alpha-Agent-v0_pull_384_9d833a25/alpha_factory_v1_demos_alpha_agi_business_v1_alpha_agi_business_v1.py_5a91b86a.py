#!/usr/bin/env python3
"""Alpha‑AGI Business v1 demo.

Bootstraps a minimal Alpha‑Factory orchestrator with two stub agents.
The demo operates fully offline but upgrades to cloud LLM tooling
automatically when ``OPENAI_API_KEY`` is present.
"""
from __future__ import annotations

import argparse
import logging
import os

from alpha_factory_v1.backend import orchestrator
from alpha_factory_v1.backend.agents import AgentBase, AgentMetadata, register_agent


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
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.opportunity", {"alpha": "supply-chain bottleneck detected"})


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
