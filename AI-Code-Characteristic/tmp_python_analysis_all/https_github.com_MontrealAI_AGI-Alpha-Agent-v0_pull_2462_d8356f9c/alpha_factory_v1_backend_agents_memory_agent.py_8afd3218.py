# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .base import AgentBase


class MemoryAgent(AgentBase):
    """Stub retrieval-augmented memory store."""

    NAME = "memory"
    CAPABILITIES = ["remember"]
    CYCLE_SECONDS = 0  # event-driven

    async def step(self) -> None:
        # In a real implementation, this would persist and recall alpha items.
        await self.publish("alpha.memory", {"msg": "memory accessed"})
