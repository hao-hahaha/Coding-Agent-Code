# SPDX-License-Identifier: Apache-2.0
"""Agent composing high level strategy from research results.

The agent consumes ``research`` messages and generates a short action plan
for the market agent. It can optionally leverage a local or remote LLM during
:meth:`handle`.
"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.retry import with_retry
from ..utils.tracing import span


class StrategyAgent(BaseAgent):
    """Turn research output into actionable strategy."""

    def __init__(
        self,
        bus: messaging.A2ABus,
        ledger: "Ledger",
        *,
        backend: str = "gpt-4o",
        island: str = "default",
    ) -> None:
        super().__init__("strategy", bus, ledger, backend=backend, island=island)

    async def run_cycle(self) -> None:
        """No-op periodic loop."""
        return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Compose a strategy from research results."""
        with span("strategy.handle"):
            val = env.payload.get("research")
            strat = {"action": f"monitor {val}"}
            if self.bus.settings.offline:
                try:
                    from ..utils import local_llm

                    with span("local_llm.chat"):
                        strat["action"] = with_retry(local_llm.chat)(str(val), self.bus.settings)
                except Exception:  # pragma: no cover - model optional
                    pass
            elif self.oai_ctx:
                try:  # pragma: no cover
                    with span("openai.run"):
                        strat["action"] = await with_retry(self.oai_ctx.run)(prompt=str(val))
                except Exception:
                    pass
            await self.emit("market", {"strategy": strat})
