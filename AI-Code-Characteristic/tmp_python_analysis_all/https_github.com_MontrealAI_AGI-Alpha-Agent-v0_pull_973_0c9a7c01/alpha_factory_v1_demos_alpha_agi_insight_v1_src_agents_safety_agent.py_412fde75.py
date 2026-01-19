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


class SafetyGuardianAgent(BaseAgent):
    """Validate generated code before persistence."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("safety", bus, ledger)

    async def run_cycle(self) -> None:
        """No-op periodic check."""
        with span("safety.run_cycle"):
            return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Simple pattern-based validation."""
        with span("safety.handle"):
            code = env.payload.get("code", "")
            status = "blocked" if "import os" in code else "ok"
            await self.emit("memory", {"code": code, "status": status})
