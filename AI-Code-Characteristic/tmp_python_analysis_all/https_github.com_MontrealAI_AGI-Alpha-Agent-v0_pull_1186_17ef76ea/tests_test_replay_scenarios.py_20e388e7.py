import time

import pytest

from src.simulation import replay


EXPECTED = {
    "1994_web",
    "2001_genome",
    "2008_mobile",
    "2012_dl",
    "2020_mrna",
}


def test_available_scenarios() -> None:
    names = set(replay.available_scenarios())
    assert EXPECTED.issubset(names)


@pytest.mark.parametrize(
    "scenario",
    [
        "scenario_1994_web",
        "scenario_2001_genome",
        "scenario_2008_mobile",
        "scenario_2012_dl",
        "scenario_2020_mrna",
    ],
    indirect=True,
)
def test_scenario_runs_fast(scenario) -> None:
    start = time.perf_counter()
    result = replay.run_scenario(scenario)
    assert len(result) == scenario.horizon
    assert time.perf_counter() - start < 120
