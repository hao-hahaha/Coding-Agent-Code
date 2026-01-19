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


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_scenario_runs_fast(name: str) -> None:
    start = time.perf_counter()
    scn = replay.load_scenario(name)
    result = replay.run_scenario(scn)
    assert len(result) == scn.horizon
    assert time.perf_counter() - start < 120
