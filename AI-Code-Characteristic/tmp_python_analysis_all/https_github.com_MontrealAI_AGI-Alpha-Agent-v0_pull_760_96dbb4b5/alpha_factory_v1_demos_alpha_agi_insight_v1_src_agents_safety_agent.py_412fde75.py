"""Safety guardian agent."""
from __future__ import annotations

from .base_agent import BaseAgent


class SafetyGuardianAgent(BaseAgent):
    def __init__(self, bus, ledger) -> None:
        super().__init__("safety", bus, ledger)

    async def run_cycle(self) -> None:
        pass

    async def handle(self, env):
        pass
