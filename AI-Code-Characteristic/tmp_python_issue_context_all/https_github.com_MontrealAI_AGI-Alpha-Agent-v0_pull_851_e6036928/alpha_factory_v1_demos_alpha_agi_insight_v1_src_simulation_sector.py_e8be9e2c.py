# SPDX-License-Identifier: Apache-2.0
"""Simple container describing a market sector.

Each ``Sector`` tracks energy, entropy and growth parameters alongside a
``disrupted`` flag used during the forecast simulation.
"""

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
