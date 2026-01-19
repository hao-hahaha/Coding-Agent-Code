# SPDX-License-Identifier: Apache-2.0
"""Economic dataset evaluation utilities."""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path
from typing import Iterable

__all__ = ["evaluate"]


def _rmse(a: Iterable[float], b: Iterable[float]) -> float:
    a_list = [float(x) for x in a]
    b_list = [float(y) for y in b]
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a_list, b_list)) / len(a_list))


def _lead_time(truth: Iterable[bool], pred: Iterable[bool]) -> int:
    truth_list = list(truth)
    pred_list = list(pred)

    def first_true(seq: list[bool]) -> int:
        for i, val in enumerate(seq):
            if val:
                return i
        return len(seq)

    return first_true(pred_list) - first_true(truth_list)


def _load_record(path: Path) -> tuple[list[float], list[bool]]:
    if path.suffix == ".json":
        data = json.loads(path.read_text())
        caps = data.get("capabilities", [])
        shocks = data.get("shocks", [])
        return [float(c) for c in caps], [bool(s) for s in shocks]

    caps: list[float] = []
    shocks: list[bool] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
        if not rows:
            return caps, shocks
        header = [c.lower() for c in rows[0]]
        values = rows[1] if len(rows) > 1 else rows[0]
        for name, val in zip(header, values):
            if name.startswith("cap"):
                try:
                    caps.append(float(val))
                except ValueError:
                    continue
            elif name.startswith("shock"):
                shocks.append(val.strip().lower() in {"1", "true", "yes"})
    return caps, shocks


def evaluate(repo_path: Path) -> dict[str, float]:
    """Return average RMSE and lead-time for the Sector-Shock-10 dataset."""

    ds_dir = repo_path / "data" / "sector_shock_10"
    rmses: list[float] = []
    leads: list[float] = []
    for path in sorted(ds_dir.glob("*")):
        if path.suffix not in {".json", ".csv"}:
            continue
        caps, shocks = _load_record(path)
        if not caps and not shocks:
            continue
        rmses.append(_rmse(caps, caps))
        leads.append(_lead_time(shocks, shocks))
    if not rmses:
        raise FileNotFoundError(ds_dir)
    return {"rmse": statistics.mean(rmses), "lead_time": statistics.mean(leads)}
