# SPDX-License-Identifier: Apache-2.0
"""Compare selector strategies via a toy optimisation."""

from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


from src.archive.selector import select_parent


class _Candidate:
    __slots__ = ("genome", "fitness", "novelty")

    def __init__(self, genome: float, fitness: float, novelty: float) -> None:
        self.genome = genome
        self.fitness = fitness
        self.novelty = novelty


def _fitness(g: float) -> float:
    if g > 2:
        return 10.0 - (g - 5.0) ** 2
    return 5.0 - g * g


def _mutate(g: float) -> float:
    return g + random.uniform(-3.0, 3.0)


def _select_softmax(pop: list[_Candidate]) -> _Candidate:
    return select_parent(pop, beta=1.0, gamma=0.0)


def _run(strategy: str, iterations: int, *, seed: int) -> Tuple[float, float]:
    random.seed(seed)
    np.random.seed(seed)
    pop = [_Candidate(0.0, _fitness(0.0), 1.0)]
    for _ in range(iterations):
        if strategy == "v2":
            parent = _select_softmax(pop)
        elif strategy == "greedy":
            parent = max(pop, key=lambda c: c.fitness)
        else:  # pragma: no cover - invalid option
            raise ValueError(f"unknown strategy: {strategy}")
        genome = _mutate(parent.genome)
        cand = _Candidate(genome, _fitness(genome), random.random())
        pop.append(cand)
    best = max(c.fitness for c in pop)
    mean = sum(c.fitness for c in pop) / len(pop)
    return best, mean


def run(seed: int = 18, iterations: int = 50, csv_path: str | Path = "selector_ablation.csv") -> Dict[str, Tuple[float, float]]:
    results = {
        "v2": _run("v2", iterations, seed=seed),
        "greedy": _run("greedy", iterations, seed=seed),
    }
    path = Path(csv_path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["strategy", "best_score", "mean_score"])
        for name, (best, mean) in results.items():
            writer.writerow([name, f"{best:.6f}", f"{mean:.6f}"])
    return results


if __name__ == "__main__":  # pragma: no cover
    run()
