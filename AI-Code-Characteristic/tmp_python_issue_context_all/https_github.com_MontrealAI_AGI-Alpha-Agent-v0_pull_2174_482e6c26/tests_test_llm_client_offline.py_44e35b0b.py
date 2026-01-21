import importlib
import sys
import types
from unittest.mock import Mock

import pytest


from types import ModuleType


def _reload_client(monkeypatch: pytest.MonkeyPatch, diff: str) -> ModuleType:
    stub = types.ModuleType("openai_agents")

    class DummyAgent:
        def __init__(self, *a: object, **k: object) -> None:
            pass

        def __call__(self, *_a: object, **_k: object) -> str:
            return diff

    stub.OpenAIAgent = DummyAgent  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai_agents", stub)
    import alpha_factory_v1.demos.self_healing_repo.agent_core.llm_client as mod

    return importlib.reload(mod)


def test_request_patch_use_local_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    diff = "--- a/x\n+++ b/x\n@@\n-old\n+new\n"
    monkeypatch.setenv("USE_LOCAL_LLM", "true")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = _reload_client(monkeypatch, diff)
    out = client.request_patch([{"role": "user", "content": "fix"}])
    assert out == diff


def test_request_patch_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    diff = "--- a/y\n+++ b/y\n@@\n-old\n+new\n"
    monkeypatch.setenv("USE_LOCAL_LLM", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    client = _reload_client(monkeypatch, diff)
    out = client.request_patch([{"role": "user", "content": "fix"}])
    assert out == diff


def test_request_patch_respects_model_env(monkeypatch: pytest.MonkeyPatch) -> None:
    diff = "--- a/z\n+++ b/z\n@@\n-old\n+new\n"
    openai_stub = types.ModuleType("openai")
    create_mock = Mock(return_value={"choices": [{"message": {"content": diff}}]})
    openai_stub.ChatCompletion = types.SimpleNamespace(create=create_mock)
    monkeypatch.setitem(sys.modules, "openai", openai_stub)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("USE_LOCAL_LLM", "false")
    client = _reload_client(monkeypatch, diff)
    client.request_patch([{"role": "user", "content": "fix"}])
    assert create_mock.call_args.kwargs.get("model") == "test-model"

