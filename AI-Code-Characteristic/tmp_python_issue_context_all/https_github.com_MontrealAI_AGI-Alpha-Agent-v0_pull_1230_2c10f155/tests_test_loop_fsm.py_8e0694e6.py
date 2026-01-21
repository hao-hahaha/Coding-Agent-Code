# SPDX-License-Identifier: Apache-2.0
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import loop


def test_fsm_cycles_three() -> None:
    result = loop.run_loop(cost_budget=3.0, cost_per_cycle=1.0)
    assert result.cycles == 3
    assert result.state is loop.State.SELECT
