# SPDX-License-Identifier: Apache-2.0
"""Evaluation helpers for the Meta Agentic Tree Search demo.

Exposes :func:`evaluate` which scores integer policies in a toy environment.
"""
from __future__ import annotations

from typing import List
from .env import NumberLineEnv


def evaluate(agents: List[int], env: NumberLineEnv | None = None) -> float:
    """Return a pseudo reward for ``agents``.

    Args:
        agents: Candidate integer policy.
        env: Optional environment instance.

    Returns:
        Calculated reward from the environment.
    """

    environment = env or NumberLineEnv()
    return environment.rollout(agents)
