# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import random
from dataclasses import dataclass

from src.simulation.selector import select_parent


@dataclass(slots=True)
class Candidate:
    rmse: float
    inference_ms: float
    gasCost: float


def test_pareto_rank_deterministic() -> None:
    pop = [
        Candidate(0.8, 40, 10),
        Candidate(0.9, 45, 20),
        Candidate(0.6, 60, 15),
    ]
    rng = random.Random(0)
    selections = [select_parent(pop, epsilon=0.0, rng=rng) for _ in range(100)]
    assert all(s is not pop[1] for s in selections)


def test_epsilon_randomness() -> None:
    pop = [
        Candidate(0.8, 40, 10),
        Candidate(0.9, 45, 20),
        Candidate(0.6, 60, 15),
    ]
    rng = random.Random(0)
    count = 0
    for _ in range(500):
        if select_parent(pop, epsilon=0.1, rng=rng) is pop[1]:
            count += 1
    rate = count / 500.0
    assert 0.05 < rate < 0.15
