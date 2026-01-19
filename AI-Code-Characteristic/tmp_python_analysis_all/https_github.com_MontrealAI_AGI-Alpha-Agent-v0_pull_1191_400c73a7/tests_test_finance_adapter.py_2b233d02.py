# SPDX-License-Identifier: Apache-2.0
import pytest

from src.finance.adapter import delta_sector_to_dcf


def test_delta_sector_to_dcf_npv() -> None:
    sector_state = {
        "delta_revenue": 1_000_000.0,
        "margin": 0.2,
        "discount_rate": 0.1,
        "years": 3,
    }
    result = delta_sector_to_dcf(sector_state)
    expected_npv = 497370.3981968444
    assert result["npv"] == pytest.approx(expected_npv, rel=0.02)

