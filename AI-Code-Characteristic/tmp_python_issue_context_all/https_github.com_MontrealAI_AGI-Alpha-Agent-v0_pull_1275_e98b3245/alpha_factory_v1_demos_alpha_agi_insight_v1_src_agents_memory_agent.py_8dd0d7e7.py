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
from ..utils.tracing import span
import json
from pathlib import Path


class MemoryAgent(BaseAgent):
    """Persist artefacts produced by other agents."""

    def __init__(
        self,
        bus: messaging.A2ABus,
        ledger: "Ledger",
        store_path: str | None = None,
        *,
        backend: str = "gpt-4o",
        island: str = "default",
    ) -> None:
        super().__init__("memory", bus, ledger, backend=backend, island=island)
        self.records: list[dict[str, object]] = []
        self._store = Path(store_path) if store_path else None
        if self._store and self._store.exists():
            for line in self._store.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    self.records.append(json.loads(line))
                except Exception:  # noqa: BLE001 - ignore bad records
                    pass

    async def run_cycle(self) -> None:
        """Periodically report memory size."""
        with span("memory.run_cycle"):
            await self.emit("orch", {"stored": len(self.records)})

    async def handle(self, env: messaging.Envelope) -> None:
        """Store payload for later retrieval."""
        with span("memory.handle"):
            self.records.append(env.payload)
            if self._store:
                with self._store.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(env.payload) + "\n")
