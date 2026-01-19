# SPDX-License-Identifier: Apache-2.0
"""Safety guardian agent."""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger


class SafetyGuardianAgent(BaseAgent):
    """Validate generated code before persistence."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("safety", bus, ledger)

    async def run_cycle(self) -> None:
        """No-op periodic check."""
        return None

    async def handle(self, env: messaging.Envelope) -> None:
        """Simple pattern-based validation."""
        code = env.payload.get("code", "")
        status = "blocked" if "import os" in code else "ok"
        await self.emit("memory", {"code": code, "status": status})
