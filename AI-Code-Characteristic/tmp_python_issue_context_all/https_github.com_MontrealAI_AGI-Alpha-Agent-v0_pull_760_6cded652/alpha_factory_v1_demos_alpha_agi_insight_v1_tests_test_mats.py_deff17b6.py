import pytest
pytestmark = pytest.mark.skip("demo")

if False:  # type: ignore
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import mats


def test_nsga2_step_runs() -> None:
    pop = [mats.Individual([0.0, 0.0]) for _ in range(4)]

    def fn(g):
        return (g[0] ** 2, g[1] ** 2)

    new = mats.nsga2_step(pop, fn, mu=4)
    assert len(new) == 4
