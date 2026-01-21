
"""backend.market_data
======================

Unified async **market‑data feed** that auto‑selects a provider at runtime:

* ``PolygonMarketData``  — equities / crypto via Polygon.io REST.
* ``BinanceMarketData`` — crypto spot prices via Binance REST.
* ``SimulatedMarketData`` — deterministic pseudo‑random walk (testing / offline).

Set ``ALPHA_MARKET_PROVIDER`` to **polygon** (default), **binance** or **simulated**.
The adapter is *lazy‑imported* so missing client libraries don’t break the build.

Example
-------
>>> from backend.market_data import MarketData
>>> md = MarketData()         # auto picks provider
>>> price = asyncio.run(md.price("AAPL"))
>>> print(price)
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import Dict

import aiohttp
import backoff

__all__ = ["MarketData", "BaseMarketData", "PolygonMarketData", "BinanceMarketData", "SimulatedMarketData"]

# ---------------------------------------------------------------------------#
#                               Base class                                   #
# ---------------------------------------------------------------------------#



class BaseMarketData:  # pragma: no cover
    """Abstract async price‑feed interface with context manager sugar."""

    async def price(self, symbol: str) -> float:  # noqa: D401
        """Return the latest *float* price for *symbol* (uppercase)."""
        raise NotImplementedError

    # Async context-manager sugar ------------------------------------------
    async def __aenter__(self):  # pragma: no cover - interface default
        return self

    async def __aexit__(self, *_exc):  # pragma: no cover - interface default
        return None

    async def close(self) -> None:  # pragma: no cover - interface default
        """Gracefully close underlying resources."""
        await self.__aexit__(None, None, None)


# ---------------------------------------------------------------------------#
#                         Provider: Polygon.io                               #
# ---------------------------------------------------------------------------#


class PolygonMarketData(BaseMarketData):
    """Lightweight REST adapter around polygon.io /v2/last/trade."""

    _BASE = "https://api.polygon.io/v2/last/trade/{symbol}?apiKey={key}"

    def __init__(self, api_key: str | None = None) -> None:
        self._key = api_key or os.getenv("POLYGON_API_KEY") or os.getenv("ALPHA_POLYGON_KEY")
        if not self._key:
            raise RuntimeError("POLYGON_API_KEY (or ALPHA_POLYGON_KEY) env‑var required")
        self._session: aiohttp.ClientSession | None = None

    async def _client(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=8)
            headers = {"User-Agent": "AlphaFactoryMarketData/1.0"}
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        jitter=backoff.full_jitter,
    )
    async def price(self, symbol: str) -> float:
        symbol = symbol.upper()
        url = self._BASE.format(symbol=symbol, key=self._key)
        sess = await self._client()
        async with sess.get(url) as r:
            r.raise_for_status()
            data = await r.json()
        return float(data["last"]["p"])

    async def __aenter__(self) -> "PolygonMarketData":
        await self._client()
        return self

    async def __aexit__(self, *_) -> None:  # noqa: D401
        if self._session:
            await self._session.close()

    async def close(self) -> None:
        await self.__aexit__(None, None, None)


# ---------------------------------------------------------------------------#
#                         Provider: Binance                                  #
# ---------------------------------------------------------------------------#


class BinanceMarketData(BaseMarketData):
    """Spot‐price adapter using Binance public REST."""

    _BASE = "https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _client(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=8)
            headers = {"User-Agent": "AlphaFactoryMarketData/1.0"}
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=5,
        jitter=backoff.full_jitter,
    )
    async def price(self, symbol: str) -> float:
        # Binance expects e.g. BTCUSDT without slash
        symbol = symbol.replace("/", "").upper()
        url = self._BASE.format(symbol=symbol)
        sess = await self._client()
        async with sess.get(url) as r:
            r.raise_for_status()
            data = await r.json()
        return float(data["price"])

    async def __aexit__(self, *_) -> None:  # noqa: D401
        if self._session:
            await self._session.close()

    async def __aenter__(self) -> "BinanceMarketData":
        await self._client()
        return self

    async def close(self) -> None:
        await self.__aexit__(None, None, None)


# ---------------------------------------------------------------------------#
#                           Provider: Simulated                              #
# ---------------------------------------------------------------------------#


class SimulatedMarketData(BaseMarketData):
    """Deterministic pseudo‑random walk based on symbol hash (offline tests)."""

    def __init__(self) -> None:
        self._state: Dict[str, float] = {}

    async def price(self, symbol: str) -> float:
        symbol = symbol.upper()
        base = self._state.get(symbol)
        if base is None:
            # deterministic seed so repeated runs are stable
            seed = sum(ord(c) for c in symbol)
            random.seed(seed)
            base = random.uniform(10, 500)
        # random walk
        pct = random.uniform(-0.01, 0.01)
        price = max(0.01, base * (1 + pct))
        self._state[symbol] = price
        await asyncio.sleep(0)  # keep signature strictly async
        return round(price, 4)

    async def __aenter__(self) -> "SimulatedMarketData":
        return self

    async def __aexit__(self, *_exc) -> None:
        return None

    async def close(self) -> None:
        return None


# ---------------------------------------------------------------------------#
#                     Factory wrapper exposed to callers                     #
# ---------------------------------------------------------------------------#


class MarketData(BaseMarketData):
    """Facade that lazy‑loads the backend selected by *ALPHA_MARKET_PROVIDER*."""

    _PROVIDERS = {
        "polygon": PolygonMarketData,
        "binance": BinanceMarketData,
        "simulated": SimulatedMarketData,
    }

    def __init__(self, provider: str | None = None) -> None:
        provider = (provider or os.getenv("ALPHA_MARKET_PROVIDER", "polygon")).lower()
        cls = self._PROVIDERS.get(provider)
        if cls is None:
            raise ValueError(f"Unknown provider {provider!r}. Valid: {', '.join(self._PROVIDERS)}")
        # Delay instantiation because Polygon may raise on missing key
        self._backend = cls()  # type: ignore[call-arg]

    async def price(self, symbol: str) -> float:
        return await self._backend.price(symbol)

    async def prices(self, symbols: list[str]) -> dict[str, float]:
        """Return latest prices for multiple symbols concurrently."""
        tasks = [asyncio.create_task(self.price(sym)) for sym in symbols]
        values = await asyncio.gather(*tasks)
        return dict(zip(symbols, values))

    async def close(self) -> None:
        if hasattr(self._backend, "close"):
            await self._backend.close()

    async def __aenter__(self) -> "MarketData":
        if hasattr(self._backend, "__aenter__"):
            await self._backend.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if hasattr(self._backend, "__aexit__"):
            await self._backend.__aexit__(exc_type, exc, tb)

    # -- synchronous convenience -------------------------------------------#
    def spot(self, symbol: str) -> float:
        """Blocking helper around *price* (for simple scripts / tests)."""
        return asyncio.run(self.price(symbol))


