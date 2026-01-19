# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .base import AgentBase


class ResearchAgent(AgentBase):
    """Stub research agent harvesting external data."""

    NAME = "research"
    CAPABILITIES = ["research"]
    CYCLE_SECONDS = 300

    async def step(self) -> None:
        await self.publish("alpha.research", {"msg": "research sweep complete"})
