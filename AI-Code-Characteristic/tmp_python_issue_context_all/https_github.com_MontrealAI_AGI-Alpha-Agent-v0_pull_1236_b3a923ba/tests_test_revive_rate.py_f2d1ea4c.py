# SPDX-License-Identifier: Apache-2.0
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import loop
import random


def test_revive_rate() -> None:
    rng = random.Random(12345)
    agents = {"A": True, "B": False}
    result = loop.run_loop(
        cost_budget=100.0,
        cost_per_cycle=1.0,
        revive_rate=10,
        agents=agents,
        rng=rng,
    )
    assert result.revives >= 1
