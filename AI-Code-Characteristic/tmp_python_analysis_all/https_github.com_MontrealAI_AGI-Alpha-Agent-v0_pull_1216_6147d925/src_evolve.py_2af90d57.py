# SPDX-License-Identifier: Apache-2.0
"""Minimal asynchronous evolution loop."""

from __future__ import annotations

import argparse
import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from src.archive.selector import select_parent
from src.monitoring import metrics


@dataclass(slots=True)
class Candidate:
    genome: Any
    fitness: float = 0.0
    novelty: float = 1.0
    cost: float = 0.0


class InMemoryArchive:
    """Trivial in-memory archive used for demos and tests."""

    def __init__(self) -> None:
        self._items: list[Candidate] = []

    def all(self) -> Sequence[Candidate]:
        return list(self._items)

    async def accept(self, cand: Candidate) -> None:
        self._items.append(cand)


async def evolve(
    operator: Callable[[Any], Any],
    evaluate: Callable[[Any], tuple[float, float]],
    archive: InMemoryArchive,
    *,
    max_cost: float | None = None,
    wallclock: float | None = None,
) -> None:
    """Run an asynchronous evolution loop until the budget is exhausted."""

    if not archive.all():
        # seed with a random candidate
        await archive.accept(Candidate(genome=0.0, fitness=0.0, novelty=1.0, cost=0.0))

    spent = 0.0
    start = time.time()

    while True:
        if max_cost is not None and spent >= max_cost:
            break
        if wallclock is not None and time.time() - start >= wallclock:
            break

        parent = select_parent(archive.all(), temp=1.0)
        genome = operator(parent.genome)
        fitness, cost = await evaluate(genome)
        child = Candidate(genome=genome, fitness=fitness, novelty=random.random(), cost=cost)
        await archive.accept(child)
        metrics.dgm_children_total.inc()
        spent += cost


async def _dummy_operator(genome: Any) -> Any:
    await asyncio.sleep(0)
    return genome


async def _dummy_evaluate(genome: Any) -> tuple[float, float]:
    await asyncio.sleep(0)
    return random.random(), 0.01


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-cost", type=float, default=1.0, help="Cost budget")
    parser.add_argument(
        "--wallclock",
        type=float,
        default=None,
        help="Wallclock limit in seconds",
    )
    args = parser.parse_args(argv)

    archive = InMemoryArchive()
    asyncio.run(
        evolve(
            lambda g: g,
            _dummy_evaluate,
            archive,
            max_cost=args.max_cost,
            wallclock=args.wallclock,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
