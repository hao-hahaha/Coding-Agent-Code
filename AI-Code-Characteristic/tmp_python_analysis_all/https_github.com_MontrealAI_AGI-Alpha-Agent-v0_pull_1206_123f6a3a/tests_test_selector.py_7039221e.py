# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from src.archive.selector import select_parent


@dataclass(slots=True)
class Candidate:
    fitness: float
    novelty: float


def softmax(arr: np.ndarray) -> np.ndarray:
    exp = np.exp(arr - np.max(arr))
    return exp / exp.sum()


def sample_distribution(pop, temp, runs=20000):
    np.random.seed(42)
    counts = {id(ind): 0 for ind in pop}
    for _ in range(runs):
        ind = select_parent(pop, temp)
        counts[id(ind)] += 1
    return np.asarray([counts[id(ind)] / runs for ind in pop])


def test_select_parent_softmax() -> None:
    pop = [
        Candidate(1.0, 1.0),
        Candidate(0.5, 2.0),
        Candidate(2.0, 0.5),
    ]
    temp = 1.0
    expected = softmax(np.asarray([p.fitness * p.novelty for p in pop]) / temp)
    observed = sample_distribution(pop, temp)
    assert np.allclose(observed, expected, atol=0.02)


def test_select_parent_temperature() -> None:
    pop = [
        Candidate(1.0, 1.0),
        Candidate(0.5, 2.0),
        Candidate(2.0, 0.5),
    ]
    temp = 0.5
    expected = softmax(np.asarray([p.fitness * p.novelty for p in pop]) / temp)
    observed = sample_distribution(pop, temp)
    assert np.allclose(observed, expected, atol=0.02)
