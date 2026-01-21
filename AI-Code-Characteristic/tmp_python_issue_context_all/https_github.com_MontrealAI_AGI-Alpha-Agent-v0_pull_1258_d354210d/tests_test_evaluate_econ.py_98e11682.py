# SPDX-License-Identifier: Apache-2.0
"""Tests for the economic evaluator."""

from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_insight_v1.src import evaluate_econ


def test_evaluate_econ_metrics() -> None:
    repo = Path(__file__).resolve().parents[1]
    result = evaluate_econ.evaluate(repo)
    assert list(result.keys()) == ["rmse", "lead_time"]
    assert result["rmse"] == 0.0
    assert result["lead_time"] == 0
