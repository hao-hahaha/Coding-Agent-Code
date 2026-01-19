# SPDX-License-Identifier: Apache-2.0
"""Foresight evaluation utilities."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

__all__ = ["evaluate"]


def _rmse(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))


def _lead_time(truth: list[bool], pred: list[bool]) -> int:
    def first_true(seq: list[bool]) -> int:
        for i, val in enumerate(seq):
            if val:
                return i
        return len(seq)

    return first_true(pred) - first_true(truth)


def evaluate(repo_path: Path) -> dict[str, float]:
    """Return average RMSE and lead-time for the Sector-Shock-10 dataset."""

    ds_dir = repo_path / "data" / "sector_shock_10"
    rmses: list[float] = []
    leads: list[float] = []
    for path in sorted(ds_dir.glob("*.json")):
        data = json.loads(path.read_text())
        truth_caps = [float(v) for v in data.get("capabilities", [])]
        truth_shocks = [bool(v) for v in data.get("shocks", [])]

        preds = data.get("predictions", {})
        pred_caps = preds.get("capabilities", data.get("pred_capabilities", truth_caps))
        pred_shocks = preds.get("shocks", data.get("pred_shocks", truth_shocks))

        pred_caps = [float(v) for v in pred_caps]
        pred_shocks = [bool(v) for v in pred_shocks]

        rmses.append(_rmse(truth_caps, pred_caps))
        leads.append(_lead_time(truth_shocks, pred_shocks))
    if not rmses:
        raise FileNotFoundError(ds_dir)
    return {"rmse": statistics.mean(rmses), "lead_time": statistics.mean(leads)}

