# SPDX-License-Identifier: Apache-2.0
"""Full Streamlit dashboard visualising simulation output.

This interface allows interactive control of the forecast parameters and
renders charts using Plotly. It can fall back to text output when
Streamlit is unavailable.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

try:  # pragma: no cover - optional dependency
    import streamlit as st
except Exception:  # pragma: no cover - optional
    st = None

from ..simulation import forecast, sector

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd


def _simulate(
    horizon: int,
    curve: str,
    pop_size: int,
    generations: int,
    energy: float = 1.0,
    entropy: float = 1.0,
) -> list[Any]:
    """Run the disruption forecast and return the trajectory."""

    secs = [sector.Sector(f"s{i:02d}", energy, entropy) for i in range(pop_size)]
    return forecast.forecast_disruptions(
        secs,
        horizon,
        curve,
        pop_size=pop_size,
        generations=generations,
    )


def _timeline_df(traj: list[Any]) -> "pd.DataFrame":
    """Convert trajectory data into a DataFrame."""

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


def main() -> None:  # pragma: no cover - entry point
    """Launch the Streamlit dashboard or print results."""

    if st is None:
        print("Streamlit not installed")
        traj = _simulate(5, "logistic", 6, 3)
        for row in _disruption_df(traj).to_dict(orient="records"):
            print(f"{row['sector']}: year {row['year']}")
        return

    st.title("α‑AGI Insight")
    horizon = st.sidebar.slider("Horizon", 1, 20, 5)
    curve = st.sidebar.selectbox("Growth curve", ["logistic", "linear", "exponential"], index=0)
    pop_size = st.sidebar.slider("Population size", 2, 20, 6)
    generations = st.sidebar.slider("Generations", 1, 20, 3)
    energy = st.sidebar.number_input("Initial energy", min_value=0.0, value=1.0)
    entropy = st.sidebar.number_input("Initial entropy", min_value=0.0, value=1.0)

    if st.sidebar.button("Run forecast"):
        traj = _simulate(horizon, curve, pop_size, generations, energy, entropy)
        df = _timeline_df(traj)
        import plotly.express as px

        fig = px.line(
            df,
            x="year",
            y="energy",
            color="sector",
            line_dash=df["disrupted"].map({True: "dash", False: "solid"}),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.table(_disruption_df(traj))


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
