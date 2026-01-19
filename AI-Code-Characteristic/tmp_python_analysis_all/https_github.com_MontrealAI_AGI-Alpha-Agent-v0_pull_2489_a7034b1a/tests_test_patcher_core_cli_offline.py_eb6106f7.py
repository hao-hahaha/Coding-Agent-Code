# SPDX-License-Identifier: Apache-2.0
import builtins
import runpy
import sys
import types
import pytest

pytest.skip("patcher_core offline CLI test requires networked LLM", allow_module_level=True)

from alpha_factory_v1.demos.self_healing_repo import patcher_core


def test_patcher_cli_offline(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (repo / "test_calc.py").write_text(
        "from calc import add\n\ndef test_add():\n    assert add(1,2)==3\n",
        encoding="utf-8",
    )

    patch = """--- a/calc.py
+++ b/calc.py
@@
-def add(a, b):
-    return a - b
+def add(a, b):
+    return a + b
"""

    # stub openai to satisfy import in llm_client
    monkeypatch.setitem(sys.modules, "openai", types.ModuleType("openai"))

    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "openai_agents":
            raise ModuleNotFoundError(name)
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(sys, "argv", ["patcher_core.py", "--repo", str(repo)])
    monkeypatch.setattr(patcher_core, "generate_patch", lambda *_a, **_k: patch)
    applied = []
    monkeypatch.setattr(
        patcher_core,
        "apply_patch",
        lambda d, repo_path: applied.append((d, repo_path)),
    )

    runpy.run_module("alpha_factory_v1.demos.self_healing_repo.patcher_core", run_name="__main__")
    assert applied
