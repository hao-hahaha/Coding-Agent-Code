import builtins
import importlib
import sys
import types

import pytest

from alpha_factory_v1.demos.self_healing_repo.agent_core import llm_client


class DummyBlocks:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def launch(self, *a, **k):
        pass


class DummyMarkdown:
    def __init__(self, *a, **k):
        pass


class DummyButton:
    def __init__(self, *a, **k):
        pass

    def click(self, *a, **k):
        pass


def test_entrypoint_offline(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "gradio",
        types.SimpleNamespace(Blocks=DummyBlocks, Markdown=DummyMarkdown, Button=DummyButton),
    )

    monkeypatch.setattr(llm_client, "call_local_model", lambda msgs: "local")

    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "openai_agents":
            raise ModuleNotFoundError(name)
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("alpha_factory_v1.demos.self_healing_repo.agent_selfheal_entrypoint", None)
    entrypoint = importlib.import_module(
        "alpha_factory_v1.demos.self_healing_repo.agent_selfheal_entrypoint"
    )

    assert entrypoint.LLM("hi") == "local"
