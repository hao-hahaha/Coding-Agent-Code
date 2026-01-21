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
