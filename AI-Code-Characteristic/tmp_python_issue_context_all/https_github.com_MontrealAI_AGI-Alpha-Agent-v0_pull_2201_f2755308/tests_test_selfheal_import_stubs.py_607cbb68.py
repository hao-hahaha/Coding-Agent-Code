# SPDX-License-Identifier: Apache-2.0
# mypy: ignore-errors
import importlib
import sys
import types


class DummyBlocks:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class DummyMarkdown:
    def __init__(self, *a, **k):
        pass


class DummyButton:
    def __init__(self, *a, **k):
        pass

    def click(self, *a, **k):
        pass


def test_entrypoint_import_with_stubs(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "gradio",
        types.SimpleNamespace(Blocks=DummyBlocks, Markdown=DummyMarkdown, Button=DummyButton),
    )
    stub = types.SimpleNamespace(
        Agent=lambda *a, **k: object(),
        OpenAIAgent=object,
        Tool=lambda *a, **k: (lambda f: f),
    )
    monkeypatch.setitem(sys.modules, "openai_agents", stub)
    sys.modules.pop(
        "alpha_factory_v1.demos.self_healing_repo.agent_selfheal_entrypoint",
        None,
    )
    mod = importlib.import_module("alpha_factory_v1.demos.self_healing_repo.agent_selfheal_entrypoint")
    assert mod.apply_patch_and_retst is mod.apply_and_test
