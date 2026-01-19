"""Reward backend template · Alpha-Factory v1 👁️✨
---------------------------------------------------------------------
Minimal skeleton illustrating how to craft a custom reward backend.
Copy this file and implement the ``reward`` function to suit your
use‑case.

The orchestrator expects ``reward(state, action, result) -> float`` and
normalises the return value to the closed interval [0, 1].  A value of
``0`` denotes the worst outcome whereas ``1`` is the best.
"""
from __future__ import annotations

from typing import Any

__all__ = ["reward"]

def reward(state: Any, action: Any, result: Any) -> float:
    """Compute a scalar reward in ``[0, 1]``.

    Parameters
    ----------
    state : Any
        Snapshot of the environment or agent state.
    action : Any
        Action executed by the agent.
    result : Any
        Observation or outcome returned by the environment.

    Returns
    -------
    float
        Normalised reward signal.
    """
    # TODO: replace this example logic with your custom calculation
    return 0.5
