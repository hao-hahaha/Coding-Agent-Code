# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from types import TracebackType
from typing import Optional, Protocol, Type


class TradeBrokerProtocol(Protocol):
    """Minimal interface for trade brokers used by Alpha‑Factory."""

    async def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
    ) -> str:
        """Place an order and return the broker-specific order identifier."""

    async def get_position(self, symbol: str) -> float:
        """Return the signed position for ``symbol`` in shares."""

    async def get_cash(self) -> float:
        """Return the available cash balance in the account currency."""

    async def __aenter__(self) -> "TradeBrokerProtocol": ...

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        """Clean up broker resources."""


__all__ = ["TradeBrokerProtocol"]
