"""Minimal orchestrator for the α‑AGI Insight demo."""
from __future__ import annotations

import asyncio
from typing import List

from .agents import (
    planning_agent,
    research_agent,
    strategy_agent,
    market_agent,
    codegen_agent,
    safety_agent,
    memory_agent,
)
from .utils import config, messaging, logging
from .utils.logging import Ledger




class Orchestrator:
    """Bootstraps agents and routes envelopes."""

    def __init__(self, settings: config.Settings | None = None) -> None:
        self.settings = settings or config.CFG
        logging.setup()
        self.bus = messaging.A2ABus(self.settings)
        self.ledger = Ledger(self.settings.ledger_path)
        self.ledger.start_merkle_task()
        self.agents = self._init_agents()

    def _init_agents(self) -> List[messaging.Envelope]:
        agents = [
            planning_agent.PlanningAgent(self.bus, self.ledger),
            research_agent.ResearchAgent(self.bus, self.ledger),
            strategy_agent.StrategyAgent(self.bus, self.ledger),
            market_agent.MarketAgent(self.bus, self.ledger),
            codegen_agent.CodeGenAgent(self.bus, self.ledger),
            safety_agent.SafetyGuardianAgent(self.bus, self.ledger),
            memory_agent.MemoryAgent(self.bus, self.ledger),
        ]
        return agents

    async def run_forever(self) -> None:
        await self.bus.start()
        try:
            while True:
                for agent in self.agents:
                    await agent.run_cycle()
                await asyncio.sleep(0.5)
        finally:
            await self.bus.stop()
            await self.ledger.stop_merkle_task()
            self.ledger.close()


async def _main() -> None:  # pragma: no cover - CLI helper
    orch = Orchestrator()
    await orch.run_forever()


if __name__ == "__main__":  # pragma: no cover - CLI
    asyncio.run(_main())
