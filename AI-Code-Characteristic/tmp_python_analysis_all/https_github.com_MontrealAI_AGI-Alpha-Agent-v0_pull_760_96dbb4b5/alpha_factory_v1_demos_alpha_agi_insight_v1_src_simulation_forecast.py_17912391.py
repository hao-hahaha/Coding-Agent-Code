"""Thermodynamic trigger forecasting."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

from .sector import Sector


@dataclass(slots=True)
class ForecastPoint:
    year: int
    capability: float
    affected: List[Sector]


def logistic_curve(t: float, k: float = 1.0, x0: float = 0.0) -> float:
    return 1.0 / (1.0 + math.exp(-k * (t - x0)))


def thermodynamic_trigger(sector: Sector, capability: float) -> bool:
    delta_g = sector.energy - capability * sector.entropy
    return delta_g < 0


def simulate_years(sectors: Iterable[Sector], horizon: int) -> List[ForecastPoint]:
    results: List[ForecastPoint] = []
    for year in range(1, horizon + 1):
        cap = logistic_curve(year / horizon * 10.0)
        affected = [s for s in sectors if thermodynamic_trigger(s, cap)]
        results.append(ForecastPoint(year, cap, affected))
    return results
