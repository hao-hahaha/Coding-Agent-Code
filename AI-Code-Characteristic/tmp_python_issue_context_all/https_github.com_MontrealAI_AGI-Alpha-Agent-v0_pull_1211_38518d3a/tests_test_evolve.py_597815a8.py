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
