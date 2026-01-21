"""Simple trade broker with optional Alpaca integration."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict

import requests

log = logging.getLogger(__name__)

ALPACA_BASE = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")


@dataclass
class Order:
    """Represents a trade order."""

    symbol: str
    qty: int
    side: str
    price: float
    ts: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "filled"

    def to_dict(self) -> Dict[str, Any]:
        """Return order as plain dictionary."""
        return asdict(self)

def _alpaca_order(symbol: str, qty: int, side: str, key: str, secret: str) -> Dict[str, Any]:
    """Send an order to Alpaca Markets and return the JSON response."""

    hdrs = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side.lower(),
        "type": "market",
        "time_in_force": "gtc",
    }
    r = requests.post(f"{ALPACA_BASE}/orders", json=data, headers=hdrs, timeout=4)
    r.raise_for_status()
    return r.json()

# ── public API ───────────────────────────────────────────────────────────
def place_order(symbol: str, qty: int, side: str, price: float) -> Dict[str, Any]:
    """Place an order via Alpaca or fall back to an in‑memory simulator.

    Parameters
    ----------
    symbol:
        Ticker symbol (e.g. ``AAPL``).
    qty:
        Quantity to trade. Must be positive.
    side:
        ``"buy"`` or ``"sell"``.
    price:
        Last trade price used for the simulator.
    """

    if qty <= 0:
        raise ValueError("qty must be positive")
    if side.lower() not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")

    key = os.getenv("ALPACA_KEY_ID")
    secret = os.getenv("ALPACA_SECRET_KEY")
    try:
        if key and secret:
            return _alpaca_order(symbol, qty, side, key, secret)
    except Exception as err:  # pragma: no cover - network failure
        log.warning("Live broker failed (%s); falling back to simulator.", err)

    log.info("Simulated order: %s %s %s@%.2f", side, qty, symbol, price)
    time.sleep(0.1)
    return Order(symbol, qty, side, price).to_dict()

