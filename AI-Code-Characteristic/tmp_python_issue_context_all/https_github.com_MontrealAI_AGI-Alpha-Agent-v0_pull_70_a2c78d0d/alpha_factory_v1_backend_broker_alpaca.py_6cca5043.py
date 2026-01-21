"""Alpaca Markets adapter.
==========================

Thin asynchronous wrapper around the Alpaca REST API used by
``Alpha‑Factory`` agents.

Environment variables
---------------------
``ALPHA_ALPACA_KEY``
    Account API key. **Required**.
``ALPHA_ALPACA_SECRET``
    API secret associated with the key. **Required**.
``ALPHA_ALPACA_PAPER``
    When ``true`` (default) use paper trading endpoints.
``ALPHA_ALPACA_BASE_URL``
    Optional base URL overriding the default live/paper endpoint.

The adapter automatically retries transient network failures using an
exponential back‑off strategy.  Use it as an async context manager to
ensure the underlying :class:`httpx.AsyncClient` is properly closed.
"""

from __future__ import annotations

import os
from typing import Final

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from .logger import get_logger
from .types import TradeBrokerProtocol

_LOG = get_logger(__name__)

_KEY: Final[str | None] = os.getenv("ALPHA_ALPACA_KEY")
_SECRET: Final[str | None] = os.getenv("ALPHA_ALPACA_SECRET")
_PAPER: Final[bool] = os.getenv("ALPHA_ALPACA_PAPER", "true").lower() in ("1", "true", "yes")

if _KEY is None or _SECRET is None:
    raise RuntimeError("ALPHA_ALPACA_KEY / ALPHA_ALPACA_SECRET env‑vars are required")

_API = os.getenv(
    "ALPHA_ALPACA_BASE_URL",
    "https://paper-api.alpaca.markets" if _PAPER else "https://api.alpaca.markets",
)
_HEADERS = {"APCA-API-KEY-ID": _KEY, "APCA-API-SECRET-KEY": _SECRET}

class AlpacaBroker(TradeBrokerProtocol):  # noqa: D101
    """Asynchronous trade broker for the Alpaca REST API."""
    _retry = AsyncRetrying(
        wait=wait_exponential(multiplier=1.5, min=1, max=30),
        stop=stop_after_attempt(4),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(base_url=_API, headers=_HEADERS, timeout=10.0)

    # ------------------------------------------------------------------ #
    async def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
    ) -> str:
        """Place a trade order and return the Alpaca order id."""
        order = {
            "symbol": symbol.upper(),
            "qty": qty,
            "side": side.lower(),
            "type": type.lower(),
            "time_in_force": "day",
        }
        async for attempt in self._retry:
            with attempt:
                r = await self._http.post("/v2/orders", json=order)
        oid = r.json()["id"]
        _LOG.info("Alpaca order %s accepted for %s %s@%s", oid, side, qty, symbol)
        return oid

    async def get_position(self, symbol: str) -> float:
        """Return the current position for ``symbol`` in shares."""
        try:
            async for attempt in self._retry:
                with attempt:
                    r = await self._http.get(f"/v2/positions/{symbol.upper()}")
            return float(r.json()["qty"])
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return 0.0
            raise

    async def get_cash(self) -> float:
        """Return the available cash balance."""
        async for attempt in self._retry:
            with attempt:
                r = await self._http.get("/v2/account")
        return float(r.json()["cash"])

    # ------------------------------------------------------------------ #
    async def __aenter__(self):
        """Context manager entry: return ``self``."""
        return self

    async def __aexit__(self, *_exc):
        """Close the underlying HTTP client on exit."""
        await self._http.aclose()
