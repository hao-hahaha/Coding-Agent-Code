# SPDX-License-Identifier: Apache-2.0
"""Agent summarising research data via the Google ADK."""
from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.tracing import span


class ADKSummariserAgent(BaseAgent):
    """Collect research updates and produce a summary using ADK."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("summariser", bus, ledger)
        self._records: list[str] = []

    async def run_cycle(self) -> None:
        """Generate and emit an ADK summary when data is available."""
        with span("summariser.run_cycle"):
            if not self._records or not self.adk:
                return
            try:
                summary = self.adk.generate_text("\n".join(self._records))
            except Exception:
                return
            await self.emit("strategy", {"summary": summary})
            self._records.clear()

    async def handle(self, env: messaging.Envelope) -> None:
        """Store research payload for later summarisation."""
        with span("summariser.handle"):
            val = env.payload.get("research")
            if val is not None:
                self._records.append(str(val))
