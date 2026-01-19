import pytest

from src.simulation import replay


@pytest.fixture(scope="module")
def scenario_1994_web() -> replay.Scenario:
    return replay.load_scenario("1994_web")


@pytest.fixture(scope="module")
def scenario_2001_genome() -> replay.Scenario:
    return replay.load_scenario("2001_genome")


@pytest.fixture(scope="module")
def scenario_2008_mobile() -> replay.Scenario:
    return replay.load_scenario("2008_mobile")


@pytest.fixture(scope="module")
def scenario_2012_dl() -> replay.Scenario:
    return replay.load_scenario("2012_dl")


@pytest.fixture(scope="module")
def scenario_2020_mrna() -> replay.Scenario:
    return replay.load_scenario("2020_mrna")


@pytest.fixture
def scenario(request) -> replay.Scenario:
    return request.getfixturevalue(request.param)
