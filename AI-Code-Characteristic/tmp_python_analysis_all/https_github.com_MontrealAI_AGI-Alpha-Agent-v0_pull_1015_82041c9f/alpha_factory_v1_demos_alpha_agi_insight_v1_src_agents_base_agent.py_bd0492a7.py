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
from .adk_adapter import ADKAdapter
from .mcp_adapter import MCPAdapter

if TYPE_CHECKING:  # pragma: no cover - type hint only
    from ..utils.logging import Ledger

try:
    from openai.agents import AgentContext as _AgentContext

    AgentContext: type | None = _AgentContext
except Exception:  # pragma: no cover - optional
    AgentContext = None


class BaseAgent:
    """Abstract agent type used by specialised agents."""

    name: str

    def __init__(self, name: str, bus: messaging.A2ABus, ledger: "Ledger") -> None:
        self.name = name
        self.bus = bus
        self.ledger = ledger
        if AgentContext is not None:
            try:
                self.oai_ctx = AgentContext(
                    model=bus.settings.model_name,
                    temperature=bus.settings.temperature,
                    context_window=bus.settings.context_window,
                )
            except TypeError:
                try:
                    self.oai_ctx = AgentContext(
                        model=bus.settings.model_name,
                        temperature=bus.settings.temperature,
                    )
                except Exception:
                    self.oai_ctx = AgentContext()
        else:
            self.oai_ctx = None
        self.adk = ADKAdapter() if ADKAdapter.is_available() else None
        self.mcp = MCPAdapter() if MCPAdapter.is_available() else None
        self._handler = self._on_envelope
        self.bus.subscribe(name, self._handler)

    async def _on_envelope(self, env: messaging.Envelope) -> None:
        await self.handle(env)

    async def emit(self, recipient: str, payload: Any) -> None:
        env = messaging.Envelope(self.name, recipient, payload, time.time())
        self.ledger.log(env)
        self.bus.publish(recipient, env)

    def close(self) -> None:
        """Unsubscribe the agent from the bus."""
        self.bus.unsubscribe(self.name, self._handler)

    async def handle(self, env: messaging.Envelope) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def run_cycle(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError
