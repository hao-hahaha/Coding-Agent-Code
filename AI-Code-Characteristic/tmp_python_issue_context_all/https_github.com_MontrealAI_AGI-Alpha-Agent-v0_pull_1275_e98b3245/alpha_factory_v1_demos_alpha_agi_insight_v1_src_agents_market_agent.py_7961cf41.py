# SPDX-License-Identifier: Apache-2.0
"""Agent that translates strategy actions into market analysis.

The market agent periodically emits neutral market data and updates its
analysis when receiving new strategy information. Generated insights are
passed to the :class:`CodeGenAgent`.
"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.retry import with_retry
from ..utils.tracing import span


class MarketAgent(BaseAgent):
    """Analyse markets and forward results to the code generator."""

    def __init__(
        self,
        bus: messaging.A2ABus,
        ledger: "Ledger",
        *,
        backend: str = "gpt-4o",
        island: str = "default",
    ) -> None:
        super().__init__("market", bus, ledger, backend=backend, island=island)

    async def run_cycle(self) -> None:
        """Emit a periodic market snapshot."""
        with span("market.run_cycle"):
            await self.emit("codegen", {"analysis": "neutral"})

    async def handle(self, env: messaging.Envelope) -> None:
        """Process strategy input and compute market impact."""
        with span("market.handle"):
            strategy = env.payload.get("strategy")
            analysis = f"impact of {strategy}"
            if self.oai_ctx and not self.bus.settings.offline:
                try:  # pragma: no cover
                    with span("openai.run"):
                        analysis = await with_retry(self.oai_ctx.run)(prompt=str(strategy))
                except Exception:
                    pass
            await self.emit("codegen", {"analysis": analysis})
