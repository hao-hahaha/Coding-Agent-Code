"""Simple evaluation environment for the MATS demo."""
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
