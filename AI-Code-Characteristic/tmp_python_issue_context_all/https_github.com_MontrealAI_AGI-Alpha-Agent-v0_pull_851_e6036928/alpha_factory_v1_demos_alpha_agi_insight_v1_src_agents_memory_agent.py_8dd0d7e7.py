# SPDX-License-Identifier: Apache-2.0
"""Simple in-memory storage for agent artefacts.

The ``MemoryAgent`` collects payloads from other agents and exposes them via
its :pyattr:`records` attribute. The :meth:`run_cycle` hook reports the number
of stored items back to the orchestrator.
"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..utils import messaging
from ..utils.logging import Ledger


class MemoryAgent(BaseAgent):
    """Persist artefacts produced by other agents."""

    def __init__(self, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        super().__init__("memory", bus, ledger)
        self.records: list[dict[str, object]] = []

    async def run_cycle(self) -> None:
        """Periodically report memory size."""
        await self.emit("orch", {"stored": len(self.records)})

    async def handle(self, env: messaging.Envelope) -> None:
        """Store payload for later retrieval."""
        self.records.append(env.payload)
