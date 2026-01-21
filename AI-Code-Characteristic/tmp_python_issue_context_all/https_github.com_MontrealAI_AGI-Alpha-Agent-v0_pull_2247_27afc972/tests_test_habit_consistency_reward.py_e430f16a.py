# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`habit_consistency_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import habit_consistency_reward as hc


def _reset() -> None:
    hc._last_seen.clear()


def test_first_occurrence_positive() -> None:
    _reset()
    res = {"context": "run 5k", "time": "2025-04-22T07:00:00Z"}
    value = hc.reward(None, None, res)
    assert isinstance(value, float)
    assert 0.0 <= value <= 1.0


def test_repeat_within_day_high_score() -> None:
    _reset()
    res1 = {"context": "run 5k", "time": "2025-04-22T07:00:00Z"}
    res2 = {"context": "run 5k", "time": "2025-04-23T06:00:00Z"}
    hc.reward(None, None, res1)
    value = hc.reward(None, None, res2)
    assert 0.0 <= value <= 1.0
    assert value > 0.5


def test_missing_fields_zero() -> None:
    _reset()
    assert hc.reward(None, None, {"context": "run"}) == 0.0
