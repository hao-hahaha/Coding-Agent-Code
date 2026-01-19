import math
import pytest
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast, sector
from alpha_factory_v1.demos.meta_agentic_agi_v3.core.physics import gibbs


def test_logistic_curve_midpoint() -> None:
    assert forecast.logistic_curve(0.0) == pytest.approx(0.5)


def test_logistic_curve_parameters() -> None:
    """Custom ``k`` and ``x0`` should shift the curve."""
    base = forecast.logistic_curve(0.0)
    shifted = forecast.logistic_curve(0.5, x0=0.5)
    steep = forecast.logistic_curve(0.1, k=2.0)
    assert shifted == pytest.approx(base)
    assert steep > forecast.logistic_curve(0.1)


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


def test_forecast_disruptions_trigger_and_gain(monkeypatch) -> None:
    monkeypatch.setattr(forecast, "_innovation_gain", lambda *_, **__: 0.5)
    sec = sector.Sector("x", energy=1.0, entropy=2.0, growth=0.0)
    traj = forecast.forecast_disruptions([sec], 1, curve="linear", pop_size=2, generations=1)
    pt = traj[0].sectors[0]
    assert pt.disrupted
    assert pt.energy == pytest.approx(1.0 + 0.5)


def test_forecast_disruptions_multiple_sectors() -> None:
    a = sector.Sector("a", energy=1.0, entropy=0.1)
    b = sector.Sector("b", energy=1.0, entropy=2.0)
    traj = forecast.forecast_disruptions([a, b], 1, curve="linear", pop_size=2, generations=1)
    assert not traj[0].sectors[0].disrupted
    assert traj[0].sectors[1].disrupted


def test_capability_growth_curves() -> None:
    """Capability growth curves should map time into [0,1]."""
    t = 0.5
    linear = forecast.capability_growth(t, curve="linear")
    logistic = forecast.capability_growth(t, curve="logistic")
    exponential = forecast.capability_growth(t, curve="exponential")
    assert linear == pytest.approx(forecast.linear_curve(t))
    assert logistic == pytest.approx(forecast.logistic_curve(10 * t))
    assert exponential == pytest.approx(forecast.exponential_curve(t))
    assert logistic > linear > exponential
    assert 0.0 <= exponential <= 1.0
    assert 0.0 <= linear <= 1.0
    assert 0.0 <= logistic <= 1.0


def test_capability_growth_params() -> None:
    """Capability growth should forward ``k`` and ``x0``."""
    val_default = forecast.capability_growth(0.5, curve="logistic")
    val_custom = forecast.capability_growth(0.5, curve="logistic", k=5.0, x0=0.0)
    assert val_custom == pytest.approx(forecast.logistic_curve(0.5, k=5.0))
    assert val_custom != val_default


def test_exponential_curve_parameters() -> None:
    """Exponential curve should honour ``k`` and ``x0``."""
    base = forecast.exponential_curve(0.5)
    shifted = forecast.exponential_curve(0.6, x0=0.1)
    steep = forecast.exponential_curve(0.5, k=5.0)
    assert shifted == pytest.approx(base)
    assert steep < base


def test_thermodynamic_trigger_edges() -> None:
    sec = sector.Sector("x", energy=1.0, entropy=2.0)
    assert not forecast.thermodynamic_trigger(sec, 0.5)
    assert forecast.thermodynamic_trigger(sec, 0.50001)
    sec2 = sector.Sector("y", energy=0.0, entropy=1.0)
    assert not forecast.thermodynamic_trigger(sec2, 0.0)
    assert forecast.thermodynamic_trigger(sec2, 0.1)


def test_innovation_gain_positive() -> None:
    gain = forecast._innovation_gain(pop_size=2, generations=1)
    assert gain > 0.0
    assert gain < 0.1


def test_innovation_gain_seed_deterministic() -> None:
    gain1 = forecast._innovation_gain(pop_size=2, generations=1, seed=123)
    gain2 = forecast._innovation_gain(pop_size=2, generations=1, seed=123)
    assert gain1 == gain2


def test_forecast_disruptions_seed_deterministic() -> None:
    sec1 = sector.Sector("x", energy=1.0, entropy=2.0, growth=0.1)
    sec2 = sector.Sector("x", energy=1.0, entropy=2.0, growth=0.1)
    traj1 = forecast.forecast_disruptions([sec1], 2, curve="linear", pop_size=2, generations=1, seed=123)
    traj2 = forecast.forecast_disruptions([sec2], 2, curve="linear", pop_size=2, generations=1, seed=123)
    result1 = [ (p.year, p.sectors[0].energy, p.sectors[0].disrupted) for p in traj1 ]
    result2 = [ (p.year, p.sectors[0].energy, p.sectors[0].disrupted) for p in traj2 ]
    assert result1 == result2
