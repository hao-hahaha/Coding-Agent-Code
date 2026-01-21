# SPDX-License-Identifier: Apache-2.0
"""Finance adapter utilities."""

from __future__ import annotations

from typing import Dict, Any


def delta_sector_to_dcf(sector_state: Dict[str, float]) -> Dict[str, Any]:
    """Convert ``sector_state`` deltas into a discounted cash flow representation.

    The input dictionary should contain the following keys:

    - ``delta_revenue``: annual revenue delta (absolute value).
    - ``margin``: operating margin as a decimal.
    - ``discount_rate``: discount rate as a decimal.
    - ``years``: number of forecast years.

    Returns a dictionary with calculated ``cash_flows`` and ``npv``.
    """

    delta_revenue = float(sector_state.get("delta_revenue", 0.0))
    margin = float(sector_state.get("margin", 0.0))
    discount_rate = float(sector_state.get("discount_rate", 0.1))
    years = int(sector_state.get("years", 1))

    cash_flow = delta_revenue * margin
    cash_flows = [cash_flow for _ in range(years)]
    npv = sum(cf / ((1 + discount_rate) ** (i + 1)) for i, cf in enumerate(cash_flows))
    return {"cash_flows": cash_flows, "npv": npv}

