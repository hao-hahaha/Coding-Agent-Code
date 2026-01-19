# SPDX-License-Identifier: Apache-2.0
"""Minimal finite-state loop for Insight demos."""

from __future__ import annotations

import json
import time
import random
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from src.monitoring import metrics


class BanditEarlyStopper:
    """Simple bandit-based early stopper."""

    def __init__(self, threshold: float) -> None:
        self.threshold = threshold
        self.cost = 0.0
        self.gain = 0.0
        self.success = 1
        self.fail = 1

    def update(self, cost: float, gain: float) -> bool:
        """Update stats and return ``True`` if training should stop."""
        self.cost += cost
        if gain > 0:
            self.gain += gain
            self.success += 1
            metrics.dgm_fitness_gain_total.inc(gain)
        else:
            self.fail += 1
        metrics.dgm_gpu_hours_total.inc(cost / 3600)
        if self.gain > 0:
            metrics.dgm_gpu_hours_per_gain.set(self.cost / 3600 / self.gain)
            metrics.dgm_gpu_seconds_per_gain.set(self.cost / self.gain)
        prob = random.betavariate(self.success, self.fail)
        expected_gain = self.gain + prob
        ratio = self.cost / expected_gain if expected_gain else float("inf")
        return ratio > self.threshold


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
    revives: int = 0


def run_loop(
    *,
    cost_budget: float | None = None,
    wallclock: float | None = None,
    cost_per_cycle: float = 1.0,
    state_file: str = "loop_state.json",
    revive_rate: int = 0,
    agents: dict[str, bool] | None = None,
    rng: random.Random | None = None,
    gains: list[float] | None = None,
    early_stopper: BanditEarlyStopper | None = None,
) -> Result:
    """Run the FSM until budgets are exhausted.

    Args:
        cost_budget: Optional cost limit.
        wallclock: Optional wall-clock limit in seconds.
        cost_per_cycle: Cost incurred per complete cycle.
        state_file: Path used when persisting state on ``KeyboardInterrupt``.
        revive_rate: Attempt revival every ``revive_rate`` cycles (0 disables).
        agents: Mapping of agent names to active state.
        rng: Random generator for deterministic tests.

    Returns:
        :class:`Result` with final state, completed cycles, cost spent and
        the number of agents revived.
    """

    state = State.SELECT
    cycles = 0
    cost_spent = 0.0
    start = time.time()
    rng = rng or random.Random()
    agents = agents or {}
    revive_count = 0

    gain_iter = iter(gains or [])

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
                gain = next(gain_iter, 0.0)
                if early_stopper and early_stopper.update(cost_per_cycle, gain):
                    break
                state = State.ARCHIVE
                continue
            if state is State.ARCHIVE:
                cycles += 1
                if revive_rate and cycles % revive_rate == 0:
                    inactive = [a for a, active in agents.items() if not active]
                    if inactive:
                        revived = rng.choice(inactive)
                        agents[revived] = True
                        revive_count += 1
                        metrics.dgm_revives_total.inc()
                        state = State.SELF_MOD
                        continue
                state = State.SELECT
                if cost_budget is not None and cost_spent >= cost_budget:
                    break
                if wallclock is not None and time.time() - start >= wallclock:
                    break
    except KeyboardInterrupt:  # pragma: no cover - interactive
        Path(state_file).write_text(json.dumps({"state": state.name, "cycles": cycles, "cost": cost_spent}))
        return Result(state=state, cycles=cycles, cost=cost_spent, revives=revive_count)

    return Result(state=state, cycles=cycles, cost=cost_spent, revives=revive_count)
