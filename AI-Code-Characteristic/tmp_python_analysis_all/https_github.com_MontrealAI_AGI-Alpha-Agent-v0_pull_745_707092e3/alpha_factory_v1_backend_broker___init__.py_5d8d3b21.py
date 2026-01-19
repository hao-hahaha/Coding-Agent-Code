# backend/broker/__init__.py
"""Broker selection factory.

Chooses the broker via ``ALPHA_BROKER``; the simulated broker is used by default.
"""

import os

_BROKER = os.getenv("ALPHA_BROKER", "sim").lower()

if _BROKER == "alpaca":
    from .broker_alpaca import AlpacaBroker as Broker
elif _BROKER == "ibkr":
    from .broker_ibkr import InteractiveBrokersBroker as Broker
else:
    from .broker_sim import SimulatedBroker as Broker

__all__ = ["Broker"]
