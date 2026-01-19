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
        self.cash = cash
        self.positions: Dict[str, float] = {}

    async def submit_order(self, symbol: str, qty: float, side: str, type: str = "market") -> str:
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
        return self.positions.get(symbol.upper(), 0.0)

    async def get_cash(self) -> float:
        return self.cash

    async def __aenter__(self) -> "SimulatedBroker":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass
