# backend/broker/__init__.py
import os

_BROKER = os.getenv("ALPHA_BROKER", "sim").lower()

if _BROKER == "alpaca":
    from .broker_alpaca import AlpacaBroker as Broker
elif _BROKER == "ibkr":
    from .broker_ibkr import InteractiveBrokersBroker as Broker
else:
    from .broker_sim import SimulatedBroker as Broker

__all__ = ["Broker"]
