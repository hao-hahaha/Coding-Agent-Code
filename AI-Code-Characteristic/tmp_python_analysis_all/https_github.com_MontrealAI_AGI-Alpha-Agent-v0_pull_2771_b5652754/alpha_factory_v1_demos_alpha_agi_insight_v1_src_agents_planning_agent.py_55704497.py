# SPDX-License-Identifier: Apache-2.0
"""Agent responsible for proposing research steps.

The planning agent periodically formulates a short plan which guides the
other agents. It demonstrates integration with both local and remote LLMs
inside :meth:`run_cycle`.
"""

from __future__ import annotations

from alpha_factory_v1.core.agents.base_agent import BaseAgent
from alpha_factory_v1.common.utils import messaging
from alpha_factory_v1.common.utils.logging import Ledger
from alpha_factory_v1.common.utils.retry import with_retry
from alpha_factory_v1.core.utils.tracing import span
from typing import Callable, Awaitable, cast


class PlanningAgent(BaseAgent):
    """Generate research plans for downstream agents."""

    def __init__(
        self,
        bus: messaging.A2ABus,
        ledger: "Ledger",
        *,
        backend: str = "gpt-4o",
        island: str = "default",
    ) -> None:
        super().__init__("planning", bus, ledger, backend=backend, island=island)

    async def run_cycle(self) -> None:
        """Emit a high level research request."""
        with span("planning.run_cycle"):
            plan = "collect baseline metrics"
            if self.bus.settings.offline:
                try:
                    from alpha_factory_v1.common.utils import local_llm

                    with span("local_llm.chat"):
                        plan = with_retry(local_llm.chat)("plan research task", self.bus.settings)
                except Exception:  # pragma: no cover - model optional
                    plan = "collect baseline metrics"
            elif self.oai_ctx:
                try:  # pragma: no cover - SDK optional
                    with span("openai.run"):
                        plan = await with_retry(cast(Callable[[str], Awaitable[str]], self.oai_ctx.run))(
                            "plan research task"
                        )
                except Exception:
                    plan = "collect baseline metrics"
            await self.emit("research", {"plan": plan})

    async def handle(self, env: messaging.Envelope) -> None:
        """Log incoming feedback for future planning."""
        self.ledger.log(env)
