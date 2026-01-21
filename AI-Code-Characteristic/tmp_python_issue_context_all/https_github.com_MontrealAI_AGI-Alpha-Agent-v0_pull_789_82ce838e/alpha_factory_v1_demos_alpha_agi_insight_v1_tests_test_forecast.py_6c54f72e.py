from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast, sector


def test_simulate_years() -> None:
    secs = [sector.Sector("x", 1.0, 1.0)]
    results = forecast.simulate_years(secs, 2)
    assert len(results) == 2
