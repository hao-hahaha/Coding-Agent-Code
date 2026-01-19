"""Business bridge offline mode tests."""

# SPDX-License-Identifier: Apache-2.0

import builtins
import importlib
import sys
import types

import requests
import check_env


def test_business_bridge_offline(monkeypatch, capsys):
    # Stub google_adk so adk_bridge imports succeed without network
    dummy = types.ModuleType("google_adk")
    dummy.Agent = object

    class _Router:
        def __init__(self):
            self.app = types.SimpleNamespace(middleware=lambda *_a, **_k: lambda f: f)

        def register_agent(self, _agent):
            pass

    dummy.Router = _Router
    dummy.AgentException = Exception
    monkeypatch.setitem(sys.modules, "google_adk", dummy)

    # Ensure OPENAI_API_KEY unset and openai_agents import fails
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        check_env, "main", lambda *_a, **_k: (_ for _ in ()).throw(requests.exceptions.ConnectionError("offline"))
    )
    sys.modules.pop("openai_agents", None)
    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "openai_agents":
            raise ModuleNotFoundError(name)
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    bridge = importlib.reload(
        importlib.import_module("alpha_factory_v1.demos.alpha_agi_business_v1.openai_agents_bridge")
    )

    assert bridge._require_openai_agents() is False

    bridge.main()
    captured = capsys.readouterr()
    assert "OpenAI Agents SDK not available; bridge inactive." in captured.out
