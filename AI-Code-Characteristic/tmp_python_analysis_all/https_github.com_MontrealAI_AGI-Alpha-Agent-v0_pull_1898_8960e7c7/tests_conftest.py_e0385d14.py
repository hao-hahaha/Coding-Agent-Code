# SPDX-License-Identifier: Apache-2.0
import pytest
import sys
import types
import importlib.util
from src.simulation import replay

rocketry_stub = types.ModuleType("rocketry")
rocketry_stub.Rocketry = type("Rocketry", (), {})
conds_mod = types.ModuleType("rocketry.conds")
conds_mod.every = lambda *_: None
rocketry_stub.conds = conds_mod
sys.modules.setdefault("rocketry", rocketry_stub)
sys.modules.setdefault("rocketry.conds", conds_mod)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Ensure core packages are installed at session start."""
    missing = [name for name in ("numpy", "torch") if importlib.util.find_spec(name) is None]
    if missing:
        try:
            import check_env
        except Exception as exc:  # pragma: no cover - fallback just prints
            print(f"check_env unavailable: {exc}")
        else:
            check_env.main(["--auto-install"])


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
