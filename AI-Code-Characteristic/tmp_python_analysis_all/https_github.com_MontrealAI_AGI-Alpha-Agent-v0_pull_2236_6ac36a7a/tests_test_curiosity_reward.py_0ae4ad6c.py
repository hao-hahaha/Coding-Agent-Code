# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`curiosity_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import curiosity_reward as cr


def _reset_cache() -> None:
    cr._seen = cr._LRUCounter(cr._MAX_ENTRIES)


def test_first_time_event_score_is_one() -> None:
    """First occurrence should return ``1.0``."""
    _reset_cache()
    value = cr.reward({}, None, {"event": 1})
    assert value == 1.0


def test_repeated_event_score_decreases() -> None:
    """Repeated events yield lower scores."""
    _reset_cache()
    first = cr.reward({}, None, {"event": 1})
    second = cr.reward({}, None, {"event": 1})
    assert first == 1.0
    assert 0.0 < second <= 1.0 and second < first
