# SPDX-License-Identifier: Apache-2.0
from src.governance.stake_registry import StakeRegistry


def test_stake_weighted_acceptance() -> None:
    reg = StakeRegistry()
    reg.set_stake("A", 50)
    reg.set_stake("B", 30)
    reg.set_stake("C", 20)
    reg.vote("p1", "A", True)
    reg.vote("p1", "B", True)
    reg.vote("p1", "C", False)
    assert reg.accepted("p1")
    reg.vote("p2", "A", True)
    reg.vote("p2", "B", False)
    reg.vote("p2", "C", False)
    assert not reg.accepted("p2")
