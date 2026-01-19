"""Interactive Streamlit dashboard for running AGI simulations.

The UI exposes simple controls for the forecast horizon, population size and
number of generations. During execution the page renders live charts of the
forecast capability timeline, number of disrupted sectors, the current Pareto
front and a scrolling log view.
"""

from __future__ import annotations

import importlib
import time
from typing import Any, TYPE_CHECKING

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


def _run_simulation(horizon: int, pop_size: int, generations: int) -> None:
    """Execute the simulation and update charts live."""
    if st is None:  # pragma: no cover - fallback
        print("Streamlit not installed")
        return

    st.session_state.logs = []
    secs = [sector.Sector(f"s{i:02d}") for i in range(pop_size)]
    capability_chart = st.line_chart()
    sector_chart = st.line_chart()
    pareto_area = st.empty()
    log_box = st.empty()

    traj = forecast.forecast_disruptions(
        secs,
        horizon,
        generations=generations,
        pop_size=pop_size,
    )
    for t in traj:
        affected = [s for s in t.sectors if s.disrupted]
        capability_chart.add_rows({"capability": [t.capability]})
        sector_chart.add_rows({"affected": [len(affected)]})
        st.session_state.logs.append(f"Year {t.year}: {len(affected)} affected")
        log_box.text("\n".join(st.session_state.logs[-20:]))
        time.sleep(0.1)

    pop = [mats.Individual([0.0, 0.0]) for _ in range(pop_size)]

    def eval_fn(genome: list[float]) -> tuple[float, float]:
        x, y = genome
        return x**2, y**2

    for _ in range(generations):
        pop = mats.nsga2_step(pop, eval_fn, mu=pop_size)
        front = [(ind.genome[0], ind.genome[1]) for ind in pop if ind.rank == 0]
        pareto_area.line_chart({"x": [x for x, _ in front], "y": [y for _, y in front]})
        time.sleep(0.1)


def main() -> None:  # pragma: no cover - entry point
    """Launch the Streamlit app."""
    if st is None:  # pragma: no cover - fallback
        print("Streamlit not installed")
        return

    st.title("AGI Simulation Dashboard")
    horizon = st.sidebar.number_input("Forecast horizon", min_value=1, max_value=20, value=5)
    pop_size = st.sidebar.number_input("Population size", min_value=2, max_value=20, value=6)
    generations = st.sidebar.number_input("Generations", min_value=1, max_value=20, value=3)
    if st.sidebar.button("Run simulation"):
        _run_simulation(horizon, pop_size, generations)


if __name__ == "__main__":  # pragma: no cover - script entry
    main()
