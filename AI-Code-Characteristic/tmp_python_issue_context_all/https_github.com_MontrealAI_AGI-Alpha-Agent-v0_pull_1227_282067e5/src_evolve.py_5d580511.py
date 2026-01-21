# SPDX-License-Identifier: Apache-2.0
"""Minimal asynchronous evolution loop."""

from __future__ import annotations

import argparse
import asyncio
import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Sequence, Awaitable, Optional

from src.simulation.mats_ops import backtrack_boost
from src.monitoring import metrics


@dataclass(slots=True)
class Candidate:
    genome: Any
    fitness: float = 0.0
    novelty: float = 1.0
    cost: float = 0.0


class Phase(Enum):
    """Execution phase."""

    SELF_MOD = auto()
    TASK_SOLVE = auto()


class InMemoryArchive:
    """Trivial in-memory archive used for demos and tests."""

    def __init__(self) -> None:
        self._items: list[Candidate] = []

    def _update_metrics(self) -> None:
        if not self._items:
            return
        scores = [c.fitness for c in self._items]
        metrics.dgm_best_score.set(max(scores))
        metrics.dgm_archive_mean.set(sum(scores) / len(scores))
        metrics.dgm_lineage_depth.set(len(self._items))

    def all(self) -> Sequence[Candidate]:
        return list(self._items)

    async def accept(self, cand: Candidate) -> None:
        self._items.append(cand)
        self._update_metrics()


async def evolve(
    operator: Callable[[Any], Any],
    evaluate: Callable[[Any], Awaitable[tuple[float, float]]],
    archive: InMemoryArchive,
    *,
    max_cost: float | None = None,
    wallclock: float | None = None,
    backtrack_rate: float = 0.0,
    phase_hook: Optional[Callable[[Phase], None]] = None,
) -> None:
    """Run the self-modification phase followed by task solving."""

    await self_mod_phase(
        operator,
        evaluate,
        archive,
        max_cost=max_cost,
        wallclock=wallclock,
        backtrack_rate=backtrack_rate,
        phase_hook=phase_hook,
    )
    await task_solve_phase(
        operator,
        evaluate,
        archive,
        max_cost=max_cost,
        wallclock=wallclock,
        backtrack_rate=backtrack_rate,
        phase_hook=phase_hook,
    )


async def _phase_loop(
    operator: Callable[[Any], Any],
    evaluate: Callable[[Any], Awaitable[tuple[float, float]]],
    archive: InMemoryArchive,
    *,
    phase: Phase,
    max_cost: float | None = None,
    wallclock: float | None = None,
    backtrack_rate: float = 0.0,
    phase_hook: Optional[Callable[[Phase], None]] = None,
) -> None:
    if not archive.all():
        await archive.accept(Candidate(genome=0.0, fitness=0.0, novelty=1.0, cost=0.0))

    spent = 0.0
    start = time.time()

    while True:
        if max_cost is not None and spent >= max_cost:
            break
        if wallclock is not None and time.time() - start >= wallclock:
            break

        population = archive.all()
        parent = backtrack_boost(population, population, backtrack_rate)
        genome = operator(parent.genome)
        if phase_hook:
            phase_hook(phase)
        fitness, cost = await evaluate(genome)
        child = Candidate(genome=genome, fitness=fitness, novelty=random.random(), cost=cost)
        await archive.accept(child)
        metrics.dgm_children_total.inc()
        spent += cost


async def self_mod_phase(
    operator: Callable[[Any], Any],
    evaluate: Callable[[Any], Awaitable[tuple[float, float]]],
    archive: InMemoryArchive,
    *,
    max_cost: float | None = None,
    wallclock: float | None = None,
    backtrack_rate: float = 0.0,
    phase_hook: Optional[Callable[[Phase], None]] = None,
) -> None:
    await _phase_loop(
        operator,
        evaluate,
        archive,
        phase=Phase.SELF_MOD,
        max_cost=max_cost,
        wallclock=wallclock,
        backtrack_rate=backtrack_rate,
        phase_hook=phase_hook,
    )


async def task_solve_phase(
    operator: Callable[[Any], Any],
    evaluate: Callable[[Any], Awaitable[tuple[float, float]]],
    archive: InMemoryArchive,
    *,
    max_cost: float | None = None,
    wallclock: float | None = None,
    backtrack_rate: float = 0.0,
    phase_hook: Optional[Callable[[Phase], None]] = None,
) -> None:
    await _phase_loop(
        operator,
        evaluate,
        archive,
        phase=Phase.TASK_SOLVE,
        max_cost=max_cost,
        wallclock=wallclock,
        backtrack_rate=backtrack_rate,
        phase_hook=phase_hook,
    )


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
    parser.add_argument(
        "--backtrack-rate",
        type=float,
        default=0.0,
        help="Probability of selecting low-scoring parents",
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
            backtrack_rate=args.backtrack_rate,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
