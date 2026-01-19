from __future__ import annotations

import random
from typing import Tuple, List

class MarketEnv:
    """Minimal stochastic market environment for demo purposes."""

    def __init__(self, start_price: float = 100.0, volatility: float = 1.0) -> None:
        """Initialize a minimal price simulator."""

        self.start_price = start_price
        self.volatility = volatility
        self.price = start_price
        self.position = 0.0
        self.cash = 0.0
        self.history: List[float] = [start_price]

    # ------------------------------------------------------------------ #
    #  Gym-like API                                                      #
    # ------------------------------------------------------------------ #
    def reset(self) -> float:
        """Reset the environment and return the starting price."""
        self.price = self.start_price
        return self.price

    def step(self, action: str) -> Tuple[float, float, bool]:
        """Execute ``action`` and return ``(price, reward, done)``."""

        if action not in self.legal_actions():
            raise ValueError(f"invalid action {action!r}")

        prev_price = self.price
        self.price = self.sample_next_price(self.price)
        self.history.append(self.price)

        if action == "BUY":
            self.position += 1
            self.cash -= prev_price
        elif action == "SELL":
            self.position -= 1
            self.cash += prev_price

        reward = self.position * (self.price - prev_price)
        done = False
        return self.price, reward, done

    def legal_actions(self) -> List[str]:
        """Available trade actions."""
        return ["HOLD", "BUY", "SELL"]

    def sample_next_price(self, price: float) -> float:
        """Return the next price using a Gaussian random walk."""
        return price + random.gauss(0.0, self.volatility)

    @property
    def portfolio_value(self) -> float:
        """Current cash + mark-to-market value of the position."""
        return self.cash + self.position * self.price

    def __repr__(self) -> str:  # noqa: D401
        return f"MarketEnv(price={self.price:.2f}, position={self.position})"

__all__ = ["MarketEnv"]
