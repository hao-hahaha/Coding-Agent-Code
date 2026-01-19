#!/usr/bin/env python3
"""alpha_agi_business_2_v1
------------------------
Minimal production-grade demo for the Alpha‑Factory stack. It
registers a couple of simple agents and launches the orchestrator.

The demo runs fully offline but automatically upgrades to cloud
LLM tools when `OPENAI_API_KEY` is detected.
"""
from __future__ import annotations

from alpha_factory_v1.backend import orchestrator
from alpha_factory_v1.backend.agents import AgentBase, AgentMetadata, register_agent


class PlanningAgent(AgentBase):
    NAME = "planning"
    CAPABILITIES = ["plan"]

    async def step(self) -> None:
        # Pretend to compute an optimal plan
        await self.publish("alpha.plan", {"plan": "explore_market"})


class ResearchAgent(AgentBase):
    NAME = "research"
    CAPABILITIES = ["research"]
    CYCLE_SECONDS = 90

    async def step(self) -> None:
        # Pretend to fetch and summarise data
        await self.publish("alpha.research", {"summary": "market stable"})


register_agent(
    AgentMetadata(
        name=PlanningAgent.NAME,
        cls=PlanningAgent,
        version="1.0.0",
        capabilities=PlanningAgent.CAPABILITIES,
    )
)

register_agent(
    AgentMetadata(
        name=ResearchAgent.NAME,
        cls=ResearchAgent,
        version="1.0.0",
        capabilities=ResearchAgent.CAPABILITIES,
    )
)


def main() -> None:
    try:
        orchestrator.Orchestrator().run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
