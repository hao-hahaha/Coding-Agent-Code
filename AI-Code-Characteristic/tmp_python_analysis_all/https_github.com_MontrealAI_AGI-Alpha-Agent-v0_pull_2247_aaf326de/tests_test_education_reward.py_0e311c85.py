# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`education_reward` backend."""

from collections import deque

from alpha_factory_v1.demos.era_of_experience.reward_backends import education_reward as ed


class DummyState:
    def __init__(self) -> None:
        self.history = deque()


def test_learning_event_in_range() -> None:
    state = DummyState()
    result = {"context": "duolingo spanish lesson", "duration": 1800}
    value = ed.reward(state, None, result)
    assert isinstance(value, float)
    assert 0.0 <= value <= 1.0


def test_non_learning_event_zero() -> None:
    state = DummyState()
    value = ed.reward(state, None, {"context": "watch tv"})
    assert value == 0.0
