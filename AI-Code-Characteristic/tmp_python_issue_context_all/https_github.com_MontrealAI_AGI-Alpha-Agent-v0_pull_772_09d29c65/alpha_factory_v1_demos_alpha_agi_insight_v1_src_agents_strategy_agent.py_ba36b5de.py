"""Strategy agent."""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger


class StrategyAgent(BaseAgent):
    """Turn research output into actionable strategy."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("strategy", bus, ledger)

    async def run_cycle(self) -> None:
        """No-op periodic loop."""
        return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Compose a strategy from research results."""
        val = env.payload.get("research")
        strat = {"action": f"monitor {val}"}
        if self.oai_ctx and not self.bus.settings.offline:
            try:  # pragma: no cover
                strat["action"] = await self.oai_ctx.run(prompt=str(val))
            except Exception:
                pass
        await self.emit("market", {"strategy": strat})
