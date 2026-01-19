"""Alpha detection utilities for Era-of-Experience demo.

This module demonstrates how one might detect simple 'alpha' signals
from offline data samples. Currently it provides a helper analysing the
U.S. Treasury yield curve to check for potential opportunities when the
curve is inverted.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

# Path to offline sample within the repo
_YIELD_CURVE_CSV = (
    Path(__file__).resolve().parent.parent / "macro_sentinel" / "offline_samples" / "yield_curve.csv"
)


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


__all__ = ["detect_yield_curve_alpha"]
