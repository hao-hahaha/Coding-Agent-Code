import random
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import mats


def test_nsga2_step_evolves_population() -> None:
    random.seed(0)
    pop = [mats.Individual([0.0, 0.0]) for _ in range(4)]

    def fn(genome):
        x, y = genome
        return x ** 2, y ** 2

    new = mats.nsga2_step(pop, fn, mu=4)
    assert len(new) == 4
    assert all(ind.fitness is not None for ind in new)
    genomes = {tuple(ind.genome) for ind in new}
    assert len(genomes) >= 1
