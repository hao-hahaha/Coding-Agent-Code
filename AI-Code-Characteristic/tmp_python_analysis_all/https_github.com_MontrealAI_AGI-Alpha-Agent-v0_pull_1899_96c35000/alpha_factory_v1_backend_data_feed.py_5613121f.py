# SPDX-License-Identifier: Apache-2.0
"""Synchronous market-data helpers used by small demos.

This module exposes a single :func:`last_price` function that attempts to fetch
the most recent trade for a symbol from online providers.  It prioritises
Polygon.io if a ``POLYGON_API_KEY`` is available and otherwise falls back to
Yahoo Finance.  When both providers fail, it returns a deterministic
pseudo-random value so that offline demos continue running.

Results are cached for a short period to avoid hammering external APIs.
"""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Optional

import af_requests as requests

__all__ = ["last_price"]

log = logging.getLogger("alpha_factory.data_feed")

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "AlphaFactoryDataFeed/1.0"})

_CACHE: dict[str, tuple[float, float]] = {}
_CACHE_TTL = float(os.getenv("ALPHA_DATAFEED_TTL", "1.0"))


# ── helpers ──────────────────────────────────────────────────────────────
def _polygon_last_price(
    symbol: str, key: str, session: Optional[requests.Session] = None
) -> float:
    """Return the latest trade price from Polygon."""

    url = f"https://api.polygon.io/v2/last/trade/{symbol}?apiKey={key}"
    resp = (session or _SESSION).get(url, timeout=4)
    resp.raise_for_status()
    data = resp.json()
    try:
        return float(data["results"]["p"])
    except (KeyError, TypeError) as exc:  # pragma: no cover - network variability
        raise ValueError("Malformed Polygon response") from exc


def _yahoo_last_price(symbol: str, session: Optional[requests.Session] = None) -> float:
    """Return the latest trade price from Yahoo Finance."""

    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=price"
    resp = (session or _SESSION).get(url, timeout=4)
    resp.raise_for_status()
    data = resp.json()
    try:
        price = data["quoteSummary"]["result"][0]["price"]
        return float(price["regularMarketPrice"]["raw"])
    except (
        KeyError,
        TypeError,
        IndexError,
    ) as exc:  # pragma: no cover - network variability
        raise ValueError("Malformed Yahoo Finance response") from exc


# ── public API ───────────────────────────────────────────────────────────
def last_price(symbol: str) -> float:
    """Return the latest price for ``symbol``.

    The provider is chosen automatically in this order:

    #. Polygon – if a ``POLYGON_API_KEY`` environment variable is set.
    #. Yahoo Finance – used when no Polygon key is present.
    #. A deterministic random-walk value when both providers fail.
    """

    cached = _CACHE.get(symbol)
    if cached and time.monotonic() - cached[1] < _CACHE_TTL:
        return cached[0]

    poly_key = os.getenv("POLYGON_API_KEY")
    try:
        if poly_key:
            price = _polygon_last_price(symbol, poly_key)
        else:
            price = _yahoo_last_price(symbol)
    except Exception as err:  # pragma: no cover - network variability
        log.warning("Live feed failed (%s); using stub.", err)
        price = 100 + random.gauss(0, 0.5)

    _CACHE[symbol] = (price, time.monotonic())
    return price
