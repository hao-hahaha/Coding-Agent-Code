import math
import pytest
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast, sector
from alpha_factory_v1.demos.meta_agentic_agi_v3.core.physics import gibbs


def test_logistic_curve_midpoint() -> None:
    assert forecast.logistic_curve(0.0) == pytest.approx(0.5)


def test_thermodynamic_trigger() -> None:
    sec = sector.Sector("x", energy=1.0, entropy=2.0)
    assert not forecast.thermodynamic_trigger(sec, 0.1)
    assert forecast.thermodynamic_trigger(sec, 1.0)


def test_simulate_years_length() -> None:
    secs = [sector.Sector("a")]
    results = forecast.simulate_years(secs, 3)
    assert [r.year for r in results] == [1, 2, 3]


def test_baseline_growth_and_disruption() -> None:
    sec = sector.Sector("x", energy=1.0, entropy=2.0, growth=0.1)
    traj = forecast.forecast_disruptions([sec], 2, curve="linear", pop_size=2, generations=1)
    first = traj[0].sectors[0]
    second = traj[1].sectors[0]
    assert first.energy == pytest.approx(1.1)
    assert not first.disrupted
    assert second.disrupted
    assert second.energy > 1.1 * 1.1


def test_gibbs_free_energy() -> None:
    logp = [math.log(0.7), math.log(0.3)]
    value = gibbs.free_energy(logp, temperature=1.0, task_cost=1.0)
    entropy = -sum(p * math.log(p) for p in [0.7, 0.3])
    assert value == pytest.approx(1.0 - entropy)
