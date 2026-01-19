# SPDX-License-Identifier: Apache-2.0
import pytest

from src.tools.ablation_runner import run_ablation


@pytest.mark.ablation
def test_innovation_ablation() -> None:
    results = run_ablation()
    for patch, scores in results.items():
        base = scores["baseline"]
        for name, val in scores.items():
            if name == "baseline":
                continue
            assert base - val >= 0.03
