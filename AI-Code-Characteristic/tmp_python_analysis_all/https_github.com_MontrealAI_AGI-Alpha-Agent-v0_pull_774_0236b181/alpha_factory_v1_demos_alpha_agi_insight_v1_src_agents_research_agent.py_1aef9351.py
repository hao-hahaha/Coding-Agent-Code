"""Research agent."""

from __future__ import annotations

import random

from .base_agent import BaseAgent
from ..simulation import forecast, sector
from ..utils import messaging
from ..utils.logging import Ledger


class ResearchAgent(BaseAgent):
    """Perform simple research based on plans from :class:`PlanningAgent`."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("research", bus, ledger)

    async def run_cycle(self) -> None:
        """Periodic sweep using a tiny evolutionary loop."""
        secs = [sector.Sector(f"s{i}") for i in range(3)]
        traj = forecast.forecast_disruptions(secs, 1)
        await self.emit("strategy", {"research": traj[0].capability})

    async def handle(self, env: messaging.Envelope) -> None:
        """Process planning requests and emit research results."""
        plan = env.payload.get("plan", "")
        cap = random.random()
        if self.oai_ctx and not self.bus.settings.offline:
            try:  # pragma: no cover
                cap = float(await self.oai_ctx.run(prompt=str(plan)))
            except Exception:
                pass
        await self.emit("strategy", {"research": cap})
