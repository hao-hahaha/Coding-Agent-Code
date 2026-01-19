# SPDX-License-Identifier: Apache-2.0
# mypy: ignore-errors
import builtins
import importlib
import sys
import types
import unittest

MODULES = [
    "alpha_factory_v1.demos.aiga_meta_evolution.utils",
    "alpha_factory_v1.demos.aiga_meta_evolution.alpha_opportunity_stub",
    "alpha_factory_v1.demos.aiga_meta_evolution.workflow_demo",
]


class TestAigaAgentsImport(unittest.TestCase):
    def test_import_with_agents_only(self, monkeypatch):
        stub = types.ModuleType("agents")
        stub.Agent = object
        stub.AgentRuntime = object
        stub.OpenAIAgent = object

        def _tool(*_a, **_k):
            def _decorator(func):
                return func

            return _decorator

        stub.Tool = _tool

        monkeypatch.setitem(sys.modules, "agents", stub)
        sys.modules.pop("openai_agents", None)

        orig_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "openai_agents":
                raise ModuleNotFoundError(name)
            return orig_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        for mod_name in MODULES:
            mod = importlib.reload(importlib.import_module(mod_name))
            self.assertIs(mod.OpenAIAgent, stub.OpenAIAgent)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
