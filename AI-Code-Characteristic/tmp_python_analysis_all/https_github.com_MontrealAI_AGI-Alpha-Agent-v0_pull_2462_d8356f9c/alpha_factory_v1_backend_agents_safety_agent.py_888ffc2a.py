# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from .base import AgentBase


class SafetyAgent(AgentBase):
    """Stub safety agent performing compliance checks."""

    NAME = "safety"
    CAPABILITIES = ["guard"]
    CYCLE_SECONDS = 250

    async def step(self) -> None:
        await self.publish("alpha.safety", {"msg": "safety check ok"})
