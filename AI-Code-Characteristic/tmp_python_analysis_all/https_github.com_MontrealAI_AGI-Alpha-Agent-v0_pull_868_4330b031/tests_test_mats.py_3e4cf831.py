from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import mats


def test_run_evolution_deterministic() -> None:
    def fn(genome: list[float]) -> tuple[float, float]:
        x, y = genome
        return x**2, y**2

    pop1 = mats.run_evolution(fn, 2, population_size=4, generations=3, mutation_rate=0.5, seed=123)
    pop2 = mats.run_evolution(fn, 2, population_size=4, generations=3, mutation_rate=0.5, seed=123)

    assert [ind.genome for ind in pop1] == [ind.genome for ind in pop2]
    assert any(any(g != 0 for g in ind.genome) for ind in pop1)


def test_run_evolution_evaluates_population() -> None:
    def fn(genome: list[float]) -> tuple[float, float]:
        x, y = genome
        return abs(x), abs(y)

    pop = mats.run_evolution(fn, 2, population_size=3, generations=1, seed=1)

    assert len(pop) == 3
    assert all(ind.fitness is not None for ind in pop)


def test_run_evolution_different_seeds() -> None:
    def fn(genome: list[float]) -> tuple[float, float]:
        x, y = genome
        return x**2, y**2

    pop1 = mats.run_evolution(fn, 2, population_size=3, generations=1, seed=1)
    pop2 = mats.run_evolution(fn, 2, population_size=3, generations=1, seed=2)

    assert [ind.genome for ind in pop1] != [ind.genome for ind in pop2]
