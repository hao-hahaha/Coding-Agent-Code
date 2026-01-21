# SPDX-License-Identifier: Apache-2.0
"""Agent responsible for proposing research steps.

The planning agent periodically formulates a short plan which guides the
other agents. It demonstrates integration with both local and remote LLMs
inside :meth:`run_cycle`.
"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.retry import with_retry


class PlanningAgent(BaseAgent):
    """Generate research plans for downstream agents."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("planning", bus, ledger)

    async def run_cycle(self) -> None:
        """Emit a high level research request."""
        plan = "collect baseline metrics"
        if self.bus.settings.offline:
            try:
                from ..utils import local_llm

                plan = with_retry(local_llm.chat)("plan research task", self.bus.settings)
            except Exception:  # pragma: no cover - model optional
                plan = "collect baseline metrics"
        elif self.oai_ctx:
            try:  # pragma: no cover - SDK optional
                plan = await with_retry(self.oai_ctx.run)(prompt="plan research task")
            except Exception:
                plan = "collect baseline metrics"
        await self.emit("research", {"plan": plan})

    async def handle(self, env: messaging.Envelope) -> None:
        """Log incoming feedback for future planning."""
        self.ledger.log(env)
