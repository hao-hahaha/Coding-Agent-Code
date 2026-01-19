# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .base import AgentBase


class StrategyAgent(AgentBase):
    """Stub agent that transforms raw alpha into actionable strategy."""

    NAME = "strategy"
    CAPABILITIES = ["strategy"]
    CYCLE_SECONDS = 240

    async def step(self) -> None:
        await self.publish("alpha.strategy", {"msg": "strategy drafted"})
