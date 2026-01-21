# SPDX-License-Identifier: Apache-2.0
"""Tests for the Macro-Sentinel live collector."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict
from unittest.mock import patch

import pytest

from alpha_factory_v1.demos.macro_sentinel.collector import collector


def test_main_logs_single_event(caplog: pytest.LogCaptureFixture) -> None:
    """``collector.main`` should log one event from the patched stream."""

    stub = {"foo": "bar"}

    async def fake_events(*_a: Any, **_kw: Any) -> AsyncIterator[Dict[str, str]]:
        yield stub

    caplog.set_level(logging.INFO, logger="macro_collector")
    with patch.object(collector, "stream_macro_events", fake_events):
        asyncio.run(collector.main())

    records = [r for r in caplog.records if r.name == "macro_collector"]
    assert len(records) == 1
    logged = json.loads(records[0].getMessage().split("event=")[1])
    assert logged == stub
