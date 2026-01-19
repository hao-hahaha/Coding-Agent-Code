import asyncio

import pytest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import retry


def test_with_retry_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retry, "backoff", None)
    calls = {"n": 0}

    def func() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("boom")
        return "ok"

    wrapped = retry.with_retry(func, max_tries=3)
    assert wrapped() == "ok"
    assert calls["n"] == 3


def test_with_retry_async(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retry, "backoff", None)
    calls = {"n": 0}

    async def func() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("fail")
        return "ok"

    wrapped = retry.with_retry(func, max_tries=2)
    result = asyncio.run(wrapped())
    assert result == "ok"
    assert calls["n"] == 2


def test_with_retry_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(retry, "backoff", None)
    calls = {"n": 0}

    def func() -> str:
        calls["n"] += 1
        raise ValueError("fail")

    wrapped = retry.with_retry(func, max_tries=2)
    with pytest.raises(ValueError):
        wrapped()
    assert calls["n"] == 2
