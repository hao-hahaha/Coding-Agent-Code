# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`fitness_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import fitness_reward as fr
from pytest import approx


def test_ideal_sensor_readings_near_one() -> None:
    """Typical ideal metrics should yield ~1.0."""
    sensors = {"steps": 10_000, "resting_hr": 60, "sleep_hours": 8, "cal_intake": 2100}
    value = fr.reward(None, None, sensors)
    assert 0.0 <= value <= 1.0
    assert value == approx(1.0, rel=0, abs=1e-7)


def test_reasonable_daily_metrics() -> None:
    """Moderate readings still return a bounded score."""
    sensors = {"steps": 8000, "resting_hr": 65, "sleep_hours": 7, "cal_intake": 2500}
    value = fr.reward(None, None, sensors)
    assert 0.0 <= value <= 1.0
    assert value < 1.0
