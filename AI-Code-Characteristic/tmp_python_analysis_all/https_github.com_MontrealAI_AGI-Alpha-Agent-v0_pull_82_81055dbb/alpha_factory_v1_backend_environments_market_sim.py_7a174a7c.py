from __future__ import annotations

import random
from typing import Tuple, List

class MarketEnv:
    """Minimal stochastic market environment for demo purposes."""

    def __init__(self, start_price: float = 100.0, volatility: float = 1.0) -> None:
        self.start_price = start_price
        self.volatility = volatility
        self.price = start_price

    # ------------------------------------------------------------------ #
    #  Gym-like API                                                      #
    # ------------------------------------------------------------------ #
    def reset(self) -> float:
        """Reset the environment and return the starting price."""
        self.price = self.start_price
        return self.price

    def step(self, action: str) -> Tuple[float, float, bool]:
        """Execute ``action`` and return (price, reward, done)."""
        self.price = self.sample_next_price(self.price)
        reward = 0.0
        done = False
        return self.price, reward, done

    def legal_actions(self) -> List[str]:
        """Available trade actions."""
        return ["HOLD", "BUY", "SELL"]

    def sample_next_price(self, price: float) -> float:
        """Return the next price using a Gaussian random walk."""
        return price + random.gauss(0.0, self.volatility)

__all__ = ["MarketEnv"]
