"""Planning agent."""
from __future__ import annotations

from .base_agent import BaseAgent


class PlanningAgent(BaseAgent):
    def __init__(self, bus, ledger) -> None:
        super().__init__("planning", bus, ledger)

    async def run_cycle(self) -> None:
        await self.emit("research", {"plan": "collect data"})

    async def handle(self, env):
        pass
