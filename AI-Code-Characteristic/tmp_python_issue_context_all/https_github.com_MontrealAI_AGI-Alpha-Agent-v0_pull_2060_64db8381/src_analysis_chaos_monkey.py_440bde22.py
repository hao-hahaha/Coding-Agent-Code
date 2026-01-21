# SPDX-License-Identifier: Apache-2.0
"""Inject adversarial mutations to stress critics."""

from __future__ import annotations

import random
from typing import List

from src.critics import DualCriticService


class ChaosMonkey:
    """Generate adversarial variations of agent responses."""

    def __init__(self, service: DualCriticService, *, threshold: float = 0.5) -> None:
        self.service = service
        self.threshold = threshold
        self.cases: List[str] = [
            "contradiction",
            "nonsense",
            "irrelevant",
            "reversal",
            "gibberish",
        ]

    def mutate(self, text: str, case: str) -> str:
        """Return ``text`` modified according to the specified ``case``."""
        match case:
            case "contradiction":
                return text + " although the opposite is true"
            case "irrelevant":
                return "Unrelated comment. " + text
            case "reversal":
                return " ".join(reversed(text.split()))
            case "gibberish":
                letters = "abcdefghijklmnopqrstuvwxyz"
                return text + " " + "".join(random.choice(letters) for _ in range(10))
            case _:
                return "xyzzy"  # nonsense

    def detected_fraction(self, context: str, response: str) -> float:
        """Return fraction of cases scoring below ``threshold``."""
        detected = 0
        for case in self.cases:
            mutated = self.mutate(response, case)
            result = self.service.score(context, mutated)
            if result["logic"] < self.threshold or result["feas"] < self.threshold:
                detected += 1
        return detected / len(self.cases) if self.cases else 0.0


__all__ = ["ChaosMonkey"]
