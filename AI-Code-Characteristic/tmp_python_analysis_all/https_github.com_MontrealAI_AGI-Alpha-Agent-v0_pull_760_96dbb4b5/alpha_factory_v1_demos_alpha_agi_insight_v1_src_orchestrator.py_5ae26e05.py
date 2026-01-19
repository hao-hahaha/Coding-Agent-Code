"""Minimal orchestrator for the α‑AGI Insight demo."""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import List

try:
    from blake3 import blake3
except ModuleNotFoundError:  # pragma: no cover - optional
    from hashlib import sha256 as blake3  # type: ignore

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


class Ledger:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, env: messaging.Envelope) -> None:
        data = json.dumps(env.__dict__, sort_keys=True).encode()
        digest = blake3(data).hexdigest()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"hash": digest, **env.__dict__}) + "\n")


class Orchestrator:
    """Bootstraps agents and routes envelopes."""

    def __init__(self, settings: config.Settings | None = None) -> None:
        self.settings = settings or config.Settings()
        logging.setup()
        self.bus = messaging.A2ABus(self.settings)
        self.ledger = Ledger(self.settings.ledger_path)
        self.agents = self._init_agents()

    def _init_agents(self) -> List[messaging.Envelope]:  # type: ignore[override]
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


async def _main() -> None:  # pragma: no cover - CLI helper
    orch = Orchestrator()
    await orch.run_forever()


if __name__ == "__main__":  # pragma: no cover - CLI
    asyncio.run(_main())
