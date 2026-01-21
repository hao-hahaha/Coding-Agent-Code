# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
import pytest

np = pytest.importorskip("numpy")

from src.archive.selector import select_parent


def softmax(arr: np.ndarray) -> np.ndarray:
    exp = np.exp(arr - np.max(arr))
    return exp / exp.sum()


@dataclass(slots=True)
class Candidate:
    score: float
    edit_children_count: int


def sample_distribution(pop, beta, gamma, runs=20000):
    np.random.seed(123)
    counts = {id(ind): 0 for ind in pop}
    for _ in range(runs):
        ind = select_parent(pop, beta=beta, gamma=gamma)
        counts[id(ind)] += 1
    return np.asarray([counts[id(ind)] / runs for ind in pop])


def test_selector_frequency_monte_carlo() -> None:
    pop = [
        Candidate(1.0, 0),
        Candidate(0.2, 3),
        Candidate(1.5, 1),
    ]
    beta, gamma = 0.7, 0.3
    logits = np.asarray([beta * p.score + gamma * p.edit_children_count for p in pop])
    expected = softmax(logits)
    observed = sample_distribution(pop, beta, gamma, runs=50000)
    assert np.allclose(observed, expected, atol=0.02)
