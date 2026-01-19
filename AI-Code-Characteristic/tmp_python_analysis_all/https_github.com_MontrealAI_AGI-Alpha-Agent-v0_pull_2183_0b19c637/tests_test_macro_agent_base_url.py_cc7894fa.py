import importlib
import sys
from types import ModuleType
from unittest.mock import patch

import pytest


def test_agent_macro_entrypoint_custom_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = ModuleType("openai_agents")
    captured = {}

    class DummyOpenAI:
        def __init__(self, *a, **kw) -> None:
            captured["base_url"] = kw.get("base_url")

    stub.Agent = object
    stub.OpenAIAgent = DummyOpenAI
    stub.Tool = lambda *_a, **_k: (lambda f: f)
    monkeypatch.setitem(sys.modules, "openai_agents", stub)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://example.com/v1")

    mod_path = "alpha_factory_v1.demos.macro_sentinel.agent_macro_entrypoint"
    sys.modules.pop(mod_path, None)

    with patch(f"{mod_path}._check_ollama"):
        importlib.import_module(mod_path)

    assert captured["base_url"] == "http://example.com/v1"
