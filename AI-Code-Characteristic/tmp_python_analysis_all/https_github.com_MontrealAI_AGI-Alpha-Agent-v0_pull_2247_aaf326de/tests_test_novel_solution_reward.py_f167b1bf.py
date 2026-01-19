# SPDX-License-Identifier: Apache-2.0
"""Tests for :mod:`novel_solution_reward` backend."""

from alpha_factory_v1.demos.era_of_experience.reward_backends import novel_solution_reward as ns


def _reset() -> None:
    ns._sig_mem.clear()
    ns._idx = 0
    if ns._emb_mem is not None:
        ns._emb_mem.clear()


def test_first_solution_yields_one() -> None:
    _reset()
    value = ns.reward(None, None, "solve x")
    assert isinstance(value, float)
    assert value == 1.0


def test_repeated_solution_zero() -> None:
    _reset()
    ns.reward(None, None, "idea")
    value = ns.reward(None, None, "idea")
    assert 0.0 <= value <= 1.0
    assert value == 0.0
