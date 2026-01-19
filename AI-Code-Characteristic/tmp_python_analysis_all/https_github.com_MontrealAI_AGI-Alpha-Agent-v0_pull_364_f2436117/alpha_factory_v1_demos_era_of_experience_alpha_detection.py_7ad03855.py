"""Alpha detection utilities for Era-of-Experience demo.

This module demonstrates how one might detect simple "alpha" signals
from offline data samples.  A tiny snapshot of the U.S. Treasury yield
curve is included to highlight macro opportunities.  For a more
industry‑agnostic flavour we also provide a toy ``stable_flows`` data
set representing supply‑chain throughput.  Both helpers are purposely
minimal yet illustrate how bespoke detectors could be plugged into the
agent toolkit.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

# Path to offline sample within the repo
_BASE = Path(__file__).resolve().parent.parent / "macro_sentinel" / "offline_samples"

_YIELD_CURVE_CSV = _BASE / "yield_curve.csv"
_STABLE_FLOWS_CSV = _BASE / "stable_flows.csv"


def detect_yield_curve_alpha() -> str:
    """Return a short message describing the yield-curve state."""
    try:
        data = pd.read_csv(_YIELD_CURVE_CSV)
    except FileNotFoundError:
        return "offline data missing"

    spread = float(data["10y"][0]) - float(data["3m"][0])
    return (
        f"Yield curve spread {spread:.2f} – consider long bonds"
        if spread < 0
        else f"Yield curve spread {spread:.2f} – curve normal"
    )


def detect_supply_chain_alpha(threshold: float = 50.0) -> str:
    """Return a basic message about supply‑chain flow levels."""
    try:
        data = pd.read_csv(_STABLE_FLOWS_CSV)
    except FileNotFoundError:
        return "offline data missing"

    flow = float(data["usd_mn"][0])
    if flow < threshold:
        return f"Flows {flow:.1f} M USD – potential bottleneck"
    return f"Flows {flow:.1f} M USD – supply chain normal"


__all__ = [
    "detect_yield_curve_alpha",
    "detect_supply_chain_alpha",
]
