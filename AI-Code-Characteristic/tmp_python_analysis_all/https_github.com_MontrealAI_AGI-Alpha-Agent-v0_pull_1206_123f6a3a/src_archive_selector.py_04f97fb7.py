# SPDX-License-Identifier: Apache-2.0
"""Parent selection helpers."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np


def select_parent(population: Sequence[Any], temp: float) -> Any:
    """Return a candidate chosen via softmax of ``fitness * novelty``.

    Args:
        population: Sequence of candidates exposing ``fitness`` and ``novelty`` attributes.
        temp: Softmax temperature. Higher values yield a more uniform distribution.

    Returns:
        The selected candidate from ``population``.
    """
    if not population:
        raise ValueError("population is empty")
    if temp <= 0:
        raise ValueError("temp must be positive")

    scores = np.asarray([float(getattr(ind, "fitness")) * float(getattr(ind, "novelty")) for ind in population])
    logits = scores / temp
    weights = np.exp(logits - np.max(logits))
    probs = weights / weights.sum()

    index = int(np.random.choice(len(population), p=probs))
    return population[index]
