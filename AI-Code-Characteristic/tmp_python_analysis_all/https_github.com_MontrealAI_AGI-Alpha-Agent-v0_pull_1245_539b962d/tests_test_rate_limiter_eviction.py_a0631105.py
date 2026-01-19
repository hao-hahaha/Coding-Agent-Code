# SPDX-License-Identifier: Apache-2.0
"""Unit tests for SimpleRateLimiter eviction logic."""

from __future__ import annotations

import asyncio
import importlib
import os
import time

import pytest
from starlette.requests import Request
from starlette.responses import Response

pytest.importorskip("fastapi")

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def _make_request(ip: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "client": (ip, 0),
    }
    return Request(scope)  # type: ignore[arg-type]


async def _call_next(_: Request) -> Response:
    return Response("ok")


def test_rate_limiter_evicts_old_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT", "5")
    from src.interface import api_server as api

    api = importlib.reload(api)

    limiter = api.SimpleRateLimiter(api.app, limit=5, window=0.1)

    asyncio.run(limiter.dispatch(_make_request("1.1.1.1"), _call_next))
    assert "1.1.1.1" in limiter.counters
    time.sleep(0.2)
    asyncio.run(limiter.dispatch(_make_request("2.2.2.2"), _call_next))
    assert "1.1.1.1" not in limiter.counters
    assert list(limiter.counters.keys()) == ["2.2.2.2"]


def test_rate_limiter_throttles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT", "1")
    from src.interface import api_server as api

    api = importlib.reload(api)

    limiter = api.SimpleRateLimiter(api.app, limit=1, window=0.1)

    resp1 = asyncio.run(limiter.dispatch(_make_request("3.3.3.3"), _call_next))
    assert resp1.status_code == 200
    resp2 = asyncio.run(limiter.dispatch(_make_request("3.3.3.3"), _call_next))
    assert resp2.status_code == 429
    time.sleep(0.11)
    resp3 = asyncio.run(limiter.dispatch(_make_request("3.3.3.3"), _call_next))
    assert resp3.status_code == 200
