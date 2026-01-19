# SPDX-License-Identifier: Apache-2.0
"""Base class shared by all Insight demo agents.

The class wires each agent into the :class:`~..utils.messaging.A2ABus` and
provides helper methods for sending and receiving envelopes. Subclasses
implement :meth:`handle` to process messages and :meth:`run_cycle` for
periodic behaviour.
"""
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
    """Abstract agent type used by specialised agents."""

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
