"""Toy evaluation utilities for the MATS demo."""
from __future__ import annotations

from typing import List
import random

TARGET = 5


def evaluate(agents: List[int]) -> float:
    """Return a pseudo reward for the agents."""
    distance = sum(abs(a - TARGET) for a in agents)
    noise = random.random() * 0.1
    return -distance + noise

