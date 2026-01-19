# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`efficiency_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import efficiency_reward as er


def test_typical_payload_returns_float() -> None:
    payload = {"latency_ms": 400, "tokens": 500, "cost_usd": 0.002, "energy_j": 20, "value": 0.8}
    value = er.reward(None, None, payload)
    assert isinstance(value, float)
    assert 0.0 <= value <= 1.0


def test_missing_value_returns_zero() -> None:
    value = er.reward(None, None, {"latency_ms": 400})
    assert value == 0.0


def test_non_dict_returns_zero() -> None:
    assert er.reward(None, None, 123) == 0.0
