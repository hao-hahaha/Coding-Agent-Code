"""Sector state representation."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Sector:
    name: str
    energy: float = 1.0
    entropy: float = 1.0
