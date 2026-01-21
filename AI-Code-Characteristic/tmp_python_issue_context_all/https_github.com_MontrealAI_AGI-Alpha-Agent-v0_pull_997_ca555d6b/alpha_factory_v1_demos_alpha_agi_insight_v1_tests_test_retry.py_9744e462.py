import sys
from pathlib import Path
import asyncio
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import retry


def test_with_retry_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retry, "backoff", None)
    monkeypatch.setattr(retry.time, "sleep", lambda *_: None)
    calls = {"n": 0}

    def func() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("fail")
        return "ok"

    wrapped = retry.with_retry(func, max_tries=2)
    assert wrapped() == "ok"
    assert calls["n"] == 2


def test_with_retry_async(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retry, "backoff", None)
    orig_sleep = asyncio.sleep
    monkeypatch.setattr(retry.asyncio, "sleep", lambda *_: orig_sleep(0))
    calls = {"n": 0}

    async def func() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("boom")
        return "ok"

    wrapped = retry.with_retry(func, max_tries=2)
    result = asyncio.run(wrapped())
    assert result == "ok"
    assert calls["n"] == 2
