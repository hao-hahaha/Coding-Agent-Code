# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`safety_compliance_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import safety_compliance_reward as sc


def _reset() -> None:
    sc._seen_request_ids.clear()


def test_no_violation_returns_one() -> None:
    _reset()
    res = {"request_id": "r1", "violation": False}
    value = sc.reward(None, None, res)
    assert isinstance(value, float)
    assert value == 1.0


def test_unhandled_violation_penalty() -> None:
    _reset()
    res = {"request_id": "r2", "violation": True, "severity": 10, "autocorrected": False}
    value = sc.reward(None, None, res)
    assert value <= -1.0
    assert value >= -2.0


def test_duplicate_request_id_zero() -> None:
    _reset()
    res = {"request_id": "r3", "violation": False}
    sc.reward(None, None, res)
    assert sc.reward(None, None, res) == 0.0
