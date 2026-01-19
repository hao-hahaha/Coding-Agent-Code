import asyncio
import importlib
import os
import sys
import types
from pathlib import Path

import src.utils.config as cfg


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

    def click(self, *a, **kw):
        pass


def test_run_tests_respects_config(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n",
        encoding="utf-8",
    )
    (repo / "test_calc.py").write_text(
        "import calc\n\n" "def test_add():\n    assert calc.add(1, 2) == 3\n",
        encoding="utf-8",
    )

    env_file = tmp_path / "config.env"
    env_file.write_text(
        f"OPENAI_MODEL=my-model\nMODEL_NAME=my-model\nCLONE_DIR={repo}\n",
        encoding="utf-8",
    )
    cfg.init_config(str(env_file))

    monkeypatch.setitem(
        sys.modules,
        "gradio",
        types.SimpleNamespace(Blocks=DummyBlocks, Markdown=DummyMarkdown, Button=DummyButton),
    )

    agent_args = {}

    class FakeAgent:
        def __init__(self, *a, **kw):
            agent_args.update(kw)

        def __call__(self, *_a, **_k):
            return "ok"

    stub = types.SimpleNamespace(
        Agent=lambda *a, **k: object(),
        OpenAIAgent=FakeAgent,
        Tool=lambda *a, **k: (lambda f: f),
    )
    monkeypatch.setitem(sys.modules, "openai_agents", stub)
    monkeypatch.setitem(
        sys.modules,
        "patcher_core",
        types.SimpleNamespace(
            generate_patch=lambda *_a, **_k: "",
            apply_patch=lambda *_a, **_k: None,
        ),
    )

    sys.modules.pop(
        "alpha_factory_v1.demos.self_healing_repo.agent_selfheal_entrypoint",
        None,
    )
    path = Path(__file__).resolve().parents[1] / "alpha_factory_v1/demos/self_healing_repo/agent_selfheal_entrypoint.py"
    spec = importlib.util.spec_from_file_location(
        "alpha_factory_v1.demos.self_healing_repo.agent_selfheal_entrypoint", path
    )
    entrypoint = importlib.util.module_from_spec(spec)
    entrypoint.apply_patch_and_retst = lambda *_a, **_k: None
    assert spec.loader
    sys.modules[spec.name] = entrypoint
    spec.loader.exec_module(entrypoint)
    monkeypatch.setattr(entrypoint, "CLONE_DIR", str(repo))

    result = asyncio.run(entrypoint.run_tests())
    assert result["rc"] == 0
    assert agent_args.get("model") == "my-model"
