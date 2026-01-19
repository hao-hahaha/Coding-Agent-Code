"""Simple Gym-like environment stub.

This minimal environment illustrates how the
Era-of-Experience agent could interact with
a simulator in place of real-world streams.
Use it as a template for custom training loops.
"""
from __future__ import annotations

from typing import Tuple, Any


class SimpleExperienceEnv:
    """Toy environment emitting integer states."""

    def __init__(self) -> None:
        self.state = 0

    def reset(self) -> int:
        """Reset the environment and return the initial state."""
        self.state = 0
        return self.state

    def step(self, action: Any) -> Tuple[int, float, bool, dict]:
        """Advance one step using ``action``.

        Parameters
        ----------
        action:
            Arbitrary action decided by the agent.
        Returns
        -------
        state:
            New integer state.
        reward:
            Simple reward of ``1.0`` when ``action`` equals ``"act"``.
        done:
            Episode termination flag after five steps.
        info:
            Extra debugging metadata (empty by default).
        """
        self.state += 1
        reward = 1.0 if action == "act" else 0.0
        done = self.state >= 5
        return self.state, reward, done, {}
