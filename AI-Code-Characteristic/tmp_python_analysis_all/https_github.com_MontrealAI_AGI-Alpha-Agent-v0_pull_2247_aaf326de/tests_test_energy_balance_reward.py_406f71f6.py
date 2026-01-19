# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`energy_balance_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import energy_balance_reward as eb


def _reset_ledger() -> None:
    eb._ledger.clear()


def test_typical_day_score_in_range() -> None:
    _reset_ledger()
    res = {"date": "2025-04-22", "calories_in": 2400, "calories_out": 600, "bmr": 1650}
    value = eb.reward(None, None, res)
    assert isinstance(value, float)
    assert 0.0 <= value <= 1.0


def test_non_dict_returns_zero() -> None:
    _reset_ledger()
    value = eb.reward(None, None, "bad")
    assert value == 0.0
