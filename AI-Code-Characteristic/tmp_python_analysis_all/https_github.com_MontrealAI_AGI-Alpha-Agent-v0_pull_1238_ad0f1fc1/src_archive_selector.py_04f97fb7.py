# SPDX-License-Identifier: Apache-2.0
"""Parent selection helpers."""

from __future__ import annotations

from typing import Any, Sequence

from src.monitoring import metrics

import numpy as np


def select_parent(population: Sequence[Any], beta: float = 1.0, gamma: float = 0.0) -> Any:
    """Return a candidate chosen via softmax of ``beta * score + gamma * edit_children_count``.

    Args:
        population: Sequence of candidates exposing ``score`` and ``edit_children_count`` attributes.
        beta: Weight applied to ``score``.
        gamma: Weight applied to ``edit_children_count``.

    Returns:
        The selected candidate from ``population``.
    """
    if not population:
        raise ValueError("population is empty")
    if beta == 0 and gamma == 0:
        raise ValueError("beta and gamma cannot both be zero")

    logits = []
    for ind in population:
        score = getattr(ind, "score", float(getattr(ind, "fitness", 0.0)) * float(getattr(ind, "novelty", 1.0)))
        edits = float(getattr(ind, "edit_children_count", 0.0))
        logits.append(beta * float(score) + gamma * edits)

    logits_arr = np.asarray(logits)
    weights = np.exp(logits_arr - np.max(logits_arr))
    probs = weights / weights.sum()

    index = int(np.random.choice(len(population), p=probs))
    metrics.dgm_parents_selected_total.inc()
    return population[index]
