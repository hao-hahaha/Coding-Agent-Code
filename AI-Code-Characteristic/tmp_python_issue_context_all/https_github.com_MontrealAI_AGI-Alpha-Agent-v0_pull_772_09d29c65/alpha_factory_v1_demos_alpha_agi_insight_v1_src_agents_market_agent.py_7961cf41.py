"""Market analysis agent."""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger


class MarketAgent(BaseAgent):
    """Analyse markets and forward results to the code generator."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("market", bus, ledger)

    async def run_cycle(self) -> None:
        """Emit a periodic market snapshot."""
        await self.emit("codegen", {"analysis": "neutral"})

    async def handle(self, env: messaging.Envelope) -> None:
        """Process strategy input and compute market impact."""
        strategy = env.payload.get("strategy")
        analysis = f"impact of {strategy}"
        if self.oai_ctx and not self.bus.settings.offline:
            try:  # pragma: no cover
                analysis = await self.oai_ctx.run(prompt=str(strategy))
            except Exception:
                pass
        await self.emit("codegen", {"analysis": analysis})
