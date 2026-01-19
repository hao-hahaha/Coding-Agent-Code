# SPDX-License-Identifier: Apache-2.0
"""Evaluation environments for the MATS demo.

This module exposes a lightweight :class:`NumberLineEnv` used by the unit tests
and demo loop along with a placeholder :class:`LiveBrokerEnv` that illustrates
how one might integrate real market data.  The live broker variant currently
inherits the toy environment so the rest of the demo remains fully runnable
offline.  It accepts an optional market data feed so advanced users can plug in
their own price sources.
"""
from __future__ import annotations

import random
from typing import List

class NumberLineEnv:
    """Toy environment where agents aim for a target integer."""

    def __init__(self, target: int = 5) -> None:
        self.target = target

    def rollout(self, agents: List[int]) -> float:
        """Return a pseudo reward after a single rollout."""
        distance = sum(abs(a - self.target) for a in agents)
        noise = random.random() * 0.1
        return -distance + noise


class LiveBrokerEnv(NumberLineEnv):
    """Placeholder environment hooking into a live execution broker.

    Parameters
    ----------
    target:
        Target integer used by the base :class:`NumberLineEnv` logic.
    market_data:
        Optional sequence of numbers representing live prices.  When omitted the
        environment behaves exactly like :class:`NumberLineEnv`.
    """

    def __init__(self, target: int = 5, market_data: List[int] | None = None) -> None:
        super().__init__(target=target)
        self.market_data = list(market_data) if market_data else []

    def rollout(self, agents: List[int]) -> float:
        if self.market_data:
            self.target = self.market_data.pop(0)
        return super().rollout(agents)
