# SPDX-License-Identifier: Apache-2.0
import logging

import pytest

from src.scheduler.spot_gpu import SpotGPUAllocator


def test_dry_run_respects_budget(caplog: pytest.LogCaptureFixture) -> None:
    alloc = SpotGPUAllocator(price_fetcher=lambda r: 0.5)
    caplog.set_level(logging.INFO)
    result = alloc.allocate(["a", "b"], ["c"], dry_run=True)
    assert result == {"a": 8, "b": 8}
    msgs = [r.getMessage() for r in caplog.records]
    assert any("Total hourly cost" in m for m in msgs)
    end_msg = [m for m in msgs if "Total hourly cost" in m][0]
    assert "8.00" in end_msg and "8.33" in end_msg
    assert any("Skip c" in m for m in msgs)
