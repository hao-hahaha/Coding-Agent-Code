# SPDX-License-Identifier: Apache-2.0
"""Tests for benchmark fitness calculation."""

from __future__ import annotations

import json
from pathlib import Path

from src.eval.fitness import compute_fitness


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_compute_fitness_table1() -> None:
    results_path = FIXTURE_DIR / "table1_results.json"
    with results_path.open() as fh:
        results = json.load(fh)

    metrics = compute_fitness(results)

    expected = json.loads((FIXTURE_DIR / "table1_metrics.json").read_text())
    assert metrics == expected
