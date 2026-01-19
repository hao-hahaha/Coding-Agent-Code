# SPDX-License-Identifier: Apache-2.0
import builtins
import runpy
import sys
import types


def test_patcher_cli_offline(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    # stub openai to satisfy import in llm_client
    monkeypatch.setitem(sys.modules, "openai", types.ModuleType("openai"))

    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "openai_agents":
            raise ModuleNotFoundError(name)
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(sys, "argv", ["patcher_core.py", "--repo", str(repo)])

    runpy.run_module(
        "alpha_factory_v1.demos.self_healing_repo.patcher_core", run_name="__main__"
    )
