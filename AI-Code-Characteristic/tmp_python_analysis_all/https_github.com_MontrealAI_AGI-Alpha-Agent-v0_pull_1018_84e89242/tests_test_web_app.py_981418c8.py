import pytest

pd = pytest.importorskip("pandas")
from src.interface import web_app
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast, sector, mats  # type: ignore[import]


def test_timeline_df() -> None:
    secs = [sector.Sector("a"), sector.Sector("b")]
    traj = forecast.forecast_disruptions(secs, 2, pop_size=2, generations=1)
    df = web_app.timeline_df(traj)
    assert set(df.columns) == {"year", "sector", "energy", "disrupted"}
    assert len(df) == 4


def test_pareto_df() -> None:
    pop = [mats.Individual([0.0, 0.0]), mats.Individual([1.0, 1.0])]
    pop[0].rank = 0
    pop[1].rank = 1
    df = web_app.pareto_df(pop)
    assert set(df.columns) == {"x", "y", "rank"}
    assert len(df) == 2


def test_population_df() -> None:
    pop = [mats.Individual([0.0, 0.0]), mats.Individual([1.0, 1.0])]
    for i, ind in enumerate(pop):
        ind.fitness = (i * 1.0, i * 2.0, i * 3.0)
        ind.rank = i
    df = web_app.population_df(pop)
    assert set(df.columns) == {"effectiveness", "risk", "complexity", "rank"}
    assert len(df) == 2


def test_run_simulation_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    """Ensure _run_simulation accepts the new num_sectors argument."""

    web_app._run_simulation(1, "logistic", 2, 3, 1)
    out, _ = capsys.readouterr()
    assert "Streamlit not installed" in out
