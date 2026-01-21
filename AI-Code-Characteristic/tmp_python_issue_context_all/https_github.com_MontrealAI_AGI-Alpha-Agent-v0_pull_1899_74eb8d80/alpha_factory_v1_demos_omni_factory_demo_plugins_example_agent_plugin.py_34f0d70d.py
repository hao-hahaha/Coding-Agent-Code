# SPDX-License-Identifier: Apache-2.0
"""Example plugin for OMNI-Factory demo.

Provides a simple policy that nudges the planner
with heuristics. Illustrates how users can extend
OMNI-Factory without modifying the core code.
"""
from __future__ import annotations

from typing import Any, List


def heuristic_policy(obs: List[float]) -> dict[str, Any]:
    """Return a suggested action based on observation heuristics."""
    power_ok, traffic_ok, _ = obs
    if power_ok < traffic_ok:
        # Prioritise power grid repairs
        return {"action": {"id": 0}}
    return {"action": {"id": 1}}


def register() -> None:
    print("[plugin] example_agent_plugin registered")

