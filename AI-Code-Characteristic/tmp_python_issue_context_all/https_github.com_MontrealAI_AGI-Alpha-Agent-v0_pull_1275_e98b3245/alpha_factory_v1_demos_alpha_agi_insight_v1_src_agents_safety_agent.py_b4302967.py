# SPDX-License-Identifier: Apache-2.0
"""Agent performing lightweight safety checks.

The safety agent inspects generated code for obvious issues before data is
persisted by the :class:`MemoryAgent`. Only minimal pattern checks are
implemented for demonstration purposes.
"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger
from ..utils.tracing import span
from src.utils.opa_policy import violates_insider_policy


class SafetyGuardianAgent(BaseAgent):
    """Validate generated code before persistence."""

    def __init__(
        self,
        bus: messaging.A2ABus,
        ledger: "Ledger",
        *,
        backend: str = "gpt-4o",
        island: str = "default",
    ) -> None:
        super().__init__("safety", bus, ledger, backend=backend, island=island)

    async def run_cycle(self) -> None:
        """No-op periodic check."""
        with span("safety.run_cycle"):
            return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Validate payload before persistence."""
        with span("safety.handle"):
            code = str(env.payload.get("code", ""))
            text_parts = [str(v) for v in env.payload.values() if isinstance(v, str)]
            text = " ".join(text_parts)
            status = "ok"
            if "import os" in code or violates_insider_policy(text):
                status = "blocked"
            payload = dict(env.payload)
            payload["status"] = status
            await self.emit("memory", payload)
