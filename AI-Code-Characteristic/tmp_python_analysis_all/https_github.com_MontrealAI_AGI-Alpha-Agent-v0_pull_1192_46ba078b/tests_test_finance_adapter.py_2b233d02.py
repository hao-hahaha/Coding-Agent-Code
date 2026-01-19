# SPDX-License-Identifier: Apache-2.0
import pytest

import json

from src.finance.adapter import delta_sector_to_dcf, propagate_shocks_to_tickers


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


def test_propagate_shocks_to_tickers() -> None:
    shocks = {"smartphones": -0.1, "retail": -0.05, "apps": 0.02}
    result_json = propagate_shocks_to_tickers(shocks)
    impacts = json.loads(result_json)
    assert impacts["AAPL"] == pytest.approx(-0.1)
    assert impacts["AMZN"] == pytest.approx(-0.05)
    # MSFT appears in apps and cloud_compute; only apps is provided
    assert impacts["MSFT"] == pytest.approx(0.02)

