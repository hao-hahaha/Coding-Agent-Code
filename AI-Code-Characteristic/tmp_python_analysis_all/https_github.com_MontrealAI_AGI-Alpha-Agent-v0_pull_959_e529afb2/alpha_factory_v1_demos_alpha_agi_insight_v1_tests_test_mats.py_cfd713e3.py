import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import mats


def test_run_evolution_runs() -> None:
    def fn(g: list[float]) -> tuple[float, float]:
        return g[0] ** 2, g[1] ** 2

    pop = mats.run_evolution(fn, 2, population_size=4, generations=1, seed=1)
    assert len(pop) == 4


def _small_population() -> list[mats.Individual]:
    """Return a tiny population with known fitness values."""

    fits = [(1.0, 3.0), (2.0, 2.0), (3.0, 1.0), (4.0, 5.0), (5.0, 4.0)]
    return [mats.Individual([], fitness=f) for f in fits]


def test_non_dominated_sort_assigns_ranks() -> None:
    pop = _small_population()
    fronts = mats._non_dominated_sort(pop)

    assert len(fronts) == 2
    first = {ind.fitness for ind in fronts[0]}
    second = {ind.fitness for ind in fronts[1]}
    assert first == {(1.0, 3.0), (2.0, 2.0), (3.0, 1.0)}
    assert second == {(4.0, 5.0), (5.0, 4.0)}
    assert {ind.rank for ind in fronts[0]} == {0}
    assert {ind.rank for ind in fronts[1]} == {1}


def test_crowding_distances() -> None:
    pop = _small_population()
    fronts = mats._non_dominated_sort(pop)
    mats._crowding(fronts[0])
    mats._crowding(fronts[1])

    cd_first = {ind.fitness: ind.crowd for ind in fronts[0]}
    assert cd_first[(2.0, 2.0)] == pytest.approx(2.0)
    assert cd_first[(1.0, 3.0)] == float("inf")
    assert cd_first[(3.0, 1.0)] == float("inf")

    cd_second = {ind.fitness: ind.crowd for ind in fronts[1]}
    assert all(d == float("inf") for d in cd_second.values())

