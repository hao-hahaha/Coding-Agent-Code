# SPDX-License-Identifier: Apache-2.0
"""Minimal finite-state loop for Insight demos."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class State(Enum):
    """Execution state."""

    SELECT = auto()
    SELF_MOD = auto()
    BENCHMARK = auto()
    ARCHIVE = auto()


@dataclass(slots=True)
class Result:
    """Loop termination snapshot."""

    state: State
    cycles: int
    cost: float


def run_loop(
    *,
    cost_budget: float | None = None,
    wallclock: float | None = None,
    cost_per_cycle: float = 1.0,
    state_file: str = "loop_state.json",
) -> Result:
    """Run the FSM until budgets are exhausted.

    Args:
        cost_budget: Optional cost limit.
        wallclock: Optional wall-clock limit in seconds.
        cost_per_cycle: Cost incurred per complete cycle.
        state_file: Path used when persisting state on ``KeyboardInterrupt``.

    Returns:
        :class:`Result` with final state, completed cycles and cost spent.
    """

    state = State.SELECT
    cycles = 0
    cost_spent = 0.0
    start = time.time()

    try:
        while True:
            if state is State.SELECT:
                state = State.SELF_MOD
                continue
            if state is State.SELF_MOD:
                state = State.BENCHMARK
                continue
            if state is State.BENCHMARK:
                cost_spent += cost_per_cycle
                state = State.ARCHIVE
                continue
            if state is State.ARCHIVE:
                cycles += 1
                state = State.SELECT
                if cost_budget is not None and cost_spent >= cost_budget:
                    break
                if wallclock is not None and time.time() - start >= wallclock:
                    break
    except KeyboardInterrupt:  # pragma: no cover - interactive
        Path(state_file).write_text(
            json.dumps({"state": state.name, "cycles": cycles, "cost": cost_spent})
        )
        return Result(state=state, cycles=cycles, cost=cost_spent)

    return Result(state=state, cycles=cycles, cost=cost_spent)
