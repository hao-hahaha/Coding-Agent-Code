# SPDX-License-Identifier: Apache-2.0
"""Visualization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Any

import pandas as pd
import plotly.express as px

__all__ = ["plot_pareto"]


def _fitness(item: Any) -> Iterable[float]:
    if isinstance(item, Mapping):
        vals = item.get("fitness") or item.get("objective_values")
        if isinstance(vals, Mapping):
            return list(vals.values())
        if isinstance(vals, Iterable):
            return list(vals)
    return list(getattr(item, "fitness", []))


def plot_pareto(elites: Iterable[Any], out_path: Path) -> None:
    """Save Pareto scatter plot and JSON data.

    Parameters
    ----------
    elites:
        Iterable of individuals or dictionaries with ``fitness`` or
        ``objective_values`` sequences.
    out_path:
        File path for the PNG output. A corresponding ``.json`` file is
        written alongside containing the plotted data.
    """

    data = [_fitness(e) for e in elites]
    if not data:
        return

    df = pd.DataFrame(data, columns=["x", "y", *range(len(data[0]) - 2)])
    fig = px.scatter(df, x="x", y="y")

    png = out_path if out_path.suffix else out_path.with_suffix(".png")
    json_path = png.with_suffix(".json")
    json_path.write_text(df.to_json(orient="records"), encoding="utf-8")
    try:
        fig.write_image(str(png))
    except Exception:
        png.write_bytes(b"")
