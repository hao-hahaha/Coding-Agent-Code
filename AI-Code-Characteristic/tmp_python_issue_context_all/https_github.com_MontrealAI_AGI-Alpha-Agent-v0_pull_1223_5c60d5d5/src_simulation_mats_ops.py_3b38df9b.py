# SPDX-License-Identifier: Apache-2.0
"""Minimal mutation operators for MATS demos."""
from __future__ import annotations

import random
from typing import Any, List

from src.self_edit.safety import is_code_safe
from src.archive.selector import select_parent


class GaussianParam:
    """Add Gaussian noise to numeric genomes within bounds."""

    def __init__(self, std: float = 0.1, bounds: tuple[float, float] = (-1.0, 1.0), rng: random.Random | None = None) -> None:
        self.std = std
        self.bounds = bounds
        self.rng = rng or random.Random()

    def __call__(self, genome: List[float]) -> List[float]:
        low, high = self.bounds
        return [min(high, max(low, g + self.rng.gauss(0.0, self.std))) for g in genome]


class PromptRewrite:
    """Basic text rewrite inserting a simple synonym."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.synonyms = {"improve": "enhance", "quick": "fast", "test": "trial"}

    def __call__(self, text: str) -> str:
        words = text.split()
        if not words:
            return text
        idx = self.rng.randrange(len(words))
        w = words[idx].lower()
        words[idx] = self.synonyms.get(w, words[idx])
        return " ".join(words)


class CodePatch:
    """Return code with a small comment appended."""

    def __call__(self, code: str) -> str:
        suffix = "# patched"
        if not code.endswith("\n"):
            code += "\n"
        return code + suffix + "\n"


class SelfRewriteOperator:
    """Apply ``PromptRewrite`` multiple times."""

    def __init__(self, steps: int = 2, rng: random.Random | None = None) -> None:
        self.steps = steps
        self.rng = rng or random.Random()
        self._op = PromptRewrite(rng=self.rng)

    def __call__(self, text: str) -> str:
        for _ in range(self.steps):
            candidate = self._op(text)
            if is_code_safe(candidate):
                text = candidate
            else:
                break
        return text


def backtrack_boost(pop: List[Any], archive: List[Any], rate: float) -> Any:
    """Return a parent possibly selected from weaker individuals.

    With probability ``rate`` the parent is drawn uniformly from the
    lower half of ``archive`` based on fitness.  Otherwise the regular
    ``select_parent`` mechanism chooses from ``pop``.
    """

    if not pop:
        raise ValueError("population is empty")
    if rate <= 0.0:
        return select_parent(pop, temp=1.0)
    if random.random() < rate:
        ranked = sorted(archive, key=lambda c: getattr(c, "fitness", 0.0))
        bottom = ranked[: max(1, len(ranked) // 2)]
        return random.choice(bottom)
    return select_parent(pop, temp=1.0)
