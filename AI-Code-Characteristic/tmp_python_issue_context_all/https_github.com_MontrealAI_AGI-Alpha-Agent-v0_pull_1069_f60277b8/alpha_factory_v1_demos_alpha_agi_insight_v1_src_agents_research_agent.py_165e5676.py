# SPDX-License-Identifier: Apache-2.0
"""Agent that converts a plan into research data.

During each cycle the agent runs a tiny evolutionary loop to estimate
capability growth. Results are forwarded to the strategy agent via
:meth:`run_cycle` and :meth:`handle` processes incoming planning messages.
"""

from __future__ import annotations

import random

from .base_agent import BaseAgent
from ..simulation import forecast, sector
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.retry import with_retry
from ..utils.tracing import span


class ResearchAgent(BaseAgent):
    """Perform simple research based on plans from :class:`PlanningAgent`."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("research", bus, ledger)

    async def run_cycle(self) -> None:
        """Periodic sweep using a tiny evolutionary loop."""
        with span("research.run_cycle"):
            secs = [sector.Sector(f"s{i}") for i in range(3)]
            traj = forecast.forecast_disruptions(secs, 1)
            if self.adk:
                try:  # pragma: no cover - optional
                    with span("adk.heartbeat"):
                        self.adk.heartbeat()
                    with span("adk.list_packages"):
                        _ = len(self.adk.list_packages())
                except Exception:
                    pass
            if self.mcp:
                try:  # pragma: no cover - optional
                    with span("mcp.heartbeat"):
                        self.mcp.heartbeat()
                    with span("mcp.invoke"):
                        try:
                            await self.mcp.invoke_tool("noop", {})
                        except Exception:
                            pass
                except Exception:
                    pass
            await self.emit("strategy", {"research": traj[0].capability})

    async def handle(self, env: messaging.Envelope) -> None:
        """Process planning requests and emit research results."""
        with span("research.handle"):
            plan = env.payload.get("plan", "")
            cap = random.random()
            if self.oai_ctx and not self.bus.settings.offline:
                try:  # pragma: no cover
                    with span("openai.run"):
                        cap = float(await with_retry(self.oai_ctx.run)(prompt=str(plan)))
                except Exception:
                    pass
            await self.emit("strategy", {"research": cap})
