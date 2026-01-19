# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import itertools
from typing import Dict

from ..logger import get_logger
from ..types import TradeBrokerProtocol

_LOG = get_logger(__name__)

class SimulatedBroker(TradeBrokerProtocol):
    """Very small in-memory broker for tests and demos."""

    _ids = itertools.count(1)

    def __init__(self, cash: float = 1_000_000.0) -> None:
        """Initialize the simulated broker.

        Args:
            cash: Starting cash balance.
        """
        self.cash = cash
        self.positions: Dict[str, float] = {}

    async def submit_order(self, symbol: str, qty: float, side: str, type: str = "market") -> str:
        """Record an order in memory and update positions.

        Args:
            symbol: The ticker symbol.
            qty: Quantity to trade.
            side: ``"buy"`` or ``"sell"``.
            type: Order type, unused.

        Returns:
            Order identifier.
        """
        qty = float(qty)
        pos = self.positions.get(symbol.upper(), 0.0)
        if side.lower() == "buy":
            pos += qty
        else:
            pos -= qty
        self.positions[symbol.upper()] = pos
        oid = next(self._ids)
        _LOG.info("Simulated order %s %s %s@%s", oid, side, qty, symbol)
        return str(oid)

    async def get_position(self, symbol: str) -> float:
        """Return current position for ``symbol``."""
        return self.positions.get(symbol.upper(), 0.0)

    async def get_cash(self) -> float:
        """Return available cash balance."""
        return self.cash

    async def __aenter__(self) -> "SimulatedBroker":
        """Return ``self`` for async context manager support."""
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Async context manager no-op."""
        pass
