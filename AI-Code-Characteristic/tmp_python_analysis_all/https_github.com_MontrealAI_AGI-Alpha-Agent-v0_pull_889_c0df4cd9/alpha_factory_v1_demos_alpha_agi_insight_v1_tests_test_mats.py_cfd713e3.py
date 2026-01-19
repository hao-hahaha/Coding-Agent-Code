import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import mats


def test_run_evolution_runs() -> None:
    def fn(g: list[float]) -> tuple[float, float]:
        return g[0] ** 2, g[1] ** 2

    pop = mats.run_evolution(fn, 2, population_size=4, generations=1, seed=1)
    assert len(pop) == 4
