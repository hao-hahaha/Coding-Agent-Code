# SPDX-License-Identifier: Apache-2.0
"""Utility functions for projecting sector wealth scenarios."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from .adapter import delta_sector_to_dcf


def projection_from_json(path: str | Path) -> Dict[str, Dict[str, Any]]:
    """Return discounted cash flow projections loaded from ``path``.

    Each top-level key in the JSON file should map to a sector. The value must be
    a mapping accepted by :func:`delta_sector_to_dcf` with keys ``delta_revenue``,
    ``margin``, ``discount_rate`` and ``years``.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    results: Dict[str, Dict[str, Any]] = {}
    for sector, vals in data.items():
        if not isinstance(vals, dict):
            continue
        results[sector] = delta_sector_to_dcf(vals)
    return results
