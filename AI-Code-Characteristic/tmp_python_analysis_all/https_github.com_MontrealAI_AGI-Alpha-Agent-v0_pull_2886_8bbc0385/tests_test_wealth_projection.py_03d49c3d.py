from pathlib import Path

from alpha_factory_v1.core.finance.wealth_projection import projection_from_json


def test_projection_from_json() -> None:
    sample = Path("tests/fixtures/wealth_scenario.json")
    result = projection_from_json(sample)
    assert abs(result["tech"]["npv"] - 49.7370) < 0.01
    assert abs(result["health"]["npv"] - 27.8911) < 0.01
