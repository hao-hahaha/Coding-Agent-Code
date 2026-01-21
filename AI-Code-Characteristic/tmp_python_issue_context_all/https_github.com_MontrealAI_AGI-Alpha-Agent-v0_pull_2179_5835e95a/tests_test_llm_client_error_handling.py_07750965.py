import sys
import types
import logging

import pytest

from tests.test_llm_client_offline import _reload_client


def test_request_patch_handles_openai_error(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    class FailError(Exception):
        pass

    openai_stub = types.ModuleType("openai")
    openai_stub.Error = FailError

    def create(*_a: object, **_k: object) -> None:
        raise FailError("boom")

    openai_stub.ChatCompletion = types.SimpleNamespace(create=create)
    monkeypatch.setitem(sys.modules, "openai", openai_stub)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("USE_LOCAL_LLM", "false")

    client = _reload_client(monkeypatch, "")

    caplog.set_level(logging.ERROR)
    out = client.request_patch([{"role": "user", "content": "fix"}])

    assert out == ""
    assert any("OpenAI API request failed" in r.getMessage() for r in caplog.records)
