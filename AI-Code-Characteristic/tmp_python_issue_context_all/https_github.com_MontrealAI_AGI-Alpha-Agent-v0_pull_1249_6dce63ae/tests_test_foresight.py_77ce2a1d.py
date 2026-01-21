# SPDX-License-Identifier: Apache-2.0
"""Tests for the foresight evaluator."""

from pathlib import Path
import statistics

from src.eval import foresight


def test_score_variance_under_two_sigma() -> None:
    repo = Path(__file__).resolve().parents[1]
    results = [foresight.evaluate(repo) for _ in range(3)]
    for key in ["rmse", "lead_time"]:
        vals = [r[key] for r in results]
        mean = statistics.mean(vals)
        sigma = statistics.pstdev(vals)
        assert all(abs(v - mean) < 2 * sigma + 1e-12 for v in vals)

