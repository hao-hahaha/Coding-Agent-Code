# SPDX-License-Identifier: Apache-2.0
"""Shared base class for insight agents."""
from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

from ..utils import messaging

if TYPE_CHECKING:  # pragma: no cover - type hint only
    from ..utils.logging import Ledger

try:
    from openai.agents import AgentContext
except Exception:  # pragma: no cover - optional
    AgentContext = object

try:
    import adk
except Exception:  # pragma: no cover - optional
    adk = None


class BaseAgent:
    """Abstract agent."""

    name: str

    def __init__(self, name: str, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        self.name = name
        self.bus = bus
        self.ledger = ledger
        self.oai_ctx = AgentContext() if isinstance(AgentContext, type) else None
        self.adk_client = adk.Client() if adk else None
        self.bus.subscribe(name, self._on_envelope)

    async def _on_envelope(self, env: messaging.Envelope) -> None:
        await self.handle(env)

    async def emit(self, recipient: str, payload: Any) -> None:
        env = messaging.Envelope(self.name, recipient, payload, time.time())
        self.ledger.log(env)
        self.bus.publish(recipient, env)

    async def handle(self, env: messaging.Envelope) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def run_cycle(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError
