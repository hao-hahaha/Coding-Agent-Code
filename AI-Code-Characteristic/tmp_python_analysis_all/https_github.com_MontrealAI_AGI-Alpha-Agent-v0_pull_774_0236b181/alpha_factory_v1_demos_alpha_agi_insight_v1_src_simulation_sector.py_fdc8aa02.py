"""Sector state representation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Sector:
    """Simple sector state used by the simulation."""

    name: str
    energy: float = 1.0
    entropy: float = 1.0
    growth: float = 0.05
    disrupted: bool = False
