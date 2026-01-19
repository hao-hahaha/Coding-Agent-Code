# SPDX-License-Identifier: Apache-2.0
"""Lightweight heuristic reviewer used in tests."""

from __future__ import annotations

import re

__all__ = ["ReviewerAgent"]


class ReviewerAgent:
    """Score explanatory reports using a simple word heuristic."""

    #: Small set of common English words for heuristic scoring
    _WORDS: set[str] = {
        "the",
        "and",
        "a",
        "to",
        "in",
        "of",
        "that",
        "is",
        "for",
        "with",
        "on",
        "this",
        "report",
        "mutant",
        "patch",
    }

    def critique(self, text: str) -> float:
        """Return a score in [0,1] based on word overlap with :data:`_WORDS`."""
        tokens = re.findall(r"[a-zA-Z']+", text.lower())
        if not tokens:
            return 0.0
        good = sum(1 for t in tokens if t in self._WORDS)
        return good / len(tokens)
