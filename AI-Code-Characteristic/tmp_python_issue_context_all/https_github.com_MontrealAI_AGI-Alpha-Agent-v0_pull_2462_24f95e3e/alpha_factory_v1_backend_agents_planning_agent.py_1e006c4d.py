# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .base import AgentBase


class PlanningAgent(AgentBase):
    """Simple stub agent planning tasks for the business demo."""

    NAME = "planning"
    CAPABILITIES = ["plan"]
    CYCLE_SECONDS = 180

    async def step(self) -> None:
        await self.publish("alpha.plan", {"msg": "planning cycle completed"})
