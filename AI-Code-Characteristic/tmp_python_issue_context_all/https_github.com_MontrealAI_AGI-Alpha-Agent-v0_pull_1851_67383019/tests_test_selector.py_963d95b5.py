# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from dataclasses import dataclass
import pytest

np = pytest.importorskip("numpy")

from src.archive.selector import select_parent


@dataclass(slots=True)
class Candidate:
    score: float
    edit_children_count: int


def softmax(arr: np.ndarray) -> np.ndarray:
    exp = np.exp(arr - np.max(arr))
    return exp / exp.sum()


def sample_distribution(pop, beta, gamma, runs=20000):
    np.random.seed(42)
    counts = {id(ind): 0 for ind in pop}
    for _ in range(runs):
        ind = select_parent(pop, beta=beta, gamma=gamma)
        counts[id(ind)] += 1
    return np.asarray([counts[id(ind)] / runs for ind in pop])


def test_select_parent_softmax() -> None:
    pop = [
        Candidate(1.0, 0),
        Candidate(0.5, 1),
        Candidate(2.0, 2),
    ]
    beta, gamma = 1.0, 0.0
    expected = softmax(np.asarray([beta * p.score + gamma * p.edit_children_count for p in pop]))
    observed = sample_distribution(pop, beta, gamma)
    assert np.allclose(observed, expected, atol=0.02)


def test_select_parent_weighting() -> None:
    pop = [
        Candidate(1.0, 0),
        Candidate(0.5, 1),
        Candidate(2.0, 2),
    ]
    beta, gamma = 0.5, 1.0
    expected = softmax(np.asarray([beta * p.score + gamma * p.edit_children_count for p in pop]))
    observed = sample_distribution(pop, beta, gamma)
    assert np.allclose(observed, expected, atol=0.02)
