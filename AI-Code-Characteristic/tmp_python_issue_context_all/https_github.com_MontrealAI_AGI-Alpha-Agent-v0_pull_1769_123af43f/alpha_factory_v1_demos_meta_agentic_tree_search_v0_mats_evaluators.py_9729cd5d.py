# SPDX-License-Identifier: Apache-2.0
"""Evaluation utilities for the MATS demo."""
from __future__ import annotations

from typing import List
from .env import NumberLineEnv


def evaluate(agents: List[int], env: NumberLineEnv | None = None) -> float:
    """Return a pseudo reward for the agents using ``env``.

    Parameters
    ----------
    agents:
        Current candidate policies represented as integers.
    env:
        Optional environment instance.  A new :class:`NumberLineEnv` is created
        when omitted so the function remains backward compatible.
    """

    environment = env or NumberLineEnv()
    return environment.rollout(agents)

