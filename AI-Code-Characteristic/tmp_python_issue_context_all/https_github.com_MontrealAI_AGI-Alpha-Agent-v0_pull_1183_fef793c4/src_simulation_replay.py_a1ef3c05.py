# SPDX-License-Identifier: Apache-2.0
"""Utilities for replaying historic scenarios."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Any, cast

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast, sector


BASE_DIR = Path(__file__).resolve().parents[2] / "data" / "historic_scenarios"


@dataclass(slots=True)
class Scenario:
    """A minimal scenario description."""

    name: str
    horizon: int
    sectors: List[sector.Sector]
    curve: str = "logistic"
    k: float | None = None
    x0: float | None = None
    pop_size: int = 6
    generations: int = 1


__all__ = ["Scenario", "available_scenarios", "load_scenario", "run_scenario"]


def _load_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data: Any = yaml.safe_load(text)
    except Exception:
        data = json.loads(text)
    return cast(dict[str, Any], data or {})


def available_scenarios(directory: str | Path | None = None) -> list[str]:
    """Return the list of available scenario names."""

    dir_path = Path(directory or BASE_DIR)
    names = {p.stem for p in dir_path.glob("*.yaml")}
    names.update(p.stem for p in dir_path.glob("*.yml"))
    return sorted(names)


def load_scenario(name: str, directory: str | Path | None = None) -> Scenario:
    """Load a scenario definition by name."""

    dir_path = Path(directory or BASE_DIR)
    path = dir_path / f"{name}.yaml"
    if not path.exists():
        path = dir_path / f"{name}.yml"
    data = _load_yaml(path)

    secs: list[sector.Sector] = []
    for entry in data.get("sectors", []):
        if isinstance(entry, str):
            secs.append(sector.Sector(entry))
        elif isinstance(entry, dict):
            secs.append(
                sector.Sector(
                    entry.get("name", ""),
                    float(entry.get("energy", 1.0)),
                    float(entry.get("entropy", 1.0)),
                    float(entry.get("growth", 0.05)),
                    bool(entry.get("disrupted", False)),
                )
            )
        else:
            raise ValueError(f"Invalid sector entry: {entry!r}")

    return Scenario(
        name=data.get("name", name),
        horizon=int(data.get("horizon", 1)),
        sectors=secs,
        curve=data.get("curve", "logistic"),
        k=data.get("k"),
        x0=data.get("x0"),
        pop_size=int(data.get("pop_size", 6)),
        generations=int(data.get("generations", 1)),
    )


def run_scenario(scn: Scenario) -> list[forecast.TrajectoryPoint]:
    """Execute ``scn`` and return its trajectory."""

    secs = [sector.Sector(s.name, s.energy, s.entropy, s.growth, s.disrupted) for s in scn.sectors]
    return forecast.forecast_disruptions(
        secs,
        scn.horizon,
        scn.curve,
        k=scn.k,
        x0=scn.x0,
        pop_size=scn.pop_size,
        generations=scn.generations,
    )
