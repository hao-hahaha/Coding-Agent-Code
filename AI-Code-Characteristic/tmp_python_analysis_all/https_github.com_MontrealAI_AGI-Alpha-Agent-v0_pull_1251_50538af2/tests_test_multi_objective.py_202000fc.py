import time
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import mats


def _fit(acc: float, nov: float, lat: float) -> tuple[float, float, float]:
    return (-acc, lat, -nov)


def test_pareto_front_performance_and_dominance() -> None:
    pop = [mats.Individual([0.0]) for _ in range(500)]
    for ind in pop[:-3]:
        ind.fitness = _fit(0.1, 0.1, 100.0)
    front_vals = [(0.9, 0.2, 20.0), (0.8, 0.5, 10.0), (0.85, 0.3, 15.0)]
    for ind, vals in zip(pop[-3:], front_vals):
        ind.fitness = _fit(*vals)
    start = time.perf_counter()
    front = mats.pareto_front(pop)
    duration = (time.perf_counter() - start) * 1000
    assert duration < 50
    assert {ind.fitness for ind in front} == {_fit(*v) for v in front_vals}
