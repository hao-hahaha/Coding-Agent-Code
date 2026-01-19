import asyncio

from src.evolve import Candidate, InMemoryArchive, evolve


async def _op(genome):
    return genome + 1


async def _eval(_genome):
    return 0.0, 0.05


def test_evolve_stops_on_cost_cap():
    arch = InMemoryArchive()
    asyncio.run(arch.accept(Candidate(0.0, fitness=0.0, novelty=1.0)))

    async def run():
        await evolve(_op, _eval, arch, max_cost=0.1)

    asyncio.run(run())
    # seed + at least two children added
    assert len(arch.all()) >= 3


def test_bandit_early_stop_reduces_cost() -> None:
    gains = [1.0, 0.2, 0.0, 0.0]

    async def run(threshold: float | None) -> InMemoryArchive:
        arch = InMemoryArchive()
        await arch.accept(Candidate(0.0, fitness=0.0, novelty=1.0))
        await evolve(_op, eval_genome, arch, max_cost=5.0, cost_threshold=threshold)
        return arch

    log: list[float] = []

    async def eval_genome(_g: float) -> tuple[float, float]:
        val = gains[len(log)] if len(log) < len(gains) else 0.0
        log.append(val)
        return val, 1.0

    naive_arch = asyncio.run(run(None))
    naive_cost = sum(c.cost for c in naive_arch.all()[1:])
    naive_gain = max(c.fitness for c in naive_arch.all())

    log.clear()
    early_arch = asyncio.run(run(1.5))
    early_cost = sum(c.cost for c in early_arch.all()[1:])
    early_gain = max(c.fitness for c in early_arch.all())

    naive_ratio = naive_cost / naive_gain
    early_ratio = early_cost / early_gain
    assert early_ratio <= 0.75 * naive_ratio
