# SPDX-License-Identifier: Apache-2.0
"""Strategy agent."""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger


class StrategyAgent(BaseAgent):  # type: ignore[misc]
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
        if self.bus.settings.offline:
            try:
                from ..utils import local_llm

                strat["action"] = local_llm.chat(str(val))
            except Exception:  # pragma: no cover - model optional
                pass
        elif self.oai_ctx:
            try:  # pragma: no cover
                strat["action"] = await self.oai_ctx.run(prompt=str(val))
            except Exception:
                pass
        await self.emit("market", {"strategy": strat})
