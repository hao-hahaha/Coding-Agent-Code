# SPDX-License-Identifier: Apache-2.0
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

import os
from pathlib import Path
from typing import Dict

try:  # Optional dependency
    import pandas as pd  # type: ignore
except ImportError:  # pragma: no cover - fallback when pandas missing
    pd = None
import csv

# Path to offline sample within the repo
_DEFAULT_BASE = Path(__file__).resolve().parent.parent / "macro_sentinel" / "offline_samples"
_BASE = Path(os.getenv("SAMPLE_DATA_DIR", _DEFAULT_BASE))

_YIELD_CURVE_CSV = _BASE / "yield_curve.csv"
_STABLE_FLOWS_CSV = _BASE / "stable_flows.csv"


def _read_first_row(path: Path) -> Dict[str, str] | None:
    """Return the first row of a CSV as a mapping or ``None`` if empty."""
    if pd is not None:  # use pandas when available for convenience
        try:
            df = pd.read_csv(path, nrows=1)
        except FileNotFoundError:
            raise
        except Exception:  # pragma: no cover - handle corrupt CSV gracefully
            pass
        else:
            if not df.empty:
                return df.iloc[0].to_dict()

    try:
        with open(path, newline="") as fh:
            reader = csv.DictReader(fh)
            return next(reader, None)
    except FileNotFoundError:
        raise

    return None


def detect_yield_curve_alpha() -> str:
    """Return a short message describing the yield-curve state."""
    try:
        row = _read_first_row(_YIELD_CURVE_CSV)
    except FileNotFoundError:
        return "offline data missing"

    if not row:
        return "offline data missing"

    spread = float(row.get("10y", 0)) - float(row.get("3m", 0))
    return (
        f"Yield curve spread {spread:.2f} – consider long bonds"
        if spread < 0
        else f"Yield curve spread {spread:.2f} – curve normal"
    )


def detect_supply_chain_alpha(threshold: float = 50.0) -> str:
    """Return a basic message about supply‑chain flow levels."""
    try:
        row = _read_first_row(_STABLE_FLOWS_CSV)
    except FileNotFoundError:
        return "offline data missing"

    if not row or "usd_mn" not in row:
        return "offline data missing"

    flow = float(row["usd_mn"])
    if flow < threshold:
        return f"Flows {flow:.1f} M USD – potential bottleneck"
    return f"Flows {flow:.1f} M USD – supply chain normal"


__all__ = [
    "detect_yield_curve_alpha",
    "detect_supply_chain_alpha",
]
