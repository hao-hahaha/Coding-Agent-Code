# SPDX-License-Identifier: Apache-2.0
"""Minimal Streamlit interface for disruption forecasts."""

from __future__ import annotations

import argparse
import sys
from typing import Any, TYPE_CHECKING, cast

from ..simulation import forecast, sector

try:  # pragma: no cover - optional dependency
    import streamlit as _st
except Exception:  # pragma: no cover - optional
    _st = None
st: Any | None = cast(Any, _st)

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd


def _simulate(horizon: int, curve: str, pop_size: int, generations: int) -> list[Any]:
    """Run the disruption forecast and return the trajectory."""
    secs = [sector.Sector(f"s{i:02d}") for i in range(pop_size)]
    return cast(
        list[Any],
        forecast.forecast_disruptions(
            secs,
            horizon,
            curve,
            pop_size=pop_size,
            generations=generations,
        ),
    )


def _timeline_df(traj: list[Any]) -> "pd.DataFrame":
    """Convert trajectory data into a pandas DataFrame."""
    import pandas as pd

    rows = []
    for point in traj:
        for sec in point.sectors:
            rows.append(
                {
                    "year": point.year,
                    "sector": sec.name,
                    "energy": sec.energy,
                    "disrupted": sec.disrupted,
                }
            )
    return pd.DataFrame(rows)


def _disruption_df(traj: list[Any]) -> "pd.DataFrame":
    """Return the first disruption year per sector."""
    import pandas as pd

    years: dict[str, int] = {}
    for point in traj:
        for sec in point.sectors:
            if sec.disrupted and sec.name not in years:
                years[sec.name] = point.year
    return pd.DataFrame({"sector": list(years.keys()), "year": list(years.values())})


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - entry point
    """Launch the minimal dashboard or print results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--text",
        action="store_true",
        help="Force text-mode output even when Streamlit is installed",
    )
    args = parser.parse_args(argv)

    if st is None and not args.text:
        sys.exit("Streamlit not installed. Re-run with --text for console output.")

    if args.text or st is None:
        traj = _simulate(5, "logistic", 6, 3)
        for record in _disruption_df(traj).to_dict(orient="records"):
            print(f"{record['sector']}: year {record['year']}")
        return

    st.title("Disruption Forecast")
    horizon = st.sidebar.slider("Horizon", 1, 20, 5)
    curve = st.sidebar.selectbox("Curve", ["logistic", "linear", "exponential"], index=0)
    pop_size = st.sidebar.slider("Population size", 2, 20, 6)
    generations = st.sidebar.slider("Generations", 1, 20, 3)

    if st.sidebar.button("Run"):
        traj = _simulate(horizon, curve, pop_size, generations)
        df = _timeline_df(traj)
        pivot = df.pivot(index="year", columns="sector", values="energy")
        st.line_chart(pivot)
        st.table(_disruption_df(traj))


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
