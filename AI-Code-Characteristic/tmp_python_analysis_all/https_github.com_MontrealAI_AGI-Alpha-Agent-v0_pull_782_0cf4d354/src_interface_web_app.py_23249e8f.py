"""Interactive Streamlit dashboard for running AGI simulations.

The app mirrors the ``cli.py`` options with widgets for the forecast horizon,
growth curve and evolutionary settings. During execution it streams run
progress, renders Plotly charts for the disruption timeline and the MATS
Pareto‑front and exposes download buttons for the collected results.
"""

from __future__ import annotations

import importlib
import json
import time
from typing import Any, TYPE_CHECKING

import pandas as pd
import plotly.express as px

try:  # pragma: no cover - optional dependency
    import streamlit as st
except Exception:  # pragma: no cover - optional
    st = None

if TYPE_CHECKING:  # pragma: no cover - typing only
    ForecastModule = Any
    SectorModule = Any
    MatsModule = Any
else:
    ForecastModule = Any
    SectorModule = Any
    MatsModule = Any

forecast = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.forecast")
sector = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.sector")
mats = importlib.import_module("alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation.mats")


def timeline_df(traj: list[Any]) -> pd.DataFrame:
    """Return a DataFrame summarising sector performance."""

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


def pareto_df(pop: list[Any]) -> pd.DataFrame:
    """Return a DataFrame for plotting a Pareto front."""

    return pd.DataFrame(
        {"x": [p.genome[0] for p in pop], "y": [p.genome[1] for p in pop], "rank": [p.rank for p in pop]}
    )


def _run_simulation(horizon: int, curve: str, pop_size: int, generations: int) -> None:
    """Execute the simulation and update charts live."""
    if st is None:  # pragma: no cover - fallback
        print("Streamlit not installed")
        return

    st.session_state.logs = []
    secs = [sector.Sector(f"s{i:02d}") for i in range(pop_size)]
    timeline_placeholder = st.empty()
    pareto_placeholder = st.empty()
    log_box = st.empty()
    progress = st.progress(0.0)

    traj = forecast.forecast_disruptions(
        secs,
        horizon,
        curve,
        pop_size=pop_size,
        generations=generations,
    )

    timeline_rows: list[dict[str, Any]] = []
    total_steps = horizon + generations
    step = 0
    for t in traj:
        step += 1
        affected = [s for s in t.sectors if s.disrupted]
        st.session_state.logs.append(f"Year {t.year}: {len(affected)} affected")
        log_box.text("\n".join(st.session_state.logs[-20:]))
        timeline_rows.extend(
            {
                "year": t.year,
                "sector": s.name,
                "energy": s.energy,
                "disrupted": s.disrupted,
            }
            for s in t.sectors
        )
        df = pd.DataFrame(timeline_rows)
        if not df.empty:
            fig = px.line(
                df,
                x="year",
                y="energy",
                color="sector",
                line_dash=df["disrupted"].map({True: "dash", False: "solid"}),
            )
            timeline_placeholder.plotly_chart(fig, use_container_width=True)
        progress.progress(step / total_steps)
        time.sleep(0.1)

    pop = [mats.Individual([0.0, 0.0]) for _ in range(pop_size)]

    def eval_fn(genome: list[float]) -> tuple[float, float]:
        x, y = genome
        return x**2, y**2

    for g in range(generations):
        step += 1
        pop = mats.nsga2_step(pop, eval_fn, mu=pop_size)
        df_pareto = pareto_df(pop)
        fig_p = px.scatter(df_pareto, x="x", y="y", color="rank")
        pareto_placeholder.plotly_chart(fig_p, use_container_width=True)
        st.session_state.logs.append(f"Generation {g + 1}")
        log_box.text("\n".join(st.session_state.logs[-20:]))
        progress.progress(step / total_steps)
        time.sleep(0.1)

    st.download_button(
        "Download results (JSON)",
        json.dumps(
            {
                "timeline": timeline_rows,
                "pareto": df_pareto.to_dict(orient="records"),
            }
        ).encode(),
        file_name="results.json",
    )
    csv_bytes = pd.DataFrame(timeline_rows).to_csv(index=False).encode()
    st.download_button("Download timeline (CSV)", csv_bytes, file_name="timeline.csv")


def main() -> None:  # pragma: no cover - entry point
    """Launch the Streamlit app."""
    if st is None:  # pragma: no cover - fallback
        print("Streamlit not installed")
        return

    st.title("AGI Simulation Dashboard")
    horizon = st.sidebar.number_input("Forecast horizon", min_value=1, max_value=20, value=5)
    curve = st.sidebar.selectbox("Growth curve", ["logistic", "linear", "exponential"], index=0)
    pop_size = st.sidebar.number_input("Population size", min_value=2, max_value=20, value=6)
    generations = st.sidebar.number_input("Generations", min_value=1, max_value=20, value=3)
    if st.sidebar.button("Run simulation"):
        _run_simulation(horizon, curve, pop_size, generations)


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
