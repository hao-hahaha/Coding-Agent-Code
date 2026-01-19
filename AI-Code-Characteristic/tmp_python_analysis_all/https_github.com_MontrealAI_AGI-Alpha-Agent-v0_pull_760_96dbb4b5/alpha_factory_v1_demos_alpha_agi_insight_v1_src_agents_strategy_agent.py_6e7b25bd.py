"""Strategy agent."""
from __future__ import annotations

from .base_agent import BaseAgent


class StrategyAgent(BaseAgent):
    def __init__(self, bus, ledger) -> None:
        super().__init__("strategy", bus, ledger)

    async def run_cycle(self) -> None:
        pass

    async def handle(self, env):
        pass
